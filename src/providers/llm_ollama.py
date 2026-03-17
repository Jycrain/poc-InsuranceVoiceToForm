"""
Provider LLM — Ollama (Mistral / Llama via API locale).

Communique avec le serveur Ollama via son API HTTP REST.
Aucune dépendance Python supplémentaire : utilise httpx.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from src.core.interfaces import LLMProviderInterface

logger = logging.getLogger(__name__)

_DEFAULT_HOST = "http://localhost:11434"
_DEFAULT_MODEL = "mistral"
_TIMEOUT_SECONDS = 120


class OllamaLLMProvider(LLMProviderInterface):
    """
    Fournisseur LLM via Ollama (API locale).

    Args:
        model: identifiant du modèle Ollama (ex: "mistral", "mistral-nemo").
        host: URL du serveur Ollama.
        timeout: timeout en secondes pour l'appel HTTP.
    """

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        host: str = _DEFAULT_HOST,
        timeout: int = _TIMEOUT_SECONDS,
    ) -> None:
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout

    async def complete_json(
        self,
        system_prompt: str,
        user_message: str,
    ) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0,
                "num_predict": 1024,
                "num_ctx": 8192,
            },
        }

        url = f"{self.host}/api/chat"
        logger.debug("Ollama request → %s (model=%s)", url, self.model)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

        body = response.json()
        content = body.get("message", {}).get("content", "{}")

        try:
            parsed = json.loads(content)
            logger.info("Ollama JSON brut : %s", json.dumps(parsed, ensure_ascii=False))
            return parsed
        except json.JSONDecodeError:
            logger.warning("Ollama a retourné du JSON invalide : %s", content[:500])
            return {}

    async def is_available(self) -> bool:
        """Vérifie si le serveur Ollama est joignable."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{self.host}/api/tags")
                return r.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False
