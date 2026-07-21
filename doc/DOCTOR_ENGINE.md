# Motor de Diagnóstico

## Objetivo

O comando `playtool doctor` analisa o projeto, identifica bloqueios, apresenta recomendações e, quando autorizado, corrige problemas seguros.

## Modelo de verificação

Cada verificação deve possuir:

- identificador;
- categoria;
- título;
- descrição;
- severidade;
- função de diagnóstico;
- causa provável;
- impacto;
- ação recomendada;
- correção automática opcional;
- referência documental.

## Severidades

- informação;
- aviso;
- erro;
- bloqueio.

## Resultado acessível

```text
Verificação: código da versão.
Resultado: erro.

Causa:
O código da versão 12 já existe na Google Play.

Impacto:
O App Bundle não pode ser enviado.

Ação recomendada:
Aumente o versionCode e gere um novo App Bundle.
```

## Correção automática

`playtool doctor --fix` só pode alterar arquivos quando:

- a correção for determinística;
- existir cópia de segurança ou reversão clara;
- o usuário confirmar a alteração;
- a mudança for registrada no relatório.

Correções destrutivas ou ambíguas não devem ser automatizadas.

## Categorias iniciais

- ambiente Python;
- configuração;
- credenciais;
- projeto Gradle;
- AndroidManifest;
- SDKs;
- App Bundle;
- código da versão;
- mapping;
- símbolos nativos;
- permissões;
- App Links;
- textos da loja;
- imagens;
- contatos;
- faixa de publicação.
