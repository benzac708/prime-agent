#!/usr/bin/env python3
"""MCP server for prime-agent — exposes tools via stdio and SSE."""

from __future__ import annotations

import argparse
import asyncio
import json

from mcp.server.mcpserver import MCPServer

from src.config import Config
from src.tools import (
    ToolRegistry,
    register_tools,
)

server = MCPServer("prime-agent")


def _build_registry() -> ToolRegistry:
    config = Config.from_env()
    registry = ToolRegistry()
    register_tools(registry, config.request_timeout)
    return registry


@server.tool()
async def check_health(url: str) -> str:
    """Check if a URL is reachable and return its HTTP status and response time."""
    registry = _build_registry()
    result = await registry.call("check_health", {"url": url})
    return json.dumps(result, indent=2)


@server.tool()
async def get_system_info() -> str:
    """Get disk, memory, and CPU usage of the system."""
    registry = _build_registry()
    result = await registry.call("get_system_info", {})
    return json.dumps(result, indent=2)


@server.tool()
async def list_services() -> str:
    """List running systemd services."""
    registry = _build_registry()
    result = await registry.call("list_services", {})
    return json.dumps(result, indent=2)


@server.tool()
async def restart_service(name: str) -> str:
    """Restart a systemd service. Requires the service to be allowlisted."""
    registry = _build_registry()
    result = await registry.call("restart_service", {"name": name})
    return json.dumps(result, indent=2)


@server.tool()
async def get_logs(service: str, lines: int = 50) -> str:
    """Get recent logs for a service via journalctl."""
    registry = _build_registry()
    result = await registry.call("get_logs", {"service": service, "lines": lines})
    return json.dumps(result, indent=2)


async def run_stdio() -> None:
    await server.run_stdio_async()


async def run_sse(host: str = "0.0.0.0", port: int = 8080) -> None:
    import uvicorn

    app = server.streamable_http_app()
    uvicorn.run(app, host=host, port=port)


def main() -> None:
    parser = argparse.ArgumentParser(description="prime-agent MCP server")
    parser.add_argument("--mode", choices=["stdio", "sse"], default="stdio")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    if args.mode == "sse":
        asyncio.run(run_sse(args.host, args.port))
    else:
        asyncio.run(run_stdio())


if __name__ == "__main__":
    main()
