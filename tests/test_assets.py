from pathlib import Path
from PIL import Image
from playtool.assets import convert, validate_kind

def test_icon_conversion(tmp_path: Path):
    src=tmp_path/'src.png'; out=tmp_path/'icon.png'
    Image.new('RGBA',(900,400),(255,0,0,128)).save(src)
    convert(src,out,'icon','contain')
    result=validate_kind(out,'icon')
    assert result['valid'] and (result['width'],result['height'])==(512,512)

def test_custom_jpeg(tmp_path: Path):
    src=tmp_path/'src.png'; out=tmp_path/'custom.jpg'
    Image.new('RGB',(300,300),'white').save(src)
    info=convert(src,out,'custom-500')
    assert info['format']=='JPEG' and (info['width'],info['height'])==(500,500)
