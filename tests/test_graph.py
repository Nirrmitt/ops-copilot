"""Graph tests require no API key."""
import asyncio

from app.graph import agent


def test_mock_graph_refuses_out_of_scope() -> None:
    result = asyncio.run(agent.ainvoke({"question": "What is the capital of France?", "confirm": False}))
    assert result["plan"].refusal
    assert result["handed_off"] is False
