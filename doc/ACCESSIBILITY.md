# Diretrizes de acessibilidade

## Objetivo

Permitir que uma pessoa cega ou com baixa visão prepare e publique um aplicativo Android usando somente teclado, terminal e leitor de telas.

## Saída textual

Mensagens devem ser lineares, curtas e autossuficientes. Use linhas em branco para separar blocos de informação.

Não use na saída principal:

- barras de progresso gráficas;
- desenhos ou molduras em ASCII;
- sequências decorativas de sinais de igual, hífen, mais, asterisco ou bloco;
- emojis como único indicador de estado;
- atualizações que reescrevem continuamente a mesma linha;
- informação comunicada somente por cor, alinhamento ou posição.

Uma mensagem de erro deve informar:

1. o que falhou;
2. qual valor foi encontrado;
3. qual valor era esperado;
4. como corrigir;
5. se alguma alteração remota ocorreu.

## Progresso

Use etapas numeradas e eventos discretos:

```text
Etapa 3 de 8: envio do App Bundle.
Upload concluído.
Código da versão recebido: 6.
```

Não anuncie percentuais em alta frequência.

## Confirmações

Operações seguras podem aceitar confirmações curtas, desde que o significado seja explicado:

```text
Deseja continuar?
Digite S para sim ou N para não.
```

Também devem ser aceitas as palavras completas `sim` e `não`, sem diferenciar maiúsculas de minúsculas.

Operações de alto impacto devem exigir frase explícita e informar:

- aplicativo;
- faixa;
- versão;
- código;
- efeito da ação.

## Teclado e prompts

- todas as ações devem funcionar sem mouse;
- `Enter` confirma apenas opções seguras;
- o valor padrão deve ser anunciado por extenso;
- respostas aceitas devem ser descritas;
- ofereça opção não interativa para automação;
- o usuário deve poder digitar `sair` em qualquer pergunta para interromper e salvar o estado.

## Compatibilidade

Testar, quando possível, com:

- JAWS no Windows;
- NVDA no Windows;
- VoiceOver no macOS;
- Orca no Linux;
- PowerShell, Prompt de Comando e terminais comuns.

## Conteúdo visual

Capturas, ícones e gráficos devem ser acompanhados de inventário textual contendo nome, dimensão, formato, tamanho, transparência e resultado da validação.

## JSON

A saída JSON deve conter os mesmos fatos essenciais da saída textual, sem exigir interpretação visual.
