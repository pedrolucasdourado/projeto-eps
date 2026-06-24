from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402
from app.routers import auth as auth_router  # noqa: E402
from app.schemas import UserPublic  # noqa: E402

pytest_plugins = ["tests.conftest_db"]


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    app.dependency_overrides.clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user() -> UserPublic:
    return UserPublic(
        id=1,
        email="admin@example.com",
        full_name="Admin Teste",
        role="administrador",
    )


@pytest.fixture
def delegado_user() -> UserPublic:
    return UserPublic(
        id=2,
        email="delegado@example.com",
        full_name="Delegado Teste",
        role="delegado",
        delegado_id=10,
    )


@pytest.fixture
def escrivao_user() -> UserPublic:
    return UserPublic(
        id=3,
        email="escrivao@example.com",
        full_name="Escrivao Teste",
        role="escrivao",
        escrivao_id=20,
    )


@pytest.fixture
def authenticated_as():
    def _override(user: UserPublic) -> UserPublic:
        app.dependency_overrides[auth_router.get_authenticated_user] = lambda: user
        return user

    return _override
