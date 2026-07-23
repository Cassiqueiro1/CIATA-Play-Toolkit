from __future__ import annotations

import json
import os
import platform
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

from .assets import validate_kind
from .context import PublishingContext
from .core import ToolError, load_config, save_json
from .googleplay import discard, prepare, remote_inventory, validate
from .listing import (
    replace_images,
    update_app_details,
    update_listing_text,
    validate_listing_text,
)
from .manifest import build_manifest
from .release import inspect_release

DEFAULT_TUTORIAL_STATE = Path('.playtool-tutorial.json')
DEFAULT_PLAY_STATE = Path('.playtool-edit.json')


@dataclass
class TutorialState:
    current_step: int = 1
    completed: bool = False
    config_path: str = 'playtool.yaml'
    package: str | None = None
    track: str | None = None
    language: str | None = None
    credentials_path: str | None = None
    aab_path: str | None = None
    mapping_path: str | None = None
    symbols_path: str | None = None
    release_name: str | None = None
    release_notes: str | None = None
    icon_path: str | None = None
    feature_path: str | None = None
    screenshot_paths: list[str] | None = None
    title_file: str | None = None
    short_file: str | None = None
    full_file: str | None = None
    video_url: str | None = None
    website: str | None = None
    support_email: str | None = None
    support_phone: str | None = None
    manifest_dir: str = 'release'
    play_state_path: str = str(DEFAULT_PLAY_STATE)
    edit_id: str | None = None
    version_code: int | None = None
    dry_run: bool = False
    execute_remote: bool = False
    completed_step_ids: list[str] = field(default_factory=list)
    context: dict | None = None

    def to_persisted_dict(self) -> dict:
        data = asdict(self)
        data['credentials_path'] = None
        return data

    @classmethod
    def from_file(cls, path: Path) -> 'TutorialState':
        if not path.is_file():
            raise ToolError(f'Estado do tutorial não encontrado: {path}')
        data = json.loads(path.read_text(encoding='utf-8'))
        return cls(**data)


class TutorialIO:
    def __init__(
        self,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
    ):
        self.input_fn = input_fn
        self.output_fn = output_fn

    def say(self, text: str = '') -> None:
        self.output_fn(text)

    def ask(self, prompt: str, default: str | None = None) -> str:
        suffix = f' Valor padrão: {default}.' if default else ''
        answer = self.input_fn(f'{prompt}{suffix}\n> ').strip()
        if answer.casefold() == 'sair':
            raise KeyboardInterrupt
        return answer or (default or '')

    def confirm(self, question: str, default: bool = False) -> bool:
        default_text = 'sim' if default else 'não'
        while True:
            answer = self.ask(
                f'{question} Digite S para sim ou N para não.',
                default_text,
            ).casefold()
            if answer in {'s', 'sim', 'y', 'yes'}:
                return True
            if answer in {'n', 'não', 'nao', 'no'}:
                return False
            self.say(
                'Resposta não reconhecida. Digite S para sim ou N para não.'
            )


@dataclass(frozen=True)
class TutorialStep:
    id: str
    title: str
    handler: str
    required: bool = True
    can_skip: bool = False
    resume: bool = True
    interactive: bool = False
    dependencies: tuple[str, ...] = ()
    learn_topic: str | None = None


