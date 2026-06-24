from __future__ import annotations

import pytest

from app import db
from app.repositories import catalog_repo
from app.repositories.acba_repository import AcbaRepository
from app.repositories import audit_repo
from app.schemas import UserPublic


pytestmark = [pytest.mark.integration, pytest.mark.postgres]


def test_db_fetch_admin_user(postgres_db):
    row = db.fetch_user_by_email("admin@admin.com")
    assert row is not None
    assert row["email"] == "admin@admin.com"


def test_db_fetch_user_by_id(postgres_db):
    row = db.fetch_user_by_email("admin@admin.com")
    assert row is not None
    by_id = db.fetch_user_by_id(row["id"])
    assert by_id["email"] == "admin@admin.com"


def test_db_ensure_and_fetch_helpers(postgres_db):
    rows = db.fetch_all("SELECT id, sigla FROM ufs ORDER BY id LIMIT 1")
    assert rows
    one = db.fetch_one("SELECT id FROM ufs WHERE id = %s", (rows[0]["id"],))
    assert one is not None


def test_catalog_repo_lists_seed_data(postgres_db):
    ufs = catalog_repo.list_ufs()
    assert any(u["sigla"] == "DF" for u in ufs)
    cidades = catalog_repo.list_cidades(uf_id=ufs[0]["id"])
    assert cidades
    assert catalog_repo.list_unidades()
    assert catalog_repo.list_delegacias()
    assert catalog_repo.list_tipos_procedimento()
    assert catalog_repo.list_delegados()
    assert catalog_repo.list_escrivaos()
    assert catalog_repo.list_agentes()
    assert catalog_repo.list_equipes()
    assert catalog_repo.list_processos()
    assert catalog_repo.list_tipos_material()


def test_catalog_repo_uf_roundtrip(postgres_db):
    created = catalog_repo.insert_uf({"sigla": "TS", "nome": "Teste UF", "ativo": True})
    assert created["sigla"] == "TS"
    fetched = catalog_repo.get_uf(created["id"])
    assert fetched["nome"] == "Teste UF"
    updated = catalog_repo.update_uf(
        created["id"],
        {"sigla": "TS", "nome": "Teste UF Atualizada", "ativo": True},
    )
    assert updated["nome"] == "Teste UF Atualizada"
    catalog_repo.delete_uf(created["id"])
    assert catalog_repo.get_uf(created["id"]) is None


def test_acba_repository_list_and_empty_scope(postgres_db):
    repo = AcbaRepository()
    all_rows = repo.list_all()
    assert isinstance(all_rows, list)
    assert repo.list_all(equipe_ids=[]) == []


def test_audit_repo_log_and_list(postgres_db):
    acba_rows = AcbaRepository().list_all()
    if not acba_rows:
        pytest.skip("Sem ACBA seed para testar auditoria")
    acba_id = acba_rows[0]["id"]
    user = UserPublic(id=1, email="admin@admin.com", full_name="Admin", role="administrador")
    audit_repo.log_audit(acba_id=acba_id, user=user, acao="pdf_gerado", ip="127.0.0.1")
    entries = audit_repo.list_for_acba(acba_id)
    assert entries
    full = audit_repo.get_entry(entries[0]["id"])
    assert full["acao"] == "pdf_gerado"
