# Checklist do primeiro commit

## Antes do commit

- [ ] confirmar o nome do repositório;
- [ ] revisar o e-mail de segurança em `SECURITY.md`;
- [ ] revisar o link institucional no template de issues;
- [ ] executar `pytest -q`;
- [ ] verificar que não existem credenciais no diretório;
- [ ] confirmar que `.pytest_cache` e `__pycache__` não estão presentes;
- [ ] confirmar a versão `1.2.0` em `pyproject.toml`;
- [ ] revisar `README.md` com JAWS ou NVDA.

## Comandos sugeridos

```powershell
git init
git branch -M main
git add .
git status
git commit -m "feat: publica versão inicial do CIATA Play Publisher Toolkit"
```

Depois de criar o repositório remoto:

```powershell
git remote add origin URL_DO_REPOSITORIO
git push -u origin main
```

## Tag inicial

Após validar o conteúdo enviado:

```powershell
git tag -a v1.2.0 -m "CIATA Play Publisher Toolkit 1.2.0"
git push origin v1.2.0
```
