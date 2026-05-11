"""Serviço de descrição + classificação de material via Gemini Vision.

Premissas:
    * Imagens não são armazenadas; o backend recebe os bytes em memória,
      computa um hash agregado para cache/auditoria e descarta.
    * `GEMINI_API_KEY` é obrigatória — sem ela o serviço levanta RuntimeError
      (os routers convertem em 503).
    * O modelo é parametrizável via `GEMINI_MODEL` (default: gemini-2.0-flash).
    * O prompt é versionado (constante `PROMPT_VERSAO`). Mudou? Suba a versão.

Quando o chamador passa `tipos_disponiveis` (catálogo do `tipos_material`),
a IA é instruída a devolver um JSON com `tipo_id` (escolhido entre os ids da
lista) e `descricao`. Senão, opera no modo legado (texto puro).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

from app.config import settings


PROMPT_VERSAO = "v2"

_PROMPT_DESCRICAO = """Descreva o item de forma OBJETIVA e técnica para constar
em auto circunstanciado (ACBA), focando em ser o mais detalhado possível,
seguindo o padrão:

  - tipo do bem,
  - marca e modelo (se visíveis),
  - cor predominante,
  - identificadores únicos visíveis (IMEI, número de série, placa, chassi, etc.),
  - estado de conservação aparente (ligado, danificado, lacrado, oxidado etc.) e
    onde estão os detalhes do estado (canto inferior esquerdo, perto do gatilho,
    no parafuso de fixação, etc.).

