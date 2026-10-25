# Post-processing workflow

This stage turns MCTS candidates into explicit, validated routes. Strict replay,
reattachment, validation, and the post-processing runner remain TODOs. See
[PLAN.md](../../PLAN.md#cost-validation-and-diversity).

```mermaid
flowchart TD
    RUNS["outputs/planning/<br/>Raw candidates and action/cohort provenance"]
    SUPPORT["data/cohorts/<br/>Matching eligible n1 decomposition pool"]
    UNWRAP["Replay composite actions into elementary steps<br/>Baseline routes pass through without replay"]
    ATTACH["Reattach exact downstream branches<br/>Validate explicit chemistry and connectivity"]
    UNION["data/stock/<br/>Frozen cleaned n1+n5 union stock"]
    LEAVES["Check every explicit leaf against union stock"]
    STATUS["Classify valid, invalid and inconclusive<br/>Record failures and enumeration caps"]
    UNIQUE["Deduplicate validated explicit routes<br/>Retain source candidates and replay-variant provenance"]
    RESULTS["outputs/postprocessing/<br/>Explicit routes, validation reports and deduplication maps"]
    COST["outputs/postprocessing/<br/>Replay, validation and deduplication costs"]
    RUNS --> UNWRAP --> ATTACH --> LEAVES --> STATUS
    SUPPORT --> UNWRAP
    UNION --> LEAVES
    STATUS -->|valid routes| UNIQUE --> RESULTS
    STATUS -->|all statuses| RESULTS
    UNWRAP -.-> COST
    ATTACH -.-> COST
    LEAVES -.-> COST
    UNIQUE -.-> COST
```

Baseline routes undergo the same explicit chemistry and stock checks. Composite
replay uses the matching cohort's eligible n1 support; n5 reference routes do not
supply decomposition alternatives. Deduplication removes duplicate explicit
routes caused by atom mappings or different macro encodings, while preserving
the distinction between independently discovered routes and replay variants.

Only fully validated routes whose leaves are all in stock count as solved.
Non-stock leaves exposed by replay cannot count as solved; immediate failure
versus a separately recorded and charged completion search remains an open
decision. Truncated or unresolved validation must remain visible in the reports.
Preserve raw planning outputs and write derived results to
[outputs/postprocessing/](../../outputs/README.md). Next: [analysis](analysis.md).
