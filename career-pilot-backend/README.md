# CareerPilot AI Backend

Python + FastAPI + LangGraph + MCP starter.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose -f docker-compose.dev.yml up -d
uvicorn app.main:app --reload --port 8000
```

MCP starter:
```bash
python -m app.mcp.servers.core_server
```

API docs: http://localhost:8000/docs
