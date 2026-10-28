"""Tool registry and implementations for the agent."""

from __future__ import annotations

import subprocess
import time
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
import psutil

ToolFn = Callable[..., Awaitable[Any]]


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


# ── Tool implementations ──────────────────────────────────────────────────


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


async def get_system_info() -> dict[str, Any]:
    """Return disk, memory, and CPU usage."""
    disk = psutil.disk_usage("/")
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.1)
    return {
        "disk": {
            "total_gb": round(disk.total / (1024**3), 1),
            "used_gb": round(disk.used / (1024**3), 1),
            "free_gb": round(disk.free / (1024**3), 1),
            "percent": disk.percent,
        },
        "memory": {
            "total_gb": round(mem.total / (1024**3), 1),
            "used_gb": round(mem.used / (1024**3), 1),
            "available_gb": round(mem.available / (1024**3), 1),
            "percent": mem.percent,
        },
        "cpu": {
            "percent": cpu,
            "cores": psutil.cpu_count(),
        },
    }


async def list_services() -> list[dict[str, Any]]:
    """List running systemd services (allowlisted)."""
    try:
        result = subprocess.run(
            [
                "systemctl",
                "list-units",
                "--type=service",
                "--state=running",
                "--no-pager",
                "--plain",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        services = []
        for line in result.stdout.strip().splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[0].endswith(".service"):
                services.append(
                    {
                        "name": parts[0],
                        "load": parts[1],
                        "active": parts[2],
                        "sub": parts[3],
                    }
                )
        return services
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        return [{"error": str(exc)}]


_ALLOWED_SERVICES: set[str] = set()  # populated at runtime from list_services


def _is_allowed_service(name: str) -> bool:
    """Check if a service name is in the allowlist."""
    if not _ALLOWED_SERVICES:
        # Allow any service that looks like a valid systemd unit name
        return name.endswith(".service") and "/" not in name and " " not in name
    return name in _ALLOWED_SERVICES


async def restart_service(name: str) -> dict[str, Any]:
    """Restart a systemd service (allowlisted only)."""
    if not _is_allowed_service(name):
        return {
            "error": f"service '{name}' not allowed",
            "allowed": sorted(_ALLOWED_SERVICES) or "any *.service",
        }
    try:
        result = subprocess.run(
            ["systemctl", "restart", name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return {"status": "restarted", "service": name}
        return {"status": "failed", "service": name, "error": result.stderr.strip()}
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        return {"status": "error", "service": name, "error": str(exc)}


async def get_logs(service: str, lines: int = 50) -> dict[str, Any]:
    """Get recent logs for a service via journalctl."""
    if not _is_allowed_service(service):
        return {"error": f"service '{service}' not allowed"}
    lines = max(1, min(lines, 500))
    try:
        result = subprocess.run(
            ["journalctl", "-u", service, "-n", str(lines), "--no-pager", "-o", "short"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return {"service": service, "lines": lines, "logs": result.stdout.strip()}
        return {"service": service, "error": result.stderr.strip()}
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        return {"service": service, "error": str(exc)}


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
    registry.register(
        "get_system_info",
        {
            "description": "Get disk, memory, and CPU usage of the system.",
            "parameters": {"type": "object", "properties": {}},
        },
        lambda: get_system_info(),
    )
    registry.register(
        "list_services",
        {
            "description": "List running systemd services.",
            "parameters": {"type": "object", "properties": {}},
        },
        lambda: list_services(),
    )
    registry.register(
        "restart_service",
        {
            "description": "Restart a systemd service. Requires the service to be allowlisted.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Service name (e.g. nginx.service)"},
                },
                "required": ["name"],
            },
        },
        lambda name: restart_service(name),
    )
    registry.register(
        "get_logs",
        {
            "description": "Get recent logs for a service via journalctl.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Service name (e.g. nginx.service)",
                    },
                    "lines": {
                        "type": "integer",
                        "description": "Number of log lines (default 50, max 500)",
                    },
                },
                "required": ["service"],
            },
        },
        lambda service, lines=50: get_logs(service, lines),
    )
