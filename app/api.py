"""FastAPI service for asking operations questions."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.graph import agent
from app.schemas import AskRequest

app = FastAPI(title="ops-copilot")


class Health(BaseModel):
    status: str


@app.get("/health", response_model=Health)
async def health() -> Health:
    return Health(status="ok")


@app.post("/ask")
async def ask(request: AskRequest) -> dict[str, object]:
    try:
        result = await agent.ainvoke({"question": request.question, "confirm": request.confirm})
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Assistant service unavailable") from exc
    if any(not item.ok for item in result.get("tool_results", [])):
        raise HTTPException(status_code=503, detail="A data tool failed; retry or contact support")
    plan = result.get("plan")
    return {"answer": result.get("answer", ""), "plan": plan.model_dump() if plan else {},
            "tool_calls": [item.model_dump() for item in result.get("tool_results", [])],
            "sources": result.get("sources", []), "confidence": result.get("confidence", 0.0),
            "handed_off": result.get("handed_off", False)}


@app.post("/mock-tickets")
async def mock_ticket(payload: dict[str, str]) -> dict[str, object]:
    """Local webhook target used only when ticket actions are explicitly enabled."""
    summary = payload.get("summary", "").strip()
    if not summary:
        raise HTTPException(status_code=422, detail="Ticket summary is required")
    return {"created": True, "ticket_id": "MOCK-001", "summary": summary}
