"""Serviço de descrição de material via Gemini Vision.

Premissas:
    * Imagens não são armazenadas; o backend recebe os bytes em memória,
      computa um hash agregado para cache/auditoria e descarta.
    * `GEMINI_API_KEY` é obrigatória — sem ela o serviço levanta RuntimeError
      (os routers convertem em 503).
    * O modelo é parametrizável via `GEMINI_MODEL` (default: gemini-2.0-flash).
    * O prompt é versionado (constante `PROMPT_VERSAO`). Mudou? Suba a versão.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable

from app.config import settings


PROMPT_VERSAO = "v1"

_PROMPT_BASE = """Você é um perito policial. Receberá uma ou mais imagens
de um item apreendido em uma operação de busca e apreensão. Descreva o item
de forma OBJETIVA e técnica para constar em auto circunstanciado (ACBA),
focando em ser o mais detalhado possível, seguindo o padrão:

  - tipo do bem,
  - marca e modelo (se visíveis),
  - cor predominante,
  - identificadores únicos visíveis (IMEI, número de série, placa, chassi, etc.),
  - estado de conservação aparente (ligado, danificado, lacrado, oxidado etc.). assim como onde está localizado detalhes referentes ao estado de conservação (no canto inferiror esquerdo, perto do gatilho, no parafuso de fixação, etc.).

Se uma informação não estiver clara na imagem, escreva "não identificado(a)".
Não invente dados. Não inclua opiniões. Não use marcadores nem emojis. Caso haja dúvidas, escreva "não identificado(a)".
"""


@dataclass
class GeminiResult:
    descricao: str
    modelo: str
    prompt_versao: str
    request_hash: str
    custo_tokens: int | None = None


def _hash_images(images: Iterable[bytes], extra: str = "") -> str:
    h = hashlib.sha256()
    h.update(PROMPT_VERSAO.encode("utf-8"))
    h.update(b"\x00")
    h.update(extra.encode("utf-8"))
    for img in images:
        h.update(b"\x01")
        h.update(hashlib.sha256(img).digest())
    return h.hexdigest()


def descrever_material(
    images: list[bytes],
    mime_types: list[str] | None = None,
    instrucoes_extra: str | None = None,
) -> GeminiResult:
    """Envia 1+ imagens ao Gemini Vision e retorna a descrição.

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
    request_hash = _hash_images(images, extra=(instrucoes_extra or ""))

    prompt = _PROMPT_BASE
    if instrucoes_extra:
        prompt = (
            f"{prompt}\nInstruções adicionais do operador: {instrucoes_extra.strip()}\n"
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

    resp = client.models.generate_content(model=modelo, contents=parts)
    descricao = (getattr(resp, "text", None) or "").strip()
    if not descricao:
        raise RuntimeError(
            f"Gemini retornou resposta vazia para o modelo '{modelo}'."
        )

    usage = getattr(resp, "usage_metadata", None)
    tokens = int(getattr(usage, "total_token_count", 0)) if usage else None

    return GeminiResult(
        descricao=descricao,
        modelo=modelo,
        prompt_versao=PROMPT_VERSAO,
        request_hash=request_hash,
        custo_tokens=tokens,
    )