TUTORIAL_STEPS: tuple[TutorialStep, ...] = (
    TutorialStep('verify-python', 'ambiente Python', 'step_environment'),
    TutorialStep(
        'load-config',
        'configuração',
        'step_config',
        interactive=True,
    ),
    TutorialStep(
        'confirm-defaults',
        'aplicativo e faixa',
        'step_defaults',
        dependencies=('load-config',),
    ),
    TutorialStep(
        'credentials',
        'credenciais',
        'step_credentials',
        required=False,
        can_skip=True,
        interactive=True,
    ),
    TutorialStep(
        'api-access',
        'acesso à API',
        'step_api_access',
        required=False,
        can_skip=True,
        dependencies=('credentials',),
    ),
    TutorialStep(
        'app-bundle',
        'App Bundle',
        'step_aab',
        required=False,
        can_skip=True,
        interactive=True,
        learn_topic='bundle',
    ),
    TutorialStep(
        'release-identity',
        'identificação da versão',
        'step_release_identity',
        interactive=True,
        dependencies=('load-config',),
    ),
    TutorialStep(
        'debug-artifacts',
        'artefatos de depuração',
        'step_artifacts',
        required=False,
        can_skip=True,
        interactive=True,
        learn_topic='mapping',
    ),
    TutorialStep(
        'listing-images',
        'imagens da ficha',
        'step_images',
        required=False,
        can_skip=True,
        interactive=True,
        learn_topic='screenshots',
    ),
    TutorialStep(
        'listing-text',
        'textos da ficha',
        'step_listing_text',
        required=False,
        can_skip=True,
        interactive=True,
    ),
    TutorialStep(
        'support-contacts',
        'contatos da ficha',
        'step_contacts',
        required=False,
        can_skip=True,
        interactive=True,
    ),
    TutorialStep(
        'release-manifest',
        'manifesto da versão',
        'step_manifest',
        required=False,
        can_skip=True,
        dependencies=('app-bundle', 'release-identity'),
    ),
    TutorialStep('summary', 'resumo', 'step_summary'),
    TutorialStep(
        'draft',
        'criação e preenchimento do rascunho',
        'step_draft',
        required=False,
        can_skip=True,
        interactive=True,
        dependencies=('summary',),
    ),
    TutorialStep(
        'validate-draft',
        'validação e publicação',
        'step_publish',
        required=False,
        can_skip=True,
        dependencies=('draft',),
    ),
)


