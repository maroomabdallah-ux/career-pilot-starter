from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def system_status():
    return {"api": "ready", "langgraph": "starter-ready", "mcp": "starter-ready"}
