from __future__ import annotations

from datetime import date, time

import pytest
from pydantic import ValidationError

from app.acba_schemas import AcbaCreate


pytestmark = pytest.mark.unit


def _base_payload(**overrides) -> dict:
    payload = {
        "processo_numero": "PROC-001",
        "protocolo_numero": "ACBA-001",
        "unidade_id": 1,
        "delegacia_id": 1,
        "cidade_id": 1,
        "data_lavratura": date(2026, 5, 26),
        "hora_lavratura": time(10, 30),
        "tipo_procedimento_id": 1,
        "procedimento_numero": "IPL-001",
        "fundamento_legal": "Mandado judicial",
        "endereco_busca": "Rua de Teste, 123",
        "alvo_busca": "Alvo Teste",
        "assinatura_responsavel": "Delegado Teste",
        "observacoes": "",
        "equipe_id": 1,
        "morador_nome": "Morador Teste",
        "morador_cpf": "00000000000",
        "morador_rg": "123456",
        "morador_filiacao": "Filiacao Teste",
        "morador_telefone": "61999990000",
        "testemunhas": [],
        "materiais": [],
    }
    payload.update(overrides)
    return payload


def test_morador_ausente_requires_arrombamento_witness():
    with pytest.raises(ValidationError) as exc:
        AcbaCreate.model_validate(
            _base_payload(
                morador_ausente_245_4=True,
                morador_ausente_245_4_obs="Morador nao localizado.",
            )
        )

    assert "testemunha" in str(exc.value)


def test_morador_ausente_normalizes_witness_and_clears_present_resident():
    acba = AcbaCreate.model_validate(
        _base_payload(
            morador_ausente_245_4=True,
            morador_ausente_245_4_obs="Morador nao localizado.",
            morador_nome="Dado enviado indevidamente",
            morador_cpf="11111111111",
            morador_rg="RG",
            morador_filiacao="Filiacao",
            morador_telefone="61999990000",
            testemunhas=[
                {
                    "tipo": "arrombamento",
                    "nome": "Vizinho Teste",
                    "cpf": "12345678900",
                    "rg": "123456",
                    "filiacao": "Filiacao Teste",
                    "endereco": "Rua Vizinha, 1",
                }
            ],
        )
    )

    assert acba.morador_nome == ""
    assert acba.morador_cpf == ""
    assert acba.testemunhas[0].tipo == "arrombamento"
    assert acba.testemunhas[0].arrombamento is not None
