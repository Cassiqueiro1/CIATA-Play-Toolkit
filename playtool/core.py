from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any
import yaml

class ToolError(Exception):
    pass

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def load_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ToolError(f"Configuração não encontrada: {path}. Execute 'playtool init'.")
    data = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    for key in ('package', 'default_track', 'language'):
        if not data.get(key):
            raise ToolError(f"Campo obrigatório ausente em {path}: {key}")
    return data

def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)
