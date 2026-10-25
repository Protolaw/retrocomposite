---
pretty_name: Retrocomposite experiment data
tags:
  - chemistry
  - retrosynthesis
  - synplanner
  - reaction-rules
---

# Retrocomposite datasets

Prepared data for [Protolaw/retrocomposite](https://github.com/Protolaw/retrocomposite).

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


## Contents and protocol

The release contains native SynPlanner rule TSVs and corresponding product/rule
policy-data TSVs, certified composite decomposition records, occurrence/support
audits, the 20,087-molecule union leaf stock and planning targets, and all three
portable grouped train/validation splits. Composite target graphs preserve every
row and label. No trained weights are included.

Inputs are the cleaned standalone n1/n5 files selected on 2026-10-25: 10,000 routes
each, SHA-256 prefixes `c1e396cd` and `5a27be2e`. The updated standalone n1
composite library uses identity v3. Only its 13,121 certified linear links enter
selection; branched and uncertified constructions are excluded.

Composite supervision uses eligible n1 root/internal motif targets from tactics
shared with n5. E1 removes n1 routes with an n5 final target; E2 removes motif
inputs present at any n5 root/internal nonterminal node; E3 removes occurrences
containing an ordered adjacent pair of InChI reaction signatures present in n5.
Each signature retains its product, complete reactant multiset and side roles;
reactant multiplicity and reaction order matter. Middle-field reagents are ignored.
Standard InChI is stereo-free and normalizes supported tautomers. Atom-map and
exact graph-state differences do not rescue E3 matches. Exact graph comparisons
are diagnostic only: `{'different': 1, 'match': 7098}` witness statuses.
The additional sensitivity cohort excludes n1 routes sharing a patent-document
ID with n5. Patent families are not inferred.

Primary retains 4,243 certified links supporting 2,221
tactics; patent-disjoint retains 2,996 links and 1,663 tactics.
The full selection has 1 links with eligibility errors and
zero n5 reference-index errors. The single error is on already-excluded n1 route 434: source and library inputs
agree, but model-input canonicalization changes a tautomer that Standard InChI
distinguishes. It enters neither cohort. Every retained occurrence was rechecked
against the frozen indexes. Full witnesses and support losses accompany the data.

The seed-42 splits group by molecule InChI and all supporting routes. They preserve
training support for every rule and have zero molecule/route/group overlap.
Validation coverage is sparse: 9,236
single-step, 2,867 primary and
2,089 sensitivity rules have
no validation example. Review this limitation before model selection.

Single-step supervision intentionally uses n1+n5, and n5 informs the shared-tactic
vocabulary. This is a controlled action-space comparison, not an unseen-molecule
or standard held-out PaRoutes benchmark. Route 9035's inferred tautomer-only step
and unresolved cyclization split remain upstream step-granularity questions.

## Download

```sh
python scripts/hub_artifacts.py download --kind dataset \
  --release n1-n5-composites-inchi-v1 --revision e4e575d7a9e066eca65f43fc3fde5b905b0cf309 \
  --output data/releases/n1-n5-composites-inchi-v1
```

The helper in the [project](https://github.com/Protolaw/retrocomposite) verifies
all checksums and records the immutable commit. The preserved source snapshots
and setup script recreate the environment. See the
[mobility guide](https://github.com/Protolaw/retrocomposite/blob/main/docs/MOBILITY.md).
Model runs will be stored separately at
[Protolaw/retrocomposite-models](https://huggingface.co/Protolaw/retrocomposite-models).

## Correction and historical release

The source-error interpretation in `audits/n1-n5-input-readiness-v1` was incorrect.
The three reported n5 precursor mismatches were false positives caused by
Retrocomposite's asymmetric extra canonicalization; stored mapped precursors
matched their route children. Stereo-free Chython InChI resolves these checks.
The new release completes indexing and cohort selection with unchanged sources.
See the [versioned correction](https://huggingface.co/datasets/Protolaw/retrocomposite-data/tree/main/audits/n1-n5-input-readiness-correction-v2).
Historical files and immutable revisions remain available.

`n1-n5-single-step-v1` at `4ba2b7f366ea881825fbebe343ccefdd7899af42` remains the
historical single-step release. Its rules, data and stock are unchanged here,
but its version-1 SMILES split is superseded by new InChI assignments. Identical
partition sizes do not mean identical assignments.

No original source dataset license is replaced by this repository; source terms
and provenance remain applicable to each release.
