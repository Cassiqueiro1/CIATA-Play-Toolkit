# Contexto de Publicação

## Objetivo

O `PublishingContext` concentra os dados necessários à publicação e evita que cada comando implemente sua própria descoberta e validação.

## Dados principais

- caminho do projeto;
- package name;
- namespace;
- nome da versão;
- código da versão;
- faixa;
- idioma;
- App Bundle;
- mapping;
- símbolos nativos;
- imagens;
- textos da loja;
- vídeo promocional;
- contatos;
- notas da versão;
- credencial referenciada;
- identificador da edição temporária;
- resultados de validação;
- manifesto da publicação.

## Regras

- segredos não devem ser serializados;
- caminhos devem ser normalizados;
- valores descobertos devem registrar sua origem;
- validações devem ser reutilizáveis;
- alterações devem produzir eventos de auditoria;
- o contexto deve poder ser exportado em JSON sem dados sensíveis.
