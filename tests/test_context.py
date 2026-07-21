from pathlib import Path

from playtool.context import PublishingContext


def test_context_tracks_origin_and_exports_without_secret(tmp_path: Path):
    context = PublishingContext(project_dir=str(tmp_path))
    context.set('package', 'br.org.ciata.teste', 'config')
    context.set_credentials_path(str(tmp_path / 'service.json'), 'environment')
    exported = context.to_public_dict()
    assert exported['package'] == 'br.org.ciata.teste'
    assert exported['origins']['package'] == 'config'
    assert exported['credentials_configured'] is True
    assert '_credentials_path' not in exported


def test_context_invalidates_missing_files(tmp_path: Path):
    existing = tmp_path / 'app.aab'
    existing.write_bytes(b'aab')
    context = PublishingContext(aab_path=str(existing), mapping_path=str(tmp_path / 'missing.txt'))
    invalidated = context.invalidate_missing_files()
    assert context.aab_path is not None
    assert context.mapping_path is None
    assert invalidated == ['mapping_path']
