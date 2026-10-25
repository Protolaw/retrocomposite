# Analysis workflow

This is the planned analysis stage. It consumes search records and validated
post-processing results; the analysis runner remains a TODO. See
[PLAN.md](../../PLAN.md#cost-validation-and-diversity).

```mermaid
flowchart TD
    RUNS["outputs/planning/<br/>All paired runs, search costs and generated-state provenance"]
    ROUTES["outputs/postprocessing/<br/>Validated unique routes, all statuses and processing costs"]
    DATA["data/ cohort audits and support manifests<br/>Frozen n5 references at recorded upstream paths"]
    JOIN["Join by target, seed, arm and cohort<br/>Preserve failed runs and separate already-in-stock targets"]
    COST["Validated solve-versus-cost<br/>Actual model calls, chemistry work and end-to-end time"]
    DIVERSITY["Explicit-route diversity<br/>Unique routes, disconnections, leaf sets and clusters"]
    RECOVERY["Reference recovery and elementary depth<br/>Separate search discoveries from replay variants"]
    AUDIT["Exclusions, support/vocabulary loss and patent coverage<br/>Audit overlap with generated search states"]
    REPORT["outputs/analysis/<br/>Paired target-level uncertainty, primary/sensitivity comparisons,<br/>tables, figures and evaluation reports"]
    RUNS --> JOIN
    ROUTES --> JOIN
    JOIN --> COST
    JOIN --> DIVERSITY
    JOIN --> RECOVERY
    DATA --> RECOVERY
    DATA --> AUDIT
    RUNS --> AUDIT
    COST --> REPORT
    DIVERSITY --> REPORT
    RECOVERY --> REPORT
    AUDIT --> REPORT
```

Include unsuccessful runs and post-processing costs in comparisons. Count only
fully validated stock-reaching routes as solved, and report invalid/inconclusive
outcomes explicitly. Compare each hybrid with the shared single-step baseline
using paired n5 targets and seeds; report uncertainty at the target level.

The patent sensitivity report must show support and vocabulary losses alongside
planning outcomes. Search-generated overlap audits describe exposure without
revising frozen training exclusions. Keep reference recovery separate from route
diversity and preserve the provenance of replay-generated alternatives.

Write summaries and figures to [outputs/analysis/](../../outputs/README.md), with
links and hashes tracing each result to its planning, post-processing, and
preparation inputs. Upstream workflows: [planning](planning.md) and
[post-processing](postprocessing.md).
