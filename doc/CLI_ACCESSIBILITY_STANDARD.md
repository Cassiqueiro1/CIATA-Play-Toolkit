# Padrão de Acessibilidade para Interface de Linha de Comando

## Objetivo

Este documento define requisitos obrigatórios para toda saída textual, pergunta interativa, mensagem de erro, relatório e fluxo guiado do CIATA Play Publisher Toolkit.

O padrão foi criado para que a ferramenta possa ser utilizada integralmente com teclado, leitores de tela e linhas Braille, sem depender de cor, posição visual, caracteres decorativos ou atualização dinâmica da mesma linha.

## Princípios obrigatórios

1. Toda informação visual deve possuir equivalente textual completo.
2. Nenhuma informação pode depender exclusivamente de cor.
3. A saída não deve utilizar barras gráficas de progresso.
4. A saída não deve utilizar molduras ou separadores formados por caracteres repetidos.
5. A mesma linha não deve ser sobrescrita continuamente.
6. Estados devem ser escritos por extenso.
7. Toda pergunta deve informar claramente as respostas aceitas.
8. Toda mensagem de erro deve informar causa, impacto e ação recomendada.
9. Uma informação relevante deve ocupar uma linha própria quando isso melhorar a compreensão.
10. A ordem de leitura deve ser lógica sem depender de alinhamento em colunas.

## Conteúdo proibido na saída principal

Não utilizar:

- barras com blocos, quadrados ou caracteres Unicode;
- fileiras de sinais de igual, hífens, sinais de adição ou asteriscos;
- desenhos ASCII;
- indicadores compostos apenas por símbolos;
- emojis como único indicador de estado;
- tabelas cuja compreensão dependa do alinhamento visual;
- mensagens que desaparecem por sobrescrita da linha atual.

## Progresso

Forma recomendada:

```text
Progresso: etapa 4 de 12.
```

Forma não permitida:

```text
████████░░░░ 33%
```

## Estados

Forma recomendada:

```text
Resultado: aprovado.
Resultado: aviso.
Resultado: erro.
```

Também é aceitável:

```text
Package name: correto.
Target SDK: correto.
App Links: não encontrados.
```

Não utilizar símbolos isolados como marca de aprovação ou falha.

## Perguntas

Formato padrão:

```text
Deseja continuar?
Digite S para sim ou N para não.
```

Respostas aceitas, sem diferenciar maiúsculas e minúsculas:

- `S`
- `Sim`
- `N`
- `Não`
- `Nao`

O formato abreviado `S/N` pode ser usado apenas como complemento, nunca como única explicação.

## Mensagens de erro

Estrutura recomendada:

```text
Erro: o arquivo App Bundle não foi encontrado.

Arquivo esperado:
app/build/outputs/bundle/release/app-release.aab

Impacto:
A publicação não pode continuar.

Ação recomendada:
Gere o App Bundle de release e execute novamente esta etapa.
```

## Saída resumida e automação

A ferramenta deve oferecer:

- saída humana acessível como padrão;
- `--quiet` para reduzir mensagens informativas;
- `--json` para integração com automações;
- códigos de saída estáveis e documentados.

O modo JSON não substitui a saída humana acessível.

## Compatibilidade mínima esperada

A saída deve ser testada, sempre que possível, com:

- NVDA no Windows;
- JAWS no Windows;
- Narrador do Windows;
- VoiceOver no macOS;
- leitores de tela em terminais Linux;
- linhas Braille conectadas aos leitores de tela anteriores.

## Critério de aceite

Uma nova funcionalidade de terminal só pode ser considerada concluída quando:

- puder ser executada integralmente pelo teclado;
- não depender de informação visual;
- produzir mensagens compreensíveis fora do contexto visual;
- tiver perguntas explícitas e previsíveis;
- não introduzir ruído decorativo na fala do leitor de tela.
