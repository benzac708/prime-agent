# prime-agent

AI agent that monitors, diagnoses, and fixes infrastructure on a self-hosted VPS.
Built from scratch in Python with an OpenAI-compatible LLM loop, tool-calling via MCP,
and RAG over ops runbooks.

## Quick start

```bash
# Install
pip install -e .

# Configure
cp .env.example .env
# Edit .env with your LLM API key (Groq is free: https://console.groq.com)

# Run
prime-agent "check if zachara.dev is up"
```

## Architecture

```
┌─────────────────────────────────────────────┐
│  prime-agent (Python)                       │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ LLM Loop │  │ Tool     │  │ RAG      │  │
│  │ (OpenAI/ │  │ Registry │  │ (FTS5 +  │  │
│  │  Groq/   │  │          │  │  BM25)   │  │
│  │  Azure)  │  │          │  │          │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │             │             │         │
│       └─────────────┼─────────────┘         │
│                     │                       │
│  ┌──────────────────┴──────────────────┐   │
│  │  MCP Server (stdio + SSE/WebMCP)    │   │
│  │  Tools: check_health, get_system,   │   │
│  │  list_services, restart_service,     │   │
│  │  get_logs, search_docs              │   │
│  └──────────────────┬──────────────────┘   │
│                     │                       │
└─────────────────────┼───────────────────────┘
                      │
┌─────────────────────┴───────────────────────┐
│  VPS (self-hosted)                           │
│  30+ apps, systemd, Docker, Prometheus       │
└─────────────────────────────────────────────┘
```

## Tech stack

- **Language:** Python 3.10+
- **LLM:** OpenAI-compatible (Groq free / Azure OpenAI / any provider)
- **Agent:** Hand-rolled loop with tool-calling, approval gates, structured logging
- **MCP:** stdio + SSE (WebMCP) via @modelcontextprotocol/sdk
- **RAG:** FTS5 + BM25 over ops runbooks
- **CI/CD:** GitHub Actions (lint, test, security, build)
- **Testing:** pytest, property-based (Hegel), 80%+ coverage
- **Deploy:** Docker + systemd + Cloudflare tunnel

## Development

```bash
# Install dev dependencies
uv sync --extra dev

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

### VPS (self-hosted)

```bash
# On the VPS:
git clone https://github.com/benzac708/bzdotfiles.git
cd bzdotfiles
bash machines/vps/setup-prime-agent.sh
```

This sets up:
- Python 3.12 + virtualenv + dependencies
- systemd service (daily health check at 08:00)
- Optional MCP SSE server behind Caddy + Cloudflare
- .env file (prompts for API key)

### Local dev

```bash
git clone https://github.com/benzac708/prime-agent.git
cd prime-agent
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with your Groq API key
prime-agent "check if zachara.dev is up"
```

### Docker

```bash
docker build -t prime-agent .
docker run --rm --env-file .env prime-agent "check if zachara.dev is up"
```

## Roadmap

- [x] Phase 0: Scaffold + CI + git hooks
- [ ] Phase 1: Core agent loop + 1 tool
- [ ] Phase 2: 5 tools + MCP server (stdio + SSE)
- [ ] Phase 3: RAG over ops docs
- [ ] Phase 4: Web dashboard + Prometheus
- [ ] Phase 5: CI/CD + security + backpressure
- [ ] Phase 6: Polish + deploy + flip public

## License

MIT
