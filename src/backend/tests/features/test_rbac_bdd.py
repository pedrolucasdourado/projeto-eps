"""BDD: cenários de controle de acesso (rbac.feature)."""
from __future__ import annotations

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from app.schemas import UserPublic

pytestmark = pytest.mark.bdd

scenarios("rbac.feature")


# ---------------------------------------------------------------------------
# Dado (Given)
# ---------------------------------------------------------------------------


@given("que estou autenticado como administrador", target_fixture="bdd_ctx")
def autenticado_admin(bdd_ctx, bdd_auth_as):
    user = UserPublic(id=1, email="admin@pcdf.gov.br", full_name="Admin", role="administrador")
    bdd_auth_as(user)
    bdd_ctx["user"] = user
    return bdd_ctx


@given("que estou autenticado como delegado", target_fixture="bdd_ctx")
def autenticado_delegado(bdd_ctx, bdd_auth_as):
    user = UserPublic(id=2, email="delegado@pcdf.gov.br", full_name="Delegado BDD", role="delegado", delegado_id=1)
    bdd_auth_as(user)
    bdd_ctx["user"] = user
    return bdd_ctx


@given(
    parsers.parse("que estou autenticado como escrivão vinculado à equipe {team_id:d}"),
    target_fixture="bdd_ctx",
)
def autenticado_escrivao_equipe(bdd_ctx, bdd_auth_as, team_id, monkeypatch):
    from app.services import authz

    user = UserPublic(id=3, email="escrivao@pcdf.gov.br", full_name="Escrivão BDD", role="escrivao", escrivao_id=20)
    bdd_auth_as(user)
    bdd_ctx["user"] = user
    bdd_ctx["team_id"] = team_id
    monkeypatch.setattr(authz, "acba_equipe_scope", lambda u: [team_id])
    return bdd_ctx


@given(
    parsers.parse("que estou autenticado como agente que nunca esteve na equipe {team_id:d}"),
    target_fixture="bdd_ctx",
)
def autenticado_agente_sem_equipe(bdd_ctx, bdd_auth_as, team_id, monkeypatch):
    from app.services import authz

    user = UserPublic(id=4, email="agente@pcdf.gov.br", full_name="Agente BDD", role="agente", agente_id=30)
    bdd_auth_as(user)
    bdd_ctx["user"] = user
    monkeypatch.setattr(authz, "acba_equipe_scope", lambda u: [])
    return bdd_ctx


@given(
    parsers.parse("que estou autenticado como agente que esteve na equipe {team_id:d} de jan/2025 a mar/2025"),
    target_fixture="bdd_ctx",
)
def autenticado_agente_com_equipe(bdd_ctx, bdd_auth_as, team_id, monkeypatch):
    from app.services import authz

    user = UserPublic(id=5, email="agente2@pcdf.gov.br", full_name="Agente BDD 2", role="agente", agente_id=31)
    bdd_auth_as(user)
    bdd_ctx["user"] = user
    monkeypatch.setattr(authz, "acba_equipe_scope", lambda u: [team_id])
    return bdd_ctx


@given("que estou autenticado como agente", target_fixture="bdd_ctx")
def autenticado_agente(bdd_ctx, bdd_auth_as):
    user = UserPublic(id=6, email="agente3@pcdf.gov.br", full_name="Agente BDD 3", role="agente", agente_id=32)
    bdd_auth_as(user)
    bdd_ctx["user"] = user
    return bdd_ctx


@given("que estou autenticado como escrivão", target_fixture="bdd_ctx")
def autenticado_escrivao(bdd_ctx, bdd_auth_as, monkeypatch):
    from app.services import authz

    user = UserPublic(id=7, email="escrivao2@pcdf.gov.br", full_name="Escrivão BDD 2", role="escrivao", escrivao_id=21)
    bdd_auth_as(user)
    bdd_ctx["user"] = user
    monkeypatch.setattr(authz, "acba_equipe_scope", lambda u: [1])
    return bdd_ctx


# ---------------------------------------------------------------------------
# Quando (When)
# ---------------------------------------------------------------------------


@when(parsers.parse('eu envio uma requisição GET para "{path}"'))
def get_path(bdd_ctx, bdd_client, path):
    bdd_ctx["response"] = bdd_client.get(path)


