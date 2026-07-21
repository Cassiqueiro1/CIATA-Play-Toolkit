from __future__ import annotations

import json
import os
import platform
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Any
from urllib.parse import urlparse

import yaml

from .assets import validate_kind
from .context import PublishingContext
from .core import ToolError

SEVERITY_ORDER = {'informação': 0, 'aviso': 1, 'erro': 2, 'bloqueio': 3}
VALID_TRACKS = {'internal', 'alpha', 'beta', 'production'}


@dataclass(frozen=True)
class DoctorCheck:
    id: str
    category: str
    title: str
    severity: str
    handler: str
    documentation: str | None = None
    fix_handler: str | None = None


@dataclass
class DoctorResult:
    check_id: str
    category: str
    title: str
    status: str
    severity: str
    message: str
    cause: str | None = None
    impact: str | None = None
    recommendation: str | None = None
    documentation: str | None = None
    fix_available: bool = False
    fixed: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


DOCTOR_CHECKS: tuple[DoctorCheck, ...] = (
    DoctorCheck('python-version', 'ambiente', 'versão do Python', 'bloqueio', 'check_python', 'doc/DOCTOR_ENGINE.md'),
    DoctorCheck('config-file', 'configuração', 'arquivo de configuração', 'bloqueio', 'check_config', 'doc/PUBLISHING_CONTEXT.md', 'fix_config'),
    DoctorCheck('package-name', 'configuração', 'package name', 'erro', 'check_package', 'doc/PUBLISHING_CONTEXT.md'),
    DoctorCheck('publication-track', 'configuração', 'faixa de publicação', 'erro', 'check_track', 'doc/PUBLISHING_CONTEXT.md'),
    DoctorCheck('language', 'configuração', 'idioma da ficha', 'aviso', 'check_language', 'doc/PUBLISHING_CONTEXT.md'),
    DoctorCheck('credentials', 'credenciais', 'credencial da conta de serviço', 'aviso', 'check_credentials', 'SECURITY.md'),
    DoctorCheck('app-bundle', 'versão', 'App Bundle', 'bloqueio', 'check_aab', 'doc/TUTORIAL_ENGINE.md'),
    DoctorCheck('mapping', 'depuração', 'arquivo mapping', 'aviso', 'check_mapping', 'doc/KNOWLEDGE_BASE.md'),
    DoctorCheck('native-symbols', 'depuração', 'símbolos nativos', 'informação', 'check_symbols', 'doc/KNOWLEDGE_BASE.md'),
    DoctorCheck('listing-text', 'ficha da loja', 'textos da ficha', 'erro', 'check_listing_text', 'doc/UX_GUIDE.md'),
    DoctorCheck('listing-images', 'ficha da loja', 'imagens da ficha', 'erro', 'check_listing_images', 'doc/UX_GUIDE.md'),
    DoctorCheck('support-contacts', 'ficha da loja', 'contatos de suporte', 'aviso', 'check_contacts', 'doc/UX_GUIDE.md'),
    DoctorCheck('review-url', 'revisão', 'URL de revisão', 'aviso', 'check_review_url', 'doc/KNOWLEDGE_BASE.md'),
    DoctorCheck('gradle-project', 'projeto Android', 'projeto Gradle', 'informação', 'check_gradle', 'doc/ARCHITECTURE.md'),
    DoctorCheck('android-manifest', 'projeto Android', 'AndroidManifest', 'informação', 'check_manifest', 'doc/ARCHITECTURE.md'),
)


