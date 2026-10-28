"""Tests for tool registry."""

from __future__ import annotations

import pytest

from src.tools import ToolRegistry


@pytest.mark.asyncio
async def test_register_and_call() -> None:
    registry = ToolRegistry()

    async def echo(msg: str) -> dict:
        return {"echo": msg}

    registry.register("echo", {"description": "Echo a message", "parameters": {}}, echo)
    assert "echo" in registry.names
    result = await registry.call("echo", {"msg": "hello"})
    assert result == {"echo": "hello"}


@pytest.mark.asyncio
async def test_unknown_tool() -> None:
    registry = ToolRegistry()
    result = await registry.call("nonexistent", {})
    assert "error" in result
    assert "unknown tool" in result["error"]


def test_schemas() -> None:
    registry = ToolRegistry()

    async def noop() -> dict:
        return {}

    registry.register("noop", {"description": "No-op", "parameters": {}}, noop)
    assert len(registry.schemas) == 1
    assert registry.schemas[0]["type"] == "function"
    assert registry.schemas[0]["function"]["name"] == "noop"
