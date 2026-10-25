# Questions to resolve

Updated: 2026-10-25. Confirmed choices are in PLAN.md; do not ask them again.

## Input choice resolved

Use the existing `route-inspector/data/clean/n1_routes.json` and `n5_routes.json`,
as explicitly selected on 2026-10-25. Their hashes begin `c1e396cd` and `5a27be2e`.
The alternate missing `source_corrected_20261021` files are not a prerequisite.
Both reference libraries match the selected files, and the identity-v3 n1
composite publication is built. n5 composite rules are not needed for overlap
selection. The detailed input audit is approved for public publication and is
published with checksum verification. See [readiness](docs/DATASET_READINESS.md).

## Blocking composite preparation

1. **Which source-chemistry policy should reconcile the three n5 precursor
   mismatches?** Routes 3032 and 9035 contain three mapped reactions whose
   precursor representations disagree with their route-tree children. They
   appear tautomer-related, but the agreed identity policy only ignores stereo.
   Recommended: resolve the witnesses in RouteInspector with a documented
   choice of authoritative representations, certify consistency, publish matching
   source/library versions, and then rerun selection and affected preparation.
   No routes have been dropped, no tautomer-equivalence rule has been added,
   and the chosen source files remain unchanged. Both composite cohorts are
   blocked until a complete n5 E3 reference index is available.

## Before training and hybrid planning

2. **Production validation settings and seed budget?** The grouped splitter and
   seeded trainer are implemented. Defaults are molecule-plus-route components,
   a 10% requested holdout, and split seed 42; patent grouping is available and
   blocks incomplete provenance. The published single-step split has 14,832
   groups (largest 54 rows), 51,642 train / 5,739 validation rows, and no partition
   overlap. However, 9,267 of 11,209 rules have no validation examples. Review
   that coverage, then freeze settings and the model-seed list. Reuse each
   frozen split across model seeds; composite development data remains n1-only.
   See [training details](docs/TRAINING.md).
3. **Top-50 split and primary cost endpoint?** Initial proposal 40/10; ablations
   45/5 and 25/25. Choose neural evaluations and/or end-to-end time, with solve
   rate reported alongside either.
4. **Non-stock components exposed by unwrapping?** Proposed first version:
   invalidate that candidate. A later completion-search variant should charge
   every extra neural call and chemistry operation. Membership is checked
   against the agreed union of cleaned n1+n5 leaves.
5. **Composite repertoire versus step compression?** Should primary composites
   require all constituent elementary rules to exist in the single-step
   vocabulary, or should this be a reported subset/ablation?
6. **Runtime resources?** Training accelerator, memory, target-level compute
   budgets, and number of model/search seeds determine final configuration.

## Already settled

- Primary composite exclusions: E1 removes all occurrences from n1 routes with
  an n5 final target; E2 removes occurrences with an n5 root/internal nonterminal
  motif input, regardless of label; E3 removes occurrences containing an exact
  concrete n5 multistep segment, including embedded segments of at least two
  reactions. Compare stereo-free identities independently of atom-map numbers.
- Apply exclusions to composite training and validation examples, variant and
  decomposition support, counts, and frequency priors. Keep variants only with
  surviving n1 support; drop unsupported tactics. The n1+n5 single-step corpus
  and union leaf stock remain unchanged.
- Patent-disjointness is an additional sensitivity analysis: remove n1 routes
  sharing a patent with n5 on top of E1-E3, then retrain the composite model.
  Freeze cohort decisions before training and report lost support and coverage.

- Composite vocabulary: linear consecutive tactics shared by n1 and n5,
  retaining tactics with eligible certified n1 supervision after exclusions.
  This deliberately uses n5 route information for vocabulary selection.
- Composite training: eligible n1 motif targets, including internal molecules
  and root targets. For `T -> A -> B -> C`, a composite covering `A -> B -> C`
  trains on A. Products, executable variants, and decomposition alternatives
  come from eligible n1 occurrences only.
- Planning stock: the deduplicated stereo-free union of terminal leaves from
  cleaned n1+n5 JSON, identical in both arms.
- Separate project and environment; no preset models; single-step training on
  n1+n5; MHN with QueryCGR-rule graphs and GPS molecule encoding; ignore stereo;
  library rebuilding in RouteInspector; hybrid implementation on a new
  SynPlanner branch.
