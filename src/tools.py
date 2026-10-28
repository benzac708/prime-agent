"""Tool registry for the agent."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

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
