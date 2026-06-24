from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from fastapi import HTTPException
from psycopg2 import Error

from tests.helpers.db_mock import PgError

from app.acba_schemas import AcbaCreate, AcbaDetail, AcbaUpdate
from app.repositories import audit_repo
from app.schemas import UserPublic
from app.services.acba_service import AcbaService
from tests.helpers.sample_data import acba_detail_dict


pytestmark = pytest.mark.unit


def _delegado() -> UserPublic:
    return UserPublic(id=2, email="d@p.com", full_name="Del", role="delegado", delegado_id=1)


def _escrivao(equipe_id: int = 1) -> UserPublic:
    return UserPublic(
        id=3, email="e@p.com", full_name="Esc", role="escrivao", escrivao_id=1
    )


def _detail(**overrides) -> AcbaDetail:
    return AcbaDetail.model_validate(acba_detail_dict(**overrides))


class FakeRepo:
    def __init__(self):
        self.rows = {}
        self.list_result = []

    def list_all(self, **kwargs):
        return self.list_result

    def get_by_id(self, record_id):
        return self.rows.get(record_id)

    def create(self, body, materiais, user_id):
        row = acba_detail_dict(id=99, **body)
        self.rows[99] = row
        return row

    def update(self, record_id, body):
        row = self.rows.get(record_id)
        if not row:
            return None
        row = {**row, **body}
        self.rows[record_id] = row
        return row

    def delete(self, record_id):
        self.rows.pop(record_id, None)

    def mark_pdf_gerado(self, record_id, user_id):
        row = self.rows[record_id]
        row["pdf_gerado_at"] = datetime.now(timezone.utc)


def _service_with_repo(repo: FakeRepo) -> AcbaService:
    svc = AcbaService()
    svc.repository = repo
    return svc


def test_list_all_returns_items(monkeypatch):
    repo = FakeRepo()
    repo.list_result = [acba_detail_dict()]
    svc = _service_with_repo(repo)
    items = svc.list_all(user=_delegado())
    assert len(items) == 1
    assert items[0].protocolo_numero == "ACBA-001"


def test_get_by_id_not_found():
    svc = _service_with_repo(FakeRepo())
    with pytest.raises(HTTPException) as exc:
        svc.get_by_id(1, user=_delegado())
    assert exc.value.status_code == 404


from tests.helpers.db_mock import PgError


def test_get_by_id_out_of_scope_returns_404(monkeypatch):
    repo = FakeRepo()
    repo.rows[1] = acba_detail_dict(equipe_id=99)
    svc = _service_with_repo(repo)
    monkeypatch.setattr("app.services.acba_service.authz.fetch_all", lambda *a, **k: [])
    with pytest.raises(HTTPException) as exc:
        svc.get_by_id(1, user=_escrivao())
    assert exc.value.status_code == 404


def test_create_logs_audit(monkeypatch):
    repo = FakeRepo()
    svc = _service_with_repo(repo)
    logged = []
    monkeypatch.setattr(audit_repo, "log_audit", lambda **kw: logged.append(kw))
    payload = AcbaCreate.model_validate(
        {
            **{k: v for k, v in acba_detail_dict().items() if k in AcbaCreate.model_fields},
            "materiais": [],
        }
    )
    detail = svc.create(payload, user=_delegado(), ip="127.0.0.1", user_agent="pytest")
    assert detail.id == 99
    assert logged[0]["acao"] == "criado"


def test_update_not_found():
    svc = _service_with_repo(FakeRepo())
    payload = AcbaUpdate.model_validate(
        {k: v for k, v in acba_detail_dict().items() if k in AcbaUpdate.model_fields}
    )
    with pytest.raises(HTTPException) as exc:
        svc.update(1, payload, user=_delegado())
    assert exc.value.status_code == 404


def test_delete_logs_audit_before_delete(monkeypatch):
    repo = FakeRepo()
    repo.rows[1] = acba_detail_dict()
    svc = _service_with_repo(repo)
    logged = []
    monkeypatch.setattr(audit_repo, "log_audit", lambda **kw: logged.append(kw))
    svc.delete(1, user=_delegado())
    assert logged[0]["acao"] == "excluido"
    assert 1 not in repo.rows


def test_assert_pdf_pronto_blocks_pending(monkeypatch):
    svc = _service_with_repo(FakeRepo())
    record = _detail(materiais_pendentes_revisao=2)
    with pytest.raises(HTTPException) as exc:
        svc.assert_pdf_pronto(record)
    assert exc.value.status_code == 409


def test_assert_pdf_pronto_allows_when_flag_set(monkeypatch):
    monkeypatch.setattr("app.services.acba_service.settings.acba_permitir_pdf_com_pendencia", True)
    svc = _service_with_repo(FakeRepo())
    svc.assert_pdf_pronto(_detail(materiais_pendentes_revisao=5))


def test_mark_pdf_gerado(monkeypatch):
    repo = FakeRepo()
    repo.rows[1] = acba_detail_dict()
    svc = _service_with_repo(repo)
    logged = []
    monkeypatch.setattr(audit_repo, "log_audit", lambda **kw: logged.append(kw))
    svc.mark_pdf_gerado(1, user=_delegado())
    assert logged[0]["acao"] == "pdf_gerado"


def test_reraise_pg_unique_protocol():
    err = PgError("23505")
    with pytest.raises(HTTPException) as exc:
        AcbaService._reraise_pg(err, on_update=False)
    assert exc.value.status_code == 409


def test_reraise_pg_fk_error():
    err = PgError("23503")
    with pytest.raises(HTTPException) as exc:
        AcbaService._reraise_pg(err, on_update=True)
    assert exc.value.status_code == 400


def test_reraise_pg_check_error():
    err = PgError("23514")
    with pytest.raises(HTTPException) as exc:
        AcbaService._reraise_pg(err, on_update=False)
    assert exc.value.status_code == 400


def test_update_success_logs_audit(monkeypatch):
    repo = FakeRepo()
    repo.rows[1] = acba_detail_dict()
    svc = _service_with_repo(repo)
    logged = []
    monkeypatch.setattr(audit_repo, "log_audit", lambda **kw: logged.append(kw))
    payload = AcbaUpdate.model_validate(
        {k: v for k, v in acba_detail_dict().items() if k in AcbaUpdate.model_fields}
    )
    updated = svc.update(1, payload, user=_delegado())
    assert updated.id == 1
    assert logged[0]["acao"] == "editado"


def test_create_pg_error(monkeypatch):
    class ErrRepo(FakeRepo):
        def create(self, body, materiais, user_id):
            raise PgError("23505")

    svc = _service_with_repo(ErrRepo())
    payload = AcbaCreate.model_validate(
        {
            **{k: v for k, v in acba_detail_dict().items() if k in AcbaCreate.model_fields},
            "materiais": [],
        }
    )
    with pytest.raises(HTTPException) as exc:
        svc.create(payload, user=_delegado())
    assert exc.value.status_code == 409


def test_get_by_id_success(monkeypatch):
    repo = FakeRepo()
    repo.rows[1] = acba_detail_dict(equipe_id=1)
    svc = _service_with_repo(repo)
    detail = svc.get_by_id(1, user=_delegado())
    assert detail.id == 1


def test_reraise_pg_non_pg_error():
    AcbaService._reraise_pg(ValueError("x"), on_update=False)

