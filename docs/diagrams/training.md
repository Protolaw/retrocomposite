# Training workflow

Native TSV preparation, cohort filtering, grouped splitting, and seed-controlled
MHN training are implemented. Production split review, full training, calibration,
and the SynPlanner hybrid implementation remain TODOs. See
[training commands](../TRAINING.md), [PLAN.md](../../PLAN.md), and
[open decisions](../../QUESTIONS.md).

```mermaid
flowchart TD
    SINGLE["data/single_step/<br/>Cleaned n1+n5 rules and examples"]
    PRIMARY["data/cohorts/primary/<br/>Eligible n1 composite assets after E1-E3"]
    SENS["data/cohorts/patent_disjoint/<br/>Eligible sensitivity assets"]
    SPLITSS["Freeze single-step train/validation assignments<br/>data/splits/"]
    SPLITP["Group eligible primary examples<br/>data/splits/"]
    SPLITS["Same grouping protocol for sensitivity examples<br/>data/splits/"]
    CONFIG["MHN ranking: QueryCGR rule graphs<br/>and GPS molecule encoding"]
    TRAINSS["Train shared single-step MHN"]
    TRAINP["Train primary composite MHN"]
    TRAINS["Train patent-disjoint composite MHN"]
    SS["outputs/training/single_step/<br/>Checkpoint, metrics and provenance"]
    CP["outputs/training/primary/<br/>Checkpoint, metrics and provenance"]
    CS["outputs/training/patent_disjoint/<br/>Checkpoint, metrics and provenance"]
    CALP["Calibrate primary hybrid<br/>Eligible primary n1 development data only"]
    CALS["Calibrate sensitivity hybrid<br/>Eligible sensitivity development data only"]
    FREEZE["outputs/training/<br/>Freeze checkpoints, calibration, vocabulary hashes and seeds"]
    SINGLE --> SPLITSS --> TRAINSS --> SS
    PRIMARY --> SPLITP --> TRAINP --> CP
    SENS --> SPLITS --> TRAINS --> CS
    CONFIG -.-> TRAINSS
    CONFIG -.-> TRAINP
    CONFIG -.-> TRAINS
    SS --> FREEZE
    SS --> CALP
    CP --> CALP --> FREEZE
    SS --> CALS
    CS --> CALS --> FREEZE
```

Single-step exposure to n5 is deliberate. No n5 composite examples enter composite
training, validation, or calibration. Grouping keeps identical motif inputs and all linked source routes together;
optional patent grouping adds patent links and requires complete provenance. The hybrid allocation
within 50 remains open; 40/10 is a proposal. Keep each checkpoint tied to its
ordered vocabulary and eligible decomposition pool in `data/`.

Prepared data and frozen splits stay in [data/](../../data/README.md). Training
results and calibration belong in [outputs/training/](../../outputs/README.md).
Next: [planning](planning.md).
