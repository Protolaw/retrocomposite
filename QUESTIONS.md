# Questions to resolve

Updated: 2026-10-28. Confirmed choices are in PLAN.md; do not ask them again.

## Input choice resolved

Use the existing `route-inspector/data/clean/n1_routes.json` and `n5_routes.json`,
as explicitly selected on 2026-10-25. Their hashes begin `c1e396cd` and `5a27be2e`.
The alternate missing `source_corrected_20261021` files are not a prerequisite.
Both reference libraries match the selected files, and the identity-v3 n1
composite publication is built. n5 composite rules are not needed for overlap
selection. Both composite cohorts, frozen splits and the corrected input audit
are public and verified. See [results](docs/COHORT_RELEASE.md).

## Preprocessing interpretation

1. **How should the inferred tautomer-only step in route 9035 be treated when
   interpreting tactics and chemical depth?** The three previously reported
   precursor mismatches were comparison false positives, now resolved with
   stereo-free Chython InChI. No precursor repair is required for those cases.
   Separately, preprocessing split one recorded nitro reduction into an inferred
   tautomer-change step and reduction; it also retained an unresolved split at
   the final cyclization. Review these granularity artifacts upstream before
   claiming that every cleaned step is an independently recorded transformation.

## Before training and hybrid planning

2. **Production validation settings and seed budget?** The grouped splitter and
   seeded trainer are implemented. Defaults are molecule-plus-route components,
   a 10% requested holdout, and split seed 42; patent grouping is available and
   blocks incomplete provenance. The new InChI single-step split has 14,832
   groups (largest 54 rows), 51,642 train / 5,739 validation rows, and no partition
   overlap. However, 9,236 of 11,209 rules have no validation examples. Both
   composite splits are now published; review their [coverage](docs/COHORT_RELEASE.md),
   then freeze settings and the model-seed list. Reuse each
   frozen split across model seeds; derive popularity settings from common
   within-cohort assignments, without reshuffling. Review the resulting retained
   holdouts before freezing settings; composite development data remains n1-only.
   See [training details](docs/TRAINING.md).
3. **Top-50 split and evaluation limits?** Initial proposal 40/10; ablations
   45/5 and 25/25. Freeze numerical call/time limits, budget checkpoints and replay
   enumeration caps on development data. Both actual neural forwards and
   end-to-end time (including replay) are required endpoints, with validated
   solve rate and source RouteCGR recovery reported against each.
4. **Non-stock components exposed by unwrapping?** Proposed first version:
   invalidate that candidate. A later completion-search variant should charge
   every extra neural call and chemistry operation. Membership is checked
   against the agreed union of cleaned n1+n5 leaves.
5. **Composite repertoire versus step compression?** Should primary composites
   require all constituent elementary rules to exist in the single-step
   vocabulary, or should this be a reported subset/ablation?
6. **Runtime resources?** Training accelerator, memory, target-level compute
   budgets, and number of model/search seeds determine final configuration.
7. **Exact RouteCGR order policy?** Proposed primary recovery uses the full ordered
   history, with order-agnostic equivalence as a separate sensitivity. Freeze
   handling of interchangeable branch serialization before n5 evaluation; neither
   net-CGR nor SB-CGR equality is a substitute for full source-route recovery.
   See [evaluation specifications](docs/EVALUATION.md).

## Residual replay failures

- Determine the treatment of the remaining 124 existing execution/representation
  failures, including source precursors unsupported by the pinned engine.
  Normalization/re-extraction is the adopted first repair; no blanket removal
  of rows, rules or evaluation targets has been authorized.
- The n1 route 166 primary composite needs upstream recertification for its
  prepared amidoxime input. Keep it blocked rather than silently substituting
  a hand-edited rule. Direct replay success does not certify unwrapping.

## Already settled

- Evaluate model-call efficiency and total inference-pipeline time including
  tactic replay, validation and deduplication, alongside stock-reaching solve rate
  and source RouteCGR recovery. SB-CGR diversity is supplementary. Alternative
  validated routes remain successful even without a source match.

- Handle normalization-only remote tautomer edits with a reaction-aware
  extraction view, preserving source reaction changes and normalized replay
  references. Accept only identity-preserving, graph-preserving alignments with
  successful serialized-rule replay. General disconnected-query grouping remains
  a separate matcher/serialization issue; it is not changed by this repair.

- All 14 remaining normalization-related failures passed the targeted repair
  trial, as did the original two. Normalize complete mapped reactions before
  single-step extraction, and audit every final pair before replacement releases.

- Primary composite exclusions: E1 removes all occurrences from n1 routes with
  an n5 final target; E2 removes occurrences with an n5 root/internal nonterminal
  motif input, regardless of label; E3 removes occurrences containing an ordered
  InChI reaction-signature sequence shared with n5, including embedded segments
  of at least two reactions. Each step preserves product and full reactant
  multiset identities, including multiplicity. Exact reaction-state graphs and
  atom correspondence are auditing only; differences or unresolved graph audits
  cannot override an E3 signature match.
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

- Molecule identity checks use Chython-generated stereo-free Standard InChI.
  No RDKit chemistry or depiction is used in the updated investigation.

## Composite vocabulary decision (2026-10-26)

Resolved: merge mapping-equivalent executable queries in both cohorts; retain
all original certified variants and tactic decompositions. Atom correspondence,
query constraints and molecule-pattern grouping remain significant. Rebuild
popularity, policy labels and grouped splits together; retain old-to-new mappings
and partition-transition audits. This does not change the chosen shared-tactic
scope, E1-E3 exclusions, or the patent-disjoint sensitivity definition.

## Popularity and target-population decisions (2026-10-27)

Resolved: main composite setting retains popularity >1; the additional setting
retains all rules with popularity >=1, including singletons. Cross this with
primary and patent-disjoint cohorts: four hybrids plus one shared single-step
baseline. Popularity is unique prepared target/merged-rule pairs after exclusions
and mapping-equivalent merging, computed independently from eligible n1 data in
each cohort before its holdout. It is not raw occurrence count or train-only
support; frequency priors remain training-only. Preserve eligible variants and
decompositions of retained labels. Filtering and matched split derivation remain
to be implemented; current counts are descriptive, pending recertification.

Plan all n5 final targets, including reference routes with no detected tactics.
Use reference support as secondary analysis strata, recomputed per repertoire,
with common-covered targets for direct comparisons. Do not use reference
annotations to choose targets, invoke the composite head or allocate its quota.
These decisions do not reopen E1-E3 or change single-step training or union stock.
