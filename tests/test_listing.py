from pathlib import Path
import pytest
from PIL import Image
from playtool.listing import _validate_files
from playtool.core import ToolError


def save(path: Path, size: tuple[int,int]):
    Image.new('RGB',size).save(path)


def test_validate_icon(tmp_path: Path):
    p=tmp_path/'icon.png'; save(p,(512,512))
    assert _validate_files('icon',[p]) == [p]


def test_screenshot_count(tmp_path: Path):
    p=tmp_path/'one.png'; save(p,(1080,1920))
    with pytest.raises(ToolError):
        _validate_files('screenshot',[p])
