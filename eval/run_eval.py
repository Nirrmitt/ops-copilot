"""Run reproducible offline baselines and write raw JSON plus a Markdown table."""
import asyncio
import json
import os
import statistics
import time
from pathlib import Path

from openai import APIError
from pydantic import ValidationError

from app.graph import agent
from app.tools.rag import rag_search
from app.tools.sql import sql_query
from eval.judges import JUDGE_USAGE, judge_faithfulness

ROOT = Path(__file__).resolve().parents[1]
DATASET = Path(__file__).with_name("dataset.jsonl")
RESULTS = Path(__file__).with_name("results")


async def evaluate() -> dict[str, object]:
    rows = [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows.sort(key=lambda row: row.get("split") == "holdout")
    latencies: list[float] = []
    steps: list[int] = []
    routed = 0
    abstained = 0
    successes = 0
    faith = []
    sql_correct = []
    rag_recall = []
    plain_llm_routing = []
    rag_only_routing = []
    case_results: list[dict[str, object]] = []
    for row in rows:
        started = time.perf_counter()
        execution_error = None
        try:
            result = await agent.ainvoke({"question": row["question"], "confirm": False})
        except (APIError, ValidationError, TimeoutError) as exc:
            execution_error = f"{type(exc).__name__}: {exc}"
            result = {}
        latencies.append((time.perf_counter() - started) * 1000)
        steps.append(1 if execution_error else 3 + bool(result.get("plan") and result["plan"].calls)
                     + 4 * result.get("retry_count", 0))
        got = {call.tool for call in result.get("plan").calls} if result.get("plan") else set()
        expected = set(row["expected_tools"])
        routed += got == expected
        did_abstain = bool(result.get("handed_off")) or bool(result.get("plan") and result["plan"].refusal)
        abstained += did_abstain == row["expected_handoff"]
        evidence = " ".join(str(item.output) for item in result.get("tool_results", []))
        faith_score = (0.0 if execution_error else
                       await judge_faithfulness(result.get("answer", ""), evidence))
        faith.append(faith_score)
        sql_case_correct = None
        if row.get("reference_sql"):
            actual_sql = next((item.output for item in result.get("tool_results", [])
                               if item.tool == "sql_query" and item.ok), None)
            expected_rows = sql_query(row["reference_sql"])["rows"]
            sql_case_correct = bool(actual_sql) and actual_sql["rows"] == expected_rows
            sql_correct.append(sql_case_correct)
        rag_recall_score = None
        missing_sources: list[str] = []
        if row.get("expected_sources"):
            retrieved = rag_search(row["question"], k=4)
            found = {item["source"] for item in retrieved}
            targets = set(row["expected_sources"])
            rag_recall_score = len(found & targets) / len(targets)
            missing_sources = sorted(targets - found)
            rag_recall.append(rag_recall_score)
        plain_llm_routing.append(not expected)
        rag_only_routing.append(expected == {"rag_search"})
        expected_results = (not expected or bool(result.get("tool_results")))
        sql_ok = not row.get("reference_sql") or sql_correct[-1]
        case_success = (not execution_error and got == expected and did_abstain == row["expected_handoff"]
                        and expected_results and sql_ok)
        successes += case_success
        tool_failures = [
            {"tool": item.tool, "error": item.output.get("error", "unknown error")}
            for item in result.get("tool_results", []) if not item.ok
        ]
        failure_categories = []
        if got != expected:
            failure_categories.append("tool_routing")
        if did_abstain != row["expected_handoff"]:
            failure_categories.append("handoff")
        if tool_failures:
            failure_categories.append("tool_execution")
        if sql_case_correct is False:
            failure_categories.append("sql_accuracy")
        if rag_recall_score is not None and rag_recall_score < 1:
            failure_categories.append("rag_recall")
        if execution_error:
            failure_categories.append("execution_error")
        case_results.append({
            "id": row["id"],
            "split": row.get("split", "unspecified"),
            "expected_tools": sorted(expected),
            "actual_tools": sorted(got),
            "expected_handoff": row["expected_handoff"],
            "actual_handoff": did_abstain,
            "sql_correct": sql_case_correct,
            "rag_recall_at_4": rag_recall_score,
            "missing_sources": missing_sources,
            "faithfulness": faith_score,
            "tool_failures": tool_failures,
            "execution_error": execution_error,
            "failure_categories": failure_categories,
            "end_to_end_success": case_success,
        })
    ordered = sorted(latencies)
    p95 = ordered[min(len(ordered)-1, int(.95 * (len(ordered)-1)))]
    from app.graph import planner
    token_usage = {"prompt_tokens": planner.prompt_tokens + JUDGE_USAGE["prompt_tokens"],
                   "completion_tokens": planner.completion_tokens + JUDGE_USAGE["completion_tokens"]}
    if os.getenv("LLM_PROVIDER", "mock") == "mock":
        cost_per_query: float | str = 0.0
    else:
        input_rate = os.getenv("MODEL_INPUT_COST_PER_1M")
        output_rate = os.getenv("MODEL_OUTPUT_COST_PER_1M")
        cost_per_query = "not configured" if input_rate is None or output_rate is None else round(
            (token_usage["prompt_tokens"] * float(input_rate) +
             token_usage["completion_tokens"] * float(output_rate)) / 1_000_000 / len(rows), 8)
    full_agent_baseline = f"full_agent_{'mock' if os.getenv('LLM_PROVIDER', 'mock') == 'mock' else 'real'}"
    return {"mode": os.getenv("LLM_PROVIDER", "mock"), "queries": len(rows), "tool_routing_accuracy": round(routed / len(rows), 4),
            "sql_execution_accuracy": round(sum(sql_correct) / len(sql_correct), 4),
            "sql_cases": len(sql_correct), "rag_recall_at_4": round(statistics.mean(rag_recall), 4),
            "rag_cases": len(rag_recall), "faithfulness": round(statistics.mean(faith), 4),
            "correct_abstention_handoff_rate": round(abstained / len(rows), 4),
            "end_to_end_success_rate": round(successes / len(rows), 4),
            "average_steps": round(statistics.mean(steps), 2),
            "latency_ms_p50": round(statistics.median(latencies), 2), "latency_ms_p95": round(p95, 2),
            "token_usage": token_usage, "cost_per_query_usd": cost_per_query,
            "case_results": case_results,
            "baselines": {
                "plain_llm_no_tools_mock": {"tool_routing_accuracy": round(sum(plain_llm_routing) / len(rows), 4)},
                "rag_only_mock": {"tool_routing_accuracy": round(sum(rag_only_routing) / len(rows), 4),
                                  "rag_recall_at_4": round(statistics.mean(rag_recall), 4)},
                full_agent_baseline: {"tool_routing_accuracy": round(routed / len(rows), 4),
                                      "end_to_end_success_rate": round(successes / len(rows), 4)}}}


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    result = asyncio.run(evaluate())
    output_name = "mock" if result["mode"] == "mock" else "real"
    result_label = "Mock" if output_name == "mock" else "Real"
    (RESULTS / f"{output_name}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    lines = [f"| Metric | {result_label} result |", "|---|---:|"]
    lines += [f"| {key.replace('_', ' ')} | {value} |" for key, value in result.items()
              if not isinstance(value, (dict, list))]
    for baseline, metrics in result["baselines"].items():
        for metric, value in metrics.items():
            lines.append(f"| {baseline} · {metric.replace('_', ' ')} | {value} |")
    (RESULTS / f"{output_name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
