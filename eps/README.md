# Assistente de Apreensão Inteligente (AAI)

Aplicação full stack para ambiente operacional com autenticação por JWT, API FastAPI, PostgreSQL com migrations Flyway, frontend Next.js e orquestração com Docker Compose.

## Stack

| Camada       | Tecnologia        |
|-------------|-------------------|
| Frontend    | Next.js 15, React 19, Tailwind CSS |
| Backend     | Python 3.12, FastAPI |
| Banco       | PostgreSQL 16 |
| Migrations  | Flyway 10 |

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e Docker Compose **v2.20+** (necessário para o backend aguardar o serviço **flyway** com `condition: service_completed_successfully`)

## Como executar

1. Na raiz do projeto:

   ```bash
   cp .env.example .env
   ```

2. Subir todos os serviços:

   ```bash
   docker compose up --build
   ```

3. Abrir no navegador:

   - **Frontend:** http://localhost:3000  
   - **API (documentação OpenAPI):** http://localhost:8000/docs  
   - **Healthcheck:** http://localhost:8000/health  

### Credenciais de teste

| Campo  | Valor            |
|--------|------------------|
| E-mail | `admin@admin.com` |
| Senha  | `admin123`        |

O usuário é criado pela migration Flyway `V1__create_users_and_seed.sql`.

## Cadastros auxiliares

As entidades de apoio ao ACBA ficam em `/api/cadastros/*` (UFs, cidades, unidades, delegacias, tipos de procedimento, autoridades, escrivãos, membros da equipe e condutores). No frontend, use o menu **Cadastros auxiliares** ou as rotas `/cadastros/{slug}`.

- **Flyway `V3__cadastros_auxiliares.sql`** — cria as tabelas e insere **DF** e **Brasília** vinculada ao DF, além de exemplos genéricos opcionais.
- **Flyway `V4__acba_refactor_catalog_fks.sql`** — redefine `acba_records` com chaves estrangeiras para esses cadastros e tabela associativa para múltiplos membros da equipe.

## Módulo ACBA

O módulo **Auto Circunstanciado de Busca e Arrecadação (ACBA)** inclui:

- CRUD (`/api/acba`): criar, listar, detalhar, editar e excluir, com vínculos aos cadastros auxiliares (evita texto livre onde há catálogo).
- Histórico de schema: `V2__create_acba_records.sql` (versão inicial da tabela); **estrutura atual** consolidada em `V4` após cadastros em `V3`.
- **PDF** (`GET /api/acba/{id}/pdf`): preenchimento de um **template DOCX** (`python-docx`) com placeholders `{{...}}` e conversão para PDF via **LibreOffice** no container do backend. Substitua o arquivo em `backend/templates/` pelo documento oficial da instituição mantendo os mesmos placeholders (veja `backend/templates/README.md`).
- Telas: `/acba`, `/acba/new`, `/acba/{id}`, `/acba/{id}/edit`; no detalhe, **Gerar PDF** faz o download do arquivo gerado.

## O que sobe no Compose

1. **postgres** — banco persistente (`postgres_data`).
2. **flyway** — executa migrations em `/flyway/sql` e encerra (`migrate`).
3. **backend** — inicia depois que o Flyway conclui com sucesso (`depends_on`).
4. **frontend** — sobe após o backend estar saudável; build com `NEXT_PUBLIC_API_URL` padrão `http://localhost:8000` (chamada direta da API, com CORS liberado para `localhost` e `127.0.0.1` na porta do frontend).

## Variáveis de ambiente

Veja [.env.example](.env.example). Principais:

- `DATABASE_URL` — montada pelo Compose para o backend (`postgresql://...`).
- `JWT_SECRET` — segredo dos tokens (troque em produção).
- `CORS_ORIGINS` — origens permitidas para o frontend (por vírgula).
- `NEXT_PUBLIC_API_URL` — URL da API no navegador (padrão no Compose: `http://localhost:8000`). O backend já envia `Access-Control-Allow-Origin` para `localhost` e `127.0.0.1` na porta do frontend.
- `INTERNAL_API_URL` — opcional. Se definir (ex.: `http://backend:8000`) **e** deixar `NEXT_PUBLIC_API_URL` vazio no build, o Next faz proxy de `/api` para esse host (útil para evitar CORS em cenários especiais). Exige que o hostname resolva dentro da rede do container.
- `ACBA_DOCX_TEMPLATE_PATH` — caminho absoluto no container para o DOCX modelo do ACBA (definido no Compose).
- `LIBREOFFICE_CMD` — comando para conversão headless (ex.: `soffice`).

> O Next.js incorpora `NEXT_PUBLIC_*` **no momento do build**. Em produção com outra URL de API, defina `NEXT_PUBLIC_API_URL` antes do `docker compose build`.

## Estrutura do repositório

```
├── frontend/          # Next.js (login, dashboard, ACBA, cadastros auxiliares)
├── backend/           # FastAPI (/api/auth, /api/acba, /api/cadastros, health)
├── database/flyway/sql/ # Scripts versionados Flyway
├── docker-compose.yml
├── .env.example
└── README.md
```

## Desenvolvimento local (sem Docker)

- **Backend:** Python 3.12, `pip install -r backend/requirements.txt`, exporte `DATABASE_URL` apontando para um Postgres com migrations aplicadas, depois `uvicorn app.main:app --reload` a partir da pasta `backend/`.
- **Frontend:** Node 20+, `npm install` e `npm run dev` na pasta `frontend/`, com `NEXT_PUBLIC_API_URL` apontando para a API.
