from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

from .assets import validate_kind
from .core import ToolError, sha256
from .googleplay import service

IMAGE_TYPES = {
    "icon": "icon",
    "feature": "featureGraphic",
    "screenshot": "phoneScreenshots",
}

TEXT_LIMITS = {
    "title": 30,
    "short_description": 80,
    "full_description": 4000,
}


def _validate_files(kind: str, files: Iterable[Path]) -> list[Path]:
    paths = [Path(p) for p in files]
    if kind in {"icon", "feature"} and len(paths) != 1:
        raise ToolError(f"O tipo {kind} exige exatamente um arquivo.")
    if kind == "screenshot" and not 2 <= len(paths) <= 8:
        raise ToolError("Capturas de telefone: informe entre 2 e 8 arquivos.")
    seen: set[str] = set()
    for path in paths:
        result = validate_kind(path, kind)
        if not result["valid"]:
            raise ToolError(f"Imagem reprovada: {path}. " + "; ".join(result["errors"]))
        digest = result["sha256"]
        if digest in seen:
            raise ToolError(f"Imagem duplicada detectada: {path}")
        seen.add(digest)
    return paths


def _read_text(value: str | None, file: Path | None, field: str, required: bool = True) -> str | None:
    if value is not None and file is not None:
        raise ToolError(f"Informe {field} diretamente ou por arquivo, nunca pelos dois meios.")
    if file is not None:
        if not file.is_file():
            raise ToolError(f"Arquivo de {field} não encontrado: {file}")
        value = file.read_text(encoding="utf-8-sig")
    if value is not None:
        value = value.strip()
    if required and not value:
        raise ToolError(f"O campo {field} é obrigatório.")
    return value or None


def _validate_youtube_url(video: str | None) -> str | None:
    if not video:
        return None
    parsed = urlparse(video.strip())
    host = (parsed.hostname or "").lower()
    allowed = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
    if parsed.scheme != "https" or host not in allowed:
        raise ToolError("O vídeo deve usar uma URL HTTPS válida do YouTube.")
    return video.strip()


def validate_listing_text(title: str, short_description: str, full_description: str, video: str | None = None) -> dict[str, Any]:
    values = {
        "title": title.strip(),
        "short_description": short_description.strip(),
        "full_description": full_description.strip(),
    }
    errors: list[str] = []
    for field, limit in TEXT_LIMITS.items():
        length = len(values[field])
        if length == 0:
            errors.append(f"{field} está vazio.")
        elif length > limit:
            errors.append(f"{field} possui {length} caracteres; o limite é {limit}.")
    checked_video = None
    try:
        checked_video = _validate_youtube_url(video)
    except ToolError as exc:
        errors.append(str(exc))
    return {
        "valid": not errors,
        "errors": errors,
        "character_counts": {field: len(text) for field, text in values.items()},
        "limits": TEXT_LIMITS,
        "video": checked_video,
    }


def list_images(package: str, edit_id: str, language: str, kind: str) -> dict[str, Any]:
    if kind not in IMAGE_TYPES:
        raise ToolError(f"Tipo de imagem desconhecido: {kind}")
    response = service().edits().images().list(
        packageName=package,
        editId=edit_id,
        language=language,
        imageType=IMAGE_TYPES[kind],
    ).execute()
    images = response.get("images", [])
    return {"kind": kind, "language": language, "count": len(images), "images": images}


