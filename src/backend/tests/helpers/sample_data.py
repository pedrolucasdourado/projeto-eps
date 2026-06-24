"""Dados de exemplo reutilizáveis nos testes."""

from __future__ import annotations

from datetime import date, datetime, time, timezone

NOW = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)


def uf_row(**overrides):
    row = {
        "id": 1,
        "sigla": "DF",
        "nome": "Distrito Federal",
        "ativo": True,
        "created_at": NOW,
    }
    row.update(overrides)
    return row


def cidade_row(**overrides):
    row = {
        "id": 1,
        "nome": "Brasília",
        "uf_id": 1,
        "uf_sigla": "DF",
        "uf_nome": "Distrito Federal",
        "ativo": True,
        "created_at": NOW,
    }
    row.update(overrides)
    return row


def unidade_row(**overrides):
    row = {"id": 1, "nome": "DPC", "ativo": True, "created_at": NOW}
    row.update(overrides)
    return row


def delegacia_row(**overrides):
    row = {
        "id": 1,
        "nome": "1ª DP",
        "unidade_id": 1,
        "cidade_id": 1,
        "ativo": True,
        "created_at": NOW,
    }
    row.update(overrides)
    return row


def tipo_proc_row(**overrides):
    row = {"id": 1, "nome": "IPL", "ativo": True, "created_at": NOW}
    row.update(overrides)
    return row


def delegado_row(**overrides):
    row = {
        "id": 1,
        "nome": "Delegado Teste",
        "matricula": "12345-X",
        "delegacia_id": 1,
        "unidade_id": 1,
        "ativo": True,
        "created_at": NOW,
    }
    row.update(overrides)
    return row


def escrivao_row(**overrides):
    row = {
        "id": 1,
        "nome": "Escrivão Teste",
        "delegacia_id": 1,
        "unidade_id": 1,
        "ativo": True,
        "created_at": NOW,
    }
    row.update(overrides)
    return row


def agente_row(**overrides):
    row = {
        "id": 1,
        "nome": "Agente Teste",
        "matricula": "A-1001",
        "funcao_padrao": "Agente",
        "ativo": True,
        "created_at": NOW,
        "equipes_atuais_resumo": "EQ-01",
    }
    row.update(overrides)
    return row


def equipe_row(**overrides):
    row = {
        "id": 1,
        "numero": "01",
        "nome": "Equipe Alfa",
        "delegado_id": 1,
        "escrivao_id": 1,
        "ativo": True,
        "created_at": NOW,
        "delegado_nome": "Delegado Teste",
        "escrivao_nome": "Escrivão Teste",
    }
    row.update(overrides)
    return row


def processo_row(**overrides):
    row = {
        "numero": "0001234-56.2025.8.07.0001",
        "descricao": "Processo teste",
        "ativo": True,
        "created_at": NOW,
    }
    row.update(overrides)
    return row


def tipo_material_row(**overrides):
    row = {
        "id": 1,
        "nome": "Celular",
        "categoria_docx": "informatica",
        "tabela_documento": "informatica",
        "ativo": True,
        "created_at": NOW,
    }
    row.update(overrides)
    return row


def acba_detail_dict(**overrides):
    detail = {
        "id": 1,
        "processo_numero": "0001234-56.2025.8.07.0001",
        "protocolo_numero": "ACBA-001",
        "unidade_id": 1,
        "delegacia_id": 1,
        "cidade_id": 1,
        "data_lavratura": date(2026, 1, 15),
        "hora_lavratura": time(10, 0),
        "tipo_procedimento_id": 1,
        "procedimento_numero": "IPL-001",
        "fundamento_legal": "Mandado judicial válido",
        "endereco_busca": "SQN 100 Bloco A",
        "alvo_busca": "Residência do investigado",
        "nome_vara_criminal": "1ª Vara",
        "nome_juiz": "Dr. Juiz",
        "assinatura_responsavel": "Delegado Teste",
        "observacoes": "Observações do auto",
        "arrombamento_245_2": False,
        "arrombamento_245_2_obs": "",
        "forca_coisas_245_3": False,
        "forca_coisas_245_3_obs": "",
        "morador_ausente_245_4": False,
        "morador_ausente_245_4_obs": "",
        "morador_nome": "João Silva",
        "morador_cpf": "12345678901",
        "morador_rg": "1234567",
        "morador_filiacao": "Maria e José",
        "morador_telefone": "61999990000",
        "created_by_user_id": 1,
        "created_at": NOW,
        "updated_at": NOW,
        "pdf_gerado_at": None,
        "pdf_gerado_por_user_id": None,
        "unidade_nome": "DPC",
        "delegacia_nome": "1ª DP",
        "cidade_nome": "Brasília",
        "uf_sigla": "DF",
        "uf_nome": "Distrito Federal",
        "tipo_procedimento_nome": "IPL",
        "processo_descricao": "Operação teste",
        "equipe_id": 1,
        "equipe_numero": "01",
        "equipe_nome": "Equipe Alfa",
        "delegado_id": 1,
        "delegado_nome": "Delegado Teste",
        "delegado_matricula": "12345-X",
        "escrivao_id": 1,
        "escrivao_nome": "Escrivão Teste",
        "agentes_equipe": [
            {
                "id": 1,
                "nome": "Agente Teste",
                "matricula": "A-1001",
                "funcao_padrao": "Agente",
            }
        ],
        "testemunhas": [
            {
                "tipo": "geral",
                "nome": "Testemunha Um",
                "cpf": "11111111111",
                "rg": "111111",
                "filiacao": "Pai e Mãe",
                "endereco": "Rua A, 1",
                "cidade": "Brasília",
                "telefone": "61999990001",
            },
            {
                "tipo": "arrombamento",
                "nome": "Testemunha Arrombamento",
                "cpf": "22222222222",
                "rg": "222222",
                "filiacao": "Pai e Mãe",
                "endereco": "Rua B, 2",
                "arrombamento": {"observacoes": "Presenciou arrombamento"},
            },
        ],
        "materiais": [
            {
                "id": 1,
                "item_num": 1,
                "categoria_docx": "informatica",
                "descricao": "Notebook Dell",
                "localizacao": "Sala",
                "tipo_id": 1,
                "tipo_nome": "Notebook",
                "revisado": True,
                "informatica": {
                    "senha_tipo": "texto",
                    "senha_texto": "1234",
                },
            },
            {
                "id": 2,
                "item_num": 1,
                "categoria_docx": "geral",
                "descricao": "Documentos",
                "localizacao": "Gaveta",
                "tipo_id": 2,
                "tipo_nome": "Documento",
                "revisado": True,
            },
            {
                "id": 3,
                "item_num": 2,
                "categoria_docx": "informatica",
                "descricao": "Celular",
                "localizacao": "Mesa",
                "tipo_id": 3,
                "tipo_nome": "Celular",
                "revisado": True,
                "informatica": {
                    "senha_tipo": "padrao",
                    "senha_padrao_pontos": [1, 2, 5, 8],
                },
            },
        ],
        "materiais_pendentes_revisao": 0,
    }
    detail.update(overrides)
    return detail
