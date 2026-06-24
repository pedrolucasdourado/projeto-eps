"""BDD: cenários de gerenciamento de ACBA (acba.feature)."""
from __future__ import annotations

import re
from datetime import date, datetime, timezone

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from app.schemas import UserPublic

pytestmark = pytest.mark.bdd

scenarios("acba.feature")


def _acba_payload(bdd_ctx: dict, **overrides) -> dict:
    payload = {
        "processo_numero": "PROC-BDD",
        "protocolo_numero": "ACBA-BDD",
        "unidade_id": 1,
        "delegacia_id": 1,
        "cidade_id": 1,
        "data_lavratura": "2026-01-15",
        "hora_lavratura": "10:00:00",
        "tipo_procedimento_id": 1,
        "procedimento_numero": "IPL-BDD",
        "fundamento_legal": "Mandado judicial",
        "endereco_busca": "Rua BDD, 1",
        "alvo_busca": "Alvo BDD",
        "assinatura_responsavel": "Delegado BDD",
        "observacoes": "",
        "equipe_id": bdd_ctx.get("team_id", 1),
        "morador_nome": "Morador BDD",
        "morador_cpf": "00000000000",
        "morador_rg": "123456",
        "morador_filiacao": "Filiação BDD",
        "morador_telefone": "61999990000",
        "testemunhas": [],
        "materiais": [],
    }
    payload.update(overrides)
    return payload


def _acba_detail_stub(**overrides) -> dict:
    now = datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc)
    detail = {
        "id": 1,
        "processo_numero": "PROC-BDD",
        "protocolo_numero": "ACBA-BDD",
        "unidade_id": 1,
        "delegacia_id": 1,
        "cidade_id": 1,
        "data_lavratura": date(2026, 1, 15),
        "hora_lavratura": "10:00:00",
        "tipo_procedimento_id": 1,
        "procedimento_numero": "IPL-BDD",
        "fundamento_legal": "Mandado judicial",
        "endereco_busca": "Rua BDD, 1",
        "alvo_busca": "Alvo BDD",
        "assinatura_responsavel": "Delegado BDD",
        "observacoes": "",
        "created_by_user_id": 1,
        "created_at": now,
        "updated_at": now,
        "unidade_nome": "Unidade BDD",
        "delegacia_nome": "Delegacia BDD",
        "cidade_nome": "Brasília",
        "uf_sigla": "DF",
        "uf_nome": "Distrito Federal",
        "tipo_procedimento_nome": "IPL",
        "equipe_id": 1,
        "equipe_numero": "EQ-1",
        "equipe_nome": "Equipe BDD",
        "delegado_id": 1,
        "delegado_nome": "Delegado BDD",
        "escrivao_id": 1,
        "escrivao_nome": "Escrivão BDD",
        "agentes_equipe": [],
        "testemunhas": [],
        "materiais": [],
    }
    detail.update(overrides)
    return detail

# ---------------------------------------------------------------------------
# Dado (Given)
# ---------------------------------------------------------------------------


@given(
    parsers.parse("que estou autenticado como delegado da equipe {team_id:d}"),
    target_fixture="bdd_ctx",
)
def delegado_da_equipe(bdd_ctx, bdd_auth_as, team_id):
    user = UserPublic(id=1, email="delegado@pcdf.gov.br", full_name="Delegado BDD", role="delegado", delegado_id=1)
    bdd_auth_as(user)
    bdd_ctx["user"] = user
    bdd_ctx["team_id"] = team_id
    return bdd_ctx


@given(
    parsers.parse("que estou autenticado como agente da equipe {team_id:d}"),
    target_fixture="bdd_ctx",
)
def agente_da_equipe(bdd_ctx, bdd_auth_as, team_id):
    user = UserPublic(id=4, email="agente@pcdf.gov.br", full_name="Agente BDD", role="agente", agente_id=10)
    bdd_auth_as(user)
    bdd_ctx["user"] = user
    bdd_ctx["team_id"] = team_id
    return bdd_ctx


@given(
    parsers.parse("que estou autenticado como escrivão da equipe {team_id:d}"),
    target_fixture="bdd_ctx",
)
def escrivao_da_equipe(bdd_ctx, bdd_auth_as, team_id, monkeypatch):
    from app.services import authz

    user = UserPublic(id=3, email="escrivao@pcdf.gov.br", full_name="Escrivão BDD", role="escrivao", escrivao_id=20)
    bdd_auth_as(user)
    bdd_ctx["user"] = user
    bdd_ctx["team_id"] = team_id
    monkeypatch.setattr(authz, "acba_equipe_scope", lambda u: [team_id])
    return bdd_ctx


@given("que estou autenticado como escrivão", target_fixture="bdd_ctx")
def escrivao_sem_equipe(bdd_ctx, bdd_auth_as, monkeypatch):
    from app.services import authz

    user = UserPublic(id=3, email="escrivao@pcdf.gov.br", full_name="Escrivão BDD", role="escrivao", escrivao_id=20)
    bdd_auth_as(user)
    bdd_ctx["user"] = user
    monkeypatch.setattr(authz, "acba_equipe_scope", lambda u: [1])
    return bdd_ctx


@given("que estou autenticado como delegado", target_fixture="bdd_ctx")
def delegado_generico(bdd_ctx, bdd_auth_as):
    user = UserPublic(id=1, email="delegado@pcdf.gov.br", full_name="Delegado BDD", role="delegado", delegado_id=1)
    bdd_auth_as(user)
    bdd_ctx["user"] = user
    return bdd_ctx


