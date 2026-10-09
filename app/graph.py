"""LangGraph orchestration for plan, tools, synthesis, and verification."""
import asyncio

from langgraph.graph import END, StateGraph

from app.llm import Planner
from app.schemas import Plan, RagArguments, SqlArguments, TicketArguments, ToolResult
from app.state import AgentState
from app.tools.rag import rag_search
from app.tools.sql import sql_query
from app.tools.ticket import create_ticket

planner = Planner()


async def plan_node(state: AgentState) -> AgentState:
    question = state["question"]
    if state.get("retry_count", 0):
        question += " Find direct supporting evidence and refine the search."
    plan = await planner.plan(question, state.get("confirm", False))
    return {"plan": plan, "tool_results": [], "retry_count": state.get("retry_count", 0),
            "retry_requested": False, "tool_steps": state.get("tool_steps", 0)}


async def tools_node(state: AgentState) -> AgentState:
    """Run the bounded plan; validate required arguments at this boundary."""
    results: list[ToolResult] = []
    used_steps = state.get("tool_steps", 0)
    available_steps = max(0, 6 - used_steps)
    for call in state["plan"].calls[:available_steps]:
        used_steps += 1
        try:
            args = call.arguments
            if call.tool == "rag_search":
                parsed = RagArguments.model_validate(args)
                output = await asyncio.wait_for(asyncio.to_thread(rag_search, parsed.query), timeout=10)
            elif call.tool == "sql_query":
                parsed = SqlArguments.model_validate(args)
                output = await asyncio.wait_for(asyncio.to_thread(sql_query, parsed.sql), timeout=5)
            else:
                parsed = TicketArguments.model_validate(args)
                output = await asyncio.wait_for(create_ticket(parsed.summary, parsed.confirm), timeout=6)
            results.append(ToolResult(tool=call.tool, arguments=args, output=output))
        except Exception as exc:  # noqa: BLE001 - tool failures become auditable handoffs.
            results.append(ToolResult(tool=call.tool, arguments=call.arguments, output={"error": str(exc)}, ok=False))
            break
    return {"tool_results": results, "tool_steps": used_steps}


def synthesize_node(state: AgentState) -> AgentState:
    """Build an answer only from observed tool output."""
    if state["plan"].refusal:
        return {"answer": state["plan"].refusal, "sources": [], "confidence": 1.0, "handed_off": False}
    results = state.get("tool_results", [])
    failed = [item for item in results if not item.ok]
    if failed:
        return {"answer": "I could not safely complete the request. A human should review it.",
                "sources": [], "confidence": 0.2, "handed_off": True}
    citations: list[str] = []
    findings: list[str] = []
    for item in results:
        if item.tool == "rag_search":
            for passage in item.output:
                citations.append(f"{passage['source']}#{passage['chunk_id']}")
                findings.append(str(passage["text"]))
        elif item.tool == "sql_query":
            citations.append(f"SQL: {item.output['sql']}")
            findings.append(f"Query returned {len(item.output['rows'])} row(s): {item.output['rows']}")
        else:
            findings.append(str(item.output.get("message", item.output)))
            if item.output.get("created") is False and "confirm" in str(item.output.get("message", "")).lower():
                return {"answer": str(item.output["message"]), "sources": [], "confidence": 1.0,
                        "handed_off": False}
    answer = "\n\n".join(findings) if findings else "No supporting findings were returned; a human should review this request."
    return {"answer": answer, "sources": citations, "confidence": 0.75 if findings else 0.1,
            "handed_off": not bool(findings)}


def verify_node(state: AgentState) -> AgentState:
    """Check that each displayed policy claim came from tool output."""
    results = state.get("tool_results", [])
    # The current synthesizer only formats raw results; it does not add generated claims.
    if any(not item.ok for item in results):
        return {"handed_off": True, "confidence": 0.1,
                "answer": "A tool failed, so a human should review the partial findings."}
    has_action = any(item.tool == "create_ticket" for item in results)
    if results and not state.get("sources") and not has_action and not state.get("plan", Plan()).refusal:
        if state.get("retry_count", 0) < 1:
            return {"retry_requested": True, "retry_count": state.get("retry_count", 0) + 1}
        return {"handed_off": True, "confidence": 0.1,
                "answer": "No citable evidence was returned. A human should review this request."}
    return {}


def _route(state: AgentState) -> str:
    return "answer" if state.get("plan") and state["plan"].refusal else "tools"


def _route_verification(state: AgentState) -> str:
    """Retry one evidence-poor answer; otherwise end the turn."""
    return "retry" if state.get("retry_requested", False) else "done"


def build_graph():
    """Compile the LangGraph state machine."""
    graph = StateGraph(AgentState)
    graph.add_node("planner", plan_node); graph.add_node("tools", tools_node)
    graph.add_node("synthesizer", synthesize_node); graph.add_node("verifier", verify_node)
    graph.set_entry_point("planner")
    graph.add_conditional_edges("planner", _route, {"answer": "synthesizer", "tools": "tools"})
    graph.add_edge("tools", "synthesizer")
    graph.add_edge("synthesizer", "verifier")
    graph.add_conditional_edges("verifier", _route_verification, {"retry": "planner", "done": END})
    return graph.compile()


agent = build_graph()
