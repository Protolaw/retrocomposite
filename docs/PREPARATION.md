# Preparation commands and contracts

Workflow: [preparation diagram](diagrams/preparation.md). For the final
experimental cohorts, use [shared-tactic selection](SELECTION.md).

Run from the Retrocomposite project with `.venv` active. Inputs are read-only;
each output directory must be new. Use the existing standalone `data/clean/`
files selected by the user on 2026-10-25, as recorded in
[dataset readiness](DATASET_READINESS.md). Single-step and stock preparation are
independent of composite-library construction; cohort selection requires the
matching identity-v3 n1 composite publication.
Save preparation artifacts and audits under [data/](../data/README.md).
Training and later-stage results go under [outputs/](../outputs/README.md).

## Single-step vocabulary and policy data

```sh
python scripts/prepare_single_step.py \
  --n1 ../route-inspector/data/clean/n1_routes.json \
  --n5 ../route-inspector/data/clean/n5_routes.json \
  --config configs/rule_extraction.yaml \
  --workers 1 --output data/single_step
```

This exports stereo-free mapped reactions, deduplicates constitutional
reactant/product multisets (including multiplicity), preserves every original
membership, and delegates rule extraction to SynPlanner. Reagents are excluded
from the duplicate key, matching `keep_reagents: false`. Reactions must already
be correctly mapped, preprocessed, and oriented as forward route reactions.
Extraction errors stop publication. The extraction profile retains all rules
with at least one unique supporting reaction; validate the retained coverage.

Native product strings are normalized with the same identity function as stock
and grouped splitting. Original policy rows and a row-level normalization audit
are preserved; row order, multiplicity, and rule IDs remain unchanged.

Outputs include `single_step.tsv`, `single_step_policy_data.tsv`, the native
rule manifest, `reaction_provenance.jsonl`, and `preparation.json`. A successful
publication has passed the current SynPlanner rule loader and QueryCGR graph
encoder. Never consume a directory containing `INCOMPLETE`.

## Leaf stock and targets

```sh
python scripts/prepare_stock.py \
  --n1 ../route-inspector/data/clean/n1_routes.json \
  --n5 ../route-inspector/data/clean/n5_routes.json \
  --output data/stock
```

Outputs are `n1.smi`, `n5.smi`, `union.smi`, `n1_targets.smi`,
`n5_targets.smi`, and a leaf-occurrence sidecar. The definition of a leaf is a
molecule node with no children. Parent `in_stock` flags never terminate traversal.
Use `union.smi`, the stereo-free union of cleaned n1+n5 leaves, as the common
stock for both planning arms.

These are pre-canonicalized files. Load with SynPlanner's
`load_building_blocks(path, standardize=False)` to preserve the declared stock
identity policy. Planning must use `stereo_mode: off` and `min_mol_size: 0`.
Stock membership describes the experimental terminal set, not commercial availability.

## Composite library adapter

```sh
python scripts/prepare_composites.py composite-library \
  --reference-library ../route-inspector/outputs/reference_libraries/n1 \
  --composite-library ../route-inspector/outputs/composite_libraries/n1-retrocomposite-v3-20261025 \
  --routes-json ../route-inspector/data/clean/n1_routes.json \
  --output data/composite
```

The adapter requires a standalone n1 identity-v3 composite publication, verifies
artifact hashes and the matching reference/source identities, resolves exact
certified variants, and joins each link to its motif-target molecule. It exports
only `rrseq_cons`, refuses n5/merged supervision, and preserves native
decomposition payloads. It does not rebuild or recertify libraries.

