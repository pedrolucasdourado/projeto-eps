# IaC — Docker Compose + Checkov (decisão arquitetural)

**Projeto:** AAI — Assistente de Apreensão Inteligente  
**Escopo:** Fase 2 DevSecOps — **Passo 7** (Infraestrutura como Código)

## Decisão

O AAI **não utiliza Terraform nem Pulumi** nesta fase. A infraestrutura de execução local, homologação, CI e DAST é declarada em:

| Artefato | Função |
|----------|--------|
| `docker-compose.yml` | Stack principal (Postgres, Flyway, backend, frontend) |
| `docker-compose.ci.yml` | Overrides para CI/DAST (Postgres interno, portas de staging, proxy Next→API) |
| `src/backend/Dockerfile` | Imagem da API FastAPI (usuário não-root `aai`) |
| `src/frontend/Dockerfile` | Imagem Next.js standalone (usuário não-root `nextjs`) |
| `.env.example` | Contrato de variáveis obrigatórias (`POSTGRES_PASSWORD`, `JWT_SECRET`) |

A **análise estática de IaC** é feita pelo **Checkov** no workflow `.github/workflows/devsecops.yml`:

- `checkov -d src --framework dockerfile` — Dockerfiles backend e frontend
- `checkov -f docker-compose.yml -f docker-compose.ci.yml --framework yaml` — Compose

Falhas **bloqueiam** o pipeline (sem `--soft-fail`).

## Justificativa (por que Compose + Checkov atende o Passo 7)

1. **Escopo acadêmico/homologação:** um único host Docker; sem multi-região ou multi-conta cloud.
2. **Paridade dev / CI / DAST:** o mesmo Compose sobe localmente e no workflow `dast.yml`, reduzindo drift.
3. **Custo operacional:** Terraform/Pulumi exigiriam backend remoto, credenciais cloud e gestão de estado — fora do escopo da entrega EPS.
4. **Conformidade DevSecOps:** Checkov valida boas práticas em Dockerfiles e Compose (rede, `security_opt`, limites, segredos, usuário não-root).
5. **Rastreabilidade:** infraestrutura versionada em Git junto ao código; PRs passam por Checkov antes do merge.

## Conformidade — Passo 7 DevSecOps

| Requisito | Implementação | Status |
|-----------|---------------|--------|
| Infraestrutura declarada como código | `docker-compose.yml` + `docker-compose.ci.yml` | Conforme |
| Análise Checkov / Terrascan | Checkov no CI (`devsecops.yml`) | Conforme |
| Rede isolada entre serviços | Rede `aai_internal` dedicada | Conforme |
| Segredos sem default fraco | `POSTGRES_PASSWORD` e `JWT_SECRET` obrigatórios (`:?`) | Conforme |
| Limites CPU/memória | `mem_limit` e `cpus` por serviço | Conforme |
| Usuário não-root nos containers | `aai` (backend), `nextjs` (frontend) | Conforme |
| Terraform/Pulumi | Não aplicável nesta fase (documentado) | N/A |

## Endurecimento aplicado (`docker-compose.yml`)

- Rede interna dedicada (`aai_internal`) com subnet `172.28.0.0/16`
- Postgres e serviços expostos apenas em `127.0.0.1` (não `0.0.0.0`) em ambiente local
- `security_opt: no-new-privileges:true` em todos os serviços
- `POSTGRES_PASSWORD` e `JWT_SECRET` **obrigatórios** via `.env` (sem defaults `change_me`)
- Limites de CPU/memória por serviço; `shm_size` no Postgres
- Frontend: `read_only`, `cap_drop: ALL`, `cap_add: NET_BIND_SERVICE`, `tmpfs` para `/tmp` e `.next/cache`
- Backend: `init: true`, `tmpfs` para `/tmp` (LibreOffice/WeasyPrint)
- Volume Flyway montado `:ro`
- Logging com rotação (`max-size: 10m`, `max-file: 3`)
- Healthchecks em postgres, backend e frontend

## Staging DAST (`docker-compose.ci.yml`)

- Postgres **sem** porta publicada no host (acesso só pela rede interna)
- Backend e frontend expostos em `8000` e `3000` para o OWASP ZAP no GitHub Actions
- Frontend com proxy `/api` → `http://backend:8000` via `INTERNAL_API_URL`
- Usado pelo workflow `.github/workflows/dast.yml` (varredura frontend **e** API)

## Quando reavaliar Terraform/Pulumi

Adotar IaC cloud quando houver deploy em **AKS/EKS/Cloud Run/App Service** com ambientes separados (dev/staging/prod), secrets manager e políticas de rede gerenciadas pelo provedor.

## Comandos úteis

```bash
# Validar IaC localmente (mesmo gate do CI)
pip install checkov
checkov -d src --framework dockerfile --compact
checkov -f docker-compose.yml -f docker-compose.ci.yml --framework yaml --compact

# Subir stack local
cp .env.example .env   # editar senhas fortes
docker compose up --build -d --wait

# Subir staging como no CI/DAST
cat > .env.ci <<'EOF'
POSTGRES_USER=aai
POSTGRES_PASSWORD=aai_secret_ci_only
POSTGRES_DB=aai_db
JWT_SECRET=ci-jwt-secret-minimum-32-bytes-long!!
EOF
docker compose --env-file .env.ci \
  -f docker-compose.yml -f docker-compose.ci.yml \
  up --build -d --wait
curl -sf http://localhost:8000/health
curl -sf -o /dev/null -w "%{http_code}\n" http://localhost:3000/
```
