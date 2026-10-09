"""Validated request and planner data models."""
from typing import Literal

from pydantic import BaseModel, Field

ToolName = Literal["rag_search", "sql_query", "create_ticket"]


class ToolCall(BaseModel):
    """One validated operation proposed by the planner."""
    tool: ToolName
    arguments: dict[str, object] = Field(default_factory=dict)


class RagArguments(BaseModel):
    """Arguments accepted by policy search."""
    query: str = Field(min_length=1, max_length=1000)


class SqlArguments(BaseModel):
    """Arguments accepted by read-only SQL."""
    sql: str = Field(min_length=1, max_length=4000)


class TicketArguments(BaseModel):
    """Arguments accepted by the ticket action."""
    summary: str = Field(min_length=1, max_length=1000)
    confirm: bool = False


class Plan(BaseModel):
    """A bounded sequence of tool calls, or a refusal."""
    calls: list[ToolCall] = Field(default_factory=list, max_length=6)
    refusal: str | None = None


class AskRequest(BaseModel):
    """Question sent to the assistant."""
    question: str = Field(min_length=1, max_length=2000)
    confirm: bool = False


class ToolResult(BaseModel):
    """Auditable output from a single tool."""
    tool: str
    arguments: dict[str, object]
    output: object
    ok: bool = True
