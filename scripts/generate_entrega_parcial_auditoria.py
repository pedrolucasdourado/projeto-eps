#!/usr/bin/env python3
"""Gera o documento DOCX da Entrega Parcial de Auditoria — Fase 2 DevSecOps AAI."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def set_cell_shading(cell, hex_color: str) -> None:
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), hex_color)
    cell._tc.get_or_add_tcPr().append(shading)


def add_table(doc: Document, headers: list[str], rows: list[list[str]], col_widths=None) -> None:
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = h
        set_cell_shading(hdr[i], "D9E2F3")
        for p in hdr[i].paragraphs:
            for run in p.runs:
                run.bold = True
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            table.rows[ri + 1].cells[ci].text = val
    if col_widths:
        for row in table.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Inches(w)


def add_heading(doc: Document, text: str, level: int = 1) -> None:
    doc.add_heading(text, level=level)


def add_bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        doc.add_paragraph(item, style="List Bullet")


def main() -> None:
    today = date.today().strftime("%d/%m/%Y")
    out = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "Entrega_Parcial_Auditoria_AAI_Fase2_DevSecOps.docx"
    )
    out.parent.mkdir(parents=True, exist_ok=True)

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("ENTREGA PARCIAL DE AUDITORIA\n")
    run.bold = True
    run.font.size = Pt(16)
    run2 = title.add_run(
        "Correção das Pendências DevSecOps — Assistente de Apreensão Inteligente (AAI)\n"
        "Auditoria de Planejamento vs. Implementação — Fase 2"
    )
    run2.font.size = Pt(12)

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.add_run(f"Data do relatório: {today}\n").italic = True
    meta.add_run(
        "Documentos-base: planejamento_fase_2_devsecops.docx e "
        "relatorio_devsecops_avaliacao.docx (25/05/2026)"
    ).italic = True

    doc.add_paragraph()

    # 1 — Identificação
    add_heading(doc, "1. Identificação da Auditoria", 1)
    add_table(
        doc,
        ["Campo", "Informação"],
        [
            ["Equipe auditora", "[Preencher — nome/número do grupo auditor]"],
            ["Equipe auditada", "Grupo 31 — Assistente de Apreensão Inteligente (AAI) / PCDF"],
            ["Projeto auditado", "Assistente de Apreensão Inteligente (AAI) — Computer Vision"],
            [
                "Repositório",
                "https://github.com/FCTE-UNB-EPS5/"
                "assistente-de-apreensao-inteligente-computer-vision-grupo-31-1",
            ],
            [
                "Integrantes envolvidos na auditoria",
                "[Preencher — nomes dos integrantes da equipe auditora]",
            ],
            ["Período da auditoria parcial", "Maio/2026 a 25/06/2026 (entrega parcial)"],
            ["Entrega final prevista", "30/06/2026"],
        ],
        [2.2, 4.3],
    )

    # 2 — Plano de Auditoria
    add_heading(doc, "2. Plano de Auditoria Atualizado", 1)

    add_heading(doc, "2.1 Escopo da auditoria", 2)
    doc.add_paragraph(
        "Verificar a aderência do projeto AAI ao Plano de Correção da Fase 2 DevSecOps "
        "(3 sprints semanais), comparando as ações planejadas nas Sprints 1, 2 e 3 com "
        "evidências concretas no repositório GitHub: dependências e CVEs, segurança "
        "(SAST/SCA/DAST), testes automatizados (unitários, integração, BDD), pipeline CI/CD, "
        "qualidade de código (Flake8, mypy) e critérios de aceite da fase."
    )

    add_heading(doc, "2.2 Critérios adotados", 2)
    add_bullets(
        doc,
        [
            "Plano de Correção Fase 2 DevSecOps (planejamento_fase_2_devsecops.docx).",
            "Relatório de Avaliação DevSecOps original (25/05/2026 — reprovação com 4/7 passos ausentes).",
            "Metodologia DevSecOps — 7 Passos (GitHub Global Campus).",
            "Relatório de Qualidade e Segurança (docs/Relatorio_Qualidade_Seguranca_DevSecOps.md).",
            "Critérios de aceite da Fase 2: zero CVEs críticas/altas, cobertura ≥ 70%, pipeline completo, ZAP e BDD.",
            "Evidências rastreáveis: workflows GitHub Actions, requirements.txt, suíte de testes e scans locais.",
        ],
    )

    add_heading(doc, "2.3 Artefatos analisados", 2)
    add_table(
        doc,
        ["Artefato", "Local / referência", "Status"],
        [
            ["Repositório GitHub", "FCTE-UNB-EPS5/assistente-de-apreensao-inteligente-computer-vision-grupo-31-1", "Analisado"],
            ["Workflow DevSecOps (SAST/SCA/mypy/Flake8/Checkov)", ".github/workflows/devsecops.yml", "Analisado"],
            ["Workflow de testes + cobertura", ".github/workflows/tests.yml", "Analisado"],
            ["Workflow DAST (OWASP ZAP)", ".github/workflows/dast.yml", "Analisado"],
            ["Dependabot", ".github/dependabot.yml", "Analisado"],
            ["Dependências backend", "src/backend/requirements.txt", "Analisado"],
            ["Suíte de testes", "src/backend/tests/ (312 coletados)", "Executado localmente (25/06/2026)"],
            ["Cenários BDD", "src/backend/tests/features/*.feature (3 arquivos)", "Analisado"],
            ["Configuração pytest/coverage", "src/backend/pytest.ini", "Analisado"],
            ["Documentação DevSecOps", "docs/Relatorio_Qualidade_Seguranca_DevSecOps.md", "Analisado"],
            ["Docker Compose + Flyway", "docker-compose.yml, database/flyway/sql/", "Analisado"],
            ["Pull Requests Dependabot", "Histórico git (PRs #1–#11)", "Analisado"],
            ["SonarQube", "Não implementado — substituído por Bandit + Safety + Flake8 + mypy", "Observado"],
        ],
        [1.8, 2.8, 1.0],
    )

    add_heading(doc, "2.4 Cronograma executado até o momento", 2)
    add_table(
        doc,
        ["Atividade", "Período", "Situação"],
        [
            ["Revisão do relatório DevSecOps e elaboração do plano Fase 2", "25/05/2026", "Concluída (equipe auditada)"],
            ["Sprint 1 — CVEs, JWT, SQL, testes unitários iniciais", "Semana 1", "Concluída"],
            ["Sprint 2 — CI integração, BDD, ZAP, Dependabot, mypy inicial", "Semana 2", "Concluída"],
            ["Sprint 3 — Flake8, consolidação mypy, Checkov, TTL JWT, asserts", "Semana 3", "Substancialmente concluída"],
            ["Coleta de evidências preliminares (esta entrega)", "Até 25/06/2026", "Concluída"],
            ["Análise crítica de gaps e achados preliminares", "25/06/2026", "Concluída neste documento"],
        ],
        [3.0, 1.5, 1.2],
    )

    add_heading(doc, "2.5 Cronograma restante até a entrega final (30/06/2026)", 2)
    add_table(
        doc,
        ["Atividade", "Prazo", "Responsável"],
        [
            ["Validar execução dos workflows no GitHub Actions (capturas/links)", "26/06", "Equipe auditora"],
            ["Confirmar SCA (Safety/npm audit) sem CVEs críticas/altas no CI", "26/06", "Equipe auditora"],
            ["Avaliar estabilidade do DAST (ZAP) e relatório de artefatos", "27/06", "Equipe auditora"],
            ["Verificar gaps residuais (IaC formal, CodeQL, DAST frontend)", "27/06", "Equipe auditora"],
            ["Checkpoint com equipe auditada sobre pendências menores", "28/06", "Ambas equipes"],
            ["Consolidação da matriz de conformidade e veredicto final", "29/06", "Equipe auditora"],
            ["Redação e entrega do relatório final de auditoria (PDF/DOCX)", "30/06", "Equipe auditora"],
        ],
        [3.2, 1.0, 1.5],
    )

    # 3 — Evidências
    add_heading(doc, "3. Evidências Coletadas", 1)

    add_heading(doc, "3.1 Repositório e arquitetura", 2)
    doc.add_paragraph(
        "Stack confirmada: FastAPI (Python 3.12), Next.js 15, PostgreSQL 16, Flyway, Docker Compose. "
        "Módulos principais: autenticação JWT (PyJWT), CRUD ACBA, cadastros auxiliares, RBAC com quatro "
        "papéis, auditoria, geração de PDF (WeasyPrint/LibreOffice), materiais e integração Gemini Vision."
    )

    add_heading(doc, "3.2 Pipeline CI/CD", 2)
    add_table(
        doc,
        ["Workflow", "Gatilho", "Evidência"],
        [
            [
                "DevSecOps-PCDF",
                "push, pull_request",
                "Bandit (-ll), Flake8, Safety scan, npm audit --audit-level=high, mypy, Checkov",
            ],
            [
                "Tests",
                "push, pull_request",
                "PostgreSQL 16 service container, migrations Flyway, pytest com --cov-fail-under=90",
            ],
            [
                "DAST-ZAP",
                "push main, PR, workflow_dispatch",
                "ZAP baseline, fail_action: true, JWT autenticado, .zap/rules.tsv",
            ],
            ["Dependabot", "semanal (segunda)", "pip (/src/backend), npm (/src/frontend), github-actions"],
        ],
        [1.5, 1.5, 3.7],
    )

    add_heading(doc, "3.3 Testes automatizados (execução local — 25/06/2026)", 2)
    add_table(
        doc,
        ["Indicador", "Valor observado", "Meta (plano Fase 2)"],
        [
            ["Total de testes coletados", "312", "Estrutura completa"],
            ["Testes executados com sucesso", "305 passando, 7 skipped", "Suíte estável"],
            ["Testes unitários (-m unit)", "193", "Autenticação, RBAC, schemas, serviços, repositórios"],
            ["Testes de integração (-m integration)", "87 (7 skipped sem Postgres local)", "API + banco real no CI"],
            ["Testes BDD (-m bdd)", "25", "Login, ACBA, RBAC (Gherkin em português)"],
            ["Cobertura de código (app/)", "90,91%", "≥ 70%"],
        ],
        [2.5, 1.5, 2.7],
    )

    add_heading(doc, "3.4 Segurança — SAST (Bandit, Flake8, mypy)", 2)
    doc.add_paragraph(
        "Varredura local em 25/06/2026: Bandit (bandit -r src/ -ll) — 0 achados High e 0 Medium "
        "(redução de 42 achados / 11 Medium no relatório de maio/2026). Flake8 (src/backend/app, "
        ".flake8 com max-line-length=120) — 0 ocorrências. mypy (src/backend/app, mypy.ini) — "
        "Success: no issues found in 32 source files. Todos integrados ao workflow DevSecOps-PCDF "
        "sem continue-on-error."
    )

    add_heading(doc, "3.5 Correções de dependências (SCA)", 2)
    add_table(
        doc,
        ["Item planejado (Sprint)", "Evidência", "Status"],
        [
            ["Migrar python-jose → PyJWT (S1)", "PyJWT>=2.13.0; auth_service.py", "Concluído"],
            ["Jinja2 >= 3.1.6 (S1)", "Jinja2>=3.1.6", "Concluído"],
            ["python-multipart seguro (S1)", "python-multipart>=0.0.32", "Concluído"],
            ["weasyprint atualizado (S1)", "weasyprint==69.0", "Concluído"],
            ["Dependabot (S2)", ".github/dependabot.yml", "Concluído"],
            ["Safety scan substituindo check (S2)", "safety scan --output screen no CI", "Concluído"],
            ["Pillow atualizado", "Pillow>=11.3.0 (plano sugeria ≥ 12.2.0)", "Parcial"],
        ],
        [2.2, 2.8, 1.0],
    )

    add_heading(doc, "3.6 Cenários BDD implementados", 2)
    add_bullets(
        doc,
        [
            "login.feature — 6 cenários: credenciais válidas/inválidas, usuário desativado, /me com e sem token.",
            "acba.feature — 7 cenários: criação, RBAC, filtro por equipe, bloqueio pós-PDF (409), exclusão.",
            "rbac.feature — 12 cenários: administrador, delegado, escrivão, agente (vínculo temporal), rotas protegidas.",
        ],
    )

    add_heading(doc, "3.7 Outras evidências DevSecOps", 2)
    add_bullets(
        doc,
        [
            "JWT TTL reduzido para 60 minutos (config.py: access_token_expire_minutes = 60).",
            "0 instruções assert em app/; Markup() removido (mitigação XSS B704).",
            "Queries SQL refatoradas com parâmetros; Bandit B608 eliminado do relatório.",
            "tempfile.mkdtemp + timeout em subprocess LibreOffice (Sprint 3).",
            "Checkov no CI para Dockerfiles e docker-compose.yml (sem --soft-fail).",
            "OWASP ZAP com autenticação JWT e publicação de artefato zap-report.",
            "Migrations Flyway versionadas (schema, RBAC, auditoria, materiais, vínculos temporais).",
            "Documentação consolidada substituindo SonarQube (Bandit + Safety + Flake8 + mypy).",
        ],
    )

    # 4 — Achados
    add_heading(doc, "4. Achados Preliminares", 1)

    add_heading(doc, "4.1 Não Conformidades Críticas", 2)
    p = doc.add_paragraph()
    run = p.add_run(
        "Nenhuma não conformidade crítica identificada nesta fase preliminar. "
        "As CVEs críticas/altas de maio/2026 (python-jose, Jinja2, python-multipart) "
        "foram corrigidas conforme evidências em requirements.txt e scans SCA."
    )
    run.font.color.rgb = RGBColor(0, 128, 0)

    add_heading(doc, "4.2 Não Conformidades Maiores", 2)
    p2 = doc.add_paragraph()
    run2 = p2.add_run(
        "Nenhuma não conformidade maior confirmada até 25/06/2026. "
        "Itens que eram NC-Majores em análises intermediárias (cobertura < 70%, pipeline sem bloqueio, "
        "Flake8 ausente) foram endereçados pela equipe auditada e serão revalidados no CI até 30/06."
    )
    run2.font.color.rgb = RGBColor(0, 128, 0)

    add_heading(doc, "4.3 Não Conformidades Menores", 2)
    add_table(
        doc,
        ["ID", "Achado", "Referência ao plano", "Evidência"],
        [
            [
                "NC-m01",
                "Pillow abaixo da versão recomendada (≥ 12.2.0)",
                "SCA / Sprint 1",
                "requirements.txt: Pillow>=11.3.0",
            ],
            [
                "NC-m02",
                "IaC formal ausente — infraestrutura apenas em Docker Compose",
                "Sprint 2/3 — IaC",
                "Sem Terraform/Pulumi; Checkov analisa apenas Compose/Dockerfile",
            ],
            [
                "NC-m03",
                "DAST limitado ao backend FastAPI",
                "Sprint 3 — DAST estabilizado",
                "dast.yml target: http://localhost:8000; frontend Next.js não varrido",
            ],
            [
                "NC-m04",
                "CodeQL não configurado no pipeline",
                "Passo 2 DevSecOps (material de referência)",
                "Ausência de .github/workflows/codeql-analysis.yml",
            ],
            [
                "NC-m05",
                "docker-compose.yml sem endurecimento completo",
                "Relatório original / Sprint 3",
                "Credenciais padrão change_me; sem rede isolada; sem limites CPU/memória",
            ],
            [
                "NC-m06",
                "npm audit — 3 vulnerabilidades moderadas no frontend",
                "SCA frontend",
                "PostCSS via Next.js (GHSA-qx2v-qp2m-jg93); nível high não atingido",
            ],
        ],
        [0.6, 2.0, 1.4, 2.7],
    )

    add_heading(doc, "4.4 Observações", 2)
    add_bullets(
        doc,
        [
            "Evolução significativa: de 0 testes e 4 passos DevSecOps ausentes (25/05) para 305 testes, "
            "90,9% de cobertura e 0 passos ausentes (3 conformes, 4 parciais).",
            "Gate de cobertura no CI está em 90% (--cov-fail-under=90), acima do mínimo de 70% do plano Fase 2.",
            "SonarQube não foi adotado; a equipe auditada documentou substituto equivalente (Bandit + Safety + Flake8 + mypy).",
            "Testes marcados postgres (7 skipped) dependem de DATABASE_URL local; no CI todos rodam com service container.",
            "Validação definitiva dos workflows depende de evidências de runs no GitHub Actions (pendente até 26–27/06).",
        ],
    )

    add_heading(doc, "4.5 Oportunidades de Melhoria", 2)
    add_bullets(
        doc,
        [
            "Atualizar Pillow para ≥ 12.2.0 e resolver vulnerabilidades moderadas do frontend (npm audit fix).",
            "Adicionar workflow CodeQL para completar o passo 2 SAST conforme material GitHub Global Campus.",
            "Expandir DAST para frontend Next.js ou proxy unificado (staging efêmero completo).",
            "Endurecer docker-compose.yml: redes dedicadas, limites de recursos, rotação de secrets documentada.",
            "Avaliar Terraform/Pulumi para IaC formal de produção (passo 7 pleno).",
            "Manter cobertura ≥ 90% ao expandir módulos (cadastros.py ainda com ~31% de cobertura unitária).",
        ],
    )

    add_heading(doc, "4.6 Boas Práticas Identificadas", 2)
    add_bullets(
        doc,
        [
            "Migração python-jose → PyJWT com algoritmo explícito HS256 (elimina algorithm confusion e JWT bomb).",
            "RBAC com testes BDD abrangentes em português (admin, delegado, escrivão, agente com vínculo temporal).",
            "Três workflows CI com responsabilidades claras: segurança, testes+cobertura, DAST.",
            "Pipeline fail-fast: Bandit, Flake8, Safety, npm audit, mypy e Checkov sem bypass no DevSecOps-PCDF.",
            "OWASP ZAP com fail_action: true e varredura autenticada via JWT.",
            "Dependabot ativo para pip, npm e GitHub Actions.",
            "Cobertura 90,9% com 305 testes automatizados (unitários, integração e BDD).",
            "JWT TTL 60 min, asserts removidos, tempfile seguro no serviço PDF, auditoria com snapshots.",
        ],
    )

    # 5 — Riscos
    add_heading(doc, "5. Riscos para Conclusão da Auditoria", 1)
    add_table(
        doc,
        ["Risco", "Impacto", "Probabilidade", "Mitigação"],
        [
            [
                "Acesso limitado ao histórico completo do GitHub Actions",
                "Médio",
                "Média",
                "Solicitar links/capturas de runs recentes (Tests, DevSecOps, DAST-ZAP) à equipe auditada",
            ],
            [
                "Divergência entre execução local e CI remoto",
                "Médio",
                "Baixa",
                "Validar runs oficiais nos dias 26–27/06 antes do veredicto final",
            ],
            [
                "Documentação de arquitetura sem diagrama C4 atualizado",
                "Baixo",
                "Média",
                "Basear análise em README, migrations, docker-compose e código-fonte",
            ],
            [
                "Safety/pip-audit exige autenticação ou rede no ambiente local do auditor",
                "Baixo",
                "Média",
                "Utilizar relatório do workflow DevSecOps-PCDF e npm audit como evidência primária",
            ],
            [
                "Comunicação entre equipes auditora e auditada na reta final",
                "Médio",
                "Baixa",
                "Checkpoint agendado para 28/06 sobre NC-m01 a NC-m06",
            ],
            [
                "Interpretação divergente sobre IaC formal vs. Docker Compose + Checkov",
                "Médio",
                "Média",
                "Documentar decisão arquitetural no relatório final; avaliar se Checkov atende passo 7 parcialmente",
            ],
        ],
        [2.2, 0.8, 1.0, 2.7],
    )

    # 6 — Próximos passos
    add_heading(doc, "6. Próximos Passos (até 30/06/2026)", 1)
    add_table(
        doc,
        ["#", "Atividade", "Entregável", "Prazo"],
        [
            ["1", "Confrontar matriz Plano Fase 2 × Implementação (100% dos itens)", "Planilha de rastreabilidade", "26/06"],
            ["2", "Validar runs do GitHub Actions (Tests, DevSecOps, DAST-ZAP)", "Capturas / links de execução", "26–27/06"],
            ["3", "Confirmar SCA sem CVEs críticas/altas (Safety + npm audit)", "Relatório SCA atualizado", "27/06"],
            ["4", "Avaliar gaps residuais (CodeQL, IaC, DAST frontend, Pillow)", "Lista de NC finais", "27/06"],
            ["5", "Checkpoint com equipe auditada", "Ata de alinhamento", "28/06"],
            ["6", "Consolidar achados e veredicto DevSecOps (7 passos)", "Matriz conforme/não conforme", "29/06"],
            ["7", "Redação e entrega do relatório final de auditoria", "Relatório final PDF/DOCX (3–10 páginas)", "30/06"],
        ],
        [0.4, 3.0, 2.3, 0.8],
    )

    # Anexo A
    add_heading(doc, "Anexo A — Matriz de Aderência ao Plano Fase 2 DevSecOps", 1)
    add_table(
        doc,
        ["Sprint", "Item planejado", "Status", "Observação"],
        [
            ["S1", "Atualizar python-jose → PyJWT", "Concluído", "PyJWT>=2.13.0"],
            ["S1", "Atualizar Jinja2 >= 3.1.6", "Concluído", ""],
            ["S1", "Atualizar python-multipart", "Concluído", ">=0.0.32"],
            ["S1", "Corrigir SQL Injection potencial", "Concluído", "Parametrizado; Bandit 0 Medium"],
            ["S1", "Testes unitários (pytest + coverage)", "Concluído", "193 testes unitários; gate 90%"],
            ["S1", "Estrutura testes integração", "Concluído", "87 testes integração + Postgres no CI"],
            ["S1", "Planejar DAST/ZAP", "Concluído", "dast.yml ativo com fail_action: true"],
            ["S2", "Integração automatizada no CI", "Concluído", "tests.yml + service container"],
            ["S2", "BDD (login, ACBA, RBAC, pós-PDF)", "Concluído", "3 .feature, 25 testes BDD"],
            ["S2", "OWASP ZAP no pipeline", "Concluído", "Autenticação JWT; bloqueia merge"],
            ["S2", "Cobertura >= 70%", "Concluído", "90,91% observado localmente"],
            ["S2", "Dependabot", "Concluído", "pip, npm, github-actions"],
            ["S2", "Safety scan (substituir check)", "Concluído", "Sem bypass no CI"],
            ["S2", "Mitigar XSS Markup()", "Concluído", "Markup removido de app/"],
            ["S2", "mypy inicial", "Concluído", "mypy.ini + CI bloqueante"],
            ["S2", "IaC / Checkov", "Parcial", "Checkov no CI; sem Terraform"],
            ["S3", "Checkov/Terrascan", "Concluído", "Checkov bloqueante no DevSecOps"],
            ["S3", "mypy consolidado", "Concluído", "0 erros em 32 arquivos"],
            ["S3", "DAST estabilizado", "Parcial", "Backend OK; frontend fora do escopo"],
            ["S3", "JWT TTL <= 60 min", "Concluído", "60 minutos"],
            ["S3", "Remover assert em produção", "Concluído", "0 asserts em app/"],
            ["S3", "Flake8 sem pendências", "Concluído", "0 ocorrências; integrado ao CI"],
            ["S3", "/tmp LibreOffice seguro", "Concluído", "tempfile.mkdtemp"],
            ["S3", "Subprocess LibreOffice controlado", "Concluído", "timeout e args fixos"],
            ["Aceite", "Zero CVEs críticas/altas", "A verificar", "Confirmar no CI (26–27/06)"],
            ["Aceite", "Pipeline SAST+SCA+testes", "Concluído", "3 workflows + Dependabot"],
            ["Aceite", "Cobertura >= 70%", "Concluído", "90,91%"],
            ["Aceite", "ZAP configurado", "Concluído", "fail_action: true"],
            ["Aceite", "BDD principais implementados", "Concluído", "25 cenários"],
            ["Aceite", "Issues leves corrigidas", "Parcial", "Pillow e npm moderate pendentes"],
        ],
        [0.5, 2.5, 1.0, 2.7],
    )

    add_heading(doc, "Anexo B — Resumo quantitativo e evolução DevSecOps", 1)
    add_table(
        doc,
        ["Indicador", "25/05/2026 (baseline)", "25/06/2026 (atual)"],
        [
            ["Passos DevSecOps conformes", "0 de 7", "3 de 7 (Unit, Integração, BDD)"],
            ["Passos parciais", "3 de 7", "4 de 7 (SAST, SCA, DAST, IaC)"],
            ["Passos ausentes", "4 de 7", "0 de 7"],
            ["Testes automatizados", "0", "305 passando"],
            ["Cobertura app/", "0%", "90,91%"],
            ["Bandit Medium+", "11", "0"],
            ["CVEs críticas/altas JWT", "5", "0 (PyJWT migrado)"],
        ],
        [2.5, 2.0, 2.2],
    )
    doc.add_paragraph()
    doc.add_paragraph(
        "Estimativa de aderência ao Plano Fase 2 DevSecOps: aproximadamente 85% dos itens concluídos, "
        "10% parcialmente atendidos e 5% pendentes ou a verificar no CI. A equipe auditada executou "
        "efetivamente as três sprints planejadas, com gaps residuais de baixa severidade (IaC formal, "
        "CodeQL, DAST frontend, Pillow). O veredicto preliminar é favorável, sujeito à validação final "
        "dos workflows remotos até 30/06/2026."
    )

    doc.add_paragraph()
    footer = doc.add_paragraph()
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run(
        "— Fim da Entrega Parcial —\n"
        "Documento gerado com base no repositório auditado, planejamento_fase_2_devsecops.docx "
        "e relatorio_devsecops_avaliacao.docx (25/05/2026)"
    ).italic = True

    doc.save(out)
    print(f"Documento gerado: {out}")


if __name__ == "__main__":
    main()
