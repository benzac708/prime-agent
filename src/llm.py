"""OpenAI-compatible LLM client."""

from __future__ import annotations

from typing import Any

import httpx


class LLMClient:
    def __init__(self, config: Any) -> None:
        self.config = config
        self._client = httpx.AsyncClient(
            base_url=config.llm_base_url,
            headers={"Authorization": f"Bearer {config.llm_api_key}"},
            timeout=config.request_timeout,
        )

    async def chat(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.config.llm_model,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        resp = await self._client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        result: dict[str, Any] = resp.json()
        return result

    async def close(self) -> None:
        await self._client.aclose()