class DoctorRunner:
    def __init__(self, context: PublishingContext, config_path: Path, fix: bool = False):
        self.context = context
        self.config_path = config_path
        self.fix = fix
        self.config: dict[str, Any] = {}
        self.results: list[DoctorResult] = []

    def run(self) -> dict[str, Any]:
        for definition in DOCTOR_CHECKS:
            result: DoctorResult = getattr(self, definition.handler)(definition)
            if self.fix and result.fix_available and definition.fix_handler:
                fixed = getattr(self, definition.fix_handler)(definition, result)
                result.fixed = fixed
                if fixed:
                    result.status = 'aprovado'
                    result.message = 'Correção automática aplicada com sucesso.'
            self.results.append(result)
            self.context.record_validation(definition.id, result.status, result.message, severity=result.severity)
        counts = {name: 0 for name in ('aprovado', 'informação', 'aviso', 'erro', 'bloqueio')}
        for item in self.results:
            counts[item.status] = counts.get(item.status, 0) + 1
        ready = counts.get('erro', 0) == 0 and counts.get('bloqueio', 0) == 0
        return {
            'ready': ready,
            'summary': counts,
            'results': [item.to_dict() for item in self.results],
            'context': self.context.to_public_dict(),
        }

    def ok(self, d: DoctorCheck, message: str, **details: Any) -> DoctorResult:
        return DoctorResult(d.id, d.category, d.title, 'aprovado', d.severity, message, documentation=d.documentation, details=details)

    def issue(self, d: DoctorCheck, status: str, message: str, cause: str, impact: str, recommendation: str, *, fix_available: bool = False, **details: Any) -> DoctorResult:
        return DoctorResult(d.id, d.category, d.title, status, d.severity, message, cause, impact, recommendation, d.documentation, fix_available, False, details)

    def check_python(self, d: DoctorCheck) -> DoctorResult:
        version = f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'
        if sys.version_info < (3, 10):
            return self.issue(d, 'bloqueio', f'Python incompatível: {version}.', 'O toolkit exige Python 3.10 ou superior.', 'Os comandos podem falhar ou nem iniciar.', 'Instale Python 3.10 ou superior.')
        return self.ok(d, f'Python {version} compatível. Sistema: {platform.system()}.')

    def check_config(self, d: DoctorCheck) -> DoctorResult:
        if not self.config_path.is_file():
            return self.issue(d, 'bloqueio', f'Configuração não encontrada: {self.config_path}.', 'O arquivo playtool.yaml não existe.', 'O toolkit não sabe qual aplicativo e faixa deve usar.', "Execute 'playtool init' ou use --fix.", fix_available=True)
        try:
            self.config = yaml.safe_load(self.config_path.read_text(encoding='utf-8')) or {}
        except Exception as exc:
            return self.issue(d, 'bloqueio', 'A configuração não pôde ser lida.', f'YAML inválido: {exc}', 'Os demais dados de publicação ficam indisponíveis.', 'Corrija a sintaxe do arquivo playtool.yaml.')
        self._load_context_from_config()
        return self.ok(d, f'Configuração carregada: {self.config_path.resolve()}.')

    def fix_config(self, d: DoctorCheck, result: DoctorResult) -> bool:
        if self.config_path.exists():
            return False
        self.config_path.write_text('package: br.org.exemplo.aplicativo\ndefault_track: beta\nlanguage: pt-BR\n', encoding='utf-8')
        self.config = yaml.safe_load(self.config_path.read_text(encoding='utf-8')) or {}
        self._load_context_from_config()
        return True

    def _load_context_from_config(self) -> None:
        mapping = {'package': 'package', 'default_track': 'track', 'language': 'language', 'review_url': 'review_url'}
        for key, field_name in mapping.items():
            if self.config.get(key):
                if field_name == 'review_url':
                    self.context.validation_results['review_url_value'] = self.config[key]
                else:
                    self.context.set(field_name, self.config[key], 'config')
        for key in ('aab_path','mapping_path','symbols_path','icon_path','feature_path','title_file','short_file','full_file','website','support_email','support_phone','video_url'):
            if self.config.get(key):
                self.context.set(key, self.config[key], 'config')
        if self.config.get('screenshot_paths'):
            self.context.set('screenshot_paths', self.config['screenshot_paths'], 'config')

    def check_package(self, d: DoctorCheck) -> DoctorResult:
        value = self.context.package
        if not value:
            return self.issue(d, 'erro', 'Package name não informado.', 'O campo package está ausente.', 'A API não consegue identificar o aplicativo.', 'Informe package no playtool.yaml.')
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*){1,}', value):
            return self.issue(d, 'erro', f'Package name inválido: {value}.', 'O valor não segue o formato de identificador Java.', 'A publicação será rejeitada.', 'Use um valor como br.org.ciata.aplicativo.')
        return self.ok(d, f'Package name válido: {value}.')

    def check_track(self, d: DoctorCheck) -> DoctorResult:
        value = self.context.track
        if not value:
            return self.issue(d, 'erro', 'Faixa não informada.', 'default_track está ausente.', 'A versão não tem destino definido.', 'Informe internal, alpha, beta ou production.')
        if value not in VALID_TRACKS:
            return self.issue(d, 'erro', f'Faixa não reconhecida: {value}.', 'O valor não corresponde às faixas suportadas pelo toolkit.', 'A atualização da faixa pode falhar.', 'Use internal, alpha, beta ou production.')
        return self.ok(d, f'Faixa configurada: {value}.')

    def check_language(self, d: DoctorCheck) -> DoctorResult:
        value = self.context.language
        if not value:
            return self.issue(d, 'aviso', 'Idioma não informado.', 'language está ausente.', 'A ficha pode ser enviada para o idioma errado.', 'Informe um código como pt-BR.')
        if not re.fullmatch(r'[a-z]{2,3}(?:-[A-Z]{2})?', value):
            return self.issue(d, 'aviso', f'Código de idioma incomum: {value}.', 'O código não segue o padrão esperado.', 'A API pode rejeitar ou criar uma ficha inesperada.', 'Use um código como pt-BR ou en-US.')
        return self.ok(d, f'Idioma configurado: {value}.')

    def check_credentials(self, d: DoctorCheck) -> DoctorResult:
        value = self.context.credentials_path or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if not value:
            return self.issue(d, 'aviso', 'Credencial não configurada.', 'GOOGLE_APPLICATION_CREDENTIALS não está definido.', 'Comandos remotos ficarão indisponíveis.', 'Defina a variável de ambiente com o caminho do JSON da conta de serviço.')
        path = Path(value)
        if not path.is_file():
            return self.issue(d, 'aviso', 'Arquivo de credencial não encontrado.', f'Caminho inexistente: {path}.', 'A autenticação com a Google Play falhará.', 'Corrija GOOGLE_APPLICATION_CREDENTIALS.')
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            return self.issue(d, 'aviso', 'Credencial não contém JSON válido.', 'O arquivo não pôde ser interpretado.', 'A autenticação falhará.', 'Baixe novamente a chave da conta de serviço.')
        if data.get('type') != 'service_account' or not data.get('client_email'):
            return self.issue(d, 'aviso', 'Credencial não parece ser uma conta de serviço.', 'Campos esperados estão ausentes.', 'A autenticação pode falhar.', 'Use o JSON de uma conta de serviço autorizada no Play Console.')
        self.context.set_credentials_path(str(path), 'environment')
        return self.ok(d, f'Credencial encontrada para: {data.get("client_email")}.')

    def _file_check(self, d: DoctorCheck, value: str | None, label: str, required: bool) -> DoctorResult:
        if not value:
            status = 'bloqueio' if required else d.severity
            return self.issue(d, status, f'{label} não informado.', f'O caminho de {label} está vazio.', 'A etapa correspondente não poderá ser executada.', f'Informe o caminho de {label} no tutorial ou na configuração.')
        path = Path(value)
        if not path.is_file():
            status = 'bloqueio' if required else d.severity
            return self.issue(d, status, f'{label} não encontrado.', f'Caminho inexistente: {path}.', 'A etapa correspondente falhará.', f'Gere ou localize {label} e atualize o caminho.')
        return self.ok(d, f'{label} encontrado: {path.resolve()}.', size_bytes=path.stat().st_size)

    def check_aab(self, d: DoctorCheck) -> DoctorResult:
        return self._file_check(d, self.context.aab_path, 'App Bundle', True)

    def check_mapping(self, d: DoctorCheck) -> DoctorResult:
        return self._file_check(d, self.context.mapping_path, 'mapping.txt', False)

    def check_symbols(self, d: DoctorCheck) -> DoctorResult:
        return self._file_check(d, self.context.symbols_path, 'arquivo de símbolos nativos', False)

    def check_listing_text(self, d: DoctorCheck) -> DoctorResult:
        fields = [('título', self.context.title_file, 30), ('resumo', self.context.short_file, 80), ('descrição completa', self.context.full_file, 4000)]
        problems = []
        details = {}
        for label, value, limit in fields:
            if not value or not Path(value).is_file():
                problems.append(f'{label} ausente')
                continue
            text = Path(value).read_text(encoding='utf-8').strip()
            details[label] = len(text)
            if not text:
                problems.append(f'{label} vazio')
            elif len(text) > limit:
                problems.append(f'{label} excede {limit} caracteres')
        if problems:
            return self.issue(d, 'erro', 'Os textos da ficha precisam de ajustes.', '; '.join(problems) + '.', 'A ficha pode ser rejeitada ou ficar incompleta.', 'Corrija os arquivos de título, resumo e descrição.', **details)
        return self.ok(d, 'Título, resumo e descrição estão presentes e dentro dos limites.', **details)

    def check_listing_images(self, d: DoctorCheck) -> DoctorResult:
        items = [('ícone', self.context.icon_path, 'icon'), ('recurso gráfico', self.context.feature_path, 'feature')]
        problems = []
        details = {}
        for label, value, kind in items:
            if not value or not Path(value).is_file():
                problems.append(f'{label} ausente')
                continue
            validation = validate_kind(Path(value), kind)
            details[label] = validation
            if not validation['valid']:
                problems.append(f'{label} inválido')
        screenshots = self.context.screenshot_paths
        if not screenshots:
            problems.append('capturas de tela ausentes')
        else:
            for index, value in enumerate(screenshots, start=1):
                if not Path(value).is_file():
                    problems.append(f'captura {index} ausente')
                    continue
                validation = validate_kind(Path(value), 'screenshot')
                if not validation['valid']:
                    problems.append(f'captura {index} inválida')
        if problems:
            return self.issue(d, 'erro', 'As imagens da ficha precisam de ajustes.', '; '.join(problems) + '.', 'A ficha pode ficar incompleta ou ser rejeitada.', 'Converta e valide as imagens com playtool assets.', **details)
        return self.ok(d, f'Ícone, recurso gráfico e {len(screenshots)} captura(s) foram validados.', **details)

    def check_contacts(self, d: DoctorCheck) -> DoctorResult:
        problems = []
        if not self.context.website or not self._valid_http_url(self.context.website):
            problems.append('site ausente ou inválido')
        if not self.context.support_email or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', self.context.support_email):
            problems.append('e-mail ausente ou inválido')
        if problems:
            return self.issue(d, 'aviso', 'Os contatos de suporte precisam de ajustes.', '; '.join(problems) + '.', 'Usuários e equipe de revisão podem não conseguir contato.', 'Informe site HTTPS e e-mail válido.')
        return self.ok(d, f'Contatos válidos: {self.context.website} e {self.context.support_email}.')

    def check_review_url(self, d: DoctorCheck) -> DoctorResult:
        value = self.config.get('review_url') if self.config else None
        if not value or not self._valid_http_url(value):
            return self.issue(d, 'aviso', 'URL de revisão ausente ou inválida.', 'review_url não aponta para HTTP ou HTTPS.', 'A equipe de revisão pode não encontrar instruções de acesso.', 'Informe review_url no playtool.yaml.')
        return self.ok(d, f'URL de revisão configurada: {value}.')

    def check_gradle(self, d: DoctorCheck) -> DoctorResult:
        root = Path(self.context.project_dir)
        candidates = [root / 'gradlew', root / 'gradlew.bat', root / 'settings.gradle', root / 'settings.gradle.kts']
        found = [str(p.resolve()) for p in candidates if p.exists()]
        if not found:
            return self.issue(d, 'informação', 'Projeto Gradle não identificado na pasta atual.', 'Arquivos comuns do Gradle não foram encontrados.', 'O Doctor não poderá analisar configurações Android locais.', 'Execute o comando na raiz do projeto Android ou informe os artefatos manualmente.')
        return self.ok(d, 'Projeto Gradle identificado.', files=found)

    def check_manifest(self, d: DoctorCheck) -> DoctorResult:
        root = Path(self.context.project_dir)
        manifests = list(root.glob('**/src/main/AndroidManifest.xml'))
        if not manifests:
            return self.issue(d, 'informação', 'AndroidManifest não localizado.', 'Nenhum arquivo src/main/AndroidManifest.xml foi encontrado.', 'Permissões e App Links não puderam ser analisados.', 'Execute o Doctor na raiz do projeto Android.')
        text = manifests[0].read_text(encoding='utf-8', errors='replace')
        permissions = re.findall(r'android\.permission\.([A-Z0-9_]+)', text)
        app_links = 'android:autoVerify="true"' in text or "android:autoVerify='true'" in text
        return self.ok(d, f'AndroidManifest localizado. Permissões encontradas: {len(set(permissions))}. App Links: {"sim" if app_links else "não"}.', manifest=str(manifests[0].resolve()), permissions=sorted(set(permissions)), app_links=app_links)

    @staticmethod
    def _valid_http_url(value: str) -> bool:
        parsed = urlparse(value)
        return parsed.scheme in {'http', 'https'} and bool(parsed.netloc)


