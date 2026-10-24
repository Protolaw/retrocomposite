# Retrocomposite

Experiment preparation for comparing a PaRoutes-derived single-step SynPlanner
RRS with a hybrid single-step/composite RRS. This is a separate project from
RouteInspector and SynPlanner.

- [General plan and scientific scope](PLAN.md)
- [Implementation tasks and status](TODO.md)
- [Questions and explanations](QUESTIONS.md)
- [Preparation commands and data contracts](docs/PREPARATION.md)

Confirmed scope: train our own single-step model on cleaned n1+n5 reactions;
MHN ranking with QueryCGR rule graphs and GPS molecule encoding; linear
consecutive composites learned from n1; planning on n5; stock derived from
cleaned route leaves; stereochemistry ignored for this experiment.

This is an intentionally exposed planning benchmark. It is not a claim of
unseen-molecule or unseen-reaction generalization. Both planning arms use the
same single-step checkpoint and stock.

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
