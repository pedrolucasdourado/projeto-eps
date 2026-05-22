# Relatório de Qualidade e Segurança — DevSecOps

**Projeto:** Assistente de Apreensão Inteligente (AAI) — Grupo 31  
**Repositório:** [FCTE-UNB-EPS5/assistente-de-apreensao-inteligente-computer-vision-grupo-31-1](https://github.com/FCTE-UNB-EPS5/assistente-de-apreensao-inteligente-computer-vision-grupo-31-1)  
**Período de referência:** Fase 1 — março a maio de 2026  
**Data da varredura:** 26/05/2026  
**Responsável pela auditoria:** Pipeline GitHub Actions (`DevSecOps-PCDF`)

---

## 1. Objetivo

Este documento substitui o relatório anteriormente previsto com **SonarQube**, consolidando a análise de **qualidade e segurança** do código-fonte do AAI por meio de ferramentas open source integradas à esteira DevSecOps:

| Camada | Ferramenta | Tipo | Escopo |
|--------|------------|------|--------|
| SAST | **Bandit** 1.9.x | Análise estática de segurança | Código Python em `src/` |
| SCA | **Safety** 3.8.x | Análise de composição de software | Dependências em `src/backend/requirements.txt` |

A substituição foi adotada por ser mais leve, não exigir servidor dedicado e encaixar diretamente no GitHub Actions, mantendo auditoria automática a cada `push` e `pull_request`.

---

## 2. Configuração da esteira DevSecOps

Arquivo: `.github/workflows/devsecops.yml`

```yaml
name: DevSecOps-PCDF
on: [push, pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install bandit safety
      - run: bandit -r src/
      - run: safety check
```

**Gatilhos:** todo commit e pull request na branch principal e derivadas.  
**Ambiente de execução:** `ubuntu-latest`, Python 3.12.  
**Política de bloqueio:** falha do job quando Bandit ou Safety retornam código de saída diferente de zero (achados reportados).

> **Observação operacional:** recomenda-se ajustar o passo do Safety para `safety check -r src/backend/requirements.txt`, garantindo que as dependências do backend sejam sempre auditadas no CI (o comando `safety check` isolado analisa apenas pacotes instalados no ambiente do runner).

---

## 3. Resumo executivo

| Indicador | SAST (Bandit) | SCA (Safety) |
|-----------|---------------|--------------|
| Escopo analisado | 5.155 linhas de código Python | 14 pacotes declarados |
| Vulnerabilidades **críticas / alta** | **0** | 0 (classificação Safety por CVE/advisory) |
| Achados **médios** | 11 | 8 advisories em 5 pacotes |
| Achados **baixos** | 31 | — |
| **Status geral** | ✅ Sem falhas críticas no código | ⚠️ Dependências desatualizadas com CVEs conhecidos |

**Conclusão:** o código-fonte **não apresenta vulnerabilidades de severidade alta ou crítica** segundo Bandit. A principal superfície de risco identificada está nas **bibliotecas de terceiros**, com 8 advisories em pacotes de autenticação, upload, templates e geração de PDF/imagem. Nenhum achado bloqueia imediatamente o uso em ambiente de desenvolvimento/homologação, porém **atualizações de dependências são recomendadas** antes de produção.

---

## 4. Resultados SAST — Bandit

**Comando:** `bandit -r src/ -f txt`  
**Data:** 26/05/2026 21:47 UTC

### 4.1 Métricas consolidadas

| Severidade | Quantidade |
|------------|------------|
| Alta (High) | **0** |
| Média (Medium) | 11 |
| Baixa (Low) | 31 |
| **Total** | **42** |

| Confiança | Quantidade |
|-----------|------------|
| Alta | 32 |
| Média | 3 |
| Baixa | 7 |

### 4.2 Distribuição por tipo de achado

| ID | Regra | Ocorrências | Severidade | Interpretação |
|----|-------|-------------|------------|---------------|
| B101 | `assert_used` | 29 | Baixa | Uso de `assert` para invariantes internas; aceitável em dev, substituir por tratamento explícito em produção |
| B608 | `hardcoded_sql_expressions` | 9 | Média | Montagem dinâmica de SQL com f-strings; **falso positivo parcial** — cláusulas `WHERE` usam placeholders parametrizados (`%s`) |
| B704 | `markupsafe_markup_xss` | 1 | Média | Uso de `Markup` em HTML de PDF; dados são gerados internamente (imagem base64), não de entrada do usuário |
| B108 | `hardcoded_tmp_directory` | 1 | Média | `HOME=/tmp` na conversão DOCX→PDF via LibreOffice |
| B404 / B603 | `subprocess` | 2 | Baixa | Conversão headless com binário fixo (`soffice`), sem shell |
| — | Outros | 0 | — | — |

### 4.3 Arquivos com maior concentração de achados

| Arquivo | Achados |
|---------|---------|
| `src/backend/app/repositories/catalog_repo.py` | 18 |
| `src/backend/app/routers/cadastros.py` | 11 |
| `src/backend/app/repositories/users_repo.py` | 5 |
| `src/backend/app/services/acba_docx_pdf_service.py` | 3 |
| Demais arquivos | ≤ 2 cada |

### 4.4 Análise técnica dos achados médios

1. **SQL dinâmico (B608):** consultas em repositórios (`catalog_repo`, `acba_repository`, `users_repo`) montam cláusulas `WHERE` a partir de listas fixas de condições; valores de filtro passam por parâmetros nomeados, mitigando injeção SQL. Recomenda-se documentar com `# nosec B608` onde a revisão manual confirmar segurança, ou migrar para query builders.

2. **Markup XSS (B704):** em `acba_pdf_context.py`, HTML embute imagem PNG gerada pelo sistema (padrão de desbloqueio). Não há concatenação de input externo não sanitizado.

3. **Diretório temporário (B108):** variável de ambiente para LibreOffice em container; aceitável em ambiente dockerizado isolado.

**Veredicto SAST:** ✅ **Aprovado** — zero vulnerabilidades críticas ou altas; achados médios revisados manualmente como risco controlado ou falso positivo.

---

## 5. Resultados SCA — Safety

**Comando:** `safety check -r src/backend/requirements.txt --full-report`  
**Data:** 26/05/2026 18:47  
**Pacotes escaneados:** 14  
**Advisories reportados:** 8 (em 5 pacotes)

### 5.1 Vulnerabilidades por dependência

| Pacote | Versão atual | CVE / Advisory | Descrição resumida | Correção sugerida |
|--------|--------------|----------------|--------------------|-------------------|
| `python-jose` | 3.3.0 | CVE-2024-33664 | DoS via JWT bomb (JWE comprimido) | ≥ 3.4.0 |
| `python-jose` | 3.3.0 | CVE-2024-33663 | Confusão de algoritmo em chaves ECDSA | ≥ 3.4.0 |
| `python-multipart` | 0.0.20 | CVE-2026-40347 | DoS em parsing multipart (preamble/epilogue) | ≥ 0.0.26 |
| `python-multipart` | 0.0.20 | CVE-2026-24486 | Path traversal em upload com filename absoluto | ≥ 0.0.26 |
| `Jinja2` | 3.1.5 | CVE-2025-27516 | Escape de sandbox via filtro `\|attr` | ≥ 3.1.6 |
| `weasyprint` | 63.1 | CVE-2025-68616 | SSRF em redirects de URL fetcher | ≥ 68.0 |
| `Pillow` | 11.0.0 | CVE-2026-25990 | Out-of-bounds write em PSD | ≥ 12.1.1 |
| `Pillow` | 11.0.0 | CVE-2026-40192 | DoS via FITS gzip bomb | ≥ 12.2.0 |

### 5.2 Pacotes sem advisories reportados

`fastapi`, `uvicorn`, `psycopg2-binary`, `bcrypt`, `pydantic-settings`, `email-validator`, `python-docx`, `docxtpl`, `google-genai` — nenhuma vulnerabilidade conhecida na base consultada pelo Safety v3.8.0.

### 5.3 Plano de remediação recomendado

```text
python-jose[cryptography]>=3.4.0
python-multipart>=0.0.26
Jinja2>=3.1.6
weasyprint>=68.0
Pillow>=12.2.0
```

Após atualização, reexecutar `safety check -r src/backend/requirements.txt` e a suíte de testes (`pytest`) para validar compatibilidade.

**Veredicto SCA:** ⚠️ **Atenção** — dependências com CVEs conhecidos; nenhum classificado como crítico imediato pelo Safety, porém **atualização obrigatória antes de deploy em produção**.

---

## 6. Comparativo: SonarQube → Bandit + Safety

| Critério | SonarQube (planejado) | Bandit + Safety (implementado) |
|----------|----------------------|--------------------------------|
| Infraestrutura | Servidor/sonarcloud dedicado | Zero infra extra; roda no GitHub Actions |
| Custo | Licença ou SonarCloud | Open source |
| SAST (código) | Multi-linguagem, quality gates | Python-focused; regras OWASP/CWE |
| SCA (dependências) | Plugin separado / Dependabot | Safety integrado no mesmo workflow |
| Integração CI | Webhook + token | Nativo em `.github/workflows/` |
| Critério de aceite PCDF | Zero blockers críticos | **Atendido no código (0 High Bandit)** |

A mudança mantém o espírito do requisito não funcional *"Pipeline CI/CD e Qualidade — bloqueio de merge se houver falha de segurança"*, com ferramentas adequadas ao stack Python/FastAPI do projeto.

---

## 7. Evidências anexáveis

| Evidência | Local / comando |
|-----------|-----------------|
| Workflow DevSecOps | `.github/workflows/devsecops.yml` |
| Dependências auditadas | `src/backend/requirements.txt` |
| Relatório Bandit (JSON) | Gerado localmente: `bandit -r src/ -f json -o bandit-report.json` |
| Relatório Safety | Saída do comando `safety check -r src/backend/requirements.txt --full-report` |
| Execução CI | Aba **Actions** do repositório GitHub → workflow `DevSecOps-PCDF` |

### Comandos para reproduzir localmente

```bash
python3 -m venv .venv-security
source .venv-security/bin/activate
pip install bandit safety
bandit -r src/ -f txt
safety check -r src/backend/requirements.txt --full-report
```

---

## 8. Declaração de conformidade (checklist Fase 1)

| Item do checklist | Status |
|-------------------|--------|
| Relatório de qualidade e segurança (substituindo SonarQube) | ✅ Este documento |
| Sem vulnerabilidades **críticas** no código-fonte (SAST) | ✅ 0 achados High no Bandit |
| Auditoria automatizada no CI/CD | ✅ GitHub Actions `DevSecOps-PCDF` |
| Dependências auditadas (SCA) | ⚠️ 8 advisories — remediação planejada |

---

*Documento gerado automaticamente a partir das varreduras Bandit e Safety executadas em 26/05/2026 sobre o repositório do Assistente de Apreensão Inteligente — Grupo 31.*
