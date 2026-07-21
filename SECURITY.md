# Política de segurança

## Versões cobertas

Enquanto o projeto estiver em desenvolvimento inicial, somente a versão mais recente recebe correções de segurança.

## Como relatar uma vulnerabilidade

Não abra uma issue pública quando o problema envolver:

- credenciais da Google Play;
- tokens ou chaves privadas;
- possibilidade de publicar ou alterar uma ficha sem autorização;
- exposição de dados pessoais;
- execução arbitrária de comandos;
- leitura de arquivos fora do escopo esperado.

Envie o relato para:

```text
seguranca@ciata.org.br
```

Inclua:

- versão do toolkit;
- sistema operacional;
- passos para reproduzir;
- impacto esperado;
- prova de conceito sem dados reais;
- sugestão de correção, quando houver.

## Credenciais

O projeto deve:

- usar `GOOGLE_APPLICATION_CREDENTIALS` ou mecanismo seguro equivalente;
- nunca incorporar chaves ao código;
- nunca registrar tokens em logs;
- ocultar caminhos sensíveis quando o relatório for compartilhável;
- manter arquivos de credenciais fora do Git.

## Divulgação responsável

Pedimos tempo razoável para análise e correção antes da divulgação pública. O mantenedor informará o recebimento e o andamento quando possível.
