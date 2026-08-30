# Backend Architecture

```text
React Frontend
      |
      v
FastAPI API
      |
      +--> Services --------> Repositories --------> PostgreSQL
      |
      +--> LangGraph Orchestrator
                |
                +--> Specialized Agents
                +--> Local Tools
                +--> MCP Client
                         |
                         +--> MCP Servers
                                  |
                                  +--> Job Sources / External Services
```

- `api/`: HTTP endpoints only
- `services/`: business logic
- `repositories/`: database access
- `models/`: SQLAlchemy models
- `schemas/`: Pydantic schemas
- `agents/`: specialized AI agents
- `graphs/`: LangGraph orchestration
- `mcp/`: MCP clients and servers
- `tools/`: local tools
- `integrations/`: external APIs/providers
- `core/`: settings/security/shared infrastructure
- `db/`: database engine/session/base

Keep MCP inside this repository for now. Split it later only if independent deployment or reuse becomes necessary.
