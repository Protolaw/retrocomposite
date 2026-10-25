# Data prepared before training

Store prepared inputs and their provenance here. Generated contents are ignored
by Git; this README keeps the folder and its contract version-controlled.

| Location | Contents |
| --- | --- |
| `single_step/` | Rules TSV, policy-data TSV, deduplicated reactions, and provenance from cleaned n1+n5. |
| `stock/` | Stereo-free cleaned n1 and n5 leaves, their union stock, and planning targets. |
| `cohorts/` | Shared-tactic selection, exclusion audits, and separate primary/patent-disjoint training and executable-support assets. |
| `splits/` | Frozen train/validation assignments, exact vocabulary/policy snapshots, and grouping/seed/coverage manifests; see [training commands](../docs/TRAINING.md). |
| `composite/`, `composite_roundtrip/` | Optional adapter transport exports for inspection; these are unfiltered and are not primary experiment training data. |

Use matching refreshed RouteInspector publications as read-only sources at
their upstream paths. Record their hashes in preparation manifests. Library
refreshing belongs to RouteInspector.

Preparation commands create their destination directories and reject existing
destinations. Do not pre-create the paths above. Use a fresh versioned destination
for a new preparation run and preserve earlier manifests.

Training consumes these artifacts; its results go to
[outputs/training/](../outputs/README.md). Cohort decomposition support remains
here and is also consumed during planning and post-processing. Evaluation reports
and search-generated molecules belong in `outputs/`; they do not modify the
frozen training data or exclusions.

See [preparation commands](../docs/PREPARATION.md),
[cohort selection](../docs/SELECTION.md), and the
[two preparation diagrams](../docs/diagrams/preparation.md).
