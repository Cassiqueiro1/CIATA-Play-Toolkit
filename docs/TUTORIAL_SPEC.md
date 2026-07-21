# Especificação inicial do modo tutorial

## Comando

```text
playtool tutorial
```

## Objetivo

Guiar uma pessoa pela configuração e primeira publicação sem exigir conhecimento prévio da Google Play Console ou da Android Publisher API.

## Princípios

- uma decisão por etapa;
- texto curto e navegável;
- retomada após interrupção;
- confirmação antes de mudanças remotas;
- nenhuma credencial exibida;
- opção de explicar termos técnicos;
- modo de simulação sem enviar nada.

## Fluxo proposto

1. verificar Python e dependências;
2. localizar ou criar `playtool.yaml`;
3. configurar pacote e faixa padrão;
4. verificar credenciais;
5. testar acesso à API;
6. localizar o AAB;
7. identificar `versionCode` e `versionName`;
8. localizar mapping e símbolos;
9. preparar e validar imagens;
10. preencher textos e contatos;
11. gerar manifesto;
12. apresentar resumo final;
13. criar edição em modo rascunho;
14. validar a edição;
15. solicitar confirmação separada para publicar.

## Modos

```text
playtool tutorial
playtool tutorial --resume
playtool tutorial --dry-run
playtool tutorial --json
playtool tutorial --verbose
```

## Estado de retomada

Salvar somente dados não secretos:

- etapa atual;
- caminhos escolhidos;
- pacote;
- faixa;
- idioma;
- resultados de validação;
- identificador de edição, quando aplicável.

## Exemplo de interação

```text
CIATA Play Publisher Toolkit.
Tutorial de primeira publicação.

Etapa 1 de 15: ambiente Python.
Python encontrado: 3.13.2.
Resultado: aprovado.

Pressione Enter para continuar ou digite sair para encerrar.
```

## Critérios de aceite

- todas as etapas funcionam apenas com teclado;
- nenhuma etapa depende de cor ou posição visual;
- o leitor de telas não recebe linhas reescritas continuamente;
- o tutorial pode ser interrompido e retomado;
- nenhuma publicação ocorre sem confirmação específica;
- `--dry-run` não altera recursos remotos;
- mensagens de erro indicam a etapa e a correção necessária.
