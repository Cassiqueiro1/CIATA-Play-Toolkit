from pathlib import Path

from PIL import Image

from playtool.doctor import DOCTOR_CHECKS, format_doctor_report, run_doctor


def test_doctor_check_ids_are_unique():
    ids = [item.id for item in DOCTOR_CHECKS]
    assert len(ids) == len(set(ids))


def test_doctor_reports_missing_config_without_ascii_decoration(tmp_path: Path):
    report = run_doctor(tmp_path / 'playtool.yaml', project_dir=tmp_path)
    assert report['ready'] is False
    assert report['summary']['bloqueio'] >= 1
    text = format_doctor_report(report)
    for forbidden in ('====', '----', '++++', '████'):
        assert forbidden not in text


def test_doctor_fix_creates_safe_config(tmp_path: Path):
    config = tmp_path / 'playtool.yaml'
    report = run_doctor(config, project_dir=tmp_path, fix=True)
    assert config.is_file()
    item = next(x for x in report['results'] if x['check_id'] == 'config-file')
    assert item['fixed'] is True


def test_doctor_validates_complete_local_listing(tmp_path: Path, monkeypatch):
    aab = tmp_path / 'app.aab'; aab.write_bytes(b'bundle')
    mapping = tmp_path / 'mapping.txt'; mapping.write_text('map', encoding='utf-8')
    symbols = tmp_path / 'symbols.zip'; symbols.write_bytes(b'zip')
    title = tmp_path / 'title.txt'; title.write_text('Aplicativo', encoding='utf-8')
    short = tmp_path / 'short.txt'; short.write_text('Resumo acessível', encoding='utf-8')
    full = tmp_path / 'full.txt'; full.write_text('Descrição completa.', encoding='utf-8')
    icon = tmp_path / 'icon.png'; Image.new('RGB',(512,512)).save(icon)
    feature = tmp_path / 'feature.png'; Image.new('RGB',(1024,500)).save(feature)
    shot = tmp_path / 'shot.png'; Image.new('RGB',(1080,1920)).save(shot)
    config = tmp_path / 'playtool.yaml'
    config.write_text(f'''package: br.org.ciata.teste
default_track: beta
language: pt-BR
review_url: https://example.org/review
aab_path: {aab}
mapping_path: {mapping}
symbols_path: {symbols}
title_file: {title}
short_file: {short}
full_file: {full}
icon_path: {icon}
feature_path: {feature}
screenshot_paths:
  - {shot}
website: https://example.org
support_email: suporte@example.org
''', encoding='utf-8')
    report = run_doctor(config, project_dir=tmp_path)
    assert report['summary']['erro'] == 0
    assert report['summary']['bloqueio'] == 0
