# API de Plugins

## Objetivo

Permitir que novos destinos de publicação e integrações sejam adicionados sem acoplamento ao núcleo.

## Exemplos futuros

- Google Play;
- F-Droid;
- Amazon Appstore;
- Huawei AppGallery;
- App Store Connect;
- Microsoft Store;
- GitHub Actions;
- Azure DevOps.

## Contrato mínimo

Um plugin de publicação deve declarar:

- identificador;
- nome;
- versão da API suportada;
- comandos registrados;
- esquema de configuração;
- verificações de diagnóstico;
- operações de preparação;
- operações de validação;
- operação de publicação;
- capacidade de descarte ou reversão;
- requisitos de credenciais.

## Segurança

Plugins não podem:

- registrar segredos em logs;
- publicar sem confirmação explícita, salvo em modo não interativo previamente autorizado;
- alterar arquivos fora do projeto sem consentimento;
- modificar a política de acessibilidade da saída.

## Acessibilidade

Todo plugin deve obedecer ao `CLI_ACCESSIBILITY_STANDARD.md`.
