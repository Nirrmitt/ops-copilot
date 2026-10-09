"""LangGraph state shared between nodes."""
from typing import TypedDict

from app.schemas import Plan, ToolResult


class AgentState(TypedDict, total=False):
    question: str
    confirm: bool
    plan: Plan
    tool_results: list[ToolResult]
    answer: str
    sources: list[str]
    confidence: float
    handed_off: bool
    retry_count: int
    retry_requested: bool
    tool_steps: int