class TutorialRunner:
    total_steps = len(TUTORIAL_STEPS)

    CONFIG_FIELDS = {
        'aab_path': 'aab_path',
        'mapping_path': 'mapping_path',
        'symbols_path': 'symbols_path',
        'release_name': 'release_name',
        'release_notes': 'release_notes',
        'icon_path': 'icon_path',
        'feature_path': 'feature_path',
        'screenshot_paths': 'screenshot_paths',
        'title_file': 'title_file',
        'short_file': 'short_file',
        'full_file': 'full_file',
        'video_url': 'video_url',
        'website': 'website',
        'support_email': 'support_email',
        'support_phone': 'support_phone',
        'manifest_dir': 'manifest_dir',
        'play_state_path': 'play_state_path',
    }

    def __init__(
        self,
        state: TutorialState,
        state_path: Path,
        io: TutorialIO,
        json_mode: bool = False,
    ):
        self.state = state
        self.state_path = state_path
        self.io = io
        self.json_mode = json_mode
        self.events: list[dict] = []
        self.context = self._build_context()

    def _build_context(self) -> PublishingContext:
        if self.state.context:
            context = PublishingContext.from_public_dict(self.state.context)
        else:
            context = PublishingContext(
                config_path=self.state.config_path,
                package=self.state.package,
                track=self.state.track,
                language=self.state.language,
                aab_path=self.state.aab_path,
                mapping_path=self.state.mapping_path,
                symbols_path=self.state.symbols_path,
                release_name=self.state.release_name,
                release_notes=self.state.release_notes,
                version_code=self.state.version_code,
                icon_path=self.state.icon_path,
                feature_path=self.state.feature_path,
                screenshot_paths=self.state.screenshot_paths or [],
                title_file=self.state.title_file,
                short_file=self.state.short_file,
                full_file=self.state.full_file,
                video_url=self.state.video_url,
                website=self.state.website,
                support_email=self.state.support_email,
                support_phone=self.state.support_phone,
                manifest_dir=self.state.manifest_dir,
                play_state_path=self.state.play_state_path,
                edit_id=self.state.edit_id,
            )
        context.set_credentials_path(
            self.state.credentials_path
            or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
            'runtime',
        )
        return context

    def _sync_context(self) -> None:
        for name in (
            'config_path',
            'package',
            'track',
            'language',
            'aab_path',
            'mapping_path',
            'symbols_path',
            'release_name',
            'release_notes',
            'version_code',
            'icon_path',
            'feature_path',
            'title_file',
            'short_file',
            'full_file',
            'video_url',
            'website',
            'support_email',
            'support_phone',
            'manifest_dir',
            'play_state_path',
            'edit_id',
        ):
            setattr(self.context, name, getattr(self.state, name))
        self.context.screenshot_paths = list(
            self.state.screenshot_paths or []
        )
        self.context.set_credentials_path(
            self.state.credentials_path,
            'runtime',
        )
        self.context.normalize_paths()
        self.state.context = self.context.to_public_dict()

    def _reuse_config(self, config: dict) -> list[str]:
        reused: list[str] = []

        self.state.package = config['package']
        self.state.track = config['default_track']
        self.state.language = config['language']

        for config_key, state_field in self.CONFIG_FIELDS.items():
            value = config.get(config_key)
            if value in (None, '', []):
                continue

            current = getattr(self.state, state_field)
            if current not in (None, '', []):
                continue

            if state_field == 'screenshot_paths':
                if isinstance(value, str):
                    value = [
                        item.strip()
                        for item in value.split(';')
                        if item.strip()
                    ]
                elif isinstance(value, (tuple, list)):
                    value = [str(item) for item in value if str(item).strip()]
                else:
                    raise ToolError(
                        'screenshot_paths deve ser uma lista YAML '
                        'ou uma sequência separada por ponto e vírgula.'
                    )

            setattr(self.state, state_field, value)
            reused.append(config_key)

        return reused

    def event(
        self,
        step: int,
        title: str,
        status: str,
        message: str,
    ) -> None:
        item = {
            'step': step,
            'total_steps': self.total_steps,
            'title': title,
            'status': status,
            'message': message,
        }
        self.events.append(item)
        step_id = (
            TUTORIAL_STEPS[step - 1].id
            if 1 <= step <= len(TUTORIAL_STEPS)
            else str(step)
        )
        self.context.record_validation(step_id, status, message)
        if not self.json_mode:
            self.io.say(f'Etapa {step} de {self.total_steps}: {title}.')
            self.io.say(message)
            self.io.say(f'Resultado: {status}.')
            self.io.say()

    def persist(self, next_step: int) -> None:
        self.state.current_step = next_step
        self._sync_context()
        save_json(self.state_path, self.state.to_persisted_dict())

    def run(self) -> dict:
        if not self.json_mode:
            self.io.say('CIATA Play Publisher Toolkit.')
            self.io.say('Assistente de primeira publicação.')
            if self.state.dry_run:
                self.io.say(
                    'Modo de simulação ativo. '
                    'Nenhuma alteração remota será realizada.'
                )
            elif self.state.execute_remote:
                self.io.say(
                    'Execução remota habilitada. O assistente poderá criar '
                    'um rascunho, mas não publicará o aplicativo.'
                )
            else:
                self.io.say(
                    'Modo orientado ativo. O assistente validará os dados '
                    'localmente e não criará alterações remotas.'
                )
            self.io.say(
                'Digite sair em qualquer pergunta para interromper. '
                'O progresso será salvo.'
            )
            self.io.say()

        start = max(1, self.state.current_step)
        for index, definition in enumerate(TUTORIAL_STEPS, start=1):
            if (
                index < start
                and definition.id in self.state.completed_step_ids
            ):
                continue
            unmet = [
                item
                for item in definition.dependencies
                if item not in self.state.completed_step_ids
            ]
            if unmet and index >= start:
                raise ToolError(
                    f'A etapa {definition.id} depende de etapas não '
                    f"concluídas: {', '.join(unmet)}."
                )
            handler = getattr(self, definition.handler)
            handler()
            if (
                definition.resume
                and definition.id not in self.state.completed_step_ids
            ):
                self.state.completed_step_ids.append(definition.id)
            self.persist(index + 1)

        self.state.completed = True
        self.persist(self.total_steps + 1)
        self._sync_context()
        return {
            'completed': True,
            'dry_run': self.state.dry_run,
            'execute_remote': self.state.execute_remote,
            'state': self.state.to_persisted_dict(),
            'context': self.context.to_public_dict(),
            'events': self.events,
        }

    def step_environment(self) -> None:
        version = (
            f'{sys.version_info.major}.'
            f'{sys.version_info.minor}.'
            f'{sys.version_info.micro}'
        )
        if sys.version_info < (3, 10):
            raise ToolError(
                f'Python {version} não é compatível. '
                'Use Python 3.10 ou superior.'
            )
        self.event(
            1,
            'ambiente Python',
            'aprovado',
            f'Python encontrado: {version}. Sistema: {platform.system()}.',
        )

    def step_config(self) -> None:
        path = Path(self.state.config_path)
        if not path.is_file():
            if self.json_mode:
                raise ToolError(f'Configuração não encontrada: {path}')
            if not self.io.confirm(
                f'O arquivo {path} não existe. Deseja criá-lo agora?',
                True,
            ):
                raise ToolError(
                    'O tutorial precisa de um arquivo de configuração.'
                )
            package = self.io.ask(
                'Informe o package name.',
                'br.org.ciata.comunicaciata',
            )
            track = self.io.ask('Informe a faixa padrão.', 'beta')
            language = self.io.ask('Informe o idioma padrão.', 'pt-BR')
            path.write_text(
                f'package: {package}\n'
                f'default_track: {track}\n'
                f'language: {language}\n',
                encoding='utf-8',
            )

        config = load_config(path)
        reused = self._reuse_config(config)

        message = f'Arquivo carregado: {path.resolve()}.'
        if reused:
            message += (
                f' Valores reutilizados do YAML: {len(reused)} '
                f"({', '.join(reused)})."
            )
        else:
            message += ' Nenhum campo opcional adicional foi encontrado.'

        self.event(2, 'configuração', 'aprovado', message)

    def step_defaults(self) -> None:
        self.event(
            3,
            'aplicativo e faixa',
            'aprovado',
            f'Aplicativo: {self.state.package}. '
            f'Faixa padrão: {self.state.track}. '
            f'Idioma: {self.state.language}.',
        )

    def step_credentials(self) -> None:
        current = (
            self.state.credentials_path
            or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '')
        )
        if not current and not self.json_mode:
            current = self.io.ask(
                'Informe o caminho da credencial da conta de serviço. '
                'Deixe em branco para configurar depois.'
            )
        self.state.credentials_path = current or None

        if current and Path(current).is_file():
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = current
            status = 'aprovado'
            message = (
                f'Credencial encontrada em: {Path(current).resolve()}. '
                'O conteúdo não será exibido.'
            )
        else:
            status = 'aviso'
            message = (
                'Credencial não encontrada. As etapas locais podem '
                'continuar, mas o acesso à Google Play ficará indisponível.'
            )
        self.event(4, 'credenciais', status, message)

    def step_api_access(self) -> None:
        if self.state.dry_run:
            self.event(
                5,
                'acesso à API',
                'simulado',
                'O teste remoto foi ignorado porque o modo de simulação '
                'está ativo.',
            )
            return
        if not self.state.execute_remote:
            self.event(
                5,
                'acesso à API',
                'não executado',
                'Use --execute para testar o acesso remoto e criar o '
                'rascunho durante o tutorial.',
            )
            return
        if (
            not self.state.credentials_path
            or not Path(self.state.credentials_path).is_file()
        ):
            raise ToolError('A execução remota exige uma credencial válida.')

        inventory = remote_inventory(self.state.package or '')
        highest = inventory.get('highest_version_code')
        message = 'Acesso à API confirmado.'
        if highest is not None:
            message += f' Maior versionCode encontrado: {highest}.'
        self.event(5, 'acesso à API', 'aprovado', message)

    def step_aab(self) -> None:
        value = self.state.aab_path
        if not value and not self.json_mode:
            value = self.io.ask(
                'Informe o caminho do arquivo AAB. '
                'Deixe em branco para continuar sem ele.'
            )
        self.state.aab_path = value or None

        if value:
            path = Path(value)
            if not path.is_file() or path.suffix.lower() != '.aab':
                raise ToolError(
                    f'AAB inválido ou não encontrado: {path}'
                )
            message = f'App Bundle encontrado: {path.resolve()}.'
            status = 'aprovado'
        else:
            message = 'Nenhum App Bundle foi informado.'
            status = 'aviso'
        self.event(6, 'App Bundle', status, message)

    def step_release_identity(self) -> None:
        if not self.json_mode:
            self.state.release_name = (
                self.state.release_name
                or self.io.ask(
                    'Informe o nome da versão.',
                    '1.0.0-beta01',
                )
            )
            self.state.release_notes = (
                self.state.release_notes
                or self.io.ask(
                    'Informe as notas da versão.',
                    'Primeira versão beta pública.',
                )
            )
        self.event(
            7,
            'identificação da versão',
            'aprovado',
            f'Nome da versão: '
            f'{self.state.release_name or "não informado"}. '
            f'Notas registradas: '
            f'{"sim" if self.state.release_notes else "não"}.',
        )

    def step_artifacts(self) -> None:
        if not self.json_mode:
            self.state.mapping_path = (
                self.state.mapping_path
                or self.io.ask(
                    'Informe o caminho do mapping.txt. '
                    'Deixe em branco se não houver.'
                )
                or None
            )
            self.state.symbols_path = (
                self.state.symbols_path
                or self.io.ask(
                    'Informe o caminho dos símbolos nativos. '
                    'Deixe em branco se não houver.'
                )
                or None
            )

        if self.state.aab_path:
            report = inspect_release(
                Path(self.state.aab_path),
                (
                    Path(self.state.mapping_path)
                    if self.state.mapping_path
                    else None
                ),
                (
                    Path(self.state.symbols_path)
                    if self.state.symbols_path
                    else None
                ),
            )
            message = (
                'AAB validado. '
                f'Mapping presente: '
                f'{"sim" if report["mapping"]["present"] else "não"}. '
                f'Símbolos presentes: '
                f'{"sim" if report["native_symbols"]["present"] else "não"}.'
            )
        else:
            message = (
                'A inspeção foi ignorada porque nenhum AAB foi informado.'
            )
        self.event(8, 'artefatos de depuração', 'aprovado', message)

    def _validate_optional_image(
        self,
        value: str | None,
        kind: str,
    ) -> str | None:
        if not value:
            return None
        path = Path(value)
        result = validate_kind(path, kind)
        if not result['valid']:
            raise ToolError(
                f'Imagem reprovada: {path}. '
                + '; '.join(result['errors'])
            )
        return str(path)

    def step_images(self) -> None:
        if not self.json_mode:
            self.state.icon_path = (
                self.state.icon_path
                or self.io.ask(
                    'Caminho do ícone de 512 por 512 pixels. '
                    'Deixe em branco para não enviar.'
                )
                or None
            )
            self.state.feature_path = (
                self.state.feature_path
                or self.io.ask(
                    'Caminho do recurso gráfico de 1024 por 500 pixels. '
                    'Deixe em branco para não enviar.'
                )
                or None
            )
            if self.state.screenshot_paths is None:
                raw = self.io.ask(
                    'Informe os caminhos das capturas, separados por '
                    'ponto e vírgula. Deixe em branco para não enviar.'
                )
                self.state.screenshot_paths = [
                    item.strip()
                    for item in raw.split(';')
                    if item.strip()
                ]

        self.state.icon_path = self._validate_optional_image(
            self.state.icon_path,
            'icon',
        )
        self.state.feature_path = self._validate_optional_image(
            self.state.feature_path,
            'feature',
        )

        screenshots = self.state.screenshot_paths or []
        if screenshots and not 2 <= len(screenshots) <= 8:
            raise ToolError(
                'Informe entre 2 e 8 capturas de telefone.'
            )
        for path in screenshots:
            self._validate_optional_image(path, 'screenshot')

        count = (
            int(bool(self.state.icon_path))
            + int(bool(self.state.feature_path))
            + len(screenshots)
        )
        status = 'aprovado' if count else 'aviso'
        self.event(
            9,
            'imagens da ficha',
            status,
            f'Arquivos de imagem validados: {count}.',
        )

    def step_listing_text(self) -> None:
        if not self.json_mode:
            self.state.title_file = (
                self.state.title_file
                or self.io.ask(
                    'Caminho do arquivo de título. '
                    'Deixe em branco para configurar depois.'
                )
                or None
            )
            self.state.short_file = (
                self.state.short_file
                or self.io.ask(
                    'Caminho do arquivo de resumo. '
                    'Deixe em branco para configurar depois.'
                )
                or None
            )
            self.state.full_file = (
                self.state.full_file
                or self.io.ask(
                    'Caminho do arquivo de descrição completa. '
                    'Deixe em branco para configurar depois.'
                )
                or None
            )
            self.state.video_url = (
                self.state.video_url
                or self.io.ask(
                    'Link do vídeo do YouTube. '
                    'Deixe em branco se não houver.'
                )
                or None
            )

        files = [
            self.state.title_file,
            self.state.short_file,
            self.state.full_file,
        ]
        for value in files:
            if value and not Path(value).is_file():
                raise ToolError(
                    f'Arquivo de texto não encontrado: {value}'
                )

        if all(files):
            validation = validate_listing_text(
                Path(self.state.title_file or '')
                .read_text(encoding='utf-8-sig')
                .strip(),
                Path(self.state.short_file or '')
                .read_text(encoding='utf-8-sig')
                .strip(),
                Path(self.state.full_file or '')
                .read_text(encoding='utf-8-sig')
                .strip(),
                self.state.video_url,
            )
            if not validation['valid']:
                raise ToolError(
                    'Textos da ficha reprovados: '
                    + '; '.join(validation['errors'])
                )

        count = sum(
            bool(value)
            for value in (*files, self.state.video_url)
        )
        self.event(
            10,
            'textos da ficha',
            'aprovado' if all(files) else 'aviso',
            f'Campos informados: {count} de 4.',
        )

    def step_contacts(self) -> None:
        if not self.json_mode:
            self.state.website = (
                self.state.website
                or self.io.ask(
                    'Informe o site de suporte. '
                    'Deixe em branco para configurar depois.'
                )
                or None
            )
            self.state.support_email = (
                self.state.support_email
                or self.io.ask(
                    'Informe o e-mail de suporte. '
                    'Deixe em branco para configurar depois.'
                )
                or None
            )
            self.state.support_phone = (
                self.state.support_phone
                or self.io.ask(
                    'Informe o telefone de suporte. '
                    'Deixe em branco se não houver.'
                )
                or None
            )

        count = sum(
            bool(value)
            for value in (
                self.state.website,
                self.state.support_email,
            )
        )
        self.event(
            11,
            'contatos da ficha',
            'aprovado' if count == 2 else 'aviso',
            f'Contatos obrigatórios informados: {count} de 2.',
        )

    def step_manifest(self) -> None:
        if (
            self.state.aab_path
            and self.state.release_name
            and self.state.release_notes
        ):
            result = build_manifest(
                self.state.package or '',
                self.state.track or '',
                self.state.release_name,
                Path(self.state.aab_path),
                (
                    Path(self.state.mapping_path)
                    if self.state.mapping_path
                    else None
                ),
                (
                    Path(self.state.symbols_path)
                    if self.state.symbols_path
                    else None
                ),
                self.state.release_notes,
                Path(self.state.manifest_dir),
            )
            self.context.manifest = result
            self.event(
                12,
                'manifesto da versão',
                'gerado',
                f'Manifesto textual: {result["text"]}. '
                f'Manifesto JSON: {result["json"]}.',
            )
        else:
            self.event(
                12,
                'manifesto da versão',
                'aviso',
                'Ainda faltam dados para gerar o manifesto da versão.',
            )

    def step_summary(self) -> None:
        images = (
            int(bool(self.state.icon_path))
            + int(bool(self.state.feature_path))
            + len(self.state.screenshot_paths or [])
        )
        summary = (
            f'Aplicativo: {self.state.package}. '
            f'Faixa: {self.state.track}. '
            f'AAB informado: '
            f'{"sim" if self.state.aab_path else "não"}. '
            f'Imagens validadas: {images}. '
            f'Textos completos: '
            f'{"sim" if self.state.title_file and self.state.short_file and self.state.full_file else "não"}. '
            f'Contatos completos: '
            f'{"sim" if self.state.website and self.state.support_email else "não"}.'
        )
        self.event(13, 'resumo', 'concluído', summary)

    def _require_remote_data(self) -> None:
        missing = []
        for label, value in (
            ('AAB', self.state.aab_path),
            ('nome da versão', self.state.release_name),
            ('notas da versão', self.state.release_notes),
            ('título', self.state.title_file),
            ('resumo', self.state.short_file),
            ('descrição completa', self.state.full_file),
            ('site de suporte', self.state.website),
            ('e-mail de suporte', self.state.support_email),
        ):
            if not value:
                missing.append(label)
        if missing:
            raise ToolError(
                'Não é possível criar o rascunho. Campos ausentes: '
                + ', '.join(missing)
                + '.'
            )

    def step_draft(self) -> None:
        if self.state.dry_run:
            self.event(
                14,
                'criação e preenchimento do rascunho',
                'simulado',
                'O AAB, os textos, os contatos e as imagens seriam '
                'enviados para uma edição temporária.',
            )
            return

        if not self.state.execute_remote:
            self.event(
                14,
                'criação e preenchimento do rascunho',
                'não executado',
                'Execute novamente com --execute para criar e preencher '
                'uma edição temporária na Google Play.',
            )
            return

        self._require_remote_data()
        if (
            not self.json_mode
            and not self.io.confirm(
                'O assistente criará uma edição temporária e enviará '
                'os arquivos. Deseja continuar?',
                False,
            )
        ):
            self.event(
                14,
                'criação e preenchimento do rascunho',
                'cancelado',
                'Nenhuma edição remota foi criada.',
            )
            return

        play_state = Path(self.state.play_state_path)
        edit_id: str | None = None

        try:
            result = prepare(
                self.state.package or '',
                self.state.track or '',
                Path(self.state.aab_path or ''),
                self.state.release_name or '',
                self.state.release_notes or '',
                self.state.language or 'pt-BR',
                play_state,
                (
                    Path(self.state.mapping_path)
                    if self.state.mapping_path
                    else None
                ),
                (
                    Path(self.state.symbols_path)
                    if self.state.symbols_path
                    else None
                ),
            )

            edit_id = str(result['edit_id'])
            self.state.edit_id = edit_id
            self.state.version_code = int(result['version_code'])

            update_listing_text(
                self.state.package or '',
                edit_id,
                self.state.language or 'pt-BR',
                title_file=Path(self.state.title_file or ''),
                short_file=Path(self.state.short_file or ''),
                full_file=Path(self.state.full_file or ''),
                video=self.state.video_url,
            )
            update_app_details(
                self.state.package or '',
                edit_id,
                self.state.language or 'pt-BR',
                self.state.website or '',
                self.state.support_email or '',
                self.state.support_phone or '',
            )

            if self.state.icon_path:
                replace_images(
                    self.state.package or '',
                    edit_id,
                    self.state.language or 'pt-BR',
                    'icon',
                    [Path(self.state.icon_path)],
                )
            if self.state.feature_path:
                replace_images(
                    self.state.package or '',
                    edit_id,
                    self.state.language or 'pt-BR',
                    'feature',
                    [Path(self.state.feature_path)],
                )
            if self.state.screenshot_paths:
                replace_images(
                    self.state.package or '',
                    edit_id,
                    self.state.language or 'pt-BR',
                    'screenshot',
                    [
                        Path(path)
                        for path in self.state.screenshot_paths
                    ],
                )

        except Exception as exc:
            if edit_id:
                try:
                    discard(self.state.package or '', edit_id)
                except Exception:
                    pass
            self.state.edit_id = None
            self.state.version_code = None
            try:
                play_state.unlink(missing_ok=True)
            except OSError:
                pass

            if isinstance(exc, ToolError):
                raise

            try:
                from googleapiclient.errors import HttpError
            except ImportError:
                HttpError = ()  # type: ignore[assignment]

            if HttpError and isinstance(exc, HttpError):
                status = getattr(exc.resp, 'status', 'desconhecido')
                raise ToolError(
                    'Falha na comunicação com a Google Play. '
                    f'HTTP {status}. A edição temporária foi descartada. '
                    f'Detalhe: {exc._get_reason()}'
                ) from exc

            raise ToolError(
                'Falha ao criar ou preencher o rascunho. '
                'A edição temporária foi descartada. '
                f'Detalhe técnico: {type(exc).__name__}: {exc}'
            ) from exc

        self.event(
            14,
            'criação e preenchimento do rascunho',
            'concluído',
            f'Edição temporária criada. '
            f'versionCode: {self.state.version_code}. '
            f'Estado salvo em: {play_state.resolve()}.',
        )

    def step_publish(self) -> None:
        if not self.state.edit_id:
            self.event(
                15,
                'validação e publicação',
                'não executado',
                'Nenhuma edição remota está ativa. '
                'Nenhuma publicação foi realizada.',
            )
            return

        try:
            validate(
                self.state.package or '',
                self.state.edit_id,
                changes_not_sent_for_review=True,
            )
        except Exception as exc:
            if isinstance(exc, ToolError):
                raise

            try:
                from googleapiclient.errors import HttpError
            except ImportError:
                HttpError = ()  # type: ignore[assignment]

            if HttpError and isinstance(exc, HttpError):
                status = getattr(exc.resp, 'status', 'desconhecido')
                raise ToolError(
                    'A Google Play recusou a validação da edição. '
                    f'HTTP {status}. O rascunho continua salvo e nada foi '
                    f'publicado. Detalhe: {exc._get_reason()}'
                ) from exc

            raise ToolError(
                'Falha ao validar a edição. O rascunho continua salvo e '
                'nada foi publicado. '
                f'Detalhe técnico: {type(exc).__name__}: {exc}'
            ) from exc

        self.event(
            15,
            'validação e publicação',
            'validado',
            f'A edição {self.state.edit_id} foi validada pela Google Play '
            'com changesNotSentForReview=true. Nada foi publicado. '
            'Revise o resumo e execute playtool play commit para confirmar '
            'separadamente; depois, envie para revisão pela Play Console.',
        )


def run_tutorial(
    *,
    resume: bool,
    dry_run: bool,
    execute_remote: bool,
    json_mode: bool,
    state_path: Path,
    config_path: Path,
) -> dict:
    if dry_run and execute_remote:
        raise ToolError(
            'Use --dry-run ou --execute, nunca os dois ao mesmo tempo.'
        )

    if resume:
        state = TutorialState.from_file(state_path)
        state.dry_run = dry_run or state.dry_run
        state.execute_remote = (
            execute_remote or state.execute_remote
        )
        if state.context:
            resumed_context = PublishingContext.from_public_dict(
                state.context
            )
            invalidated = resumed_context.invalidate_missing_files()
            state.context = resumed_context.to_public_dict()
            if invalidated:
                state.completed_step_ids = []
                state.current_step = 1
    else:
        state = TutorialState(
            config_path=str(config_path),
            dry_run=dry_run,
            execute_remote=execute_remote,
        )

    runner = TutorialRunner(
        state,
        state_path,
        TutorialIO(),
        json_mode=json_mode,
    )
    return runner.run()
