# Planning workflow

This is the planned MCTS experiment; the hybrid policy, search instrumentation,
and experiment runner remain TODOs. Planning produces candidate routes for
[post-processing](postprocessing.md). See [PLAN.md](../../PLAN.md).

```mermaid
flowchart TD
    MODELS["outputs/training/<br/>Frozen checkpoints, calibration and vocabulary hashes"]
    DATA["data/stock/ and data/cohorts/<br/>Paired n5 targets, union stock and matching action support"]
    DESIGN["Freeze paired seeds, evaluator and search budgets<br/>Stereo off; common elementary chemical horizon"]
    BASE["Baseline MCTS<br/>50 single-step recommendations"]
    PRIMARY["Primary hybrid MCTS<br/>One total top-50 budget across both heads"]
    SENS["Patent-disjoint hybrid MCTS<br/>Same allocation protocol and matched settings"]
    RUNS["outputs/planning/<br/>All run statuses, raw candidates and action/cohort provenance"]
    COST["outputs/planning/<br/>Requests, cache hits, actual neural forwards, chemistry and time"]
    MODELS --> DESIGN
    DATA --> DESIGN
    DESIGN --> BASE
    DESIGN --> PRIMARY
    DESIGN --> SENS
    BASE --> RUNS
    PRIMARY --> RUNS
    SENS --> RUNS
    BASE -.-> COST
    PRIMARY -.-> COST
    SENS -.-> COST
```

All arms share the single-step checkpoint, targets, stock, and evaluator. Use
`stereo_mode: off` and `min_mol_size: 0`; record chemical depth separately from
macro-action depth. The hybrid allocation is still an open decision. Preserve
unsuccessful runs, timeouts, generated-state provenance, and already-in-stock
targets for analysis.

Candidate routes and search-reported solves are provisional until explicit
validation. Save raw search outputs under
[outputs/planning/](../../outputs/README.md), then pass candidates and their
manifests to [post-processing](postprocessing.md).
