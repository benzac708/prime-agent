"""Integration tests for the agent loop."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from agent import run_agent


@pytest.mark.asyncio
async def test_agent_returns_llm_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    mock_response = {
        "choices": [{"message": {"role": "assistant", "content": "All systems up."}}],
    }
    with patch("agent.LLMClient") as mock_llm:
        instance = mock_llm.return_value
        instance.chat = AsyncMock(return_value=mock_response)
        instance.close = AsyncMock()
        result = await run_agent("check health")
        assert result == "All systems up."
        instance.chat.assert_called_once()


@pytest.mark.asyncio
async def test_agent_calls_tool_then_responds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    tool_call_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "check_health",
                                "arguments": '{"url": "https://example.com"}',
                            },
                        }
                    ],
                }
            }
        ],
    }
    final_response = {
        "choices": [{"message": {"role": "assistant", "content": "example.com is up (200 OK)."}}],
    }
    with patch("agent.LLMClient") as mock_llm:
        instance = mock_llm.return_value
        instance.chat = AsyncMock(side_effect=[tool_call_response, final_response])
        instance.close = AsyncMock()
        with patch("tools.check_health", new_callable=AsyncMock) as mock_health:
            mock_health.return_value = {
                "status": "up",
                "status_code": 200,
                "response_time_ms": 42,
                "url": "https://example.com",
            }
            result = await run_agent("check example.com")
            assert result == "example.com is up (200 OK)."
            assert instance.chat.call_count == 2
            mock_health.assert_called_once_with("https://example.com", 10.0)


@pytest.mark.asyncio
async def test_agent_handles_unknown_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    tool_call_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "nonexistent_tool", "arguments": "{}"},
                        }
                    ],
                }
            }
        ],
    }
    final_response = {
        "choices": [
            {"message": {"role": "assistant", "content": "Sorry, that tool doesn't exist."}}
        ],
    }
    with patch("agent.LLMClient") as mock_llm:
        instance = mock_llm.return_value
        instance.chat = AsyncMock(side_effect=[tool_call_response, final_response])
        instance.close = AsyncMock()
        result = await run_agent("do something")
        assert result == "Sorry, that tool doesn't exist."
