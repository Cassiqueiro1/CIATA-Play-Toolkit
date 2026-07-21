from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError
from .core import ToolError, sha256

@dataclass(frozen=True)
class Preset:
    name: str; width: int; height: int; format: str
PRESETS = {
    'icon': Preset('Ícone da Play Store', 512, 512, 'PNG'),
    'feature': Preset('Recurso gráfico', 1024, 500, 'PNG'),
    'custom-500': Preset('Personalizado 500 x 500', 500, 500, 'JPEG'),
    'custom-1024x800': Preset('Personalizado 1024 x 800', 1024, 800, 'JPEG'),
}

def inspect(path: Path) -> dict:
    if not path.is_file(): raise ToolError(f"Imagem não encontrada: {path}")
    try:
        with Image.open(path) as im:
            im.load()
            return {'path': str(path.resolve()), 'width': im.width, 'height': im.height,
                    'format': (im.format or 'desconhecido').upper(), 'mode': im.mode,
                    'bytes': path.stat().st_size, 'sha256': sha256(path)}
    except (OSError, UnidentifiedImageError) as e:
        raise ToolError(f"Arquivo de imagem inválido: {path}") from e

def convert(source: Path, output: Path, preset: str, mode: str='contain', quality: int=92,
            background: str='white') -> dict:
    if preset not in PRESETS: raise ToolError(f"Preset desconhecido: {preset}")
    p = PRESETS[preset]
    if mode not in {'contain','cover','stretch'}: raise ToolError('Modo deve ser contain, cover ou stretch.')
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with Image.open(source) as src:
            src.load(); im = src.convert('RGBA')
            if mode == 'contain':
                fitted = ImageOps.contain(im, (p.width,p.height), Image.Resampling.LANCZOS)
                canvas = Image.new('RGBA',(p.width,p.height),background)
                canvas.alpha_composite(fitted,((p.width-fitted.width)//2,(p.height-fitted.height)//2)); result=canvas
            elif mode == 'cover':
                result = ImageOps.fit(im,(p.width,p.height),Image.Resampling.LANCZOS,centering=(0.5,0.5))
            else:
                result = im.resize((p.width,p.height),Image.Resampling.LANCZOS)
            if p.format == 'JPEG':
                result.convert('RGB').save(output,'JPEG',quality=quality,optimize=True)
            else:
                result.save(output,'PNG',optimize=True)
    except (OSError, UnidentifiedImageError) as e:
        raise ToolError(f"Não foi possível converter: {source}") from e
    return inspect(output)

def validate_kind(path: Path, kind: str) -> dict:
    info=inspect(path); errors=[]
    if kind == 'icon':
        if (info['width'],info['height']) != (512,512): errors.append('dimensão esperada: 512 x 512')
        if info['format'] != 'PNG': errors.append('formato esperado: PNG')
        if info['bytes'] > 1024*1024: errors.append('tamanho máximo: 1 MB')
    elif kind == 'feature':
        if (info['width'],info['height']) != (1024,500): errors.append('dimensão esperada: 1024 x 500')
        if info['format'] not in {'PNG','JPEG'}: errors.append('formato esperado: PNG ou JPEG')
        if info['bytes'] > 15*1024*1024: errors.append('tamanho máximo: 15 MB')
    elif kind == 'screenshot':
        small,large=min(info['width'],info['height']),max(info['width'],info['height'])
        if small < 320 or large > 3840: errors.append('dimensões devem ficar entre 320 e 3840 pixels')
        if large > 2*small: errors.append('a maior dimensão não pode exceder duas vezes a menor')
    else: raise ToolError(f"Tipo desconhecido: {kind}")
    return {**info,'kind':kind,'valid':not errors,'errors':errors}
