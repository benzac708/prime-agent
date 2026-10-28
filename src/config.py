"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _clean(value: str) -> str:
    """Strip whitespace and inline comments from env values."""
    if "#" in value:
        value = value.split("#", 1)[0]
    return value.strip()


@dataclass
class Config:
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    max_tool_calls: int
    request_timeout: float

    @classmethod
    def from_env(cls) -> Config:
        api_key = _clean(os.getenv("LLM_API_KEY", ""))
        if not api_key:
            raise ValueError("LLM_API_KEY is required")
        return cls(
            llm_api_key=api_key,
            llm_base_url=_clean(os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")),
            llm_model=_clean(os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")),
            max_tool_calls=int(_clean(os.getenv("MAX_TOOL_CALLS", "10"))),
            request_timeout=float(_clean(os.getenv("REQUEST_TIMEOUT", "10.0"))),
        )
