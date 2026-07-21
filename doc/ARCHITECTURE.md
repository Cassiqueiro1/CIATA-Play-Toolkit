# Arquitetura do CIATA Play Publisher Toolkit

## Visão

O projeto oferece uma forma acessível, auditável e automatizável de preparar e publicar aplicativos em lojas digitais, começando pela Google Play.

## Princípios arquiteturais

- acessibilidade como requisito funcional;
- separação entre descoberta, validação, preparação e publicação;
- confirmação explícita para operações de alto impacto;
- núcleo independente de interfaces específicas;
- saída humana e JSON equivalentes;
- credenciais fora do código e dos relatórios;
- componentes pequenos, testáveis e reutilizáveis.

## Camadas

### Interface de linha de comando

Interpreta argumentos, conduz perguntas e apresenta resultados.

### Motores interativos

- tutorial;
- wizard;
- doctor;
- learn.

### Contexto de publicação

Concentra dados, origens, validações e estado da edição.

### Serviços de domínio

- artefatos;
- imagens;
- listing;
- manifesto;
- inventário;
- relatórios;
- segurança.

### Adaptadores de plataforma

Implementam APIs externas, inicialmente Google Play.

### Plugins

Permitem novos destinos e integrações.

## Fluxo principal

1. Carregar configuração.
2. Descobrir projeto e artefatos.
3. Construir `PublishingContext`.
4. Executar validações locais.
5. Consultar estado remoto.
6. Gerar manifesto.
7. Criar edição temporária.
8. Enviar artefatos e metadados.
9. Validar edição.
10. Apresentar resumo.
11. Publicar somente após confirmação separada.

## Organização proposta

```text
playtool/
  cli/
  context/
  tutorial/
  wizard/
  doctor/
  learn/
  assets/
  listing/
  release/
  reports/
  security/
  platforms/
    google_play/
  plugins/
```

A migração para essa estrutura deve ser incremental para preservar compatibilidade com os comandos existentes.
