# Preparation commands and contracts

Run from the Retrocomposite project with `.venv` active. Inputs are read-only;
each output directory must be new. Production commands should wait for the
matching refreshed standalone publications. Paths below describe the expected
layout and are not evidence that those publications have been refreshed.

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
The stock scope used in planning is still a question in QUESTIONS.md.

These are pre-canonicalized files. Load with SynPlanner's
`load_building_blocks(path, standardize=False)` to preserve the declared stock
identity policy. Planning must use `stereo_mode: off` and `min_mol_size: 0`.
Stock membership describes the experimental terminal set, not commercial availability.

## Composite library adapter

```sh
python scripts/prepare_composites.py composite-library \
  --reference-library ../route-inspector/outputs/reference_libraries/n1 \
  --composite-library ../route-inspector/outputs/composite_libraries/n1 \
  --routes-json ../route-inspector/data/clean/n1_routes.json \
  --output data/composite
```

The adapter requires a standalone n1 identity-v3 composite publication, verifies
artifact hashes and the matching reference/source identities, resolves exact
certified variants, and joins each link to its motif-target molecule. It exports
only `rrseq_cons`, refuses n5/merged supervision, and preserves native
decomposition payloads. It does not rebuild or recertify libraries.

This first adapter exports all certified n1 linear occurrences. Shared-tactic
selection and cross-dataset exclusion manifests remain TODOs; do not describe
this export alone as a leakage-controlled split.

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
  --results_dir outputs/single_step --workers 1
```

The analogous composite command uses `data/composite/composite_policy_data.tsv`.
Do not start long training until validation/seed/hardware decisions are frozen.
This is the stock CLI interface: it performs SynPlanner's internal product-based
split, not an externally grouped experimental split. A seed-controlled grouped
training wrapper is explicitly unfinished. Configuration loading, rule loading,
and rule-graph encoding are checked by bootstrap/tests; full model training is
not part of project setup.

## Environment reproducibility

`scripts/setup_environment.py` creates a new `.venv`, copies package source
files to temporary build directories, installs local `SynPlanner[all]`, installs
RouteInspector while explicitly overriding its SynPlanner Git pin, and installs
this project. It then runs `pip check`, checks imports/configuration, and writes
`environment/sources.json` plus `environment/requirements.lock.txt`.

The source manifest includes exact copied-file hashes and upstream dirty status;
a Git commit alone is insufficient when local changes are present. The dependency
lock records the tested platform's installed versions, not a universal lock for
all operating systems. Reproduction needs both those dependency pins and matching
source snapshots. Review intentional upstream changes and recreate the environment
when switching to the future hybrid branch; never silently upgrade a benchmark run.
When saved environment metadata exists, setup checks the upstream source hashes
and uses the saved dependency pins as installation constraints. A deliberate
source/dependency refresh requires `--refresh-lock` and a new environment.
