"""Tool registry and implementations for the agent."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

ToolFn = Callable[..., Awaitable[dict[str, Any]]]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolFn] = {}
        self._schemas: list[dict[str, Any]] = []

    def register(self, name: str, schema: dict[str, Any], fn: ToolFn) -> None:
        self._tools[name] = fn
        self._schemas.append({"type": "function", "function": {"name": name, **schema}})

    async def call(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name not in self._tools:
            return {"error": f"unknown tool: {name}"}
        fn = self._tools[name]
        result: dict[str, Any] = await fn(**args)
        return result

    @property
    def schemas(self) -> list[dict[str, Any]]:
        return self._schemas

    @property
    def names(self) -> list[str]:
        return list(self._tools.keys())


async def check_health(url: str, timeout: float = 10.0) -> dict[str, Any]:
    """Check if a URL is reachable and return status + response time."""
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, follow_redirects=True)
        elapsed = round((time.monotonic() - start) * 1000)
        return {
            "status": "up" if resp.status_code < 400 else "down",
            "status_code": resp.status_code,
            "response_time_ms": elapsed,
            "url": url,
        }
    except httpx.TimeoutException:
        elapsed = round((time.monotonic() - start) * 1000)
        return {
            "status": "down",
            "status_code": None,
            "response_time_ms": elapsed,
            "url": url,
            "error": "timeout",
        }
    except httpx.HTTPError as exc:
        elapsed = round((time.monotonic() - start) * 1000)
        return {
            "status": "down",
            "status_code": None,
            "response_time_ms": elapsed,
            "url": url,
            "error": str(exc),
        }


def register_tools(registry: ToolRegistry, timeout: float = 10.0) -> None:
    """Register all available tools."""
    registry.register(
        "check_health",
        {
            "description": "Check if a URL is reachable and return "
            "its HTTP status and response time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to check"},
                },
                "required": ["url"],
            },
        },
        lambda url: check_health(url, timeout),
    )
