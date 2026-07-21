from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


_PATH_FIELDS = {
    'project_dir', 'config_path', 'aab_path', 'mapping_path', 'symbols_path',
    'icon_path', 'feature_path', 'title_file', 'short_file', 'full_file',
    'manifest_dir', 'play_state_path',
}


@dataclass
class ContextValue:
    value: Any = None
    source: str = 'unknown'


@dataclass
class PublishingContext:
    """Contexto único e serializável da publicação.

    O contexto guarda os valores usados pelo tutorial, a origem de cada valor e
    resultados de validação. Credenciais e outros segredos ficam apenas na
    memória e nunca aparecem em ``to_public_dict``.
    """

    project_dir: str = '.'
    config_path: str = 'playtool.yaml'
    package: str | None = None
    namespace: str | None = None
    track: str | None = None
    language: str | None = None
    aab_path: str | None = None
    mapping_path: str | None = None
    symbols_path: str | None = None
    release_name: str | None = None
    release_notes: str | None = None
    version_code: int | None = None
    icon_path: str | None = None
    feature_path: str | None = None
    screenshot_paths: list[str] = field(default_factory=list)
    title_file: str | None = None
    short_file: str | None = None
    full_file: str | None = None
    video_url: str | None = None
    website: str | None = None
    support_email: str | None = None
    support_phone: str | None = None
    manifest_dir: str = 'release'
    play_state_path: str = '.playtool-edit.json'
    edit_id: str | None = None
    validation_results: dict[str, Any] = field(default_factory=dict)
    manifest: dict[str, Any] | None = None
    origins: dict[str, str] = field(default_factory=dict)
    audit_events: list[dict[str, Any]] = field(default_factory=list)
    _credentials_path: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self.normalize_paths()

    @property
    def credentials_path(self) -> str | None:
        return self._credentials_path

    def set_credentials_path(self, value: str | None, source: str = 'runtime') -> None:
        self._credentials_path = self._normalize_path(value)
        self.origins['credentials_path'] = source

    def set(self, field_name: str, value: Any, source: str) -> None:
        if not hasattr(self, field_name) or field_name.startswith('_'):
            raise AttributeError(f'Campo de contexto desconhecido: {field_name}')
        if field_name in _PATH_FIELDS:
            value = self._normalize_path(value)
        elif field_name == 'screenshot_paths':
            value = [self._normalize_path(item) for item in (value or []) if item]
        setattr(self, field_name, value)
        self.origins[field_name] = source
        self.audit('context_value_set', field=field_name, source=source)

    def get_origin(self, field_name: str) -> str:
        return self.origins.get(field_name, 'unknown')

    def record_validation(self, check_id: str, status: str, message: str, **details: Any) -> None:
        self.validation_results[check_id] = {
            'status': status,
            'message': message,
            'details': details,
        }
        self.audit('validation_recorded', check_id=check_id, status=status)

    def audit(self, event: str, **details: Any) -> None:
        self.audit_events.append({'event': event, **details})

    def normalize_paths(self) -> None:
        for field_name in _PATH_FIELDS:
            value = getattr(self, field_name, None)
            if value:
                setattr(self, field_name, self._normalize_path(value))
        self.screenshot_paths = [self._normalize_path(item) for item in self.screenshot_paths if item]
        if self._credentials_path:
            self._credentials_path = self._normalize_path(self._credentials_path)

    def invalidate_missing_files(self) -> list[str]:
        """Revalida referências locais ao retomar uma execução.

        Retorna os campos invalidados. Valores ausentes são limpos para que a
        etapa declarativa correspondente seja executada novamente.
        """
        invalidated: list[str] = []
        for field_name in ('aab_path', 'mapping_path', 'symbols_path', 'icon_path', 'feature_path', 'title_file', 'short_file', 'full_file'):
            value = getattr(self, field_name)
            if value and not Path(value).is_file():
                setattr(self, field_name, None)
                invalidated.append(field_name)
                self.audit('file_reference_invalidated', field=field_name)
        valid_screenshots = [item for item in self.screenshot_paths if Path(item).is_file()]
        if len(valid_screenshots) != len(self.screenshot_paths):
            self.screenshot_paths = valid_screenshots
            invalidated.append('screenshot_paths')
            self.audit('file_reference_invalidated', field='screenshot_paths')
        return invalidated

    def to_public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop('_credentials_path', None)
        data['credentials_configured'] = bool(self._credentials_path)
        return data

    @classmethod
    def from_public_dict(cls, data: dict[str, Any]) -> 'PublishingContext':
        allowed = {name for name in cls.__dataclass_fields__ if not name.startswith('_')}
        return cls(**{key: value for key, value in data.items() if key in allowed})

    @staticmethod
    def _normalize_path(value: str | Path | None) -> str | None:
        if value is None or str(value).strip() == '':
            return None
        return str(Path(value).expanduser().resolve(strict=False))
