"""BDD: cenários de autenticação (login.feature)."""
from __future__ import annotations

import bcrypt
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from app.services import auth_service

pytestmark = pytest.mark.bdd

scenarios("login.feature")


# ---------------------------------------------------------------------------
# Dado (Given)
# ---------------------------------------------------------------------------


@given(
    parsers.parse('que existe um usuário com e-mail "{email}" e senha "{password}"'),
    target_fixture="bdd_ctx",
)
def usuario_com_email_e_senha(bdd_ctx, monkeypatch, email, password):
    hash_ = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    bdd_ctx.update({"email": email, "password": password})
    monkeypatch.setattr(
        auth_service,
        "fetch_user_by_email",
        lambda e: {
            "id": 1,
            "email": email,
            "password_hash": hash_,
            "full_name": "Delegado BDD",
            "role": "delegado",
            "ativo": True,
            "delegado_id": 1,
            "escrivao_id": None,
            "agente_id": None,
        },
    )
    return bdd_ctx


@given(
    parsers.parse('que existe um usuário com e-mail "{email}"'),
    target_fixture="bdd_ctx",
)
def usuario_com_email(bdd_ctx, monkeypatch, email):
    hash_ = bcrypt.hashpw(b"Senha@123", bcrypt.gensalt()).decode()
    bdd_ctx.update({"email": email, "password": "Senha@123"})
    monkeypatch.setattr(
        auth_service,
        "fetch_user_by_email",
        lambda e: {
            "id": 1,
            "email": email,
            "password_hash": hash_,
            "full_name": "Delegado BDD",
            "role": "delegado",
            "ativo": True,
            "delegado_id": 1,
            "escrivao_id": None,
            "agente_id": None,
        },
    )
    return bdd_ctx


@given(
    parsers.parse(
        'que existe um usuário com e-mail "{email}" e situação "{situacao}"'
    ),
    target_fixture="bdd_ctx",
)
def usuario_com_situacao(bdd_ctx, monkeypatch, email, situacao):
    ativo = situacao != "desativado"
    hash_ = bcrypt.hashpw(b"Senha@123", bcrypt.gensalt()).decode()
    bdd_ctx.update({"email": email, "password": "Senha@123"})
    monkeypatch.setattr(
        auth_service,
        "fetch_user_by_email",
        lambda e: {
            "id": 2,
            "email": email,
            "password_hash": hash_,
            "full_name": "Inativo BDD",
            "role": "delegado",
            "ativo": ativo,
            "delegado_id": 1,
            "escrivao_id": None,
            "agente_id": None,
        },
    )
    return bdd_ctx


@given(
    parsers.parse('que não existe usuário com e-mail "{email}"'),
    target_fixture="bdd_ctx",
)
def usuario_inexistente(bdd_ctx, monkeypatch, email):
    bdd_ctx.update({"email": email, "password": "qualquer"})
    monkeypatch.setattr(auth_service, "fetch_user_by_email", lambda e: None)
    return bdd_ctx


@given(
    parsers.parse('que estou autenticado como "{email}"'),
    target_fixture="bdd_ctx",
)
def autenticado_como(bdd_ctx, monkeypatch, email):
    token = auth_service.create_access_token(3, email)
    bdd_ctx.update({"token": token})
    monkeypatch.setattr(
        auth_service,
        "fetch_user_by_id",
        lambda uid: {
            "id": 3,
            "email": email,
            "password_hash": "x",
            "full_name": "Escrivão BDD",
            "role": "escrivao",
            "ativo": True,
            "delegado_id": None,
            "escrivao_id": 5,
            "agente_id": None,
        },
    )
    return bdd_ctx


# ---------------------------------------------------------------------------
# Quando (When)
# ---------------------------------------------------------------------------


@when(
    parsers.parse(
        'eu envio uma requisição POST para "{path}" com as credenciais'
    )
)
def post_com_credenciais(bdd_ctx, bdd_client, path):
    bdd_ctx["response"] = bdd_client.post(
        path,
        json={"email": bdd_ctx["email"], "password": bdd_ctx["password"]},
    )


@when(
    parsers.parse(
        'eu envio uma requisição POST para "{path}" com esse e-mail'
    )
)
def post_com_email_inexistente(bdd_ctx, bdd_client, path):
    bdd_ctx["response"] = bdd_client.post(
        path,
        json={"email": bdd_ctx["email"], "password": "qualquer"},
    )


@when(parsers.parse('eu envio login com a senha "{password}"'))
def post_com_senha_errada(bdd_ctx, bdd_client, password):
    bdd_ctx["response"] = bdd_client.post(
        "/api/auth/login",
        json={"email": bdd_ctx["email"], "password": password},
    )


@when("eu envio login com as credenciais corretas")
def post_com_credenciais_corretas(bdd_ctx, bdd_client):
    bdd_ctx["response"] = bdd_client.post(
        "/api/auth/login",
        json={"email": bdd_ctx["email"], "password": bdd_ctx["password"]},
    )


@when(parsers.parse('eu envio uma requisição GET para "{path}" sem token'))
def get_sem_token(bdd_ctx, bdd_client, path):
    bdd_ctx["response"] = bdd_client.get(path)


@when(parsers.parse('eu envio uma requisição GET para "{path}" com o token'))
def get_com_token(bdd_ctx, bdd_client, path):
    bdd_ctx["response"] = bdd_client.get(
        path,
        headers={"Authorization": f"Bearer {bdd_ctx['token']}"},
    )


# ---------------------------------------------------------------------------
# Então (Then)
# ---------------------------------------------------------------------------


@then(parsers.parse("o sistema retorna status {status_code:d}"))
def verifica_status(bdd_ctx, status_code):
    assert bdd_ctx["response"].status_code == status_code


@then(parsers.parse('o corpo da resposta contém um "{field}"'))
def corpo_contem_campo(bdd_ctx, field):
    assert field in bdd_ctx["response"].json()


@then(parsers.parse('o campo "token_type" é "{value}"'))
def campo_token_type(bdd_ctx, value):
    assert bdd_ctx["response"].json()["token_type"] == value


@then(parsers.parse('o campo "user.role" é "{value}"'))
def campo_user_role(bdd_ctx, value):
    assert bdd_ctx["response"].json()["user"]["role"] == value


@then(parsers.parse('o campo "role" é "{value}"'))
def campo_role(bdd_ctx, value):
    assert bdd_ctx["response"].json()["role"] == value


@then(parsers.parse('o corpo da resposta contém o detalhe "{detail}"'))
def corpo_contem_detalhe(bdd_ctx, detail):
    assert bdd_ctx["response"].json()["detail"] == detail
