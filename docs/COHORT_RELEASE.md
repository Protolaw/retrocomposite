# Composite cohort release

The [verified composite release](https://huggingface.co/datasets/Protolaw/retrocomposite-data/tree/e4e575d7a9e066eca65f43fc3fde5b905b0cf309/releases/n1-n5-composites-inchi-v1) is **`n1-n5-composites-inchi-v1`**, pinned at
`e4e575d7a9e066eca65f43fc3fde5b905b0cf309`. It contains both composite cohorts, unchanged single-step data and
union stock, new InChI-grouped splits, and complete selection/support audits.
All 62 payload files passed anonymous download and SHA-256 checks; all three
relocated splits loaded successfully. The full code suite passes 80 tests.

| Cohort | Rules | Product/rule pairs | Train | Validation |
| --- | ---: | ---: | ---: | ---: |
| Single-step | 11,209 | 57,381 | 51,642 | 5,739 |
| Primary composites | 3,185 | 4,232 | 3,809 | 423 |
| Patent-disjoint composites | 2,322 | 2,988 | 2,689 | 299 |


## Frozen selection

The selected standalone n1 identity-v3 publication supplies 13,121 certified
linear occurrence/variant links. Native tactic comparison identifies
5,239 shared linear tactics before occurrence exclusions.
Only eligible n1 evidence supplies composite products, variants and decompositions.
The primary cohort retains 4,243 links supporting 2,221
tactics and 3,185 variants; the patent-disjoint sensitivity cohort
retains 2,996 links, 1,663 tactics and 2,322 variants.
Primary support covers 4,890 n5 routes with a matching retained
tactic; sensitivity support covers 4,311. These are repertoire
coverage counts, not planning solve rates.

Policy `retrocomposite-cohort-selection/3` uses stereo-free Chython Standard InChI
for E1/E2 and `ordered-stereo-free-inchi-reaction-pair/1` for E3. Each reaction
signature preserves its product, complete reactant multiset and side roles;
pairs preserve root-to-leaf order. Any matching embedded pair excludes its n1
occurrence. Exact graph matches are auditing only and never override E3.

Exclusion counts per certified link (overlapping):

- `E1_SHARED_FINAL_TARGET`: 3,684.
- `E2_SHARED_MOTIF_INPUT`: 4,499.
- `E3_SHARED_CONCRETE_SEGMENT`: 4,679.
- `NOT_SHARED_TACTIC`: 4,312.

Primary statuses: `{'eligible': 4243, 'excluded': 8878}`. Sensitivity statuses:
`{'eligible': 2996, 'excluded': 10125}`. Links with eligibility errors: 1.
Exact graph audit witness counts: `{'different': 1, 'match': 7098}`.
Witness counts may repeat a chemical pair across links and are not unique-pair counts.
The full n5 index covers 10,000 routes and
28,958 adjacent pairs, with zero reference errors.
All selected source routes have complete recognized patent-document provenance;
patent-family identity is not inferred.

The one eligibility error concerns n1 route 434, already excluded by E1/E2.
Its recorded route and library motif inputs agree. Existing model-input
canonicalization changes a keto/enol tautomer that Standard InChI distinguishes;
this prepared example enters neither cohort. Its E3 assessment is unresolved,
not a negative overlap finding. The diagnostic is retained in the audit.

All retained primary links were rechecked against the published E1/E2/E3 indexes.
Both composite TSVs pass SynPlanner rule loading, QueryCGR encoding and molecule
graph construction with zero dropped/reordered rows. Source, implementation and
output hashes are in the manifests and
[verification receipt](../environment/composite_release_verification.json).

## Splits and limitations

All three splits use seed 42, molecule-plus-route connected components and a
requested 10% holdout. Every rule retains training support. All splits have zero
InChI-molecule, route and group overlap. Rules without validation examples:

- `patent_disjoint`: 2,089; 2,245 groups; largest 9 rows.
- `primary`: 2,867; 3,133 groups; largest 10 rows.
- `single_step`: 9,236; 14,832 groups; largest 54 rows.

These coverage limits need review before model selection. The new single-step
assignments replace the old SMILES grouping for this experiment; the single-step
rules/rows and stock remain byte-identical. Two previously normalized keto/enol
products have different Standard InChIs; their native rows and normalization
ledger establish provenance, while grouping uses the actual model input.

The benchmark intentionally exposes n1+n5 elementary reactions and uses n5 to
select shared tactics. It is not an unseen-molecule PaRoutes benchmark.
The inferred tautomer-only step and unresolved final-cyclization split in route
9035 remain a separate chemical-step granularity question. No production model
training or planning has run.

## Download and train

After installing the portable environment:

```sh
python scripts/hub_artifacts.py download --kind dataset \
  --release n1-n5-composites-inchi-v1 --revision e4e575d7a9e066eca65f43fc3fde5b905b0cf309 \
  --output data/releases/n1-n5-composites-inchi-v1
retrocomposite train --split data/releases/n1-n5-composites-inchi-v1/splits/primary \
  --config configs/mhn_querycgr_gps.yaml --seed 17 --accelerator cpu \
  --output outputs/training/primary/seed_17
```

Use `splits/single_step` or `splits/patent_disjoint` for the other models.
Seed 17 and CPU above are an example; choose the model-seed list and accelerator
before production fitting. Training outputs remain under `outputs/training/`.

The release includes `cohorts/primary/composite.tsv` and
`composite_policy_data.tsv`, the corresponding `patent_disjoint/` files,
`composite_records.jsonl` with certified n1 provenance/decompositions, support
manifests, all cohort audits and portable split snapshots.

## Correction of the historical public audit

The source-error interpretation in `audits/n1-n5-input-readiness-v1` was incorrect.
The three reported n5 precursor mismatches were caused by asymmetric extra
canonicalization in Retrocomposite. Recorded mapped precursors matched their
route children. Chython-generated stereo-free InChIs resolve those comparisons;
no input repair was needed. The new release supersedes that diagnosis and
records successful indexing and full cohort selection with unchanged sources.
Historical files and their immutable revisions remain available.
