# Evaluation failures

This log records genuine routing mismatches from early mock evaluation passes and the fixes applied afterward. The final reported mock run was rerun on all 50 cases.

| Run / case | What broke | How I found it | How I fixed it |
|---|---|---|---|
| Initial mock run, q05/q07/q10/q12/q13 | Cancellation, customer privacy, tracking, fraud, and price-match questions were refused or routed to SQL instead of policy search. | Compared planned tools with labeled dev examples and found missing retail-policy intents in the mock planner. | Added policy intents and narrowed SQL routing to explicit data requests. |
| Initial mock run, q34/q35 | Mixed policy plus order/product questions did not consistently call both required tools. | Compared planned tools with labeled dev examples. | Added explicit multi-tool routing for policy cues combined with product/order data requests. |
