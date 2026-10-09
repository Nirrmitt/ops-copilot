"""Tool argument validation and action confirmation tests."""
import asyncio

import pytest
from pydantic import ValidationError

from app.schemas import Plan, RagArguments
from app.tools.ticket import create_ticket


def test_plan_rejects_unknown_tool() -> None:
    with pytest.raises(ValidationError):
        Plan.model_validate({"calls": [{"tool": "shell", "arguments": {}}]})


def test_tool_arguments_reject_empty_query() -> None:
    with pytest.raises(ValidationError):
        RagArguments.model_validate({"query": ""})


def test_ticket_does_not_fire_without_confirmation() -> None:
    result = asyncio.run(create_ticket("Need help", False))
    assert result["created"] is False