def replace_images(package: str, edit_id: str, language: str, kind: str, files: Iterable[Path]) -> dict[str, Any]:
    if kind not in IMAGE_TYPES:
        raise ToolError(f"Tipo de imagem desconhecido: {kind}")
    from googleapiclient.http import MediaFileUpload
    paths = _validate_files(kind, files)
    images_api = service().edits().images()
    image_type = IMAGE_TYPES[kind]
    deleted = images_api.deleteall(
        packageName=package,
        editId=edit_id,
        language=language,
        imageType=image_type,
    ).execute().get("deleted", [])
    uploaded = []
    for path in paths:
        mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
        response = images_api.upload(
            packageName=package,
            editId=edit_id,
            language=language,
            imageType=image_type,
            media_body=MediaFileUpload(str(path), mimetype=mime, resumable=False),
        ).execute()
        image = response.get("image", response)
        uploaded.append({"path": str(path.resolve()), "local_sha256": sha256(path), "remote": image})
    return {"kind": kind, "language": language, "deleted_count": len(deleted), "uploaded_count": len(uploaded), "uploaded": uploaded}


def get_listing_text(package: str, edit_id: str, language: str) -> dict[str, Any]:
    result = service().edits().listings().get(
        packageName=package,
        editId=edit_id,
        language=language,
    ).execute()
    return {
        "language": result.get("language", language),
        "title": result.get("title", ""),
        "short_description": result.get("shortDescription", ""),
        "full_description": result.get("fullDescription", ""),
        "video": result.get("video", ""),
    }


def update_listing_text(
    package: str,
    edit_id: str,
    language: str,
    title: str | None = None,
    title_file: Path | None = None,
    short_description: str | None = None,
    short_file: Path | None = None,
    full_description: str | None = None,
    full_file: Path | None = None,
    video: str | None = None,
    clear_video: bool = False,
) -> dict[str, Any]:
    title_value = _read_text(title, title_file, "título")
    short_value = _read_text(short_description, short_file, "resumo")
    full_value = _read_text(full_description, full_file, "descrição completa")
    if clear_video and video:
        raise ToolError("Use --video ou --clear-video, não os dois.")
    video_value = "" if clear_video else _validate_youtube_url(video)
    validation = validate_listing_text(title_value or "", short_value or "", full_value or "", video_value)
    if not validation["valid"]:
        raise ToolError("Textos da ficha reprovados: " + "; ".join(validation["errors"]))
    body = {
        "language": language,
        "title": title_value,
        "shortDescription": short_value,
        "fullDescription": full_value,
        "video": video_value or "",
    }
    result = service().edits().listings().update(
        packageName=package,
        editId=edit_id,
        language=language,
        body=body,
    ).execute()
    return {
        "language": language,
        "title": result.get("title", title_value),
        "short_description": result.get("shortDescription", short_value),
        "full_description": result.get("fullDescription", full_value),
        "video": result.get("video", video_value or ""),
        "character_counts": validation["character_counts"],
    }


def get_app_details(package: str, edit_id: str) -> dict[str, Any]:
    result = service().edits().details().get(packageName=package, editId=edit_id).execute()
    return {
        "default_language": result.get("defaultLanguage", ""),
        "contact_website": result.get("contactWebsite", ""),
        "contact_email": result.get("contactEmail", ""),
        "contact_phone": result.get("contactPhone", ""),
    }


def update_app_details(
    package: str,
    edit_id: str,
    default_language: str,
    contact_website: str,
    contact_email: str,
    contact_phone: str = "",
) -> dict[str, Any]:
    website = urlparse(contact_website)
    if website.scheme != "https" or not website.netloc:
        raise ToolError("O site de contato deve ser uma URL HTTPS válida.")
    if "@" not in contact_email or contact_email.startswith("@") or contact_email.endswith("@"):
        raise ToolError("O e-mail de contato parece inválido.")
    body = {
        "defaultLanguage": default_language,
        "contactWebsite": contact_website,
        "contactEmail": contact_email,
        "contactPhone": contact_phone,
    }
    result = service().edits().details().update(
        packageName=package,
        editId=edit_id,
        body=body,
    ).execute()
    return {
        "default_language": result.get("defaultLanguage", default_language),
        "contact_website": result.get("contactWebsite", contact_website),
        "contact_email": result.get("contactEmail", contact_email),
        "contact_phone": result.get("contactPhone", contact_phone),
    }
