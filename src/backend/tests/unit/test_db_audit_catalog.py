from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

import pytest

from app.db import ensure
from app.repositories import audit_repo
from app.repositories import catalog_repo


pytestmark = pytest.mark.unit


def test_ensure_returns_value():
    assert ensure(42) == 42


def test_ensure_raises_on_none():
    with pytest.raises(RuntimeError, match="custom"):
        ensure(None, "custom")


def test_json_safe_converts_types():
    assert audit_repo._json_safe(date(2026, 1, 1)) == "2026-01-01"
    assert audit_repo._json_safe(time(10, 30)) == "10:30:00"
    assert audit_repo._json_safe(Decimal("1.5")) == "1.5"
    assert audit_repo._json_safe({"a": date(2026, 1, 1)}) == {"a": "2026-01-01"}
    assert audit_repo._json_safe([datetime(2026, 1, 1, 8, 0)])[0].startswith("2026")


def test_serialize_snapshot_none():
    assert audit_repo.serialize_snapshot(None) is None


def test_serialize_snapshot_dict():
    result = audit_repo.serialize_snapshot({"x": 1})
    assert result == {"x": 1}


def test_compute_changes_detects_diff():
    changes = audit_repo.compute_changes({"a": 1, "b": 2}, {"a": 1, "b": 3})
    assert changes == {"b": {"de": 2, "para": 3}}


def test_compute_changes_ignores_metadata():
    changes = audit_repo.compute_changes(
        {"updated_at": 1, "nome": "A"},
        {"updated_at": 2, "nome": "A"},
    )
    assert changes == {}


def test_log_audit_rejects_invalid_action():
    class User:
        id = 1
        email = "a@b.com"
        full_name = "A"
        role = "delegado"

    with pytest.raises(ValueError, match="Ação inválida"):
        audit_repo.log_audit(acba_id=1, user=User(), acao="invalida")


def test_list_ufs_without_filter(monkeypatch):
    monkeypatch.setattr(catalog_repo, "fetch_all", lambda q, p=None: [{"id": 1}])
    assert catalog_repo.list_ufs() == [{"id": 1}]


def test_list_ufs_with_query(monkeypatch):
    captured = {}

    def fake_fetch_all(query, params=None):
        captured["params"] = params
        return []

    monkeypatch.setattr(catalog_repo, "fetch_all", fake_fetch_all)
    catalog_repo.list_ufs("df")
    assert captured["params"]["like"] == "%df%"


def test_list_ufs_empty_query_uses_unfiltered(monkeypatch):
    calls = []

    def fake_fetch_all(query, params=None):
        calls.append(params)
        return []

    monkeypatch.setattr(catalog_repo, "fetch_all", fake_fetch_all)
    catalog_repo.list_ufs("   ")
    assert calls == [None]


def test_insert_uf_calls_fetch_one(monkeypatch):
    payload = {"sigla": "GO", "nome": "Goiás", "ativo": True}
    monkeypatch.setattr(
        catalog_repo,
        "fetch_one",
        lambda q, p=None: {"id": 2, **payload, "created_at": datetime.now()},
    )
    row = catalog_repo.insert_uf(payload)
    assert row["sigla"] == "GO"


def test_insert_uf_raises_when_missing_row(monkeypatch):
    monkeypatch.setattr(catalog_repo, "fetch_one", lambda q, p=None: None)
    with pytest.raises(RuntimeError):
        catalog_repo.insert_uf({"sigla": "GO", "nome": "Goiás", "ativo": True})


def test_delete_uf_executes_query(monkeypatch):
    captured = []
    monkeypatch.setattr(catalog_repo, "execute_query", lambda q, p=None: captured.append(p))
    catalog_repo.delete_uf(9)
    assert captured == [(9,)]


def test_list_cidades_passes_filters(monkeypatch):
    captured = {}

    def fake_fetch_all(query, params=None):
        captured["params"] = params
        return []

    monkeypatch.setattr(catalog_repo, "fetch_all", fake_fetch_all)
    catalog_repo.list_cidades("bras", uf_id=1)
    assert captured["params"]["uf_id"] == 1
    assert captured["params"]["like"] == "%bras%"


def test_agentes_atuais_resumo_empty():
    assert catalog_repo._agentes_atuais_resumo([]) is None


def test_agentes_atuais_resumo_formats():
    equipes = [{"equipe_numero": "01", "equipe_nome": "Alfa"}, {"equipe_numero": "02", "equipe_nome": None}]
    result = catalog_repo._agentes_atuais_resumo(equipes)
    assert "01" in result
    assert "02" in result
