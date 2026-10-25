# Shared-tactic selection and experimental cohorts

Run with the Retrocomposite environment active. This is a read-only consumer of
RouteInspector publications; it does not merge routes, rebuild libraries, fit
models, or change the n1+n5 single-step corpus and union stock.

```sh
retrocomposite select-cohorts \
  --n1 ../route-inspector/data/clean/n1_routes.json \
  --n5 ../route-inspector/data/clean/n5_routes.json \
  --n1-reference ../route-inspector/outputs/reference_libraries/n1 \
  --n5-reference ../route-inspector/outputs/reference_libraries/n5 \
  --n1-composites ../route-inspector/outputs/composite_libraries/n1-retrocomposite-v3-20261025 \
  --output data/cohorts
```

The same arguments work with `python scripts/select_cohorts.py`. Paths above are
the currently selected publications. The n1 identity-v3 library is built, but
three n5 source inconsistencies currently block a complete E3 index. Resolve the
[input-readiness findings](DATASET_READINESS.md) before rerunning full selection;
the published input audit is not a completed occurrence-selection audit.
The output directory
must be new. The n1 composite publication must use identity version 3. Reference
tactic identity has its own version namespace: both reference libraries must
use compatible profiles and the same tactic identity version. All library
artifacts are verified and their source hashes/route rosters checked against
the cleaned JSON. n5 composites are not imported.

## Selection semantics

Shared `rrseq_cons` tactics are matched using RouteInspector's native complete
identity equivalence. Lookup hashes locate candidates; neither hash equality,
dataset-local entry IDs, nor literal SMARTS equality determines sharedness.
Only certified n1 links provide executable variants, products, and decompositions.

For every certified n1 occurrence/variant link, record all applicable reasons:

- **E1_SHARED_FINAL_TARGET:** remove every occurrence in an n1 route whose final
  target equals an n5 target, even if the occurrence starts internally.
- **E2_SHARED_MOTIF_INPUT:** remove an occurrence whose input equals any n5 root
  or internal nonterminal molecule, regardless of its rule label or stock flag.
- **E3_SHARED_CONCRETE_SEGMENT:** remove an occurrence containing a concrete
  consecutive n5 multistep segment, including one embedded inside a longer tactic.
- **NOT_SHARED_TACTIC:** the abstract tactic is absent from the shared vocabulary.

Molecular keys ignore stereo and atom-map numbering and retain isotope and charge.
The n5 reference sets cover all cleaned evaluation routes, not only shared tactics.

E3 indexes every adjacent pair in n5. This is exhaustive for the exclusion rule:
every repeated segment of two or more consecutive reactions contains a repeated
adjacent pair. A graph comparison preserves both full reaction sides, intermediate
states, component membership, intra-reaction atom correspondence, and continuity
between steps. All exact alignments of the intermediate are considered, including
symmetry-related alignments. The two reactions may have independent atom-map
namespaces. Participating reactants and their multiplicity are retained; middle-field
reagents are ignored. This is exact comparison of the cleaned representation,
not a tautomer or patent-family equivalence procedure.

`--max-alignments 256` is the default bound per pair. A truncated enumeration,
invalid selected path, inconsistent route chemistry, or unresolved comparison
is an audit error and cannot make a candidate eligible. If a definite exclusion
is also known, the status is `excluded` and its errors remain recorded. Otherwise
the status is `quarantined`. An incomplete n5 reference index blocks the entire
primary cohort because absence of overlap can no longer be established.

## Patent-disjoint sensitivity cohort

Apply the patent filter to primary survivors. Source IDs are read through
RouteInspector's PaRoutes adapter, which preserves original IDs behind generated
preprocessing split nodes. Normalize the publication ID by uppercasing and removing
whitespace, slashes, and hyphens. Retain any supplied publication kind code.
Policy `paroutes-document-identifiers-including-legacy-us-reissue-sir/2` accepts
legacy US grants without kind codes and RE/H number prefixes, preserving the
literal normalized ID without inventing suffixes or merging patent families.
All 20,000 selected routes now have recognized provenance. Missing or
unrecognized IDs are unresolved; a route can carry several patents, and any
intersection with n5 excludes the whole route's composite evidence.

