"""Tests for MCP server."""

from __future__ import annotations

import json

import pytest


@pytest.mark.asyncio
async def test_mcp_lists_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    from mcp_server import server

    tools = await server.list_tools()
    names = [t.name for t in tools]
    assert "check_health" in names
    assert "get_system_info" in names
    assert "list_services" in names
    assert "restart_service" in names
    assert "get_logs" in names
    assert len(names) == 5


@pytest.mark.asyncio
async def test_mcp_call_get_system_info(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    from mcp_server import server

    result = await server.call_tool("get_system_info", {})
    assert result is not None
    text = result.content[0].text if hasattr(result, "content") else str(result)
    data = json.loads(text)
    assert "disk" in data
    assert "memory" in data
    assert "cpu" in data
