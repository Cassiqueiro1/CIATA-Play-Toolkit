"""Gerencia assets da ficha pt-BR do Comunica-CIATA na Google Play.

As operações que alteram a ficha permanecem em uma edição não confirmada até
que o comando ``confirmar`` receba a frase de confirmação exata.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence
from urllib.parse import urlsplit, urlunsplit

from PIL import Image, UnidentifiedImageError

try:
    from googleapiclient.errors import HttpError
except ImportError:  # permite que o diagnóstico de dependências seja acionado
    class HttpError(Exception):
        """Fallback para manter o carregamento até criar_servico()."""


PACKAGE_NAME = "br.org.ciata.comunicaciata"
LANGUAGE = "pt-BR"
SCOPE = "https://www.googleapis.com/auth/androidpublisher"
STATE_FILE = Path(__file__).with_name(".play-edit.json")
CONFIRMATION_TEXT = "CONFIRMAR PUBLICACAO"

EXIT_SUCCESS = 0
EXIT_VALIDATION = 1
EXIT_AUTH = 2
EXIT_API = 3
EXIT_CONFIRMATION_CANCELLED = 4

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
ALLOWED_FORMATS = {"PNG", "JPEG"}


@dataclass(frozen=True)
class AssetType:
    display_name: str
    api_name: str


# A API v3 usa "icon" para o recurso exibido pela ferramenta como appIcon.
ASSET_TYPES = (
    AssetType("appIcon", "icon"),
    AssetType("featureGraphic", "featureGraphic"),
    AssetType("phoneScreenshots", "phoneScreenshots"),
)


class ValidationError(Exception):
    """Erro local que deve impedir qualquer chamada à API."""


class AuthenticationError(Exception):
    """Erro ao localizar ou carregar a credencial configurada."""


def confirmar_texto(texto: str) -> bool:
    return texto == CONFIRMATION_TEXT


def _format_dimensions(width: int, height: int) -> str:
    return f"{width} x {height} px"


def _check_extension(path: Path) -> None:
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Arquivo: {path}. Extensão encontrada: {path.suffix or 'sem extensão'}. "
            "Regra esperada: PNG ou JPEG."
        )


def _open_image(path: Path) -> tuple[int, int, str, str, Any]:
    if not path.is_file():
        raise ValidationError(
            f"Arquivo: {path}. Regra esperada: o arquivo deve existir e ser legível."
        )
    _check_extension(path)
    try:
        image = Image.open(path)
        image.verify()
        image = Image.open(path)
        image.load()
    except (OSError, UnidentifiedImageError) as error:
        raise ValidationError(
            f"Arquivo: {path}. Regra esperada: imagem PNG ou JPEG válida."
        ) from error
    image_format = (image.format or "").upper()
    if image_format not in ALLOWED_FORMATS:
        image.close()
        raise ValidationError(
            f"Arquivo: {path}. Formato encontrado: {image_format or 'desconhecido'}. "
            "Regra esperada: PNG ou JPEG."
        )
    expected_format = "PNG" if path.suffix.lower() == ".png" else "JPEG"
    if image_format != expected_format:
        image.close()
        raise ValidationError(
            f"Arquivo: {path}. Formato encontrado: {image_format}. "
            f"Regra esperada para a extensão {path.suffix.lower()}: {expected_format}."
        )
    width, height = image.size
    return width, height, image_format, image.mode, image


def _check_size(path: Path, maximum_bytes: int, label: str) -> None:
    size = path.stat().st_size
    if size > maximum_bytes:
        raise ValidationError(
            f"Arquivo: {path}. Tamanho encontrado: {size} bytes. "
            f"Regra esperada: {label}."
        )


def validar_icone(path_value: str | Path) -> Path:
    path = Path(path_value).expanduser()
    width, height, _, _, image = _open_image(path)
    image.close()
    if (width, height) != (512, 512):
        raise ValidationError(
            f"Arquivo: {path}. Dimensão encontrada: {_format_dimensions(width, height)}. "
            "Dimensão esperada: 512 x 512 px."
        )
    _check_size(path, 1 * 1024 * 1024, "até 1 MB")
    return path.resolve()


def validar_recurso_grafico(path_value: str | Path) -> Path:
    path = Path(path_value).expanduser()
    width, height, _, _, image = _open_image(path)
    image.close()
    if (width, height) != (1024, 500):
        raise ValidationError(
            f"Arquivo: {path}. Dimensão encontrada: {_format_dimensions(width, height)}. "
            "Dimensão esperada: 1024 x 500 px."
        )
    _check_size(path, 15 * 1024 * 1024, "até 15 MB")
    return path.resolve()


def _has_problematic_transparency(image: Any) -> bool:
    if image.mode in {"RGBA", "LA"}:
        alpha = image.getchannel("A")
        return alpha.getextrema()[0] < 255
    if image.mode == "P" and "transparency" in image.info:
        converted = image.convert("RGBA")
        try:
            return converted.getchannel("A").getextrema()[0] < 255
        finally:
            converted.close()
    return False


def validar_captura(path_value: str | Path) -> Path:
    path = Path(path_value).expanduser()
    width, height, _, _, image = _open_image(path)
    try:
        if _has_problematic_transparency(image):
            raise ValidationError(
                f"Arquivo: {path}. Regra esperada: captura sem pixels transparentes."
            )
    finally:
        image.close()
    smaller = min(width, height)
    larger = max(width, height)
    if smaller < 320 or larger > 3840:
        raise ValidationError(
            f"Arquivo: {path}. Dimensão encontrada: {_format_dimensions(width, height)}. "
            "Regra esperada: cada dimensão entre 320 e 3840 px."
        )
    if larger > 2 * smaller:
        raise ValidationError(
            f"Arquivo: {path}. Dimensão encontrada: {_format_dimensions(width, height)}. "
            "Regra esperada: a maior dimensão não pode exceder duas vezes a menor."
        )
    if width == height:
        raise ValidationError(
            f"Arquivo: {path}. Dimensão encontrada: {_format_dimensions(width, height)}. "
            "Regra esperada: orientação retrato ou paisagem, não quadrada."
        )
    return path.resolve()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validar_capturas(path_values: Sequence[str | Path]) -> list[Path]:
    if len(path_values) < 2:
        raise ValidationError(
            f"Quantidade de capturas encontrada: {len(path_values)}. "
            "Regra esperada: ao menos duas capturas de telefone."
        )
    if len(path_values) > 8:
        raise ValidationError(
            f"Quantidade de capturas encontrada: {len(path_values)}. "
            "Regra esperada: no máximo oito capturas de telefone."
        )
    paths = [validar_captura(path) for path in path_values]
    hashes = [_sha256(path) for path in paths]
    if len(set(hashes)) != len(hashes):
        raise ValidationError(
            "Arquivos de captura repetidos encontrados. "
            "Regra esperada: todas as capturas devem ser diferentes."
        )
    return paths


def validar_assets(
    icon_value: str | Path,
    feature_value: str | Path,
    screenshot_values: Sequence[str | Path],
) -> tuple[Path, Path, list[Path]]:
    icon = validar_icone(icon_value)
    feature = validar_recurso_grafico(feature_value)
    screenshots = validar_capturas(screenshot_values)
    return icon, feature, screenshots


def _load_credentials() -> Any:
    credential_value = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not credential_value:
        raise AuthenticationError(
            "A variável GOOGLE_APPLICATION_CREDENTIALS não está definida."
        )
    credential_path = Path(credential_value).expanduser()
    if not credential_path.is_file():
        raise AuthenticationError(
            "O arquivo indicado por GOOGLE_APPLICATION_CREDENTIALS não existe."
        )
    try:
        from google.oauth2 import service_account

        return service_account.Credentials.from_service_account_file(
            str(credential_path), scopes=[SCOPE]
        )
    except (ImportError, OSError, ValueError) as error:
        raise AuthenticationError(
            "Não foi possível carregar a credencial da conta de serviço."
        ) from error


def criar_servico() -> Any:
    credentials = _load_credentials()
    try:
        from googleapiclient.discovery import build

        return build(
            "androidpublisher",
            "v3",
            credentials=credentials,
            cache_discovery=False,
        )
    except ImportError as error:
        raise AuthenticationError(
            "Dependências ausentes. Instale o arquivo requirements.txt."
        ) from error


def _create_edit(service: Any) -> dict[str, Any]:
    return service.edits().insert(packageName=PACKAGE_NAME, body={}).execute()


def _delete_edit(service: Any, edit_id: str) -> None:
    service.edits().delete(packageName=PACKAGE_NAME, editId=edit_id).execute()


def _list_images(service: Any, edit_id: str, asset_type: AssetType) -> list[dict[str, Any]]:
    response = (
        service.edits()
        .images()
        .list(
            packageName=PACKAGE_NAME,
            editId=edit_id,
            language=LANGUAGE,
            imageType=asset_type.api_name,
        )
        .execute()
    )
    return response.get("images", [])


def _print_assets(service: Any, edit_id: str) -> None:
    for asset_type in ASSET_TYPES:
        images = _list_images(service, edit_id, asset_type)
        print(f"Tipo: {asset_type.display_name}")
        print(f"Quantidade total: {len(images)}")
        for image in images:
            print(f"ID: {image.get('id', 'não retornado')}")
            if image.get("url"):
                print(f"URL: {image['url']}")


def _save_state(edit: dict[str, Any]) -> None:
    state = {
        "packageName": PACKAGE_NAME,
        "language": LANGUAGE,
        "editId": edit["id"],
        "expiryTimeSeconds": edit.get("expiryTimeSeconds"),
    }
    temporary = STATE_FILE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(STATE_FILE)


def _load_state() -> dict[str, Any]:
    if not STATE_FILE.is_file():
        raise ValidationError(
            "Nenhuma edição salva foi encontrada. Execute substituir primeiro."
        )
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValidationError(
            "O arquivo .play-edit.json está inválido ou não pode ser lido."
        ) from error
    if (
        state.get("packageName") != PACKAGE_NAME
        or state.get("language") != LANGUAGE
        or not isinstance(state.get("editId"), str)
        or not state["editId"]
    ):
        raise ValidationError(
            "O arquivo .play-edit.json não pertence ao pacote e idioma esperados."
        )
    return state


def _mime_type(path: Path) -> str:
    return "image/png" if path.suffix.lower() == ".png" else "image/jpeg"


def _upload(service: Any, edit_id: str, asset_type: AssetType, path: Path) -> None:
    from googleapiclient.http import MediaFileUpload

    media = MediaFileUpload(str(path), mimetype=_mime_type(path), resumable=False)
    (
        service.edits()
        .images()
        .upload(
            packageName=PACKAGE_NAME,
            editId=edit_id,
            language=LANGUAGE,
            imageType=asset_type.api_name,
            media_body=media,
        )
        .execute()
    )


def command_verificar_acesso(_: argparse.Namespace) -> int:
    service = criar_servico()
    edit = _create_edit(service)
    try:
        pass
    finally:
        _delete_edit(service, edit["id"])
    print("Acesso à Google Play Developer API verificado com sucesso.")
    return EXIT_SUCCESS


def command_listar(_: argparse.Namespace) -> int:
    service = criar_servico()
    edit = _create_edit(service)
    try:
        _print_assets(service, edit["id"])
    finally:
        _delete_edit(service, edit["id"])
    return EXIT_SUCCESS


def command_substituir(args: argparse.Namespace) -> int:
    icon, feature, screenshots = validar_assets(
        args.icone, args.recurso_grafico, args.capturas
    )
    print("Todos os arquivos foram validados localmente.")
    print("A autenticidade do conteúdo das capturas deve ser conferida por uma pessoa antes da confirmação.")
    service = criar_servico()
    edit = _create_edit(service)
    edit_id = edit["id"]
    _save_state(edit)
    for asset_type in ASSET_TYPES:
        (
            service.edits()
            .images()
            .deleteall(
                packageName=PACKAGE_NAME,
                editId=edit_id,
                language=LANGUAGE,
                imageType=asset_type.api_name,
            )
            .execute()
        )
        print(f"Recursos antigos removidos da edição: {asset_type.display_name}")
    _upload(service, edit_id, ASSET_TYPES[0], icon)
    print(f"Arquivo enviado para appIcon: {icon}")
    _upload(service, edit_id, ASSET_TYPES[1], feature)
    print(f"Arquivo enviado para featureGraphic: {feature}")
    for screenshot in screenshots:
        _upload(service, edit_id, ASSET_TYPES[2], screenshot)
        print(f"Arquivo enviado para phoneScreenshots: {screenshot}")
    print("Resumo da edição não confirmada:")
    _print_assets(service, edit_id)
    print(f"Edição salva localmente em: {STATE_FILE}")
    print("A edição não foi confirmada.")
    return EXIT_SUCCESS


def command_validar(_: argparse.Namespace) -> int:
    state = _load_state()
    service = criar_servico()
    response = service.edits().validate(
        packageName=PACKAGE_NAME, editId=state["editId"]
    ).execute()
    # Normalmente a API sinaliza falhas lançando HttpError. Alguns proxies e
    # versões do cliente, porém, devolvem um corpo de validação com erros sem
    # lançar exceção; trate esse formato explicitamente para não anunciar
    # sucesso quando a edição ainda está inválida.
    response_errors = []
    if isinstance(response, dict):
        for key in ("errors", "validationErrors"):
            values = response.get(key, [])
            if isinstance(values, list):
                response_errors.extend(values)
    if response_errors:
        print("Erros encontrados na validação oficial:", file=sys.stderr)
        for item in response_errors:
            if isinstance(item, dict):
                message = item.get("message") or item.get("description") or str(item)
            else:
                message = str(item)
            print(f"Erro: {message}", file=sys.stderr)
        return EXIT_API
    print("A validação oficial da edição foi concluída com sucesso.")
    print("A edição não foi confirmada.")
    return EXIT_SUCCESS


def command_confirmar(_: argparse.Namespace) -> int:
    state = _load_state()
    service = criar_servico()
    print("Resumo da edição que será confirmada:")
    _print_assets(service, state["editId"])
    print(f"Para confirmar, digite exatamente: {CONFIRMATION_TEXT}")
    response = input()
    if not confirmar_texto(response):
        print("Confirmação cancelada. A edição permanece aberta e não confirmada.")
        return EXIT_CONFIRMATION_CANCELLED
    service.edits().commit(
        packageName=PACKAGE_NAME, editId=state["editId"]
    ).execute()
    STATE_FILE.unlink(missing_ok=True)
    print("Edição confirmada com sucesso.")
    return EXIT_SUCCESS


def _safe_uri(uri: Any) -> str:
    """Remove query e fragmento da URI antes de mostrá-la no terminal."""
    if not uri:
        return "(não retornada)"
    try:
        parsed = urlsplit(str(uri))
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    except ValueError:
        return "(URI inválida, omitida por segurança)"


_SENSITIVE_KEYS = {
    "access_token",
    "authorization",
    "client_email",
    "private_key",
    "refresh_token",
    "token",
}


def _redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if str(key).lower() in _SENSITIVE_KEYS else _redact_sensitive(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_sensitive(item) for item in value]
    return value


def _http_category(status: int | None) -> str:
    categories = {
        400: "Requisição inválida",
        401: "Falha de autenticação",
        403: "Permissão insuficiente",
        404: "Pacote ou app não encontrado",
        409: "Conflito",
    }
    if status in categories:
        return categories[status]
    if status is not None and 500 <= status <= 599:
        return "Falha temporária do Google"
    return "Erro HTTP da Google Play Developer API"


def _http_error_lines(error: Exception) -> Iterable[str]:
    response = getattr(error, "resp", None)
    status = getattr(response, "status", None)
    reason = getattr(response, "reason", None) or "(não retornada)"
    yield f"Código HTTP: {status if status is not None else '(não retornado)'}"
    yield f"Categoria: {_http_category(status)}"
    yield f"Razão HTTP: {reason}"
    yield f"URI chamada: {_safe_uri(getattr(error, "uri", None))}"

    raw_content = getattr(error, "content", b"")
    if isinstance(raw_content, bytes):
        content = raw_content.decode("utf-8", errors="replace")
    else:
        content = str(raw_content) if raw_content else ""
    try:
        payload = json.loads(content) if content else None
    except json.JSONDecodeError:
        payload = None

    if payload is None:
        yield "Conteúdo retornado pela API (texto bruto):"
        yield content or "(vazio)"
        return

    safe_payload = _redact_sensitive(payload)
    yield "Conteúdo JSON retornado pela API:"
    yield json.dumps(safe_payload, ensure_ascii=False, indent=2)
    api_error = payload.get("error", {}) if isinstance(payload, dict) else {}
    if not isinstance(api_error, dict):
        return
    if api_error.get("message") is not None:
        yield f"error.message: {api_error['message']}"
    if api_error.get("status") is not None:
        yield f"error.status: {api_error['status']}"
    details = api_error.get("errors", [])
    if isinstance(details, list):
        for index, detail in enumerate(details, start=1):
            if not isinstance(detail, dict):
                yield f"error.errors[{index}]: {detail}"
                continue
            yield f"error.errors[{index}].reason: {detail.get('reason', '(não retornado)')}"
            yield f"error.errors[{index}].message: {detail.get('message', '(não retornado)')}"
            yield f"error.errors[{index}].domain: {detail.get('domain', '(não retornado)')}"


def _status_code(error: Exception) -> int | None:
    response = getattr(error, "resp", None)
    return getattr(response, "status", None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gerencia assets pt-BR do Comunica-CIATA na Google Play."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify = subparsers.add_parser("verificar-acesso", help="Testa o acesso sem confirmar alterações.")
    verify.set_defaults(handler=command_verificar_acesso)
    list_parser = subparsers.add_parser("listar", help="Lista os assets atuais.")
    list_parser.set_defaults(handler=command_listar)
    replace = subparsers.add_parser("substituir", help="Substitui assets em uma edição não confirmada.")
    replace.add_argument("--icone", required=True)
    replace.add_argument("--recurso-grafico", required=True)
    replace.add_argument("--captura", dest="capturas", action="append", required=True)
    replace.set_defaults(handler=command_substituir)
    validate = subparsers.add_parser("validar", help="Valida oficialmente a edição salva.")
    validate.set_defaults(handler=command_validar)
    confirm = subparsers.add_parser("confirmar", help="Confirma a edição após autorização textual.")
    confirm.set_defaults(handler=command_confirmar)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        return int(args.handler(args))
    except ValidationError as error:
        print(f"Erro de validação: {error}", file=sys.stderr)
        return EXIT_VALIDATION
    except AuthenticationError as error:
        print(f"Erro de autenticação: {error}", file=sys.stderr)
        return EXIT_AUTH
    except (EOFError, KeyboardInterrupt):
        print("Confirmação cancelada pelo usuário.", file=sys.stderr)
        return EXIT_CONFIRMATION_CANCELLED
    except HttpError as error:
        status = _status_code(error)
        for line in _http_error_lines(error):
            print(line, file=sys.stderr)
        if status in {401, 403}:
            return EXIT_AUTH
        return EXIT_API
    except Exception as error:
        status = _status_code(error)
        print("A Google Play Developer API retornou um erro sem detalhes em texto.", file=sys.stderr)
        if status in {401, 403}:
            return EXIT_AUTH
        return EXIT_API


if __name__ == "__main__":
    raise SystemExit(main())
