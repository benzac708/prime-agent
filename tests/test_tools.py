"""Tests for tool registry and tool implementations."""

from __future__ import annotations

from typing import Any

import pytest

from tools import ToolRegistry, check_health


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


@pytest.mark.asyncio
async def test_check_health_up(httpx_mock: Any) -> None:
    httpx_mock.add_response(url="https://example.com", status_code=200)
    result = await check_health("https://example.com")
    assert result["status"] == "up"
    assert result["status_code"] == 200
    assert "response_time_ms" in result
    assert result["url"] == "https://example.com"


@pytest.mark.asyncio
async def test_check_health_down(httpx_mock: Any) -> None:
    httpx_mock.add_response(url="https://example.com", status_code=500)
    result = await check_health("https://example.com")
    assert result["status"] == "down"
    assert result["status_code"] == 500


@pytest.mark.asyncio
async def test_check_health_timeout() -> None:
    result = await check_health("https://httpbin.org/delay/30", timeout=0.01)
    assert result["status"] == "down"
    assert result["error"] == "timeout"