def build_context(config_path: Path, project_dir: Path | None = None) -> PublishingContext:
    context = PublishingContext(project_dir=str(project_dir or Path.cwd()), config_path=str(config_path))
    credentials = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if credentials:
        context.set_credentials_path(credentials, 'environment')
    return context


def run_doctor(config_path: Path, project_dir: Path | None = None, fix: bool = False) -> dict[str, Any]:
    context = build_context(config_path, project_dir)
    return DoctorRunner(context, config_path, fix=fix).run()


def format_doctor_report(report: dict[str, Any]) -> str:
    lines = ['Google Play Doctor.', '', 'Análise concluída.', '']
    summary = report['summary']
    lines.extend([
        f"Itens aprovados: {summary.get('aprovado', 0)}.",
        f"Informações: {summary.get('informação', 0)}.",
        f"Avisos: {summary.get('aviso', 0)}.",
        f"Erros: {summary.get('erro', 0)}.",
        f"Bloqueios: {summary.get('bloqueio', 0)}.",
        '',
        'Pronto para publicação.' if report['ready'] else 'Ainda não está pronto para publicação.',
    ])
    for index, item in enumerate(report['results'], start=1):
        lines.extend(['', f"Verificação {index} de {len(report['results'])}: {item['title']}.", f"Resultado: {item['status']}.", item['message']])
        if item.get('cause'):
            lines.extend(['', 'Causa:', item['cause']])
        if item.get('impact'):
            lines.extend(['', 'Impacto:', item['impact']])
        if item.get('recommendation'):
            lines.extend(['', 'Ação recomendada:', item['recommendation']])
        if item.get('fixed'):
            lines.extend(['', 'Correção automática aplicada: sim.'])
    return '\n'.join(lines) + '\n'
