# Arquitetura

## Visão geral

O CIATA Play Publisher Toolkit é uma aplicação de linha de comando modular. O núcleo coordena configuração, validações, relatórios e operações da Google Play, mantendo a interface textual separada das regras de negócio.

## Camadas

### CLI

Responsável por:

- analisar argumentos;
- apresentar ajuda;
- solicitar confirmações;
- selecionar saída textual ou JSON;
- mapear códigos de saída.

A CLI não deve conter regras de publicação.

### Núcleo

Responsável por:

- carregar configuração;
- validar caminhos e entradas;
- padronizar mensagens e erros;
- controlar estado de uma edição;
- aplicar políticas de segurança.

### Serviços

Módulos especializados:

- `assets`: conversão e validação de imagens;
- `listing`: textos, contatos e recursos da ficha;
- `release`: artefatos e metadados de versão;
- `googleplay`: comunicação com a Android Publisher API;
- `manifest`: relatórios e hashes.

### Adaptadores externos

A integração com a Google Play deve ficar atrás de funções pequenas e testáveis. Código de interface não deve depender diretamente de respostas cruas da API.

## Estado da edição

Operações remotas usam uma edição temporária. O estado local deve registrar ao menos:

- pacote;
- identificador da edição;
- faixa;
- código da versão;
- nome da versão;
- arquivos enviados;
- hashes;
- data e hora;
- status atual.

Uma edição pode ser validada, descartada ou confirmada. A confirmação nunca deve ocorrer implicitamente.

## Formatos de saída

Cada operação importante deve oferecer:

- texto linear para uso humano;
- JSON estável para automações;
- código de saída previsível.

## Códigos de saída propostos

- `0`: sucesso;
- `1`: erro geral;
- `2`: entrada inválida;
- `3`: configuração ausente;
- `4`: falha de autenticação;
- `5`: falha de validação;
- `6`: operação cancelada;
- `7`: conflito de versão ou edição;
- `8`: falha remota da Google Play.

## Regras de dependência

- módulos de domínio não imprimem diretamente;
- a CLI não acessa credenciais diretamente;
- conversão de imagens não conhece a API da Google Play;
- relatórios recebem estruturas normalizadas;
- nenhuma operação destrutiva é chamada por efeito colateral.
