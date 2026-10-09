# Evaluation failures

This log records failures observed in the final real-model evaluation and historical mock-planner fixes. The final OpenRouter run evaluated the 38 development cases before the 12 holdout cases; per-case results are in [`results/real.json`](results/real.json).

## Final real-model run

Run on 2026-10-09 with `openai/gpt-4o-mini` via OpenRouter. The aggregate end-to-end success rate was 0.10 (5/50); the holdout success rate was 0.0833 (1/12).

| What broke | Evidence from the run | Impact |
|---|---|---|
| The planner refused or misrouted in-scope requests. | 31/50 tool-routing mismatches and 31/50 incorrect handoff decisions. Routing-mismatch cases: q01, q02, q03, q04, q05, q06, q07, q08, q09, q10, q11, q12, q13, q14, q15, q27, q31, q32, q33, q34, q35, q36, q37, q38, q39, q40, q41, q42, q43, q44, q45. | Policy, SQL, mixed, and ticket questions often did not receive the labeled tool plan; q43 also received an extra SQL call. |
| SQL plans used the wrong schema or returned the wrong rows. | SQL result-set accuracy was 0/25. Eight SQL calls failed on nonexistent columns: q16/q31 (`order_date`), q17/q34 (`created_at`), q18 (`product_name`), q26/q37 (`total`), and q30 (`sale_date`). Three cases did not call the expected SQL tool; the remaining 14 calls completed but returned result sets that disagreed with the reference. | No labeled SQL case passed. |
| One source label was missed by retrieval. | RAG Recall@4 was 24/25 (0.96); q12 had recall 0. | The expected policy source was absent from the top four retrieved documents for that case. |
| The judge found weak evidence support overall. | Mean LLM-judge faithfulness was 0.488. | This is a model-judge result, not a human factuality audit. |

An earlier real-model attempt, before the completed run, stopped on a development case because the model returned SQL `arguments` as a string instead of an object. `Plan` rejected it with a validation error. The planner prompt was clarified to show the required object shape; the completed run recorded no planner execution errors.

| Run / case | What broke | How I found it | How I fixed it |
|---|---|---|---|
| Initial mock run, q05/q07/q10/q12/q13 | Cancellation, customer privacy, tracking, fraud, and price-match questions were refused or routed to SQL instead of policy search. | Compared planned tools with labeled dev examples and found missing retail-policy intents in the mock planner. | Added policy intents and narrowed SQL routing to explicit data requests. |
| Initial mock run, q34/q35 | Mixed policy plus order/product questions did not consistently call both required tools. | Compared planned tools with labeled dev examples. | Added explicit multi-tool routing for policy cues combined with product/order data requests. |