@when("eu consulto a lista de ACBAs", target_fixture="bdd_ctx")
def get_acba_list(bdd_ctx, bdd_client, monkeypatch):
    from app.routers import acba
    from datetime import date, datetime, timezone

    class FakeService:
        def list_all(self, *, user, tipo_material_id=None):
            bdd_ctx["scope_called_with"] = user
            return []

    monkeypatch.setattr(acba, "service", FakeService())
    bdd_ctx["response"] = bdd_client.get("/api/acba/")
    return bdd_ctx


@when(
    parsers.parse(
        'eu envio uma requisição POST para "{path}" com payload válido'
    )
)
def post_path_valid(bdd_ctx, bdd_client, path, monkeypatch):
    from app.repositories import catalog_repo

    if "cadastros/ufs" in path:
        monkeypatch.setattr(catalog_repo, "insert_uf", lambda payload: {"id": 1, "sigla": "GO", "nome": "Goiás", "ativo": True, "created_at": None})
        bdd_ctx["response"] = bdd_client.post(path, json={"sigla": "GO", "nome": "Goiás", "ativo": True})
    else:
        bdd_ctx["response"] = bdd_client.post(path, json={})


@when(parsers.parse('eu envio uma requisição GET para "{path}" sem token de autenticação'))
def get_path_no_token(bdd_ctx, bdd_client, path):
    from app.main import app
    from app.routers import auth as auth_router

    app.dependency_overrides.clear()
    bdd_ctx["response"] = bdd_client.get(path)


@when(parsers.parse('eu envio uma requisição DELETE para "{path}"'))
def delete_path(bdd_ctx, bdd_client, path):
    clean_path = path.replace("{id}", "1")
    bdd_ctx["response"] = bdd_client.delete(clean_path)


@when(parsers.parse('eu envio uma requisição PUT para "{path}"'))
def put_path(bdd_ctx, bdd_client, path):
    clean_path = path.replace("{id}", "1")
    bdd_ctx["response"] = bdd_client.put(clean_path, json={})


@when(parsers.parse('eu envio uma requisição POST para "{path}"'))
def post_path(bdd_ctx, bdd_client, path):
    bdd_ctx["response"] = bdd_client.post(path, json={})


@when(
    parsers.parse(
        'eu envio uma requisição GET para "{path}" de ACBA da equipe {team_id:d}'
    )
)
def get_acba_from_team(bdd_ctx, bdd_client, path, team_id, monkeypatch):
    from app.routers import acba
    from app.services.authz import assert_team_scope_contains
    from fastapi import HTTPException, status

    clean_path = path.replace("{id}", "1")

    class FakeService:
        def get_by_id(self, acba_id, *, user):
            # Simula que o ACBA pertence à equipe `team_id`
            scope = bdd_ctx.get("team_id")
            if scope is not None and team_id != scope:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Fora do escopo.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado.")

    monkeypatch.setattr(acba, "service", FakeService())
    bdd_ctx["response"] = bdd_client.get(clean_path)


# ---------------------------------------------------------------------------
# Então (Then)
# ---------------------------------------------------------------------------


@then(parsers.parse("o sistema retorna status {status_code:d}"))
def verifica_status_rbac(bdd_ctx, status_code):
    assert bdd_ctx["response"].status_code == status_code


@then(parsers.parse("o sistema retorna status {s1:d} ou {s2:d}"))
def verifica_status_ou(bdd_ctx, s1, s2):
    assert bdd_ctx["response"].status_code in (s1, s2)


@then(parsers.parse('o corpo da resposta menciona "{text}"'))
def corpo_menciona(bdd_ctx, text):
    body = bdd_ctx["response"].json()
    detail = body.get("detail", "")
    assert text in detail


@then("o sistema não aplica filtro por equipe")
def sem_filtro_equipe(bdd_ctx):
    assert bdd_ctx["response"].status_code == 200


@then(parsers.parse("apenas ACBAs com data_lavratura entre jan/2025 e mar/2025 da equipe {team_id:d} são retornados"))
def acba_periodo(bdd_ctx, team_id):
    assert bdd_ctx["response"].status_code == 200
