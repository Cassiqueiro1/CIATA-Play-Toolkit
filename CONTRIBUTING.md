# Como contribuir

Obrigado por considerar uma contribuição ao CIATA Play Publisher Toolkit.

## Princípios

Toda contribuição deve preservar:

- uso completo por teclado;
- saída textual compreensível por leitores de tela;
- ausência de dependência obrigatória de cor, animação ou interface gráfica;
- mensagens de erro com problema, causa provável e ação recomendada;
- segurança em operações destrutivas;
- nenhum segredo em logs, relatórios ou testes.

## Preparar o ambiente

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

No Linux ou macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

## Antes de enviar uma alteração

Execute:

```powershell
pytest -q
```

Verifique também:

- comandos novos possuem ajuda clara;
- mensagens funcionam sem contexto visual;
- opções perigosas exigem confirmação explícita;
- arquivos e textos usam UTF-8;
- exemplos não contêm chaves, tokens ou dados pessoais;
- documentação foi atualizada.

## Commits

Prefira commits pequenos e coerentes. Exemplos:

```text
feat: adiciona validação de App Links
fix: evita confirmação duplicada de edição
 docs: documenta fluxo de teste aberto
```

## Pull requests

A descrição deve informar:

- problema resolvido;
- solução adotada;
- impactos de acessibilidade;
- testes executados;
- riscos ou limitações;
- capturas somente quando úteis, sempre acompanhadas por descrição textual.

## Relatando barreiras de acessibilidade

Barreiras de acessibilidade são defeitos funcionais, não melhorias cosméticas. Informe:

- leitor de tela e versão;
- sistema operacional;
- comando executado;
- saída recebida;
- saída esperada;
- passos para reproduzir.
