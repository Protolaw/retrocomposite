# Results from training onward

Store generated results here, separated by stage. Generated contents are ignored
by Git; this README keeps the folder and its contract version-controlled.

| Location | Contents |
| --- | --- |
| `training/` | Single-step, primary-composite, and patent-disjoint checkpoints; training/validation metrics, logs, configuration snapshots, and calibration results. |
| `planning/` | Raw MCTS candidates and action provenance, run configurations, search statuses, model-call/cache counters, and timing records. |
| `postprocessing/` | Unwrapped explicit routes, replay/reattachment evidence, stock and chemistry validation, deduplication maps, failure/truncation reports, and processing costs. |
| `analysis/` | Paired comparisons, solve-versus-cost and diversity summaries, reference recovery, uncertainty estimates, tables, figures, and evaluation audit reports. |

Create stage directories as results are produced. Within a stage, keep distinct
model/cohort, run, and seed directories. Command examples start with
`training/single_step/`, `training/primary/`, and `training/patent_disjoint/`;
repeat runs need separate destinations to preserve earlier results.

Each result manifest should identify its stage, arm/cohort, run and seed, input
paths and hashes, configuration, and outputs. Planning references frozen training
checkpoints and prepared `data/` assets. Post-processing references planning runs
and matching eligible decomposition support. Analysis references all runs,
including failures, plus preparation audits and reference routes. Preserve these
links so each reported metric can be traced back to its inputs.

The [seeded training runner](../docs/TRAINING.md) is implemented and saves native
checkpoints, local logs, verified validation metrics, and complete/failed run
manifests. Planning, post-processing, and analysis runners remain planned work.
Full production training and evaluation have not been executed. Prepared training
data, stock, split assignments, and cohort-selection audits remain in
[data/](../data/README.md).

Workflows: [training](../docs/diagrams/training.md),
[planning](../docs/diagrams/planning.md),
[post-processing](../docs/diagrams/postprocessing.md), and
[analysis](../docs/diagrams/analysis.md).
