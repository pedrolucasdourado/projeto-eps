# Política de Segurança

**Projeto:** Assistente de Apreensão Inteligente (AAI) — Grupo 31  
**Instituição:** EPS / FCTE-UnB (em parceria com a PCDF)  
**Repositório:** [projeto-eps](https://github.com/pedrolucasdourado/projeto-eps)

Este documento descreve como reportar vulnerabilidades e quais versões recebem correções de segurança.

---

## Versões suportadas

O AAI está em desenvolvimento acadêmico. Apenas a branch principal (`main`) recebe correções de segurança ativas.

| Versão / branch      | Suporte a correções de segurança |
| -------------------- | -------------------------------- |
| `main` (atual)       | ✅ Sim                           |
| Tags / releases antigas | ❌ Não (salvo aviso explícito) |
| Branches de feature  | ❌ Não                           |
| Forks não oficiais   | ❌ Não                           |

> **Ambiente de produção:** este software foi concebido para homologação e entrega acadêmica. Não utilize em produção sem revisão de segurança, hardening de infraestrutura e validação pela equipe responsável.

---

## Escopo

**Dentro do escopo:**

- Backend FastAPI (`src/backend/`)
- Frontend Next.js (`src/frontend/`)
- Autenticação JWT, RBAC e APIs REST
- Infraestrutura declarada (`docker-compose.yml`, Dockerfiles)
- Dependências Python (`requirements.txt`) e Node (`package.json`)

**Fora do escopo:**

- Vulnerabilidades em serviços de terceiros (GitHub Actions, Docker Hub, Google Gemini API etc.) — reporte diretamente ao fornecedor
- Ataques que exijam acesso físico ou administrativo ao servidor do avaliador
- Denial of Service (DoS) em ambiente de homologação compartilhado
- Problemas em forks ou deploys não mantidos por este repositório

---

## Como reportar uma vulnerabilidade

**Não abra issues públicas** para falhas de segurança. Use um dos canais abaixo:

### 1. GitHub Security Advisories (preferencial)

1. Acesse **Security → Advisories → Report a vulnerability** no repositório  
2. Descreva o problema de forma técnica e reproduzível  

### 2. Contato direto com os mantenedores

Envie e-mail para a equipe do Grupo 31:

- **pedrolucasdourado@hotmail.com**
- **lucas.ramon@aluno.unb.br**

**Assunto sugerido:** `[AAI Security] Descrição breve da vulnerabilidade`

### O que incluir no reporte

- Descrição clara do problema e impacto
- Passos para reproduzir (request HTTP, payload, usuário/perfil usado)
- Versão ou commit (`git rev-parse HEAD`)
- Evidências (logs, screenshots, PoC) — **sem dados reais de operações policiais**
- Sugestão de correção (opcional)

---

## O que esperar após o reporte

| Etapa                         | Prazo estimado   |
| ----------------------------- | ---------------- |
| Confirmação de recebimento    | até 3 dias úteis |
| Avaliação inicial de severidade | até 7 dias úteis |
| Correção (crítica/alta)       | até 14 dias úteis |
| Correção (média/baixa)        | próximo ciclo de entrega |
| Divulgação coordenada         | após patch na `main` |

**Se a vulnerabilidade for aceita:** publicaremos correção na `main`, atualizaremos dependências afetadas quando aplicável e agradeceremos o reporte (se autorizado).

**Se for recusada ou fora de escopo:** explicaremos o motivo (falso positivo, configuração local, versão não suportada, etc.).

---

## Práticas de segurança do projeto

A esteira DevSecOps do AAI inclui, entre outras:

- **SAST:** Bandit, flake8, mypy, CodeQL  
- **SCA:** Safety (CI), Dependabot, `npm audit`  
- **DAST:** OWASP ZAP em staging (Docker Compose)  
- **IaC:** Checkov em Dockerfiles e Compose  

Relatórios e evidências estão em `docs/` e nos workflows em `.github/workflows/`.

---

## Divulgação responsável

Solicitamos que:

- Não explore vulnerabilidades além do necessário para demonstrá-las
- Não acesse, altere ou exfiltre dados de terceiros
- Aguarde prazo razoável para correção antes de divulgação pública
- Respeite a LGPD e a confidencialidade de dados sensíveis

Agradecemos contribuições que ajudem a manter o AAI mais seguro.
