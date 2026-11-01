# Preparation commands and contracts

Workflow: [preparation diagram](diagrams/preparation.md). For the final
experimental cohorts, use [shared-tactic selection](SELECTION.md).

Run from the Retrocomposite project after `conda activate retrocomposite_env`. Inputs are read-only;
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

This normalizes every mapped reactant, product and reagent after removing
stereo **before extracting rules**. Policy:
`stereo-free-complete-reaction-before-extraction/1`. A separate reaction-aware
extraction policy, `source-unchanged-tautomer-alignment-with-replay/1`, aligns
normalization-only spectator tautomers to the prepared product representation.
It preserves every source reaction edit and accepts only hydrogen-conserving
single/double bond shifts with unchanged Standard InChI and normalized mapped
graphs. A serialized-rule replay must recover the exact prepared precursors.
Rejected proposals keep the fully normalized reaction.

Deduplication retains the existing normalized reactant/product multisets for
unaffected reactions. Accepted alignment views also enter the duplicate key,
so distinct extraction views cannot be silently merged. Multiplicity and every
original source occurrence are preserved. Reagents remain excluded from the duplicate key, matching
`keep_reagents: false`. Native SynPlanner performs rule extraction.

`reaction_provenance.jsonl` retains the prepared extraction reaction and each
original mapped source reaction. Every occurrence retains `original_mapped`,
`normalized_mapped` and `extraction_mapped`; `mapped` is the selected extraction
representative. The replay reference always uses `normalized_mapped`, including
when the extraction view aligns a different tautomer. `reaction_alignment.jsonl`
records proposed, accepted and rejected alignments with bond changes and replay
evidence. `reaction_normalization.jsonl` records changed
occurrences and before/after stereo-free InChIs. Existing unsupported source
valences are preserved for diagnosis; normalization must not introduce new
valence errors or change heavy-atom map/isotope inventory.

Final policy serialization still has a native copy and change ledger. Every
exported product/rule pair must then pass the actual SynPlanner reactor against
**every supporting expected precursor multiset**, after uniform preparation.
The audit also checks molecule graph loading, repeated normalization, encoder
canonicalization and one deterministic atom-renumbering probe. This is an
executability check, separate from the agreed InChI leakage exclusions.

The audit defaults to `<output>.replay-audit/`; override it with `--audit-output`.
It contains `summary.json`, all `pairs.jsonl`, and `failures.jsonl`, with input
and implementation hashes. A blocked audit preserves diagnostic assets under
`<output>.candidate/` with `INCOMPLETE`; it does not create the requested training
dataset or silently remove examples. A passing audit is copied into the finished
dataset under `replay_audit/`. Always choose new output paths.

Outputs include `single_step.tsv`, `single_step_policy_data.tsv`, native rule
metadata, source/normalization evidence, replay evidence, and `preparation.json`.
Never consume a directory containing `INCOMPLETE`. See
[normalization and replay results](NORMALIZATION_REPLAY.md).

## Audit existing final training pairs

```sh
retrocomposite audit-pairs \
  --assets data/single_step \
  --output data/diagnostics/single_step_final_pairs

retrocomposite audit-pairs \
  --assets data/cohorts/primary \
  --output data/diagnostics/primary_final_pairs
```

Run the same command on `data/cohorts/patent_disjoint/`. The audit is read-only
with respect to its inputs and returns a nonzero exit status if any pair fails.
For single-step rules, the expected boundary follows native spectator removal.
For composites, it uses the explicit certified `synplanner_net_reactants_v1`
retained components. This audits **direct composite application**; ordered
unwrapping still requires the separate post-processing implementation.

