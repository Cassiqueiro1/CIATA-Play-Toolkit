# Guia de Experiência da Interface de Linha de Comando

## Estrutura de uma etapa interativa

Toda etapa guiada deve seguir esta ordem quando aplicável:

1. Identificação da etapa.
2. Objetivo.
3. Informação encontrada ou solicitada.
4. Resultado da validação.
5. Consequência.
6. Próxima ação.

Exemplo:

```text
Etapa 4 de 12: App Bundle.

Objetivo:
Localizar e validar o arquivo de publicação.

Arquivo encontrado:
app-release.aab

Versão: 1.0.0.
Código da versão: 12.

Resultado: aprovado.

Deseja continuar?
Digite S para sim ou N para não.
```

## Títulos

Títulos devem ser curtos e lidos naturalmente.

Recomendado:

```text
Assistente de publicação.
```

Evitar caixa alta integral, molduras e títulos cercados por símbolos.

## Listas

Listas devem ser lineares e não depender de colunas.

```text
Itens aprovados: 8.
Avisos: 2.
Erros: 0.
```

Ao detalhar:

```text
Aviso 1 de 2.
App Links não encontrados.
```

## Caminhos e valores técnicos

O rótulo deve aparecer antes do valor:

```text
Arquivo:
app/build/outputs/bundle/release/app-release.aab
```

## Confirmações de alto impacto

Uma confirmação de publicação deve informar:

- operação;
- aplicativo;
- faixa;
- versão;
- se a ação é reversível;
- frase de confirmação exigida.

## Consistência terminológica

Usar sempre os mesmos termos:

- App Bundle;
- código da versão;
- nome da versão;
- faixa de publicação;
- edição temporária;
- validar;
- publicar;
- descartar edição.
