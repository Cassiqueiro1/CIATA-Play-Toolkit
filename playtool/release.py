from __future__ import annotations
from pathlib import Path
from .core import ToolError, sha256

def inspect_release(aab: Path, mapping: Path|None=None, symbols: Path|None=None) -> dict:
    if not aab.is_file() or aab.suffix.lower() != '.aab': raise ToolError(f"AAB inválido ou ausente: {aab}")
    def item(p: Path|None):
        if p is None: return {'present':False}
        if not p.is_file(): raise ToolError(f"Artefato não encontrado: {p}")
        return {'present':True,'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha256(p)}
    return {'aab':item(aab),'mapping':item(mapping),'native_symbols':item(symbols)}