Se uma informação não estiver clara na imagem, escreva "não identificado(a)".
Não invente dados. Não inclua opiniões. Não use marcadores nem emojis.
"""

_PROMPT_BASE_TEXTO = (
    "Você é um perito policial. Receberá uma ou mais imagens de um item "
    "apreendido em uma operação de busca e apreensão. "
    + _PROMPT_DESCRICAO
)


@dataclass
class GeminiResult:
    descricao: str
    modelo: str
    prompt_versao: str
    request_hash: str
    custo_tokens: int | None = None
    tipo_id_sugerido: int | None = None
    tipo_nome_sugerido: str | None = None


def _hash_images(images: Iterable[bytes], extra: str = "") -> str:
    h = hashlib.sha256()
    h.update(PROMPT_VERSAO.encode("utf-8"))
    h.update(b"\x00")
    h.update(extra.encode("utf-8"))
    for img in images:
        h.update(b"\x01")
        h.update(hashlib.sha256(img).digest())
    return h.hexdigest()


def _tipos_to_extra(tipos: list[dict[str, Any]] | None) -> str:
    """Serializa o catálogo de tipos pro hash de cache (estável)."""
    if not tipos:
        return ""
    pairs = sorted((int(t["id"]), str(t.get("nome", ""))) for t in tipos)
    return "|".join(f"{i}:{n}" for i, n in pairs)


def _build_prompt_com_tipos(
    tipos: list[dict[str, Any]], instrucoes_extra: str | None
) -> str:
    linhas = [
        "Você é um perito policial. Receberá uma ou mais imagens de um item",
        "apreendido em uma operação de busca e apreensão.",
        "",
        "A partir das imagens, você deve:",
        "1) Escolher EXATAMENTE um tipo da lista abaixo (use o id correspondente).",
        "2) Descrever o item conforme o padrão do ACBA.",
        "",
        "LISTA DE TIPOS DISPONÍVEIS (escolha um id da lista; se nenhum tipo for",
        "claramente adequado, escolha o id do tipo 'Outros' caso exista, senão",
        "use o id que mais se aproxima):",
    ]
    for t in tipos:
        linhas.append(f"  - id={t['id']}: {t['nome']}")
    linhas.append("")
    linhas.append(_PROMPT_DESCRICAO)
    if instrucoes_extra:
        linhas.append("")
        linhas.append(
            f"Instruções adicionais do operador: {instrucoes_extra.strip()}"
        )
    linhas.append("")
    linhas.append(
        "Responda APENAS um JSON único no formato exato: "
        '{"tipo_id": <id inteiro da lista acima>, "descricao": "<texto>"}. '
        "Não inclua comentários, markdown nem texto fora do JSON."
    )
    return "\n".join(linhas)


def _parse_json_resposta(
    raw: str, tipos: list[dict[str, Any]]
) -> tuple[str, int | None, str | None]:
    """Lê o JSON devolvido pelo Gemini. Retorna (descricao, tipo_id, tipo_nome).

    Tolerante a respostas envolvidas em ```json ... ``` ou prefixadas.
    """
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        ini = text.index("{")
        fim = text.rindex("}") + 1
        payload = json.loads(text[ini:fim])
    except (ValueError, json.JSONDecodeError):
        return raw.strip(), None, None
    descricao = str(payload.get("descricao") or "").strip() or raw.strip()
    tipo_id_raw = payload.get("tipo_id")
    try:
        tipo_id = int(tipo_id_raw) if tipo_id_raw is not None else None
    except (TypeError, ValueError):
        tipo_id = None
    tipo_nome: str | None = None
    if tipo_id is not None:
        for t in tipos:
            if int(t["id"]) == tipo_id:
                tipo_nome = str(t.get("nome") or "")
                break
        else:
            tipo_id = None
    return descricao, tipo_id, tipo_nome


def descrever_material(
    images: list[bytes],
    mime_types: list[str] | None = None,
    instrucoes_extra: str | None = None,
    tipos_disponiveis: list[dict[str, Any]] | None = None,
) -> GeminiResult:
    """Envia 1+ imagens ao Gemini Vision e retorna descrição (e, se houver
    catálogo, classificação do tipo).

    Raises:
        ValueError: se `images` estiver vazio.
        RuntimeError: se a API key não estiver configurada, se o SDK do Gemini
            não estiver instalado, ou se o modelo retornar resposta vazia.
    """
    if not images:
        raise ValueError("Pelo menos uma imagem é necessária.")

    api_key = (settings.gemini_api_key or "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY não configurado. Defina a variável no .env do backend."
        )

    modelo = (settings.gemini_model or "").strip() or "gemini-2.0-flash"
    extra_hash = (instrucoes_extra or "") + "\n" + _tipos_to_extra(tipos_disponiveis)
    request_hash = _hash_images(images, extra=extra_hash)

    if tipos_disponiveis:
        prompt = _build_prompt_com_tipos(tipos_disponiveis, instrucoes_extra)
    else:
        prompt = _PROMPT_BASE_TEXTO
        if instrucoes_extra:
            prompt = (
                f"{prompt}\nInstruções adicionais do operador: "
                f"{instrucoes_extra.strip()}\n"
            )

    try:
        from google import genai  # type: ignore
        from google.genai import types as genai_types  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Pacote google-genai não instalado. "
            "Adicione 'google-genai' em requirements.txt e rebuilde a imagem."
        ) from exc

    client = genai.Client(api_key=api_key)
    mt = mime_types or ["image/jpeg"] * len(images)
    parts: list = [prompt]
    for blob, ct in zip(images, mt):
        parts.append(
            genai_types.Part.from_bytes(data=blob, mime_type=ct or "image/jpeg")
        )

    cfg = None
    if tipos_disponiveis:
        # Resposta estruturada em JSON. Modelos atuais aceitam o schema simples
        # abaixo; se o SDK reclamar (versão antiga), seguimos sem schema —
        # o parser de fallback (_parse_json_resposta) ainda extrai o JSON.
        try:
            cfg = genai_types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        except Exception:  # pragma: no cover
            cfg = None

    if cfg is not None:
        resp = client.models.generate_content(
            model=modelo, contents=parts, config=cfg
        )
    else:
        resp = client.models.generate_content(model=modelo, contents=parts)

    raw_text = (getattr(resp, "text", None) or "").strip()
    if not raw_text:
        raise RuntimeError(
            f"Gemini retornou resposta vazia para o modelo '{modelo}'."
        )

    if tipos_disponiveis:
        descricao, tipo_id, tipo_nome = _parse_json_resposta(
            raw_text, tipos_disponiveis
        )
    else:
        descricao, tipo_id, tipo_nome = raw_text, None, None

    usage = getattr(resp, "usage_metadata", None)
    tokens = int(getattr(usage, "total_token_count", 0)) if usage else None

    return GeminiResult(
        descricao=descricao,
        modelo=modelo,
        prompt_versao=PROMPT_VERSAO,
        request_hash=request_hash,
        custo_tokens=tokens,
        tipo_id_sugerido=tipo_id,
        tipo_nome_sugerido=tipo_nome,
    )
