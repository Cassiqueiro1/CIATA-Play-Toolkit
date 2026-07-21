from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .core import ToolError, save_json
from .release import inspect_release


def build_manifest(
    package: str,
    track: str,
    version_name: str,
    aab: Path,
    mapping: Path | None,
    symbols: Path | None,
    notes: str,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    release = inspect_release(aab, mapping, symbols)
    manifest = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "package": package,
        "track": track,
        "version_name": version_name,
        "release_notes": notes,
        "artifacts": release,
    }
    json_path = output_dir / "manifesto-release.json"
    txt_path = output_dir / "manifesto-release.txt"
    save_json(json_path, manifest)
    lines = [
        "CIATA Play Publisher Toolkit",
        "Manifesto da release",
        "",
        f"Pacote: {package}",
        f"Faixa: {track}",
        f"Nome da versão: {version_name}",
        f"Gerado em UTC: {manifest['generated_at_utc']}",
        "",
        "Notas da versão:",
        notes,
        "",
    ]
    for label, key in (("AAB", "aab"), ("Mapping R8", "mapping"), ("Símbolos nativos", "native_symbols")):
        item = release[key]
        lines.append(label)
        lines.append(f"Presente: {'sim' if item['present'] else 'não'}")
        if item["present"]:
            lines.append(f"Arquivo: {item['path']}")
            lines.append(f"Tamanho em bytes: {item['bytes']}")
            lines.append(f"SHA-256: {item['sha256']}")
        lines.append("")
    txt_path.write_text("\n".join(lines), encoding="utf-8")
    return {"manifest": manifest, "json": str(json_path.resolve()), "text": str(txt_path.resolve())}
