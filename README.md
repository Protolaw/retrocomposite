# Retrocomposite

Experiment preparation for comparing a PaRoutes-derived single-step SynPlanner
RRS with a hybrid single-step/composite RRS. This is a separate project from
RouteInspector and SynPlanner.

- [General plan and scientific scope](PLAN.md)
- [Implementation tasks and status](TODO.md)
- [Questions and explanations](QUESTIONS.md)
- [Preparation commands and data contracts](docs/PREPARATION.md)
- [Shared-tactic selection, exclusion filters, and audits](docs/SELECTION.md)
- [Grouped splits and seeded training commands](docs/TRAINING.md)
- Mermaid workflows: [preparation](docs/diagrams/preparation.md),
  [training](docs/diagrams/training.md), [planning](docs/diagrams/planning.md),
  [post-processing](docs/diagrams/postprocessing.md), and
  [analysis](docs/diagrams/analysis.md).

Confirmed scope: train our own single-step model on cleaned n1+n5 reactions;
MHN ranking with QueryCGR rule graphs and GPS molecule encoding; linear
consecutive tactics shared by n1 and n5, learned from eligible n1 motif targets
including internal molecules; planning on n5; the union of cleaned n1+n5 leaves
as stock for both arms; stereochemistry ignored for this experiment. Composite
supervision uses the three primary exclusions in PLAN.md, with an additional
patent-disjoint sensitivity analysis. `retrocomposite select-cohorts` implements
this selection and publishes audited training assets for both cohorts.

This is an intentionally exposed planning benchmark. It is not a claim of
unseen-molecule or unseen-reaction generalization. Both planning arms use the
same single-step checkpoint and stock.

## Project files

Use [data/](data/README.md) for artifacts prepared before training and
[outputs/](outputs/README.md) for results from training onward:

```text
data/
  single_step/          rules, policy data, and reaction provenance
  stock/                union stock and planning targets
  cohorts/              primary and patent-disjoint assets and exclusion audits
  splits/               frozen train/validation assignments
outputs/
  training/             checkpoints, training metrics, and calibration
  planning/             MCTS candidates, search logs, and inference counters
  postprocessing/       unwrapped routes, validation, and deduplication
  analysis/             comparisons, tables, figures, and reports
```

Stage directories are created as artifacts are produced. Preparation commands
require a new destination, so do not pre-create their output directories.
Keep generated data and results out of Git; the two folder READMEs are tracked.
Version-controlled configuration stays in `configs/`, environment records in
`environment/`, and workflow documentation in `docs/`.

## Setup

Use Python 3.12 for the initial local environment:

```sh
python scripts/setup_environment.py --route-inspector ../route-inspector --synplanner ../SynPlanner
source .venv/bin/activate
retrocomposite --help
python -m pytest -q
```

The setup installs the complete `SynPlanner[all]` dependency set from the local
SynPlanner source snapshot and RouteInspector from its local source snapshot.
RouteInspector currently pins a different SynPlanner Git revision. Setup
explicitly overrides only that dependency, records source hashes/revisions,
installs its other dependencies, and checks package consistency. Existing
environments and source repositories are not changed. Source edits require
reinstallation; this environment does not silently follow editable upstream code.

Library reconstruction belongs to RouteInspector. This repository consumes its
refreshed publications; it does not contain a library rebuilding workflow.
Hybrid-policy implementation belongs on a future SynPlanner branch. No training,
full corpus extraction, or planning is run by setup.
