# Especificação do assistente de primeira publicação

## Comando

```text
playtool tutorial
```

## Objetivo

Guiar uma pessoa pela configuração e primeira publicação sem exigir conhecimento prévio da Google Play Console ou da Android Publisher API.

## Princípios

- uma decisão por etapa;
- texto curto e navegável;
- nenhuma barra gráfica ou arte ASCII;
- retomada após interrupção;
- confirmação antes de mudanças remotas;
- nenhuma credencial exibida;
- opção de explicar termos técnicos;
- modo de simulação sem enviar nada.

## Fluxo

1. verificar Python e dependências;
2. localizar ou criar `playtool.yaml`;
3. confirmar pacote, faixa e idioma;
4. verificar credenciais;
5. testar acesso à API;
6. localizar o AAB;
7. registrar nome e notas da versão;
8. localizar mapping e símbolos;
9. orientar preparação das imagens;
10. coletar textos e vídeo da ficha;
11. coletar contatos;
12. verificar dados do manifesto;
13. apresentar resumo final;
14. preparar edição em modo rascunho;
15. manter a publicação em comando separado com confirmação explícita.

## Modos

```text
playtool tutorial
playtool tutorial --resume
playtool tutorial --dry-run
playtool tutorial --json
```

## Confirmações

Prompts comuns devem usar:

```text
Deseja continuar?
Digite S para sim ou N para não.
```

Respostas aceitas:

- `S` ou `sim`;
- `N`, `não` ou `nao`;
- equivalentes em inglês para uso futuro de localização.

Operações de publicação continuam exigindo frase completa e não podem ser confirmadas apenas com `S`.

## Estado de retomada

Salvar somente dados não secretos:

- etapa atual;
- caminhos escolhidos;
- pacote;
- faixa;
- idioma;
- resultados de validação;
- identificador de edição, quando aplicável.

O arquivo padrão é:

```text
.playtool-tutorial.json
```

## Exemplo de interação

```text
CIATA Play Publisher Toolkit.
Assistente de primeira publicação.

Etapa 1 de 15: ambiente Python.
Python encontrado: 3.13.2.
Resultado: aprovado.

Deseja continuar?
Digite S para sim ou N para não.
```

## Critérios de aceite

- todas as etapas funcionam apenas com teclado;
- nenhuma etapa depende de cor ou posição visual;
- não existem barras gráficas, molduras ou separadores decorativos;
- o leitor de telas não recebe linhas reescritas continuamente;
- o tutorial pode ser interrompido e retomado;
- nenhuma publicação ocorre sem confirmação específica;
- `--dry-run` não altera recursos remotos;
- mensagens de erro indicam a etapa e a correção necessária.


## Execução remota controlada

O parâmetro `--execute` habilita apenas a criação e o preenchimento de uma edição temporária. O assistente pode enviar o App Bundle, artefatos de depuração, textos, contatos e imagens, e então solicitar a validação da edição.

O tutorial não chama a operação `commit`. A publicação permanece em um comando separado e exige a frase de confirmação de alto impacto. `--execute` e `--dry-run` são mutuamente exclusivos.

## Padrão das perguntas

Confirmações devem informar `S para sim` e `N para não`. As formas completas `sim`, `não` e `nao` também são aceitas. Não usar barras gráficas, arte ASCII, molduras ou separadores repetitivos.
