# Motor do Assistente de Publicação

## Objetivo

O assistente coleta dados, localiza artefatos, valida a configuração e prepara uma edição completa para publicação.

## Diferença entre tutorial e assistente

O tutorial explica conceitos e acompanha iniciantes.

O assistente prioriza execução, reutiliza valores existentes e faz menos pausas.

## Fluxo sugerido

1. Carregar configuração.
2. Localizar o projeto Android.
3. Validar credenciais.
4. Consultar inventário remoto.
5. Localizar App Bundle.
6. Validar código da versão.
7. Localizar mapping e símbolos.
8. Validar textos e contatos.
9. Validar imagens.
10. Gerar manifesto.
11. Criar edição temporária.
12. Enviar artefatos.
13. Validar edição.
14. Apresentar resumo.
15. Encerrar sem commit automático.

## Perguntas

O motor deve utilizar componentes reutilizáveis para:

- confirmação sim ou não;
- entrada de caminho;
- entrada de texto curto;
- seleção de faixa;
- seleção de idioma;
- confirmação de alto impacto.

## Não interativo

Todo fluxo deve possuir equivalente por argumentos, arquivo de configuração ou JSON, permitindo integração contínua.
