# Histórico de alterações

Todas as mudanças relevantes deste projeto serão registradas neste arquivo.

O formato segue a ideia de Keep a Changelog e o projeto usa versionamento semântico.

## Não lançado

### Planejado

- modo tutorial guiado e totalmente textual;
- comando `playtool doctor`;
- auditoria de Manifest, permissões, App Links e requisitos da Google Play;
- publicação automatizada por GitHub Actions;
- suporte ampliado a idiomas e recursos gráficos.

## 1.3.1 - 2026-07-21

### Adicionado

- opção `playtool tutorial --execute`;
- teste real de acesso à API e inventário de versões;
- seleção e validação guiada de ícone, recurso gráfico e capturas;
- geração automática dos manifestos TXT e JSON;
- criação da edição temporária com upload de AAB, mapping e símbolos;
- preenchimento automático de textos, vídeo, contatos e imagens;
- validação remota da edição ao final do assistente;
- garantia de que o tutorial nunca executa `commit`;
- testes do fluxo remoto por simulação.

## 1.3.0

- adiciona o comando `playtool tutorial`;
- adiciona retomada com `--resume`;
- adiciona simulação com `--dry-run`;
- adiciona saída estruturada com `--json`;
- salva o progresso em `.playtool-tutorial.json`;
- aceita `S para sim` e `N para não`, além das palavras completas;
- proíbe barras gráficas, arte ASCII e separadores decorativos na saída principal;
- adiciona testes específicos de acessibilidade para a interface textual.

## 1.2.0 - 2026-07-21

### Adicionado

- gerenciamento de título, resumo e descrição completa da ficha da loja;
- suporte a vídeo promocional do YouTube;
- atualização e consulta de site, e-mail, telefone e idioma padrão;
- validação local de limites de caracteres;
- leitura de textos em arquivos UTF-8;
- comandos para consultar a ficha antes da confirmação;
- testes automatizados para textos e detalhes da listagem.

## 1.1.0 - 2026-07-21

### Adicionado

- gerenciamento integrado de ícone, recurso gráfico e capturas;
- inventário remoto de faixas e códigos de versão;
- bloqueio de `versionCode` duplicado;
- descarte seguro de edição;
- manifesto TXT e JSON com hashes SHA-256.

## 0.1.0 - 2026-07-21

### Adicionado

- estrutura inicial do toolkit;
- conversão e validação acessível de imagens;
- preparação de versão em teste aberto;
- upload de AAB, mapping e símbolos nativos;
- validação e confirmação explícita da edição.

## [Não lançado]

### Documentação arquitetural

- Padronização da pasta `doc/`.
- Padrão acessível para interfaces de linha de comando.
- Princípios de acessibilidade do CIATA.
- Especificações dos motores Tutorial, Wizard, Doctor e Learn.
- Contrato inicial de plugins.
- Contexto central de publicação.
- Diretrizes de relatórios e auditoria.
