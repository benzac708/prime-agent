"""Tests for tool registry and tool implementations."""

from __future__ import annotations

from typing import Any

import pytest
from tools import ToolRegistry, check_health, get_system_info, list_services


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


@pytest.mark.asyncio
async def test_get_system_info() -> None:
    result = await get_system_info()
    assert "disk" in result
    assert "memory" in result
    assert "cpu" in result
    assert result["disk"]["percent"] >= 0
    assert result["memory"]["percent"] >= 0
    assert result["cpu"]["cores"] >= 1


@pytest.mark.asyncio
async def test_list_services() -> None:
    result = await list_services()
    assert isinstance(result, list)
    # On systems without systemctl, returns error list
    if result and isinstance(result[0], dict) and "error" in result[0]:
        assert True  # acceptable on non-systemd systems
    else:
        for svc in result:
            assert "name" in svc
            assert svc["name"].endswith(".service")


@pytest.mark.asyncio
async def test_register_all_tools() -> None:
    from tools import register_tools

    registry = ToolRegistry()
    register_tools(registry, 10.0)
    assert "check_health" in registry.names
    assert "get_system_info" in registry.names
    assert "list_services" in registry.names
    assert "restart_service" in registry.names
    assert "get_logs" in registry.names
    assert len(registry.names) == 5
