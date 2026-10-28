"""Tests for config loading."""

from __future__ import annotations

import pytest

from config import Config


def test_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    config = Config.from_env()
    assert config.llm_api_key == "test-key"
    assert config.llm_base_url == "https://example.com/v1"
    assert config.llm_model == "test-model"
    assert config.max_tool_calls == 10
    assert config.request_timeout == 10.0


def test_config_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    config = Config.from_env()
    assert config.llm_base_url == "https://api.groq.com/openai/v1"
    assert config.llm_model == "llama-3.3-70b-versatile"


def test_config_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(ValueError, match="LLM_API_KEY is required"):
        Config.from_env()
