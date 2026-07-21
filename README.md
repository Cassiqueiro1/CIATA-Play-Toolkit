# CIATA Play Publisher Toolkit

Toolkit de linha de comando acessível para preparar, validar e publicar aplicativos Android na Google Play sem depender da navegação visual no Play Console.

Versão atual: **1.2.0**.

## Propósito

O projeto foi criado para permitir que uma pessoa cega ou com baixa visão execute o fluxo de publicação usando teclado, terminal e leitor de telas. As mesmas decisões também tornam a ferramenta mais segura e previsível para qualquer desenvolvedor.

## Recursos atuais

- conversão e validação de imagens;
- presets para ícone e recurso gráfico;
- inventário de faixas e códigos de versão;
- upload de AAB, mapping e símbolos nativos;
- preparação de versão em teste aberto;
- gerenciamento de ícone, recurso gráfico e capturas;
- título, resumo, descrição completa e vídeo do YouTube;
- site, e-mail, telefone e idioma padrão;
- manifesto TXT e JSON com hashes SHA-256;
- validação, descarte e confirmação explícita de edição;
- saída textual linear e JSON para automações.

## Princípios de acessibilidade e segurança

- nenhuma operação exige mouse;
- nenhuma informação depende apenas de cor ou posição;
- mensagens informam problema, valor, expectativa e ação necessária;
- nenhuma publicação ocorre automaticamente;
- operações destrutivas possuem comandos separados;
- credenciais são lidas por `GOOGLE_APPLICATION_CREDENTIALS`;
- segredos não devem aparecer em logs ou relatórios.

Leia também:

- [Arquitetura](docs/ARCHITECTURE.md)
- [Diretrizes de acessibilidade](docs/ACCESSIBILITY.md)
- [Especificação do tutorial](docs/TUTORIAL_SPEC.md)
- [Roadmap](ROADMAP.md)
- [Como contribuir](CONTRIBUTING.md)

## Instalação no Windows com PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

## Instalação no Linux ou macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Configuração inicial

```powershell
playtool init
```

O arquivo padrão usa a faixa `beta`, correspondente ao teste aberto.

Configure a conta de serviço:

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="D:\chaves\conta-servico.json"
```

## Converter e validar imagens

```powershell
playtool assets convert --input logo.png --output build\icon.png --preset icon --mode contain
playtool assets convert --input arte.png --output build\feature.png --preset feature --mode cover
playtool assets validate --input build\icon.png --kind icon
playtool assets validate --input build\feature.png --kind feature
```

## Consultar versões existentes

```powershell
playtool play inventory
```

## Gerar manifesto da versão

```powershell
playtool release manifest `
  --aab app-release.aab `
  --name "1.0.0-beta01" `
  --notes "Primeira versão beta pública." `
  --mapping mapping.txt `
  --symbols native-debug-symbols.zip `
  --output release
```

## Preparar uma edição em teste aberto

```powershell
playtool play prepare `
  --aab app-release.aab `
  --name "1.0.0-beta01" `
  --notes "Primeira versão beta pública." `
  --mapping mapping.txt `
  --symbols native-debug-symbols.zip
```

A versão permanece como rascunho.

## Atualizar textos da ficha

```powershell
playtool listing text-update `
  --title-file "textos\titulo.txt" `
  --short-file "textos\resumo.txt" `
  --full-file "textos\descricao-completa.txt" `
  --video "https://youtu.be/CODIGO"
```

## Atualizar contatos

```powershell
playtool listing details-update `
  --default-language "pt-BR" `
  --website "https://ciata.org.br" `
  --email "contato@ciata.org.br"
```

## Enviar imagens

```powershell
playtool listing replace --kind icon build\icon.png
playtool listing replace --kind feature build\feature.png
playtool listing replace --kind screenshot screenshots\01.png screenshots\02.png
```

## Conferir e concluir

```powershell
playtool listing text-show
playtool listing details-show
playtool play validate
```

Descartar tudo sem publicar:

```powershell
playtool play discard
```

Confirmar a edição:

```powershell
playtool play commit
```

## Testes

```powershell
python -m pip install -r requirements-dev.txt
pytest -q
```

## Estado do projeto

O toolkit está em desenvolvimento ativo. Antes de usar em uma conta de produção, teste com uma faixa não pública e confira o resumo textual completo.

## Licença

Distribuído sob a licença MIT. Consulte [LICENSE](LICENSE).
