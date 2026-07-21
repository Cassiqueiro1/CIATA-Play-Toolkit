from pathlib import Path

from playtool.tutorial import TutorialIO, TutorialRunner, TutorialState


def test_confirm_accepts_short_and_full_answers():
    answers = iter(['S', 'não'])
    io = TutorialIO(input_fn=lambda _: next(answers), output_fn=lambda _: None)
    assert io.confirm('Continuar?') is True
    assert io.confirm('Continuar?', True) is False


def test_tutorial_dry_run_json_flow(tmp_path: Path):
    config = tmp_path / 'playtool.yaml'
    config.write_text('package: br.org.ciata.teste\ndefault_track: beta\nlanguage: pt-BR\n', encoding='utf-8')
    state_path = tmp_path / '.playtool-tutorial.json'
    state = TutorialState(config_path=str(config), dry_run=True)
    io = TutorialIO(input_fn=lambda _: '', output_fn=lambda _: None)
    result = TutorialRunner(state, state_path, io, json_mode=True).run()
    assert result['completed'] is True
    assert result['dry_run'] is True
    assert len(result['events']) == 15
    assert state_path.is_file()


def test_output_has_no_decorative_progress_characters(tmp_path: Path):
    config = tmp_path / 'playtool.yaml'
    config.write_text('package: br.org.ciata.teste\ndefault_track: beta\nlanguage: pt-BR\n', encoding='utf-8')
    output: list[str] = []
    state = TutorialState(config_path=str(config), dry_run=True)
    io = TutorialIO(input_fn=lambda _: '', output_fn=output.append)
    TutorialRunner(state, tmp_path / 'state.json', io, json_mode=False).run()
    text = '\n'.join(output)
    for forbidden in ('████', '====', '----', '++++'):
        assert forbidden not in text
    assert 'Etapa 1 de 15' in text


def test_execute_and_dry_run_are_mutually_exclusive(tmp_path: Path):
    from playtool.core import ToolError
    from playtool.tutorial import run_tutorial

    config = tmp_path / 'playtool.yaml'
    config.write_text('package: br.org.ciata.teste\ndefault_track: beta\nlanguage: pt-BR\n', encoding='utf-8')
    try:
        run_tutorial(
            resume=False,
            dry_run=True,
            execute_remote=True,
            json_mode=True,
            state_path=tmp_path / 'state.json',
            config_path=config,
        )
    except ToolError as exc:
        assert 'nunca os dois' in str(exc)
    else:
        raise AssertionError('Era esperado ToolError')


def test_remote_draft_flow_never_commits(tmp_path: Path, monkeypatch):
    import playtool.tutorial as tutorial

    config = tmp_path / 'playtool.yaml'
    config.write_text('package: br.org.ciata.teste\ndefault_track: beta\nlanguage: pt-BR\n', encoding='utf-8')
    credentials = tmp_path / 'service.json'
    credentials.write_text('{}', encoding='utf-8')
    aab = tmp_path / 'app.aab'
    aab.write_bytes(b'aab')
    title = tmp_path / 'title.txt'; title.write_text('Aplicativo', encoding='utf-8')
    short = tmp_path / 'short.txt'; short.write_text('Resumo acessível', encoding='utf-8')
    full = tmp_path / 'full.txt'; full.write_text('Descrição completa do aplicativo.', encoding='utf-8')

    calls: list[str] = []
    monkeypatch.setattr(tutorial, 'remote_inventory', lambda package: {'highest_version_code': 10})
    monkeypatch.setattr(tutorial, 'build_manifest', lambda *args, **kwargs: {'text': 'manifesto.txt', 'json': 'manifesto.json'})
    monkeypatch.setattr(tutorial, 'prepare', lambda *args, **kwargs: {'edit_id': 'edit-1', 'version_code': 11})
    monkeypatch.setattr(tutorial, 'update_listing_text', lambda *args, **kwargs: calls.append('text'))
    monkeypatch.setattr(tutorial, 'update_app_details', lambda *args, **kwargs: calls.append('details'))
    monkeypatch.setattr(tutorial, 'replace_images', lambda *args, **kwargs: calls.append('image'))
    monkeypatch.setattr(tutorial, 'validate', lambda *args, **kwargs: calls.append('validate'))

    state = TutorialState(
        config_path=str(config), credentials_path=str(credentials), aab_path=str(aab),
        release_name='1.0.0', release_notes='Notas', title_file=str(title),
        short_file=str(short), full_file=str(full), website='https://ciata.org.br',
        support_email='contato@ciata.org.br', execute_remote=True,
        play_state_path=str(tmp_path / 'play-state.json'), manifest_dir=str(tmp_path / 'release'),
    )
    result = TutorialRunner(state, tmp_path / 'tutorial-state.json', TutorialIO(output_fn=lambda _: None), json_mode=True).run()
    assert result['completed'] is True
    assert state.edit_id == 'edit-1'
    assert calls == ['text', 'details', 'validate']
    assert 'commit' not in calls


def test_tutorial_uses_declarative_steps():
    from playtool.tutorial import TUTORIAL_STEPS
    assert len(TUTORIAL_STEPS) == 15
    assert TUTORIAL_STEPS[0].id == 'verify-python'
    assert TUTORIAL_STEPS[-1].id == 'validate-draft'
    assert len({step.id for step in TUTORIAL_STEPS}) == len(TUTORIAL_STEPS)


def test_persisted_state_does_not_expose_credentials(tmp_path: Path):
    import json
    credentials = tmp_path / 'service.json'
    credentials.write_text('{}', encoding='utf-8')
    state = TutorialState(credentials_path=str(credentials), dry_run=True)
    runner = TutorialRunner(state, tmp_path / 'state.json', TutorialIO(output_fn=lambda _: None), json_mode=True)
    runner.persist(1)
    saved = json.loads((tmp_path / 'state.json').read_text(encoding='utf-8'))
    assert saved['credentials_path'] is None
    assert saved['context']['credentials_configured'] is True
    assert str(credentials) not in (tmp_path / 'state.json').read_text(encoding='utf-8')