This first adapter exports all certified n1 linear occurrences, including
internal motif targets. The agreed experiment requires restricting these to
tactics shared by n1 and n5 and applying the confirmed E1-E3 exclusions in
[PLAN.md](../PLAN.md#primary-occurrence-exclusions): shared final-target routes,
shared motif inputs, and exact concrete multistep segments, including embedded
segments. Derive the additional patent-disjoint cohort from those survivors.
Rebuild all composite support and supervision from each eligible cohort.
Use the implemented `select-cohorts` command described in [SELECTION.md](SELECTION.md)
to perform that selection. This raw export command does not filter a cohort. Use n5 only for tactic-overlap
selection, frozen exclusion checks, and evaluation, never as a source of
composite training examples or
decomposition alternatives.

Outputs are `composite.tsv`, `composite_policy_data.tsv`, vocabulary and
preparation manifests, and `composite_records.jsonl`. The latter retains all
occurrences while policy data deduplicates exact canonical-product/exact-rule
pairs. Multiple different rules for the same product remain separate positives.
`reaction_indices` in this adapter refer to unique training-pair indices, not
indices in a synthetic-reaction file.

## Composite JSON adapter

```sh
python scripts/prepare_composites.py composite-json \
  --records data/composite/composite_records.jsonl \
  --output data/composite_roundtrip
```

Accepts a JSON array or JSONL records with this explicit contract:

```json
{
  "kind": "rrseq_cons",
  "dataset_id": "n1",
  "composite_identity_version": 3,
  "composite_rule": "<exact mapped retrosynthetic SMARTS>",
  "product_smiles": "<molecule where this tactic starts>",
  "certificate": {
    "source_occurrence_certified": true,
    "source_chemistry_equivalent": true,
    "source_mapping_consistent": true,
    "composite_chemistry_equivalent": true,
    "composite_mapping_consistent": true
  },
  "provenance": {"reference_occurrence_id": "<source occurrence>"},
  "decomposition": {"raw_sequence": "<recorded linear program>"}
}
```

The library export supplies the complete real certificate/provenance/decomposition,
not these explanatory placeholders. The JSON adapter validates this supplied
contract; it does not independently prove chemistry certification. Arbitrary
legacy JSON field names are not guessed. An additional format-specific adapter
can be added once its schema is identified.

## Training compatibility

```sh
retrocomposite validate --rules data/single_step/single_step.tsv
retrocomposite validate --rules data/composite/composite.tsv
synplan ranking_policy_training \
  --config configs/mhn_querycgr_gps.yaml \
  --policy_data data/single_step/single_step_policy_data.tsv \
  --results_dir outputs/training/single_step --workers 1
```

The primary composite training command uses
`data/cohorts/primary/composite_policy_data.tsv`; the sensitivity command uses
`data/cohorts/patent_disjoint/composite_policy_data.tsv`. Use separate result
directories `outputs/training/primary/` and
`outputs/training/patent_disjoint/`, with distinct run/seed subdirectories
for repeated experiments. Check each cohort's
`support.json` for `status: ready` first. Raw unfiltered exports are transport
artifacts and must not be used for the primary experiment.
The command above demonstrates native CLI compatibility and uses SynPlanner's
internal split. For the experiment, use the implemented Retrocomposite
[grouped split and seed-controlled trainer](TRAINING.md), which freezes explicit
assignments under `data/splits/` and saves runs under `outputs/training/`.
Freeze production validation/seed/hardware settings before long training.
Full model training is not part of project setup.

## Environment reproducibility

`scripts/setup_environment.py` creates a new environment from the committed,
hash-verified RouteInspector and SynPlanner installation-source archives. It
installs `SynPlanner[all]`, overrides RouteInspector's SynPlanner Git pin with
that exact bundled source, and constrains other dependencies to the saved pins.
It verifies package consistency and imports/configuration. The original source
receipt and lock stay unchanged; actual installation metadata is saved inside
the new environment and copied into subsequent training runs.

See [mobility](MOBILITY.md) for reconstruction, source-only verification,
per-platform dependency refresh, and Hugging Face transfers. The dependency pins
were verified on macOS arm64; other platforms need their own installation and
accelerator checks.

Use `--workers 1` for single-step extraction with this pinned SynPlanner source.
Its multiprocessing initializer cannot deserialize the functional-group query
objects in this profile. Sequential extraction preserves the same chemistry and
passes the native validation checks; the failed parallel attempt published no
partial dataset.
