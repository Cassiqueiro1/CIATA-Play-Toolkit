from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .core import ToolError, save_json

SCOPE = 'https://www.googleapis.com/auth/androidpublisher'


def service() -> Any:
    cred = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if not cred or not Path(cred).is_file():
        raise ToolError('Defina GOOGLE_APPLICATION_CREDENTIALS com o caminho da conta de serviço.')
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        credentials = service_account.Credentials.from_service_account_file(
            cred,
            scopes=[SCOPE],
        )
        return build(
            'androidpublisher',
            'v3',
            credentials=credentials,
            cache_discovery=False,
        )
    except Exception as exc:
        raise ToolError(
            f'Falha ao criar serviço Google Play: {type(exc).__name__}'
        ) from exc


def create_edit(package: str) -> str:
    return str(
        service()
        .edits()
        .insert(packageName=package, body={})
        .execute()['id']
    )


def discard(package: str, edit_id: str) -> None:
    service().edits().delete(
        packageName=package,
        editId=edit_id,
    ).execute()


def remote_inventory(package: str, edit_id: str | None = None) -> dict:
    svc = service()
    own_edit = False

    if edit_id is None:
        edit_id = create_edit(package)
        own_edit = True

    try:
        tracks = (
            svc.edits()
            .tracks()
            .list(packageName=package, editId=edit_id)
            .execute()
            .get('tracks', [])
        )
        bundles = (
            svc.edits()
            .bundles()
            .list(packageName=package, editId=edit_id)
            .execute()
            .get('bundles', [])
        )

        codes = sorted(
            {
                int(bundle['versionCode'])
                for bundle in bundles
                if 'versionCode' in bundle
            }
        )

        releases = []
        for track in tracks:
            for release in track.get('releases', []) or []:
                releases.append(
                    {
                        'track': track.get('track'),
                        'name': release.get('name'),
                        'status': release.get('status'),
                        'version_codes': [
                            int(value)
                            for value in release.get('versionCodes', [])
                        ],
                    }
                )

        return {
            'package': package,
            'edit_id': edit_id,
            'version_codes': codes,
            'highest_version_code': max(codes) if codes else None,
            'releases': releases,
        }
    finally:
        if own_edit:
            try:
                discard(package, edit_id)
            except Exception:
                pass


def prepare(
    package: str,
    track: str,
    aab: Path,
    name: str,
    notes: str,
    language: str,
    state_path: Path,
    mapping: Path | None = None,
    symbols: Path | None = None,
) -> dict:
    from googleapiclient.http import MediaFileUpload

    if not aab.is_file() or aab.suffix.lower() != '.aab':
        raise ToolError(f'AAB inválido ou ausente: {aab}')

    for optional in (mapping, symbols):
        if optional is not None and not optional.is_file():
            raise ToolError(f'Artefato não encontrado: {optional}')

    svc = service()
    edit = svc.edits().insert(
        packageName=package,
        body={},
    ).execute()
    edit_id = str(edit['id'])

    try:
        before = (
            svc.edits()
            .bundles()
            .list(packageName=package, editId=edit_id)
            .execute()
            .get('bundles', [])
        )
        used_codes = {
            int(bundle['versionCode'])
            for bundle in before
            if 'versionCode' in bundle
        }

        bundle = (
            svc.edits()
            .bundles()
            .upload(
                packageName=package,
                editId=edit_id,
                media_body=MediaFileUpload(
                    str(aab),
                    mimetype='application/octet-stream',
                    resumable=True,
                ),
            )
            .execute()
        )

        version_code = int(bundle['versionCode'])
        if version_code in used_codes:
            raise ToolError(
                f'O versionCode {version_code} já existe na Google Play. '
                'Gere um AAB com código maior.'
            )

        if mapping:
            (
                svc.edits()
                .deobfuscationfiles()
                .upload(
                    packageName=package,
                    editId=edit_id,
                    apkVersionCode=version_code,
                    deobfuscationFileType='proguard',
                    media_body=MediaFileUpload(
                        str(mapping),
                        mimetype='application/octet-stream',
                        resumable=False,
                    ),
                )
                .execute()
            )

        if symbols:
            (
                svc.edits()
                .deobfuscationfiles()
                .upload(
                    packageName=package,
                    editId=edit_id,
                    apkVersionCode=version_code,
                    deobfuscationFileType='nativeCode',
                    media_body=MediaFileUpload(
                        str(symbols),
                        mimetype='application/octet-stream',
                        resumable=False,
                    ),
                )
                .execute()
            )

        body = {
            'track': track,
            'releases': [
                {
                    'name': name,
                    'versionCodes': [str(version_code)],
                    'releaseNotes': [
                        {
                            'language': language,
                            'text': notes,
                        }
                    ],
                    'status': 'draft',
                }
            ],
        }

        track_result = (
            svc.edits()
            .tracks()
            .update(
                packageName=package,
                editId=edit_id,
                track=track,
                body=body,
            )
            .execute()
        )

        state = {
            'package': package,
            'edit_id': edit_id,
            'track': track,
            'language': language,
            'version_code': version_code,
            'version_name': name,
            'status': 'draft',
            'bundle': bundle,
            'track_result': track_result,
        }
        save_json(state_path, state)
        return state

    except Exception:
        try:
            svc.edits().delete(
                packageName=package,
                editId=edit_id,
            ).execute()
        except Exception:
            pass
        raise


def validate(package: str, edit_id: str) -> None:
    service().edits().validate(
        packageName=package,
        editId=edit_id,
        changesNotSentForReview=True,
    ).execute()

def commit(package: str, edit_id: str) -> dict:
    return (
        service()
        .edits()
        .commit(packageName=package, editId=edit_id)
        .execute()
    )
