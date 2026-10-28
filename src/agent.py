"""Agent entry point and loop."""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from config import Config
from llm import LLMClient
from tools import ToolRegistry
from tools import register_tools as _register_tools


async def run_agent(message: str) -> str:
    config = Config.from_env()
    llm = LLMClient(config)
    registry = ToolRegistry()
    _register_tools(registry, config.request_timeout)

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": "You are an infrastructure monitoring agent. "
            "You can check system health, list services, restart services, "
            "read logs, and search ops documentation. "
            "Diagnose issues and suggest fixes. Be concise.",
        },
        {"role": "user", "content": message},
    ]

    for _ in range(config.max_tool_calls):
        response = await llm.chat(messages, tools=registry.schemas or None)
        choice: dict[str, Any] = response["choices"][0]["message"]

        tool_calls = choice.get("tool_calls")
        if tool_calls:
            messages.append(choice)
            for tc in tool_calls:
                fn_name = str(tc["function"]["name"])
                fn_args: dict[str, Any] = json.loads(tc["function"]["arguments"])
                result = await registry.call(fn_name, fn_args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": str(tc["id"]),
                        "content": json.dumps(result),
                    }
                )
        else:
            await llm.close()
            return str(choice.get("content", ""))

    await llm.close()
    return "Max tool calls reached."


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: prime-agent <message>")
        sys.exit(1)
    result = asyncio.run(run_agent(" ".join(sys.argv[1:])))
    print(result)


if __name__ == "__main__":
    main()
