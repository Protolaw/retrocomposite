# Mapping-equivalent composite merge — 2026-10-26

The completed local bundle is `data/composite_mapping_merged_v1/`.
It was rebuilt from `data/composite_popularity_v1/` with
`scripts/merge_composites.py`; original datasets and published releases remain
available. Preparation/reproduction instructions are in [PREPARATION.md](PREPARATION.md).

| Cohort | Rules before → after | Pairs before → after | Preserved occurrences | Final replay |
| --- | --- | --- | --- | --- |
| Primary | 3,185 → 2,094 | 4,232 → 4,225 | 4,243 | 4,224 pass; 1 no outcomes |
| Patent-disjoint | 2,322 → 1,555 | 2,988 → 2,984 | 2,996 | All 2,984 pass |

Pair counts fall only when the same prepared target previously carried multiple
mapping-equivalent labels. No source occurrence, variant, certificate or tactic
decomposition was removed. All exported identities used exact canonical graph
certificates; none required fallback to exact SMARTS.

The originally reported patent-disjoint rows 0, 2, 8, 82, 208, 860 and 1010 now
share **rule 0**, with **49 unique targets**, **seven exact variants** and
**nine tactics**. Each original variant remains in `composite_records.jsonl`;
`composite_rule_mapping.json` indexes them under the merged label. No certificate
is reassigned from an original variant to a different representation.

The comparison with `data/diagnostics/final-pairs-reaction-aware-v3-20261026/`
verified every original target and expected precursor multiset. At occurrence
level, primary has 4,242 pass→pass and one no-outcomes→no-outcomes; patent-disjoint
has 2,996 pass→pass. **There are no new replay failures.** The remaining primary
failure is n1 route 166, target `c1ccccc1C(F)(F)C(NO)=N`. Primary remains blocked
for training pending the already identified upstream recertification. Direct
net-precursor replay does not certify ordered tactic unwrapping.

Both splits retain seed 42, route grouping with stereo-free InChI molecule
components, and a requested 10% validation fraction. Primary has 3,802 train /
423 validation pairs; patent-disjoint has 2,686 / 298. All molecule, route and
group overlaps are zero. Connected components are unchanged, but merging labels
relaxes training-coverage constraints: primary moves 220 old pairs in each
direction; patent-disjoint moves 164 train→validation and 165 validation→train.
These transition counts use original pair rows, before pair deduplication.

Use the new `splits/{primary,patent_disjoint}` together with their vocabulary
snapshots. Old checkpoint labels and cached rule encodings are incompatible.
The rule-analysis notebook now points at the merged patent-disjoint vocabulary;
rerun it to render new rule IDs and counts.

Evidence:

- `data/composite_mapping_merged_v1/merging.json`: old-to-new IDs/pair indices,
  preservation checks, split transitions, and replay summaries.
- `data/composite_mapping_merged_v1/replay/{primary,patent_disjoint}/`: every
  final pair, every occurrence boundary, failures and hashed manifests.
- `data/composite_mapping_merged_v1/implementation/`: exact code used for the
  rebuild and audits.
- `data/diagnostics/composite-mapping-merged-v1-verification/verification.json`:
  independent comparison with the previous audits, plus its executable verifier.

The unchanged `selection.json`, `support.json` and `vocabulary_reordering.json`
in the rebuilt cohorts are historical source-selection evidence. Their original
rule/pair counts describe exact variants before this merge. The current training
counts are in `merging.json`, cohort `preparation.json`, and the new vocabularies.
Fresh cohort selection now reports merged training counts and separate exact
variant counts.
