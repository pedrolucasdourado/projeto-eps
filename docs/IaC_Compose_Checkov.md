# IaC — Docker Compose + Checkov (decisão arquitetural)

**Projeto:** AAI — Assistente de Apreensão Inteligente  
**Escopo:** Fase 2 DevSecOps — item 7 (Infraestrutura como código)

## Decisão

O AAI **não utiliza Terraform nem Pulumi** nesta fase. A infraestrutura de execução local, homologação e CI é declarada em:

| Artefato | Função |
|----------|--------|
| `docker-compose.yml` | Stack principal (Postgres, Flyway, backend, frontend) |
| `docker-compose.ci.yml` | Overrides para CI/DAST (Postgres interno, proxy Next→API) |
| `src/backend/Dockerfile` | Imagem da API FastAPI |
| `src/frontend/Dockerfile` | Imagem Next.js (standalone, usuário não-root) |
| `.env.example` | Contrato de variáveis obrigatórias (`POSTGRES_PASSWORD`, `JWT_SECRET`) |

A **análise estática de IaC** é feita pelo **Checkov** no workflow `.github/workflows/devsecops.yml`, com frameworks `dockerfile` (imagens) e `yaml` (Compose). Falhas bloqueiam o pipeline.

## Justificativa

1. **Escopo do projeto:** ambiente acadêmico/homologação com um único host Docker; não há provisionamento multi-região ou multi-conta em nuvem.
2. **Paridade dev/CI:** o mesmo Compose sobe localmente e no DAST (ZAP), reduzindo drift.
3. **Custo operacional:** Terraform/Pulumi exigiriam backend remoto, credenciais cloud e estado — fora do escopo atual da entrega.
4. **Conformidade DevSecOps:** Checkov cobre boas práticas em Dockerfiles e Compose (rede, `security_opt`, limites, segredos).

## Endurecimento aplicado (`docker-compose.yml`)

- Rede interna dedicada (`aai_internal`) com subnet definida
- Postgres e serviços expostos apenas em `127.0.0.1` (não `0.0.0.0`)
- `security_opt: no-new-privileges:true` em todos os serviços
- `POSTGRES_PASSWORD` e `JWT_SECRET` **obrigatórios** via `.env` (sem defaults fracos)
- Limites de CPU/memória por serviço
- Frontend com filesystem `read_only` + `tmpfs` para `/tmp`
- Backend com `tmpfs` para `/tmp` (LibreOffice/WeasyPrint)
- Volume Flyway montado `:ro`

## Quando reavaliar Terraform/Pulumi

Adotar IaC cloud quando houver deploy em **AKS/EKS/Cloud Run/App Service** com ambientes separados (dev/staging/prod), secrets manager e políticas de rede gerenciadas pelo provedor.

## Comandos úteis

```bash
# Validar IaC localmente (mesmo gate do CI)
checkov -d src --framework dockerfile --compact
checkov -f docker-compose.yml -f docker-compose.ci.yml --framework yaml --compact

# Subir stack local
cp .env.example .env   # editar senhas
docker compose up --build -d

# Subir como no CI/DAST
docker compose --env-file .env.ci -f docker-compose.yml -f docker-compose.ci.yml up --build -d --wait
```