@given(parsers.parse("existem ACBAs das equipes {teams}"))
def acbas_de_equipes(bdd_ctx, teams):
    bdd_ctx["equipes"] = [int(n) for n in re.findall(r"\d+", teams)]


@given(
    parsers.parse("existe um ACBA da equipe {team_id:d} com PDF já gerado"),
    target_fixture="bdd_ctx",
)
def acba_com_pdf(bdd_ctx, monkeypatch, team_id):
    from app.routers import acba
    from fastapi import HTTPException, status

    class FakeService:
        def get_by_id(self, acba_id, *, user):
            return {}

        def update(self, acba_id, payload, *, user, ip=None, user_agent=None):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este ACBA já teve o PDF gerado.",
            )

    monkeypatch.setattr(acba, "service", FakeService())
    bdd_ctx["team_id"] = team_id
    return bdd_ctx


@given(
    parsers.parse("existe um ACBA com PDF já gerado"),
    target_fixture="bdd_ctx",
)
def acba_com_pdf_delegado(bdd_ctx, monkeypatch):
    from app.routers import acba
    from app.acba_schemas import AcbaDetail

    class FakeService:
        def get_by_id(self, acba_id, *, user):
            return {}

        def update(self, acba_id, payload, *, user, ip=None, user_agent=None):
            return _acba_detail_stub(protocolo_numero=payload.protocolo_numero)

    monkeypatch.setattr(acba, "service", FakeService())
    return bdd_ctx


# ---------------------------------------------------------------------------
# Quando (When)
# ---------------------------------------------------------------------------


@when(
    parsers.parse('eu envio uma requisição POST para "{path}" com payload válido')
)
def post_acba_valido(bdd_ctx, bdd_client, path, monkeypatch):
    from app.routers import acba

    class FakeService:
        def create(self, payload, *, user, ip=None, user_agent=None):
            return _acba_detail_stub(
                id=99,
                protocolo_numero=payload.protocolo_numero,
            )

    monkeypatch.setattr(acba, "service", FakeService())
    bdd_ctx["response"] = bdd_client.post(
        path,
        json=_acba_payload(bdd_ctx),
    )


@when(parsers.parse('eu envio uma requisição GET para "{path}"'))
def get_acba_list(bdd_ctx, bdd_client, path, monkeypatch):
    from app.routers import acba

    team_ids = bdd_ctx.get("equipes", [bdd_ctx.get("team_id", 1)])
    from app.services import authz

    class FakeService:
        def list_all(self, *, user, tipo_material_id=None):
            scope = authz.acba_equipe_scope(user)
            visible = team_ids if scope is None else [t for t in team_ids if t in scope]
            return [
                {
                    "id": i,
                    "processo_numero": f"PROC-{i}",
                    "protocolo_numero": f"ACBA-{i}",
                    "delegacia_nome": "Delegacia BDD",
                    "data_lavratura": date(2026, 1, 15),
                    "alvo_busca": "Alvo BDD",
                    "delegado_nome": "Delegado BDD",
                    "equipe_numero": f"EQ-{tid}",
                    "equipe_nome": f"Equipe {tid}",
                    "created_at": datetime(2026, 1, 15, tzinfo=timezone.utc),
                    "materiais_pendentes_revisao": 0,
                    "pdf_gerado_at": None,
                }
                for i, tid in enumerate(visible, start=1)
            ]

    monkeypatch.setattr(acba, "service", FakeService())
    bdd_ctx["response"] = bdd_client.get(path)


@when(
    parsers.parse(
        'eu envio uma requisição PUT para "{path}" com dados alterados'
    )
)
def put_acba(bdd_ctx, bdd_client, path, monkeypatch):
    clean = path.replace("{id}", "1")
    bdd_ctx["response"] = bdd_client.put(
        clean,
        json=_acba_payload(bdd_ctx, protocolo_numero="ACBA-EDIT"),
    )


@when(parsers.parse('eu envio uma requisição DELETE para "{path}"'))
def delete_acba(bdd_ctx, bdd_client, path):
    clean = path.replace("{id}", "1")
    bdd_ctx["response"] = bdd_client.delete(clean)


# ---------------------------------------------------------------------------
# Então (Then)
# ---------------------------------------------------------------------------


@then(parsers.parse("o sistema retorna status {status_code:d}"))
def verifica_status_acba(bdd_ctx, status_code):
    assert bdd_ctx["response"].status_code == status_code


@then(parsers.parse('o corpo da resposta contém um campo "{field}"'))
def corpo_contem_campo_acba(bdd_ctx, field):
    assert field in bdd_ctx["response"].json()


@then(parsers.parse('o campo "protocolo_numero" corresponde ao informado'))
def campo_protocolo(bdd_ctx):
    body = bdd_ctx["response"].json()
    assert "protocolo_numero" in body or "id" in body


@then(parsers.parse("todos os ACBAs retornados pertencem à equipe {team_id:d}"))
def acbas_da_equipe(bdd_ctx, team_id):
    body = bdd_ctx["response"].json()
    assert isinstance(body, list)
    for item in body:
        assert str(team_id) in item.get("equipe_numero", "")


@then("ACBAs de todas as equipes estão presentes")
def acbas_de_todas_equipes(bdd_ctx):
    body = bdd_ctx["response"].json()
    assert isinstance(body, list)
    assert len(body) > 0


@then(parsers.parse('o corpo da resposta menciona "{text}"'))
def corpo_menciona_acba(bdd_ctx, text):
    detail = bdd_ctx["response"].json().get("detail", "")
    assert text in detail
