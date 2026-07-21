# Diretrizes de acessibilidade

## Objetivo

Permitir que uma pessoa cega ou com baixa visão prepare e publique um aplicativo Android usando somente teclado, terminal e leitor de telas.

## Saída textual

Mensagens devem ser lineares, curtas e autossuficientes. Evite tabelas largas, arte ASCII, barras de progresso animadas e atualizações que reescrevem a mesma linha.

Uma mensagem de erro deve informar:

1. o que falhou;
2. qual valor foi encontrado;
3. qual valor era esperado;
4. como corrigir;
5. se alguma alteração remota ocorreu.

## Progresso

Use etapas numeradas e eventos discretos:

```text
Etapa 3 de 8: enviando o bundle.
Upload concluído.
Código de versão recebido: 6.
```

Não anuncie percentuais em alta frequência.

## Confirmações

Operações de alto impacto devem exigir frase explícita e informar:

- aplicativo;
- faixa;
- versão;
- código;
- efeito da ação.

## Teclado e prompts

- todas as ações devem funcionar sem mouse;
- `Enter` confirma apenas opções seguras;
- respostas aceitas devem ser descritas por extenso;
- não use apenas letras soltas sem explicar o significado;
- ofereça opção não interativa para automação.

## Compatibilidade

Testar, quando possível, com:

- JAWS no Windows;
- NVDA no Windows;
- VoiceOver no macOS;
- Orca no Linux;
- terminal padrão e PowerShell.

## Conteúdo visual

Capturas, ícones e gráficos devem ser acompanhados de inventário textual contendo nome, dimensão, formato, tamanho, transparência e resultado da validação.

## JSON

A saída JSON deve conter os mesmos fatos essenciais da saída textual, sem exigir interpretação visual.
