# Training workflow

Grouped splitting and seed-controlled MHN training are implemented. The new
popularity exports and matched split derivation, production training, calibration
and hybrid implementation remain TODOs. See [training commands](../TRAINING.md)
and [experiment matrix](../../PLAN.md#composite-popularity-experiment).

```mermaid
flowchart TD
    SINGLE["Cleaned n1+n5 single-step assets"]
    SSPLIT["Freeze shared single-step split"]
    SS["Train shared single-step MHN"]
    COHORTS["Eligible n1 merged composites<br/>Primary and patent-disjoint cohorts"]
    GROUP["Freeze full-cohort molecule/route groups and assignments"]
    POP["Derive matched settings per cohort<br/>pop_gt1 main; pop_ge1 includes singletons"]
    AUDIT["data/experiments/cohort/popularity/<br/>Vocabulary, policy rows, splits, replay and lineage audits"]
    TRAIN["Train four composite MHNs per model seed<br/>Same seed list and tuning protocol"]
    CONFIG["MHN; QueryCGR rule graphs; GPS encoders"]
    CAL["Calibrate each hybrid on eligible n1 development data"]
    FREEZE["outputs/training/cohort/popularity/seed/<br/>Freeze checkpoints, calibration, logs and metrics"]
    SINGLE --> SSPLIT --> SS
    COHORTS --> GROUP --> POP --> AUDIT --> TRAIN
    CONFIG -.-> SS
    CONFIG -.-> TRAIN
    SS --> CAL
    TRAIN --> CAL --> FREEZE
```

Popularity counts unique prepared target/merged-rule pairs from eligible n1,
before its holdout. Preserve assignments when deriving >1; verify train support
and report common validation pairs. No n5 composite examples enter training,
validation or calibration. Single-step exposure to n5 is deliberate.

Prepared data and frozen splits stay in [data/](../../data/README.md). Each
checkpoint must match its ordered vocabulary and eligible decomposition pool.
Results belong in [outputs/training/](../../outputs/README.md).
Next: [planning](planning.md).
