# Planning workflow

This is the planned MCTS experiment; the hybrid policy, instrumentation and
experiment runner remain TODOs. See the
[experiment matrix](../../PLAN.md#composite-popularity-experiment).

```mermaid
flowchart TD
    MODELS["Frozen shared single-step model and four composite models<br/>Matching calibration, vocabularies and n1 action support"]
    DATA["All cleaned n5 final targets, including no-tactic references<br/>Same stereo-free union leaf stock"]
    DESIGN["Freeze paired search seeds, evaluator and budgets<br/>Common elementary chemical horizon and hybrid allocation"]
    BASE["B50 shared baseline<br/>50 single-step proposals"]
    MAIN["Primary / pop_gt1<br/>Main hybrid"]
    ALL["Primary / pop_ge1<br/>Includes singleton rules"]
    PAT["Patent-disjoint / pop_gt1<br/>Patent sensitivity"]
    PATALL["Patent-disjoint / pop_ge1<br/>Combined sensitivity"]
    RUNS["outputs/planning/<br/>All statuses, candidates, cohort/popularity IDs and action provenance"]
    COST["Requests, cache hits, actual forwards, chemistry and time"]
    MODELS --> DESIGN
    DATA --> DESIGN
    DESIGN --> BASE
    DESIGN --> MAIN
    DESIGN --> ALL
    DESIGN --> PAT
    DESIGN --> PATALL
    BASE --> RUNS
    MAIN --> RUNS
    ALL --> RUNS
    PAT --> RUNS
    PATALL --> RUNS
    RUNS --> COST
```

All four hybrids share one total top-50 budget; 40 single-step / 10 composite
slots remains a proposal. Do not use n5 reference-tactic annotations to select
targets or gate recommendations. The baseline is reused in paired comparisons.
Use `stereo_mode: off` and `min_mol_size: 0`; preserve unsuccessful runs,
timeouts and already-in-stock targets for analysis.

Search-reported solves remain provisional until explicit validation. Save raw
search outputs under [outputs/planning/](../../outputs/README.md), then pass
candidates and matching manifests to [post-processing](postprocessing.md).
