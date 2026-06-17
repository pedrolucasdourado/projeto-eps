"""Fixtures compartilhadas entre todos os cenários BDD."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import auth as auth_router
from app.schemas import UserPublic


@pytest.fixture
def bdd_client():
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def bdd_ctx():
    """Contexto compartilhado entre os passos de um cenário."""
    return {}


@pytest.fixture
def bdd_auth_as():
    """Override de autenticação para um UserPublic específico."""

    def _override(user: UserPublic) -> None:
        app.dependency_overrides[auth_router.get_authenticated_user] = lambda: user

    return _override