Unknown n1 patent provenance quarantines that route from the sensitivity cohort.
Unknown n5 patent provenance blocks usable sensitivity assets for the fixed n5
evaluation set. Resolving provenance is required before claiming disjointness;
the command does not silently shrink n5. Primary selection can still succeed.

## Published artifacts

| File | Contents |
| --- | --- |
| `selection.json` | Policy versions, configuration, cohort status, counts, coverage, exclusions and unresolved provenance totals. |
| `shared_tactics.json` | Exact shared identities, n1/n5 entry membership, and n5 occurrence evidence used for coverage only. |
| `occurrence_audit.jsonl` | Every certified n1 link's primary/sensitivity decision, all exclusion reasons, n5 witnesses, and comparison errors. |
| `route_audit.jsonl` | Original source/route IDs, normalized and raw patent provenance, unresolved IDs, and shared-patent witnesses. |
| `n5_molecule_index.jsonl` | Frozen target and model-input keys with occurrence witnesses. |
| `n5_segment_index.jsonl` | Concrete adjacent-pair context and source paths; exact chemistry is reconstructible from hashed input files. |
| `reference_errors.jsonl` | n5 reference failures that prevent complete indexing. |
| `preparation.json` | All input hashes, software versions, selector/comparator code hashes, and recursive output hashes. |
| `primary/` and `patent_disjoint/` | Separately rebuilt eligible training assets and support manifests. |

A ready cohort contains `composite.tsv`, `composite_policy_data.tsv`, its native
SynPlanner rule manifest, `composite_records.jsonl`, and `support.json`. The
records preserve only retained n1 decompositions. `support.json` lists surviving
occurrences for each tactic/variant, dropped shared tactics, and n5 coverage.
A variant remains when any independent eligible n1 occurrence supports it.
Policy rows deduplicate exact product/rule pairs; rule popularity is the number
of unique training pairs. Occurrence counts remain separate for later prior
choices. No prior calibration or train/validation splitting is performed by selection;
use the subsequent [grouped split command](TRAINING.md).

Counts in the main audit are per certified occurrence/variant link. Reason counts
overlap; `reason_combinations` and cohort status counts expose their union without
double-counting removals. `unique_occurrences` supplies the occurrence denominator.
Patents are publication IDs, not inferred patent families. Report vocabulary and
coverage losses when comparing the primary and sensitivity models.

`support.json` has one of three cohort statuses:

- `ready`: usable, nonempty training assets were exported and validated with
  SynPlanner's loader and QueryCGR encoder.
- `empty`: the audit completed but no eligible supervision remains; no training
  TSV is written.
- `blocked`: reference completeness or n5 patent provenance prevents a claim
  of eligibility/disjointness; audits are written, but that cohort has no training TSV.

The CLI prints both statuses and exits with code 2 if either cohort is blocked.
An empty cohort is an audited result, not a trainable model. Existing outputs are
never overwritten; do not consume a directory containing `INCOMPLETE`.

## Validation and next stage

Tests cover native identity matching, a real tiny certified-library-to-CLI run,
whole-route/internal exclusions, embedded concrete segments, map/stereo
invariance, atom correspondence differences, symmetry limits, support rebuilding,
patent ancestry, unknown provenance, deterministic output, and source mismatches.
The synthetic transport fixtures are not claims about production data chemistry.

After reviewing audits from the refreshed publications, create grouped validation
splits only within each eligible cohort. Use the shared single-step checkpoint,
the same n5 targets, and union stock for primary and sensitivity planning.
See the [preparation](diagrams/preparation.md), [training](diagrams/training.md),
[planning](diagrams/planning.md), [post-processing](diagrams/postprocessing.md),
and [analysis](diagrams/analysis.md) diagrams for the remaining workflow.
Cohort assets and selection audits stay under `data/cohorts/`; results from
training onward follow the [outputs layout](../outputs/README.md).
