# CareerPilot API

See the [project README](../README.md) for setup, environment, migration, authentication, and verification commands.

Auth endpoints are under `/api/v1/auth`; JWT-owned career data endpoints are under `/api/v1/me`. Repositories perform database access, services enforce ownership/business rules, and application exceptions are mapped centrally.

## MCP foundation

CareerPilot exposes one read-only MCP server using MCP 1.29's stateless Streamable HTTP transport. Start it separately from FastAPI:

```bash
cd career-pilot-backend
.venv/bin/python -m app.mcp.server
```

The endpoint is `http://127.0.0.1:8001/mcp`. A caller creates a request-scoped MCP client with the current CareerPilot access token via `build_mcp_client(access_token)`. FastMCP validates that bearer JWT, places its subject in authenticated MCP request context, and every tool re-resolves that subject to an active user in a fresh database session. Tools then call existing user-scoped services; model-generated arguments never contain ownership identity.

The initial tools are read-only: `get_my_profile`, `get_my_skills`, `get_my_experience`, `get_my_education`, `get_my_projects`, `search_my_career_knowledge`, `list_my_resumes`, and `get_my_resume`. Human approval remains outside MCP and no existing Agent uses MCP yet.

Run the focused foundation tests with:

```bash
.venv/bin/pytest -q tests/test_mcp_foundation.py
```
