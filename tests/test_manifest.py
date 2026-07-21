from pathlib import Path
from playtool.manifest import build_manifest


def test_build_manifest(tmp_path: Path):
    aab=tmp_path/'app.aab'; aab.write_bytes(b'bundle')
    result=build_manifest('br.org.ciata.app','beta','1.1.0',aab,None,None,'Notas',tmp_path/'out')
    assert Path(result['json']).is_file()
    assert Path(result['text']).is_file()
    assert result['manifest']['artifacts']['aab']['present'] is True
