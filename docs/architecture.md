# Architecture

```mermaid
flowchart LR
  Q[Question] --> P[Planner]
  P -->|refusal| S[Synthesizer]
  P -->|bounded plan| T{Tool calls}
  T --> R[Policy search]
  T --> D[Guarded read-only SQL]
  T --> A[Confirmed ticket action]
  R --> S
  D --> S
  A --> S
  S --> V[Verifier]
  V -->|supported| O[Answer with citations]
  V -->|weak or failure| H[Human handoff]
```

The graph has a hard six-call cap. SQL is validated and row-limited before execution. Ticket actions require both request confirmation and an explicit configuration opt-in. Retrieved policy text is evidence only; it cannot change planner instructions.
