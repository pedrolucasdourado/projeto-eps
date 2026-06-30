#!/usr/bin/env python3
"""Gera Relatório de Avaliação DevSecOps — reavaliação pós Fase 2."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def shade(cell, color: str) -> None:
    el = OxmlElement("w:shd")
    el.set(qn("w:fill"), color)
    cell._tc.get_or_add_tcPr().append(el)


def table(doc: Document, headers: list[str], rows: list[list[str]], widths=None) -> None:
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = h
        shade(c, "D9E2F3")
        for p in c.paragraphs:
            for r in p.runs:
                r.bold = True
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            t.rows[ri + 1].cells[ci].text = val
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)


def h(doc: Document, text: str, level: int = 1) -> None:
    doc.add_heading(text, level=level)


def bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        doc.add_paragraph(item, style="List Bullet")


def main() -> None:
    today = date.today().strftime("%d/%m/%Y")
    out = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "Relatorio_DevSecOps_Avaliacao_Reavaliacao.docx"
    )
    out.parent.mkdir(parents=True, exist_ok=True)

    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(11)

    # Capa
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("RELATÓRIO DE AVALIAÇÃO DevSecOps\n")
    r.bold = True
    r.font.size = Pt(18)
    r2 = p.add_run("Assistente de Apreensão Inteligente (AAI) — PCDF\n")
    r2.font.size = Pt(13)
    r2.bold = True

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for line in [
        f"Data da Avaliação: {today}",
        "Avaliador: Grupo de Avaliação entre Pares",
        'Metodologia: DevSecOps – 7 Passos (GitHub Global Campus)',
        "Repositório: GitHub — assistente-de-apreensao-inteligente-computer-vision-grupo-31-1 (branch: main)",
        "Stack: Python 3.12 / FastAPI + Next.js 15 + PostgreSQL 16",
        "Referência anterior: Relatório de 25/05/2026 (REPROVADO COM PENDÊNCIAS CRÍTICAS)",
    ]:
        meta.add_run(line + "\n")

    v = doc.add_paragraph()
    v.alignment = WD_ALIGN_PARAGRAPH.CENTER
    vr = v.add_run("Veredicto Final:\n⚠️  REPROVADO COM PENDÊNCIAS MÉDIAS")
    vr.bold = True
    vr.font.size = Pt(14)
    vr.font.color.rgb = RGBColor(192, 96, 0)

    doc.add_paragraph()

    # 1
    h(doc, "1. Sumário Executivo")
    doc.add_paragraph(
        "O projeto AAI (Assistente de Apreensão Inteligente) é um sistema web de gestão de Autos "
        "Circunstanciados de Busca e Arrecadação (ACBA) para a Polícia Civil do Distrito Federal (PCDF). "
        "Esta reavaliação foi conduzida após a Fase 2 de correção DevSecOps (planejamento de maio/2026), "
        "comparando o estado atual do repositório com o relatório anterior de 25/05/2026."
    )
    doc.add_paragraph(
        "Desde a avaliação anterior, a equipe implementou progresso substancial: migração de python-jose "
        "para PyJWT, atualização de dependências vulneráveis, suíte de 100 testes automatizados "
        "(unitários, integração e BDD), três workflows CI/CD (DevSecOps, Tests, DAST-ZAP), Dependabot, "
        "OWASP ZAP com autenticação JWT, Checkov e redução de achados Bandit de 42 (11 Medium) para "
        "0 Medium e 0 High. Contudo, persistem pendências que impedem aprovação plena: cobertura de testes "
        "em 50% (meta: 70%), ausência de Flake8, pipeline sem bloqueio efetivo em falhas de segurança "
        "(|| true / fail_action: false) e IaC formal ainda não implementada."
    )
    doc.add_paragraph(
        "Comparado ao relatório anterior (0 passos conformes, 4 ausentes), o projeto evoluiu para "
        "2 passos conformes, 5 parciais e 0 ausentes. O veredicto atual é REPROVADO COM PENDÊNCIAS MÉDIAS, "
        "podendo ser reaprovado após atingir 70% de cobertura, reforçar gates do CI e concluir pendências "
        "de qualidade (Flake8, mypy bloqueante, SCA sem bypass)."
    )

    # 2
    h(doc, "2. Resumo dos 7 Passos DevSecOps")
    table(
        doc,
        ["#", "Passo / Categoria", "Ferramentas Exigidas", "Status Anterior (25/05)", "Status Atual"],
        [
            ["1", "Testes de Unidade", "pytest, coverage.py", "❌ Ausente", "⚠️ Parcial"],
            ["2", "Análise Estática (SAST)", "Bandit, flake8, mypy", "⚠️ Parcial", "⚠️ Parcial"],
            ["3", "Testes de Integração", "pytest + Service Containers", "⚠️ Parcial", "✅ Conforme"],
            ["4", "SCA", "Dependabot, Safety", "⚠️ Parcial", "⚠️ Parcial"],
            ["5", "BDD / Aceitação", "pytest-bdd, Gherkin", "❌ Ausente", "✅ Conforme"],
            ["6", "DAST", "OWASP ZAP", "❌ Ausente", "⚠️ Parcial"],
            ["7", "IaC", "Checkov / Terraform", "❌ Ausente", "⚠️ Parcial"],
        ],
        [0.35, 1.6, 1.5, 1.2, 1.0],
    )
    doc.add_paragraph(
        "Legenda: ✅ Conforme — atende plenamente | ⚠️ Parcial — atende parcialmente | ❌ Ausente — não implementado"
    )

    # 3
    h(doc, "3. Análise Detalhada dos 7 Passos")

    h(doc, "3.1 Passo 1 — Testes de Unidade  ⚠️ Parcial (antes: ❌ Ausente)", 2)
    doc.add_paragraph(
        "Status atual: Estrutura completa de testes unitários implementada com pytest, pytest-cov e markers."
    )
    bullets(
        doc,
        [
            "Evidência: 54 testes unitários em src/backend/tests/unit/ (auth, RBAC, schemas, serviços).",
            "Configuração: pytest.ini com marker unit, coverage HTML/XML e conftest.py.",
            "CI: workflow .github/workflows/tests.yml executa pytest -m unit a cada push/PR.",
            "Cobertura total (app/): 50% — abaixo da meta de 70% definida no plano Fase 2.",
            "Gaps: repositórios (18–27%), routers/cadastros (33%), acba_pdf_context (15%).",
        ],
    )
    doc.add_paragraph("Correção em relação ao relatório anterior: de zero testes para 54 unitários + infraestrutura de cobertura.")

    h(doc, "3.2 Passo 2 — Análise Estática e Linting (SAST)  ⚠️ Parcial", 2)
    doc.add_paragraph(
        "Status atual: Bandit integrado e efetivo. mypy configurado mas não bloqueante. Flake8 ainda ausente."
    )
    table(
        doc,
        ["Indicador", "25/05/2026", "Atual"],
        [
            ["Bandit High", "0", "0"],
            ["Bandit Medium", "11", "0"],
            ["Bandit Low", "31", "171 (majoritariamente informativos)"],
            ["mypy no CI", "Ausente", "Presente (|| true — não bloqueia)"],
            ["Flake8", "8 ocorrências locais", "Não integrado ao CI"],
            ["Markup XSS (B704)", "1 ocorrência", "Removido — sem Markup() em app/"],
            ["assert em produção (B101)", "31 ocorrências", "0 em app/"],
        ],
        [2.5, 1.5, 2.7],
    )
    doc.add_paragraph(
        "Achados Bandit residuais (Low): subprocess LibreOffice (nosec documentado), padrões SQL dinâmico "
        "em repositórios com valores parametrizados. SQL Injection potencial (B608) mitigado por placeholders, "
        "mas a montagem dinâmica de cláusulas persiste como alerta SAST."
    )

    h(doc, "3.3 Passo 3 — Testes de Integração  ✅ Conforme (antes: ⚠️ Parcial)", 2)
    bullets(
        doc,
        [
            "21 testes de integração em src/backend/tests/integration/ (auth, users, catalog, ACBA, security headers).",
            "GitHub Actions com service container PostgreSQL 16, aplicação de migrations Flyway e execução pytest -m integration.",
            "Validação de endpoints HTTP, autenticação, RBAC e interação com banco real.",
            "Docker Compose + Flyway mantidos como infraestrutura de integração local.",
        ],
    )

    h(doc, "3.4 Passo 4 — Análise de Composição de Software (SCA)  ⚠️ Parcial", 2)
    doc.add_paragraph("Status atual: Dependabot ativo e dependências críticas atualizadas. Safety scan no CI com bypass.")
    table(
        doc,
        ["Pacote", "Versão anterior", "Versão atual", "Status"],
        [
            ["python-jose", "3.3.0 (2 CVEs altas)", "Removido → PyJWT>=2.13.0", "✅ Corrigido"],
            ["Jinja2", "3.1.5 (CVE-2025-27516)", "Jinja2>=3.1.6", "✅ Corrigido"],
            ["python-multipart", "0.0.20 (2 CVEs)", "python-multipart>=0.0.32", "✅ Corrigido"],
            ["weasyprint", "63.1 (CVE média)", "weasyprint==69.0", "✅ Corrigido"],
            ["Pillow", "11.0.0 (2 CVEs médias)", "Pillow>=11.3.0", "⚠️ Parcial (meta ≥ 12.2.0)"],
        ],
        [1.5, 1.8, 1.5, 1.0],
    )
    bullets(
        doc,
        [
            "Dependabot: .github/dependabot.yml para pip, npm e github-actions (PRs #1–#11 mergeados).",
            "Safety: migrado de 'safety check' para 'safety scan' — porém com || true no workflow.",
            "npm audit executado no CI para o frontend (também com || true).",
            "CVEs críticas/altas da autenticação JWT eliminadas com migração para PyJWT.",
        ],
    )

    h(doc, "3.5 Passo 5 — Testes Funcionais e de Aceitação (BDD)  ✅ Conforme (antes: ❌ Ausente)", 2)
    bullets(
        doc,
        [
            "pytest-bdd==8.1.0 nas dependências; 25 testes BDD no CI (pytest -m bdd).",
            "login.feature — 6 cenários: login válido/inválido, usuário desativado, /me.",
            "acba.feature — 7 cenários: criação, RBAC, filtro por equipe, bloqueio pós-PDF, exclusão.",
            "rbac.feature — 12 cenários: administrador, delegado, escrivão, agente (vínculo temporal).",
            "Cenários em português (Gherkin) alinhados às regras de negócio PCDF.",
        ],
    )

    h(doc, "3.6 Passo 6 — Testes de Segurança Dinâmicos (DAST)  ⚠️ Parcial (antes: ❌ Ausente)", 2)
    bullets(
        doc,
        [
            "Workflow .github/workflows/dast.yml com OWASP ZAP Baseline (zaproxy/action-baseline@v0.15.0).",
            "Ambiente efêmero: PostgreSQL + uvicorn + migrations; target http://localhost:8000.",
            "Varredura autenticada: token JWT obtido via POST /api/auth/login antes do scan.",
            "Arquivo .zap/rules.tsv para suprimir ruído de API (cache headers).",
            "Limitações: fail_action: false (não bloqueia merge); escopo limitado ao backend; sem staging dedicado; frontend Next.js não varrido.",
        ],
    )

    h(doc, "3.7 Passo 7 — Testes de Infraestrutura como Código (IaC)  ⚠️ Parcial (antes: ❌ Ausente)", 2)
    bullets(
        doc,
        [
            "Checkov integrado ao workflow DevSecOps para Dockerfiles e docker-compose.yml.",
            "Modo --soft-fail: achados não bloqueiam o pipeline.",
            "Terraform/Pulumi/CloudFormation: ainda ausentes — infraestrutura permanece em docker-compose.yml.",
            "Melhorias pendentes: redes isoladas, limites CPU/memória, secrets de produção documentados.",
        ],
    )

    # 4
    h(doc, "4. Pontos Positivos — Conformidades e Melhorias desde 25/05/2026")
    bullets(
        doc,
        [
            "✅ 100 testes automatizados passando (54 unit + 21 integração + 25 BDD)",
            "✅ Migração python-jose → PyJWT (elimina CVEs de algorithm confusion e JWT bomb)",
            "✅ Dependências críticas atualizadas (Jinja2, python-multipart, weasyprint)",
            "✅ JWT TTL reduzido de 24h para 60 minutos (access_token_expire_minutes = 60)",
            "✅ Remoção de assert e Markup() do código de produção",
            "✅ Diretório temporário seguro no serviço DOCX/PDF (tempfile.mkdtemp + timeout subprocess)",
            "✅ Dependabot configurado (pip, npm, github-actions)",
            "✅ OWASP ZAP configurado com autenticação JWT",
            "✅ Checkov para análise de Dockerfiles e Compose",
            "✅ Três workflows CI: DevSecOps-PCDF, Tests, DAST-ZAP",
            "✅ RBAC, auditoria, bcrypt, CORS, Flyway — mantidos e testados via BDD",
            "✅ Documentação DevSecOps consolidada (docs/Relatorio_Qualidade_Seguranca_DevSecOps.md)",
        ],
    )

    # 5
    h(doc, "5. Lista de Não-Conformidades Remanescentes")
    table(
        doc,
        ["Severidade", "Problema", "Descrição", "Status vs. 25/05"],
        [
            [
                "Alta",
                "Cobertura de testes abaixo de 70%",
                "Cobertura atual: 50%. Repositórios e routers com baixa cobertura.",
                "Novo — parcialmente endereçado (testes existem, meta não atingida)",
            ],
            [
                "Alta",
                "Pipeline não bloqueia falhas de segurança",
                "Safety, mypy, npm audit, Checkov e ZAP com || true ou fail_action: false.",
                "Novo",
            ],
            [
                "Média",
                "Flake8 ausente no CI",
                "8 problemas de estilo identificados em maio; ferramenta não integrada.",
                "Pendente",
            ],
            [
                "Média",
                "Pillow abaixo da versão recomendada",
                "Pillow>=11.3.0 instalado; advisories recomendavam ≥ 12.2.0.",
                "Parcialmente corrigido",
            ],
            [
                "Média",
                "mypy não bloqueante",
                "Configurado (mypy.ini) mas CI usa || true.",
                "Parcialmente corrigido",
            ],
            [
                "Média",
                "IaC formal ausente",
                "Apenas docker-compose.yml; sem Terraform/Pulumi.",
                "Parcialmente corrigido (Checkov adicionado)",
            ],
            [
                "Média",
                "DAST incompleto",
                "ZAP não bloqueia merge; frontend não varrido; sem staging.",
                "Parcialmente corrigido",
            ],
            [
                "Baixa",
                "SQL dinâmico (Bandit B608 residual)",
                "Queries parametrizadas, mas montagem dinâmica de cláusulas persiste.",
                "Parcialmente corrigido",
            ],
        ],
        [0.9, 1.6, 2.8, 1.4],
    )

    h(doc, "5.1 Não-Conformidades Corrigidas desde 25/05/2026", 2)
    table(
        doc,
        ["Severidade original", "Problema", "Correção aplicada"],
        [
            ["Crítica", "Ausência total de testes unitários", "54 testes unitários + pytest/coverage"],
            ["Crítica", "8 CVEs em dependências (python-jose, Jinja2, multipart)", "PyJWT, Jinja2>=3.1.6, multipart>=0.0.32, weasyprint 69"],
            ["Crítica", "SQL Injection potencial (B608)", "Refatoração com parâmetros; 0 Medium no Bandit"],
            ["Alta", "Ausência de testes de integração automatizados", "21 testes + Postgres no GitHub Actions"],
            ["Alta", "Ausência de testes BDD", "3 arquivos .feature, 25 testes BDD"],
            ["Alta", "Ausência de DAST (OWASP ZAP)", "Workflow dast.yml com ZAP baseline + JWT"],
            ["Média", "Dependabot não configurado", ".github/dependabot.yml ativo"],
            ["Média", "XSS potencial (Markup)", "Markup() removido de app/"],
            ["Média", "Safety: comando deprecated", "Migrado para safety scan"],
            ["Média", "mypy não configurado", "mypy.ini + step no CI"],
            ["Média", "Sem Checkov", "Checkov no workflow DevSecOps"],
            ["Baixa", "JWT 24h", "Reduzido para 60 minutos"],
            ["Baixa", "assert em produção (31×)", "0 asserts em app/"],
            ["Baixa", "Uso inseguro de /tmp (LibreOffice)", "tempfile.mkdtemp controlado"],
        ],
        [1.2, 2.5, 2.8],
    )

    # 6
    h(doc, "6. Recomendações e Plano de Ação")
    table(
        doc,
        ["Prazo", "Ação", "Justificativa", "Prioridade"],
        [
            ["Imediata", "Elevar cobertura para ≥ 70% (--cov-fail-under=70)", "Critério de aceite Fase 2 DevSecOps", "Alta"],
            ["Imediata", "Remover || true e fail_action: false nos workflows", "Pipeline deve bloquear vulnerabilidades", "Alta"],
            ["Curto prazo", "Integrar Flake8 ou Ruff no CI", "Passo 2 SAST completo", "Média"],
            ["Curto prazo", "Atualizar Pillow para ≥ 12.2.0", "Advisories CVE-2026 residuais", "Média"],
            ["Curto prazo", "Tornar mypy bloqueante progressivamente", "Qualidade estática de tipos", "Média"],
            ["Médio prazo", "Expandir DAST para frontend ou proxy unificado", "Cobertura dinâmica completa", "Média"],
            ["Médio prazo", "Checkov sem --soft-fail ou corrigir achados", "IaC com enforcement", "Média"],
            ["Longo prazo", "Avaliar Terraform/Pulumi para produção", "IaC formal conforme passo 7", "Baixa"],
        ],
        [1.0, 2.5, 2.2, 0.8],
    )

    # 7
    h(doc, "7. Veredicto Final")
    v2 = doc.add_paragraph()
    vr2 = v2.add_run("⚠️  REPROVADO COM PENDÊNCIAS MÉDIAS")
    vr2.bold = True
    vr2.font.size = Pt(14)
    vr2.font.color.rgb = RGBColor(192, 96, 0)

    table(
        doc,
        ["Indicador", "25/05/2026", "Atual"],
        [
            ["Passos Conformes (✅)", "0 de 7", "2 de 7 (Integração, BDD)"],
            ["Passos Parciais (⚠️)", "3 de 7", "5 de 7 (Unit, SAST, SCA, DAST, IaC)"],
            ["Passos Ausentes (❌)", "4 de 7", "0 de 7"],
            ["CVEs Críticas/Altas (auth/JWT)", "5 CVEs", "0 CVEs conhecidas (PyJWT migrado)"],
            ["Issues SAST Bandit Medium+", "11 Medium", "0 Medium, 0 High"],
            ["Testes automatizados", "0", "100 (50% cobertura)"],
        ],
        [2.5, 1.5, 2.7],
    )

    doc.add_paragraph(
        "Evolução: o projeto saiu de REPROVADO COM PENDÊNCIAS CRÍTICAS para REPROVADO COM PENDÊNCIAS MÉDIAS. "
        "As vulnerabilidades críticas de dependências e a ausência total de testes foram endereçadas. "
        "Para aprovação plena nos critérios DevSecOps, ainda é necessário:"
    )
    bullets(
        doc,
        [
            "Atingir cobertura mínima de 70% com gate no CI",
            "Tornar o pipeline fail-fast em falhas de SCA, SAST, mypy e DAST",
            "Integrar Flake8/Ruff e concluir pendências de qualidade da Sprint 3",
            "Consolidar IaC (Checkov bloqueante ou Terraform documentado)",
        ],
    )
    doc.add_paragraph(
        "O projeto pode ser reaprovado após a correção das pendências Altas e Médias listadas, "
        "mediante nova avaliação de pares."
    )

    doc.add_paragraph()
    foot = doc.add_paragraph()
    foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    foot.add_run(
        f"Relatório gerado em {today} — Reavaliação DevSecOps pós Fase 2\n"
        "Avaliação entre Pares DevSecOps | GitHub Global Campus | EPS UnB"
    ).italic = True

    doc.save(out)
    print(f"Relatório gerado: {out}")


if __name__ == "__main__":
    main()
