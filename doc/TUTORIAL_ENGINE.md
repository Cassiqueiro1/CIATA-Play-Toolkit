# Motor do Tutorial

## Objetivo

O tutorial ensina o processo de publicação, verifica o ambiente e prepara o usuário para executar o fluxo com segurança.

## Características

- etapas declarativas;
- retomada após interrupção;
- detecção automática de itens já concluídos;
- explicações opcionais;
- modo de simulação;
- saída JSON;
- nenhuma publicação automática.

## Modelo de etapa

Cada etapa deve declarar:

```yaml
id: verify-python
title: Verificar ambiente Python
required: true
can_skip: false
resume: true
interactive: false
```

Campos recomendados:

- `id`: identificador estável;
- `title`: nome apresentado ao usuário;
- `required`: indica se bloqueia o fluxo;
- `can_skip`: permite avanço manual;
- `resume`: registra conclusão;
- `interactive`: exige entrada do usuário;
- `dependencies`: etapas anteriores;
- `learn_topic`: conteúdo relacionado;
- `validator`: função de validação;
- `executor`: função opcional de execução.

## Estados

Uma etapa pode terminar como:

- `pending`;
- `running`;
- `passed`;
- `warning`;
- `failed`;
- `skipped`;
- `cancelled`.

Na saída humana, esses estados devem ser traduzidos e escritos por extenso.

## Retomada

O estado deve ser salvo em arquivo local, sem credenciais ou segredos.

Ao retomar, o tutorial deve:

1. informar a última etapa concluída;
2. validar se os arquivos ainda existem;
3. repetir apenas etapas invalidadas;
4. pedir confirmação antes de continuar.

## Detecção inteligente

Quando uma informação já estiver disponível e válida, o tutorial deve anunciar a descoberta e evitar perguntas redundantes.

## Segurança

O tutorial pode preparar e validar uma edição temporária, mas o commit final deve permanecer em comando separado.
