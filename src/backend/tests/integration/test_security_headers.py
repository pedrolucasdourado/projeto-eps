"""Testes de integração para verificar headers de segurança HTTP (CSP/XSS)."""
from __future__ import annotations

import pytest


pytestmark = pytest.mark.integration

_SECURITY_HEADERS = [
    "x-content-type-options",
    "x-frame-options",
    "x-xss-protection",
    "referrer-policy",
    "content-security-policy",
]


def test_health_endpoint_has_security_headers(client):
    response = client.get("/health")

    assert response.status_code == 200
    for header in _SECURITY_HEADERS:
        assert header in response.headers, f"Header ausente: {header}"


def test_x_content_type_options_is_nosniff(client):
    response = client.get("/health")

    assert response.headers["x-content-type-options"] == "nosniff"


def test_x_frame_options_is_deny(client):
    response = client.get("/health")

    assert response.headers["x-frame-options"] == "DENY"


def test_content_security_policy_blocks_scripts(client):
    response = client.get("/health")

    csp = response.headers["content-security-policy"]
    assert "script-src 'none'" in csp
    assert "object-src 'none'" in csp


def test_unauthenticated_route_also_has_security_headers(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    for header in _SECURITY_HEADERS:
        assert header in response.headers, f"Header ausente em rota 401: {header}"