Default diagnostic limits are 100 outcomes and 100,000 mapping-work units per
pair (`--max-outcomes`, `--max-mapping-work`). A missing precursor match after a
limit is reached is inconclusive, not proof that the chemistry is impossible.
Finding the expected set is an existential replay witness, not a guarantee that
it appears within a smaller planning-time outcome budget.

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
  --composite-library ../route-inspector/outputs/composite_libraries/n1 \
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
shared motif inputs, and ordered InChI reaction-signature sequences, including
embedded pairs. Exact graphs are auditing only. Derive the additional patent-disjoint cohort from those survivors.
Rebuild all composite support and supervision from each eligible cohort.
Use the implemented `select-cohorts` command described in [SELECTION.md](SELECTION.md)
to perform that selection. This raw export command does not filter a cohort. Use n5 only for tactic-overlap
selection, frozen exclusion checks, and evaluation, never as a source of
composite training examples or
decomposition alternatives.

Outputs are `composite.tsv`, `composite_policy_data.tsv`, vocabulary and
preparation manifests, `composite_rule_mapping.json`, and
`composite_records.jsonl`. Occurrence records retain the **original certified
mapped SMARTS**, certificates, variant IDs, tactic IDs and complete decomposition
payloads. Their `rule_id` selects the equivalent training representative;
`training_rule_identity` records its stable identity.

Training labels merge mapping-equivalent queries under
`joint-query-correspondence-and-patterns/1`. One exact labelled graph includes
both query sides, cross-side atom correspondence, full atom/bond predicates,
side-only atoms and membership in each input/output pattern. Atom numbers,
traversal and pattern order do not affect identity. Different correspondence,
query constraints, component multiplicity or pattern grouping remain distinct.
Unsupported query predicates fall back to exact SMARTS identity. This uses
Chython and the pinned RouteInspector graph canonicalizer; it does not alter
RouteInspector's broader identity-v3 families or the InChI leakage exclusions.

Each training representative is the lexicographically smallest eligible exact
variant in its mapping-equivalent group. Popularity counts unique prepared
product/merged-rule pairs; duplicate occurrence evidence does not inflate it.
Sort by descending popularity, breaking ties by representative SMARTS, then
assign all rule labels and pair indices. `composite_rule_mapping.json` records
the full identity encoding and every eligible original variant with its source
family/tactic IDs. The representative is replayed against every supporting
occurrence's certified net-precursor boundary; its use does not transfer an
original variant's certificate or certify ordered unwrapping.

To merge both audited cohorts, regenerate matching grouped splits, and rerun
complete replay audits:

```sh
python scripts/merge_composites.py \
  --cohorts data/composite_popularity_v1/cohorts \
  --splits data/composite_popularity_v1/splits \
  --output data/composite_mapping_merged_v1
```

The new bundle contains `cohorts/{primary,patent_disjoint}`, matching `splits/`,
`replay/`, an implementation snapshot, and `merging.json`. It verifies that no
original occurrence, variant, certificate, decomposition or mapped-query/product
support was lost. The report records old-to-new rule IDs and pair indices,
source/output hashes, replay outcomes and split transitions. Original source
selection audits and `support.json` remain unchanged evidence about occurrences,
tactics and source families; use `merging.json` for new training-label counts.
The copied `vocabulary_reordering.json` is historical source-bundle metadata.

Splits reuse the source seed, grouping and requested validation fraction. Whole
molecule/route components remain intact, but their partitions may change because
merged labels change coverage constraints. Every transition is reported and
leakage overlaps must remain zero. A blocked replay still saves the complete
bundle and exits with status 2; inspect `merging.json` and `replay/*/summary.json`
before training. `INCOMPLETE` indicates an interrupted build. Existing model
weights and cached encodings remain tied to the old ordered vocabulary.

The historical `scripts/reorder_composites.py` explicitly retains exact variant
labels and only changes ordering. Use the merge command above for new training
assets. No source library or published release is overwritten.

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

Create `retrocomposite_env` with `environment/conda.yml`, activate it, then run
`python scripts/setup_environment.py --active-conda`. The installer uses the
committed, hash-verified RouteInspector and SynPlanner installation-source archives. It
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
