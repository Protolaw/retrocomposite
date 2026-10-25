# Grouped splits and seeded MHN training

Run from Retrocomposite with `.venv` active. Production execution requires the
refreshed, matching inputs and reviewed cohort audits. These commands create
new destinations and never overwrite a split or training run.

## Freeze splits under data/

```sh
retrocomposite split --assets data/single_step \
  --output data/splits/single_step --seed 42 --validation-fraction 0.1
retrocomposite split --assets data/cohorts/primary \
  --output data/splits/primary --seed 42 --validation-fraction 0.1
retrocomposite split --assets data/cohorts/patent_disjoint \
  --output data/splits/patent_disjoint --seed 42 --validation-fraction 0.1
```

`python scripts/prepare_splits.py` accepts the same arguments. Seed 42 and a 10%
requested holdout are configurable implementation defaults; the final replication
budget and validation policy still need to be frozen before production fitting.

The default `--grouping route` creates connected components across canonical,
stereo-free input molecules and **every supporting source route**. Identical
inputs stay together across rule labels; shared reactions or deduplicated pairs
link all their source routes transitively. Single-step provenance is joined by
product/rule and reaction indices, independently of the native policy-row order.
Composite provenance comes from eligible n1 occurrence records only. Raw composite
adapter exports and blocked cohorts are rejected.

`--grouping patent` additionally joins all known patent IDs using the cohort's
audited provenance. For single-step data, also supply `--n1` and `--n5` with the
same cleaned sources used for preparation. The parser and normalization match
cohort selection. Incomplete patent provenance blocks a patent-grouped split;
unknown patents cannot establish disjointness. This option controls the holdout
*within* a training corpus and is separate from the patent-disjoint sensitivity
cohort's n1-versus-n5 exclusion.

The splitter orders whole components reproducibly using the split seed and
approximates the requested row fraction while retaining at least one training
example for every vocabulary rule. It does not guarantee per-rule stratification
or an exact validation fraction. Large connected components and rare rules can
restrict the holdout. The audit reports actual sizes, group sizes, rule coverage,
and molecule/route/patent overlap. If no nonempty holdout is possible, it writes
a `blocked` audit and exits with status 2. The trainer refuses blocked splits.
Review this result; grouping is never silently weakened.

Each split contains:

| File | Purpose |
| --- | --- |
| `split.json` | Split seed, grouping policy, requested/actual holdout sizes, per-rule counts, overlap checks, source/cohort identity, and status. |
| `assignments.jsonl` | Original row index, molecule, global rule ID, all supporting routes, optional patents, component ID, and partition. |
| `train.tsv`, `validation.tsv` | Inspectable partition views; these do not renumber labels. |
| `assets/` | Exact copies of the full ordered rule TSV, native policy-data TSV, and vocabulary manifest. |
| `preparation.json` | Input/output hashes, software versions, and splitter implementation hash. |

The split is frozen before training. The ordered vocabulary stays unchanged;
train/validation row subsets are explicit. Original rule popularity describes
the whole prepared corpus, so any future training-frequency prior must use the
split's **train** rule counts. Selection audits and executable decomposition
support remain in the source cohort, linked by its manifest hash.

## Train under outputs/training/

```sh
retrocomposite train --split data/splits/single_step \
  --config configs/mhn_querycgr_gps.yaml --seed 17 \
  --accelerator cpu --threads 1 --workers 0 \
  --output outputs/training/single_step/seed_17
retrocomposite train --split data/splits/primary \
  --config configs/mhn_querycgr_gps.yaml --seed 17 \
  --accelerator cpu --threads 1 --workers 0 \
  --output outputs/training/primary/seed_17
retrocomposite train --split data/splits/patent_disjoint \
  --config configs/mhn_querycgr_gps.yaml --seed 17 \
  --accelerator cpu --threads 1 --workers 0 \
  --output outputs/training/patent_disjoint/seed_17
```

`python scripts/train_policy.py` accepts the same arguments. Repeat with distinct
model seeds and output paths while reusing the same frozen split. The split seed
and model seed have different roles and are both recorded. No presets are loaded.
The wrapper requires the agreed MHN, QueryCGR rule graphs, and GPS encoders.

Each run starts a fresh interpreter with `PYTHONHASHSEED` and CUDA workspace
settings established before importing PyTorch. It seeds Python, NumPy, Torch,
data-loader sampling and workers; fixes the requested CPU thread count; disables
CuDNN benchmarking/TF32; and uses deterministic algorithms. Supported accelerators
are `cpu`, `cuda`, and `mps`, with one device per run. `--device` selects a CUDA
index; `--workers` controls loader workers. Graph preprocessing is serial to
preserve frozen row order, and dropped or reordered graphs are a hard error.

`--determinism strict` is the default. Unsupported deterministic accelerator
operations fail with a saved error log. `--determinism warn` is an explicit,
recorded relaxation; it does not promise identical results. Reproducibility is
scoped to the same software, hardware, precision, and thread/worker configuration.
Small CPU checks verify equal model tensors and metrics for repeated seeds;
accelerator determinism needs validation on the eventual training hardware.

The wrapper owns full-epoch training/validation, local CSV logging, checkpoint
selection, and determinism. Config `logger` is replaced with local CSV logging.
Allowed `trainer` overrides are `precision`, `accumulate_grad_batches`,
`gradient_clip_val`, and `gradient_clip_algorithm`; other overrides are rejected
so debug limits cannot silently change the experiment. Epochs and batch size
come from the model configuration.

## Results and verification

| File | Purpose |
| --- | --- |
| `run.json` | Running/complete/failed status, split/model seeds, input and output hashes, source-code hashes, software, device settings, and elapsed time. |
| `config.yaml`, `effective_config.json`, `split.json` | Original/effective model configuration and frozen split summary. |
| `console.log` | Worker output, warnings, progress summaries, and errors. |
| `logs/metrics/metrics.csv` | Step/epoch training loss and epoch validation loss/top-1 accuracy. |
| `checkpoints/best.ckpt`, `checkpoints/last.ckpt` | Best validation-loss and final checkpoints in SynPlanner's native bare-network format. |
| `metrics.json` | Metrics recomputed over the complete validation partition after reloading the best checkpoint through SynPlanner. |
| `runtime_sources.json` | Exact installed SynPlanner training/model source-file hashes. |
| `graph_alignment.json` | Policy-row versus graph-row alignment check, with missing row indices when conversion drops examples. |
| `environment/` | Copies of the project source/dependency snapshots when available. |

Loss and accuracy are weighted by actual batch size, including a partial last
batch. Final metrics include sample-mean cross entropy, top-k accuracy for
applicable k, and macro recall over labels observed in validation. These remain
observed-label metrics: a molecule may have other applicable rules that were not
labelled. They are not planning solve rates.

Failed runs retain their log and manifest and cannot be overwritten. Check
`run.json` for `status: complete` before consuming a checkpoint. Native saved
weights are verified for inference loading; resuming optimizer/trainer state is
not implemented. Full production fits, hybrid calibration, and planning remain
separate steps. See the [training workflow](diagrams/training.md),
[TODO](../TODO.md), and [open decisions](../QUESTIONS.md).
