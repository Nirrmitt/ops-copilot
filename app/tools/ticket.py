"""Explicitly confirmed mock ticket action."""
import os

import httpx


async def create_ticket(summary: str, confirm: bool) -> dict[str, object]:
    """Post to the configured endpoint only after confirmation and opt-in."""
    if not confirm:
        return {"created": False, "message": "Please confirm before I create this ticket."}
    if os.getenv("ALLOW_TICKET_ACTIONS", "false").lower() != "true":
        return {"created": False, "message": "Ticket actions are disabled by configuration."}
    endpoint = os.getenv("TICKET_WEBHOOK_URL", "http://localhost:8000/mock-tickets")
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.post(endpoint, json={"summary": summary})
        response.raise_for_status()
        return response.json()
