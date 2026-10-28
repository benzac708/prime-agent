# prime-agent

AI agent that monitors, diagnoses, and fixes infrastructure on a self-hosted VPS.
Built from scratch in Python with an OpenAI-compatible LLM loop, tool-calling via MCP,
and RAG over ops runbooks.

## Quick start

```bash
# Install from GitHub
pip install git+https://github.com/benzac708/prime-agent.git

# Configure
mkdir -p ~/.config/prime-agent
cat > ~/.config/prime-agent/.env << 'ENV_EOF'
LLM_API_KEY=gsk_your_groq_key_here
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
MAX_TOOL_CALLS=10
REQUEST_TIMEOUT=10.0
ENV_EOF

# Run
prime-agent "check if zachara.dev is up"
```

## Installation

### Prerequisites

- Python 3.10+
- pip
- Groq API key (free at https://console.groq.com)

### Install from GitHub (recommended)

```bash
pip install git+https://github.com/benzac708/prime-agent.git
```

This installs the `prime-agent` CLI command and the `mcp_server` module.

### Install from source (development)

```bash
git clone https://github.com/benzac708/prime-agent.git
cd prime-agent
pip install -e ".[dev]"
```

### Verify installation

```bash
prime-agent --help
# Usage: prime-agent <message>

# Test with a simple health check
LLM_API_KEY=gsk_... prime-agent "check if zachara.dev is up"
```

## Configuration

prime-agent reads configuration from environment variables. It checks (in order):

1. Environment variables (highest priority)
2. `.env` file in current directory (auto-loaded via python-dotenv)
3. `~/.config/prime-agent/.env` (user config)
4. Defaults (Groq free tier)

### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `LLM_API_KEY` | Yes | — | LLM provider API key (Groq, OpenAI, Azure, etc.) |
| `LLM_BASE_URL` | No | `https://api.groq.com/openai/v1` | OpenAI-compatible API base URL |
| `LLM_MODEL` | No | `llama-3.3-70b-versatile` | Model name |
| `MAX_TOOL_CALLS` | No | `10` | Max tool calls per agent run |
| `REQUEST_TIMEOUT` | No | `10.0` | HTTP request timeout (seconds) |

### Switching providers

No code changes needed — just env vars:

```bash
# Groq (free, fast) — default
LLM_API_KEY=gsk_...
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile

# Azure OpenAI (student credits)
LLM_API_KEY=<azure-key>
LLM_BASE_URL=https://<resource>.openai.azure.com/openai/deployments/<model>
LLM_MODEL=gpt-4o

# OpenAI
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

## Usage

### CLI

```bash
# Check a single app
prime-agent "check if zachara.dev is up"

# Check all apps
prime-agent "check all apps and report any that are down"

# Diagnose an issue
prime-agent "what is wrong with the jobs app?"

# System info
prime-agent "show disk and memory usage"

# List services
prime-agent "list running services"

# Get logs
prime-agent "show last 20 lines of jobs-app logs"

# Search ops docs
prime-agent "how do I restart the analytics app?"
```

### MCP server (stdio)

For Claude Desktop, Cursor, or opencode:

```bash
# Start MCP server (stdio mode)
python3 mcp_server.py
```

Add to your MCP client config (e.g., opencode.json):

```json
{
  "mcp": {
    "servers": {
      "prime-agent": {
        "type": "local",
        "command": ["python3", "mcp_server.py"]
      }
    }
  }
}
```

### MCP server (SSE / WebMCP)

For remote access:

```bash
python3 mcp_server.py --mode sse --port 8080
```

Connect via: `http://localhost:8080/sse`

## Architecture

```
+---------------------------------------------+
|  prime-agent (Python)                       |
|                                             |
|  +----------+  +----------+  +----------+   |
|  | LLM Loop |  | Tool     |  | RAG      |   |
|  | (OpenAI/ |  | Registry |  | (FTS5 +  |   |
|  |  Groq/   |  |          |  |  BM25)   |   |
|  |  Azure)  |  |          |  |          |   |
|  +----+-----+  +----+-----+  +----+-----+   |
|       |            |             |         |
|       +------------+-------------+         |
|                    |                       |
|  +-----------------+------------------+    |
|  |  MCP Server (stdio + SSE/WebMCP)   |    |
|  |  Tools: check_health, get_system,  |    |
|  |  list_services, restart_service,    |    |
|  |  get_logs, search_docs             |    |
|  +-----------------+------------------+    |
|                    |                       |
+--------------------+-----------------------+
                     |
+--------------------+-----------------------+
|  VPS (self-hosted)                          |
|  30+ apps, systemd, Docker, Prometheus      |
+---------------------------------------------+
```

## Tech stack

- **Language:** Python 3.10+
- **LLM:** OpenAI-compatible (Groq free / Azure OpenAI / any provider)
- **Agent:** Hand-rolled loop with tool-calling, approval gates, structured logging
- **MCP:** stdio + SSE (WebMCP) via @modelcontextprotocol/sdk
- **RAG:** FTS5 + BM25 over ops runbooks
- **CI/CD:** GitHub Actions (lint, test, security, build)
- **Testing:** pytest, property-based (Hegel), 80%+ coverage
- **Deploy:** pip install, systemd, Docker

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .
ruff format --check .

# Type check
mypy src/

# Security scan
bandit -r src/ -x tests/
```

## Deployment

### VPS (self-hosted, recommended)

```bash
# On the VPS:
pip install git+https://github.com/benzac708/prime-agent.git

# Configure
mkdir -p ~/.config/prime-agent
cat > ~/.config/prime-agent/.env << 'ENV_EOF'
LLM_API_KEY=gsk_your_groq_key_here
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
MAX_TOOL_CALLS=10
REQUEST_TIMEOUT=10.0
ENV_EOF

# Test
prime-agent "check if zachara.dev is up"

# Schedule daily (systemd timer)
# See: machines/vps/setup-prime-agent.sh in bzdotfiles
```

### Docker

```bash
docker build -t prime-agent .
docker run --rm --env-file .env prime-agent "check if zachara.dev is up"

# With host access (for monitoring)
docker run --rm --network host \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --env-file .env \
  prime-agent "check all apps"
```

### Azure (v2, using student credits)

```bash
# Switch to Azure OpenAI
export LLM_API_KEY=<azure-key>
export LLM_BASE_URL=https://<resource>.openai.azure.com/openai/deployments/gpt-4o
export LLM_MODEL=gpt-4o

# Deploy to Azure Container Apps
az containerapp create --name prime-agent --image ghcr.io/benzac708/prime-agent:latest
```

## Roadmap

- [x] Phase 0: Scaffold + CI + git hooks
- [x] Phase 1: Core agent loop + check_health tool
- [x] Phase 2: 5 tools + MCP server (stdio + SSE)
- [ ] Phase 3: RAG over ops docs
- [ ] Phase 4: Web dashboard + Prometheus
- [ ] Phase 5: CI/CD + security + backpressure
- [ ] Phase 6: Polish + deploy + flip public

## License

MIT
