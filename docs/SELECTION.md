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
  --n1-composites ../route-inspector/outputs/composite_libraries/n1 \
  --output data/releases/n1-n5-composites-inchi-v1/cohorts
```

The same arguments work with `python scripts/select_cohorts.py`. Paths above are
the currently selected publications. The n1 identity-v3 library is built and
the InChI-based n5 reference index passes all 10,000 routes. The original public
input audit incorrectly attributed three comparison false positives to source
inconsistency; see the [correction](MOLECULE_IDENTITY.md). Full occurrence
selection and both cohort exports are complete; see [verified results](COHORT_RELEASE.md). The output directory
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

Molecular keys are full stereo-free Standard InChIs from Chython. They ignore
atom maps, keep InChI charge/protonation and isotope layers, and normalize
supported tautomers. See the versioned [identity policy](MOLECULE_IDENTITY.md).
The n5 reference sets cover all cleaned evaluation routes, not only shared tactics.

E3 indexes every adjacent pair in n5 using
`ordered-stereo-free-inchi-reaction-pair/1`. Each reaction is represented by its
product InChI and sorted **multiset** of all participating reactant InChIs.
Duplicates remain in the tuple. Side roles and root-to-leaf reaction order are
preserved; middle-field reagents are ignored. The selected intermediate is the
second reaction's product and must connect the actual route nodes. Every repeated
sequence of two or more reactions contains a repeated adjacent pair, so a pair
match anywhere inside the candidate occurrence is sufficient for exclusion.

The stable reason code `E3_SHARED_CONCRETE_SEGMENT` now means equality under this
signature policy. It does not require identical bond-state graphs or atom
correspondence. This conservative definition also excludes supported tautomer
variants and mapping variants with the same ordered molecular signatures.

Exact graphs are retained **only for auditing** each signature-match witness:
`exact_graph_audit.status` is `match`, `different`, or `unresolved`. The graph
comparison uses exact NetworkX VF2 matching with every atom and bond label
preserved. It preserves full reaction states and correspondence, enumerating all
exact intermediate alignments up to `--max-alignments 256`. Truncation and graph
comparison errors are recorded as unresolved diagnostics, never as a reason to
retain or quarantine an already matching occurrence. Summary counts are per
occurrence/variant-link witness, not unique chemical pairs.

Invalid selected paths, inconsistent route chemistry, or failed InChI generation
are eligibility errors. Known exclusions still give status `excluded`; otherwise
the candidate is `quarantined`. An incomplete n5 signature index blocks the entire
primary cohort because absence of overlap cannot be established.

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
| `occurrence_audit.jsonl` | Every certified n1 link's primary/sensitivity decision, all exclusion reasons, n5 witnesses, graph diagnostics, and eligibility errors. |
| `route_audit.jsonl` | Original source/route IDs, normalized and raw patent provenance, unresolved IDs, and shared-patent witnesses. |
| `n5_molecule_index.jsonl` | Frozen target and model-input keys with occurrence witnesses. |
| `n5_segment_index.jsonl` | Ordered InChI reaction-pair signatures and source paths; exact chemistry is reconstructible from hashed input files. |
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
invariance, signature matches despite atom correspondence differences, audit-only symmetry limits, support rebuilding,
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
