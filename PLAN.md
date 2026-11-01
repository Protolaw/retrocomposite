# General experiment plan

Updated: 2026-10-29. This file records scientific decisions and architecture;
execution status belongs in TODO.md and unresolved choices in QUESTIONS.md.
Workflow diagrams: [preparation](docs/diagrams/preparation.md),
[training](docs/diagrams/training.md), [planning](docs/diagrams/planning.md),
[post-processing](docs/diagrams/postprocessing.md), and
[analysis](docs/diagrams/analysis.md). Preparation has three diagrams in the
same file: shared data preparation, primary occurrence exclusions, then composite
cohorts and vocabulary audits. Post-processing also has three diagrams: candidate
preparation, replay and reconciliation, then validation and finalization.

## Objective and interpretation

Measure whether learned linear composite actions improve validated stock-reaching
solve rate and source-route recovery over a shared single-step reaction
recommendation system (RRS), while requiring fewer actual model calls and less
end-to-end time, including tactic replay. These are hypotheses to test jointly;
report tradeoffs if gains in success require more computation. Exact RouteCGR
recovery measures reproduction of a recorded source route; other validated
stock-reaching routes remain successful solutions. SB-CGR diversity is a
supplementary analysis of the final explicit routes.

The single-step vocabulary and policy data come from reactions in cleaned n1
and n5. We intentionally accept exposure to molecules and reactions used in
planning. We train our own model and do not use pretrained presets. The main
claim is therefore a controlled comparison of planning action spaces under
shared chemical exposure, not unseen-target generalization or a standard
held-out PaRoutes benchmark result.

The composite vocabulary is restricted to linear tactics shared by n1 and n5.
Use n5 to establish tactic overlap and evaluate planning; composite training
examples and decomposition alternatives come from eligible n1 occurrences only,
including internal motif targets. This is a shared-tactic planning comparison.

Composite supervision comes from n1 only. Audit its overlap with n5 separately:
the single-step exposure is deliberate, but duplicate-route exposure in the
composite head is still a distinct confound. Report the exact composite split
policy instead of describing the entire experiment as leakage-free.

## Confirmed decisions

- Separate Git project: `projects/retrocomposite`, initially located beside the
  existing RouteInspector and SynPlanner repositories.
- New isolated environment with RouteInspector and the full `SynPlanner[all]`
  dependency set. Pin installed dependencies and record source content/revisions.
  Bundle the exact installation sources in Git, including recorded working-tree
  changes, so reconstruction does not require either original checkout.
- Use the existing `route-inspector/data/clean/n1_routes.json` and
  `n5_routes.json` selected by the user on 2026-10-25. Match libraries to those
  exact source hashes and require composite identity version 3. Library
  construction stays in RouteInspector; no rebuilding code here.
- Extract a single-step vocabulary and standard `*_policy_data.tsv` from
  cleaned n1+n5 reactions.
- MHN ranking architecture; `query_cgr_graph` rule encoding; GPS molecule
  encoder, and the supported GPS rule graph encoder.
- Adapt certified RouteInspector composites and associated motif products to
  the same SynPlanner training format, preserving executable variants.
- Linear consecutive `RRseq_cons` tactics shared by n1 and n5 only. Gapped and
  branched tactics are outside this first experiment.
- Train on eligible n1 motif targets, including internal molecules as well as
  route roots, after the three primary exclusions E1-E3 below.
- Exclude shared final-target routes, shared n5 motif inputs, and ordered InChI
  reaction-sequence overlap from all composite-derived assets.
- Run patent-disjointness as an additional sensitivity analysis.
- Main composite vocabulary: popularity >1 after exclusions and mapping-equivalent
  merging. Add an all-rules (popularity >=1, including singletons) experiment in
  both cohorts; use eligible n1 support only to calculate popularity.
- Plan all cleaned n5 final targets, including routes without detected tactics;
  reference-tactic coverage is an analysis stratum, never a target-selection gate.
- Use the union of actual terminal molecule nodes in cleaned n1+n5 JSON as
  the stock for both planning arms.
  Do not use the original PaRoutes stock files or blindly trust `in_stock` flags.
- Ignore stereochemistry in exported model inputs, reactions, targets, stock,
  and planning evaluation; keep original sources unchanged.
- Implement the future hybrid policy on a separate SynPlanner branch.

## Normalization and final-pair acceptance

Normalize complete mapped reactions after removing stereo and before single-step
rule extraction. Preserve source reactions and the normalization ledger. The
16 previously flagged rows all passed the targeted re-extraction trial; this
supports the repair but does not establish whole-corpus validity.

Use a reaction-aware extraction view when independent normalization adds a
remote proton/bond-order shift in a source-unchanged region. Preserve all
recorded source changes, the prepared target, atom maps and full normalized
source precursor references. Align only assessed single/double bond shifts
that conserve hydrogens, preserve Standard InChI and normalize back to the
identical mapped precursor graph. Accept the view only when its serialized
rule replays to the exact prepared precursors. Uncertain proposals retain
complete normalization and remain visible to the final audit. Record original,
normalized and extraction reactions separately; do not substitute rules by ID.

Before rebuilding a training release, audit every final product/rule pair
against all supporting precursor multisets through the actual SynPlanner
reactor. Keep source valence limitations, mismatches, no-outcome cases and
budget-limited cases visible. A failed audit blocks publication; do not silently
filter failures or change benchmark targets. Recompute vocabularies and grouped
splits only for accepted assets. Existing public files remain historical.

Audit composite final targets against their certified net boundaries as well.
A source certificate alone cannot validate a subsequently normalized target.
Rebuilding/recertifying composite libraries remains RouteInspector's job.
Direct replay does not replace ordered unwrapping and final stock checks.
Normalization changes do not redefine Standard InChI or E1-E3; audit any changed
model-input overlap before a replacement composite release.

See [normalization/replay evidence](docs/NORMALIZATION_REPLAY.md).

## Artifact organization

Store artifacts prepared before training in [data/](data/README.md): single-step
rules and examples, stock and targets, eligible composite cohorts with their
exclusion/support manifests, and frozen validation assignments. Upstream
RouteInspector publications remain in their existing locations and are referenced
by path and hash; library refresh remains upstream.

Store generated results in [outputs/](outputs/README.md), separated by stage:
`training/` for checkpoints, metrics, and calibration; `planning/` for MCTS
candidates and search costs; `postprocessing/` for replay, validation, and
deduplicated explicit routes; `analysis/` for comparisons, tables, figures, and
reports. Preserve run/cohort/seed identities and input hashes between stages.
Preparation audits belong with their input cohorts in `data/`; evaluation
audits belong with the relevant result stage in `outputs/`.

## Data release and provenance

Freeze matching cleaned routes, reference libraries, and composite libraries
before producing production training assets. Check file hashes, library IDs,
processing profiles, and composite identity versions. Reject version-2
composite publications rather than silently treating them as refreshed.

Single-step and stock preparation need the selected n1/n5 JSONs, but do not
depend on composite libraries. They may be published as an explicitly partial
release once those source hashes are verified. See the current
[input-readiness audit](docs/DATASET_READINESS.md) for the chosen source files
and composite prerequisites. The single-step/stock release and grouped split are
published. The n1 identity-v3 library is built. The earlier three n5 precursor
mismatches were false positives caused by asymmetric SMILES canonicalization.
Stereo-free Chython InChI identity now indexes all 10,000 n5 routes with zero
reference errors. See [identity policy](docs/MOLECULE_IDENTITY.md). The [composite release](docs/COHORT_RELEASE.md) now contains both verified cohorts
and all three InChI-grouped splits. It also corrects the historical public
source-error diagnosis. Primary: 3,185 rules / 4,232 pairs;
patent-disjoint: 2,322 rules / 2,988 pairs.

The earlier corrected merged audit recorded 2,127 duplicate routes and 2,146
shared-target pairs. Those numbers are descriptive of that release, not
guaranteed counts for refreshed standalone publications. Recompute overlap
for the selected standalone source release. Do not mix its hashes with the
alternative merged release. The selected source hashes start with `c1e396cd`
(n1) and `5a27be2e` (n5), rather than `9902ff12` and `fb8bf966` in the merged
publication's source ledger.

Every generated asset receives a manifest with input hashes, configuration,
software versions, and output hashes. Preserve dataset, route, reaction-node
path, original reaction ID, reference occurrence, composite family, exact
variant, and decomposition provenance where applicable.

Cohort selection now runs through Retrocomposite's read-only audit interface,
independently of merged-dataset publication. It uses RouteInspector's native
tactic equivalence and exact labelled-graph comparison APIs. Preserve
the original n1/n5 IDs and membership; merging and renumbering routes must not
be a prerequisite for a train/test decision. The present merger buckets targets
with stereochemistry retained, while this experiment ignores it. Therefore
compute a separate stereo-free target/model-input exclusion key; the merger's
exact-duplicate audit alone cannot establish the intended split. Report target,
exact-route, patent, reaction, tactic, and motif-input overlaps separately.

Single-step preparation deterministically deduplicates constitutional reaction
identities across n1+n5 while retaining all source memberships in a sidecar.
This avoids overweighting shared routes merely because they occur in both
files. Record this policy explicitly; occurrence-weighted training is a future
ablation. Retained molecular inputs are canonical, unmapped, and stereo-free.

## Shared-tactic selection

Compute the intersection of n1 and n5 linear tactic identities from the matching
refreshed publications, recording identity definitions, versions, source hashes,
and both dataset memberships. Match stable tactic identities, not dataset-local
entry IDs or raw SMARTS spelling. Apply the agreed n1 occurrence exclusions, then
retain only shared tactics with eligible certified n1 supervision. Record tactics
lost through exclusions and the resulting n5 coverage.

Select each retained tactic's executable variants, products, and decomposition
alternatives from eligible n1 occurrences only. Include all eligible motif-start
molecules, whether root or internal; never add n5 product/rule training pairs or
n5-only decomposition alternatives. Apply the confirmed primary exclusions below
before materializing training data and executable support.

## Primary occurrence exclusions

The following three rules are confirmed for composite training. Freeze the
reference sets from the cleaned n5 evaluation corpus before training; include
all its reference routes, not only routes containing retained shared tactics.

| Rule | Comparison | Exclusion scope |
| --- | --- | --- |
| E1: shared final target | An n1 route's final target equals any n5 final target. This includes exact duplicate routes. | Remove every composite occurrence from that n1 route. |
| E2: shared motif input | An n1 occurrence's motif target equals any n5 root or internal nonterminal molecule, even when its composite label differs. | Remove the occurrence. |
| E3: shared reaction-signature sequence | An n1 occurrence contains two or more consecutive reactions whose ordered InChI signatures also occur in n5, including an embedded segment. | Remove the occurrence and its decomposition evidence. |

Use full stereo-free Standard InChI molecular identities generated by Chython,
independent of atom maps, retaining InChI charge/protonation and isotope layers.
Standard InChI normalizes supported tautomers. Define nonterminal molecules by
the reference route structure, irrespective of stock membership.

E3 uses `ordered-stereo-free-inchi-reaction-pair/1`. Each reaction signature is
`(product InChI, sorted tuple of all reactant InChIs)`. Preserve repeated reactants,
reaction side roles, and consecutive root-to-leaf order. Ignore middle-field
reagents. Index every adjacent n5 pair: any repeated consecutive sequence of
length at least two contains a matching pair. A matching pair anywhere inside
an n1 occurrence excludes the entire occurrence. Abstract tactic equality alone
does not establish E3; atom-map or tautomer-state differences do not undo a match.

Exact reaction-state graph matching is diagnostic only. For every signature-match
witness, record `match`, `different`, or `unresolved`, including an error when
alignment enumeration exceeds the default bound of 256. These diagnostics never
change exclusion or quarantine decisions. Invalid paths, inconsistent route-edge
identities, or incomplete n5 signature indexing still prevent eligibility.
See [selection commands and audit contracts](docs/SELECTION.md).

Apply the union of E1, E2, and E3. Keep all matching reason codes per occurrence,
with source IDs and matching n5 evidence; report individual and overlapping
exclusion counts without double-counting total removals. Unresolved eligibility-check
failures must be quarantined and reported rather than treated as eligible.

Filter before grouping or aggregating composite examples. Rebuild training and
validation pairs, occurrence counts, executable-variant support, decomposition
alternatives, and frequency-based priors from retained n1 evidence only. A
variant may remain when independently supported by surviving n1 occurrences.
Drop shared tactics with no eligible n1 support and report the lost vocabulary
and n5 coverage. Do not restore them using n5 evidence.

These rules do not filter the deliberately exposed n1+n5 single-step corpus or
the union leaf stock. Shared abstract tactics and elementary chemistry remain
allowed. This protocol supports a shared-tactic comparison without direct n5
reference-route composite supervision; it does not establish unseen-chemistry
generalization. Audit overlap with additional MCTS-generated molecules after
search, without changing the frozen training split retrospectively.

## Patent-disjoint sensitivity analysis

In addition to E1-E3, exclude every n1 route sharing an authoritative patent ID
with any n5 route. Recompute all composite assets and train a separate composite
model from the surviving cohort. Keep the single-step checkpoint, n5 evaluation
targets, union stock, and matched search settings fixed. Apply the same validation
and tuning procedure using only the eligible development data for each cohort.

The implemented patent policy uses original PaRoutes reaction IDs, including
preprocessing split ancestry; it uppercases IDs and removes whitespace, slashes,
and hyphens while retaining supplied publication kind codes. Policy
`paroutes-document-identifiers-including-legacy-us-reissue-sir/2` also recognizes
legacy US grants without kind codes and RE/H identifiers. It does not invent
suffixes or infer patent families. All 20,000 selected routes have recognized
provenance under this policy; record coverage for each future release. Quarantine
n1 routes with unresolved patent provenance; any unresolved n5 patent provenance
blocks usable sensitivity assets, because the common n5 evaluation set remains
fixed. Unknown IDs are not evidence of disjointness. Report the reduction in examples, tactics, and
variants alongside outcomes so repertoire loss is visible. Patent-disjointness
is an additional sensitivity analysis, not a replacement for the primary cohort.

## Training artifacts

For an asset stem `single_step` or `composite`:

1. `<stem>.tsv`: `rule_smarts`, `popularity`, `reaction_indices`.
2. `<stem>_policy_data.tsv`: `product_smiles`, `rule_id`.
3. `<stem>.manifest.json`: SynPlanner `synplan-rules/2` vocabulary digest.
4. Experiment manifests and provenance sidecars, separate from CLI inputs.

Rule IDs are zero-based row indices in the ordered rule file. The policy-data
stem must correspond to its rule TSV: the MHN trainer discovers the vocabulary
using that naming convention. Never reorder the vocabulary independently.
Composite exports order rules by descending popularity (unique prepared
product/mapping-equivalent-rule pairs), breaking ties by representative SMARTS text. Assign IDs only
after sorting and regenerate all labels, pair indices, manifests and split
snapshots together. Occurrence duplicates remain in provenance without
inflating popularity.

Single-step extraction delegates chemistry to SynPlanner's current extraction
API. The checked-in extraction configuration starts from RouteInspector's
functional-group configuration, with stereo ignored and minimum popularity 1.
The extraction settings have been checked against both selected reference
profiles. Any later source/profile release requires a new compatibility check.

Composite export retains each certified link's exact executable SMARTS and
complete tactic decomposition in occurrence evidence. Training labels merge only
queries equivalent under simultaneous atom renumbering across both sides, with
all query predicates, side presence and molecule-pattern grouping preserved.
The lexicographically smallest eligible exact variant represents each class;
RouteInspector v3 family identity alone is insufficient because it ignores
cross-side atom correspondence. Unsupported predicates keep exact identity.
The product is the occurrence's `motif_target_smiles`. Deduplicate prepared
product/merged-rule pairs while preserving every original occurrence, variant,
certificate and decomposition. Keep non-equivalent labels as separate positives.
Replay each chosen representative against every supporting certified boundary.
Unobserved rule applicability is not exhaustively labelled, and direct replay
does not certify ordered tactic unwrapping. Regenerate matching grouped splits
with the original settings and audit any partition changes.

The standard SynPlanner CLI makes its own ranking train/validation split.
Retrocomposite now supplies `split` and `train` commands that bypass that split
using frozen row assignments. Default grouping joins inputs with identical stereo-free Standard InChIs
and every supporting source route into connected components. Optional patent
grouping adds shared patent IDs and requires complete patent provenance. Whole
groups are assigned reproducibly while retaining training support for every rule;
reports expose achieved holdout fraction, rule coverage, and any blocked split.
The configurable defaults are a 10% requested holdout and split seed 42. Freeze
production settings after reviewing actual component sizes; no grouping is
silently relaxed.

Split snapshots and assignments live under `data/splits/`. Model seeds are
separate from split seeds. Each training run uses a fresh seeded interpreter,
explicit data-loader subsets, deterministic settings, and a new directory under
`outputs/training/`. Record native best/final checkpoints, logs, metrics,
configuration and source hashes; verify the best checkpoint through SynPlanner's
inference loader. CPU reproducibility checks use invented chemistry; accelerator
verification and full production training remain pending. Keep n5 composite
supervision out of training, validation, and calibration. See
[training commands and contracts](docs/TRAINING.md).

## Architecture inspected in the local repositories

The exact installed source-file hashes, Git revisions, and dirty status are in
`environment/sources.json`. The following entry points were inspected before
implementing these adapters; paths identify the current local checkouts.

| Finding | Source | Consequence |
| --- | --- | --- |
| Route merge uses a stereo-sensitive target bucket and exact ordered RouteCGR history, with intermediate states retained. | [merge.py](../route-inspector/route_inspector/datasets/merge.py#L25) | Separate audit from publication and add the experiment's stereo-free exclusion policy. |
| Composite libraries bind to a reference library and resolve an exact certified variant for each link. | [library.py](../route-inspector/route_inspector/composite_rules/library.py#L721), [certified_rule](../route-inspector/route_inspector/composite_rules/library.py#L815) | Verify matching publications and export the linked variant, preserving decomposition and provenance. |
| Reference occurrences record the molecule where the motif starts. | [models.py](../route-inspector/route_inspector/reference_library/models.py#L211) | Train on `motif_target_smiles`, including internal contexts. |
| Ranking data reads `product_smiles`/`rule_id`; its default split forces repeated products into training and stratifies remaining examples by rule. | [preprocessing.py](../SynPlanner/synplan/ml/training/preprocessing.py#L154), [supervised.py](../SynPlanner/synplan/ml/training/supervised.py#L43) | Retrocomposite freezes grouped assignments and bypasses the native split while using the native dataset/model/checkpoint interfaces. |
| The molecule encoder defaults to GCN unless explicitly configured. | [config.py](../SynPlanner/synplan/ml/config.py#L60) | Set GPS explicitly for the molecule and QueryCGR rule graph encoders. |
| Existing `CompositePolicy` merges filtering/ranking logits over one rule vocabulary; priority rules are additive with prior 1.0. | [composite.py](../SynPlanner/synplan/mcts/policy/composite.py#L17), [tree.py](../SynPlanner/synplan/mcts/tree.py#L541) | Implement the separate-vocabulary hybrid on the future SynPlanner branch, with one shared quota. |
| Policy molecules remove stereo; small non-stock molecules can be assumed trivial at positive `min_mol_size`. | [precursor.py](../SynPlanner/synplan/chem/precursor.py#L64), [termination](../SynPlanner/synplan/chem/precursor.py#L101) | Use stereo-free identities consistently and set `min_mol_size=0`. |
| RouteInspector pins an older SynPlanner Git revision. | [pyproject.toml](../route-inspector/pyproject.toml:41) | The isolated setup explicitly overrides that one pin with the inspected local snapshot and records the override. |

## What the two earlier questions mean

**Independent transfer versus shared-tactic performance.** Let T1 and T5 be the
tactic identities observed in n1 and n5. Choosing the vocabulary from T1 alone
and then evaluating n5 tests transfer of n1-selected tactics. Choosing T1∩T5
first tests performance on tactics already known to occur in both datasets.
The latter uses test-route information to select the vocabulary, even though
the composite weights are trained only on n1. Both are useful, but they support
different claims. Given the deliberately exposed single-step baseline, call
this study a controlled planning comparison and state which composite-vocabulary
selection rule was used. Confirmed choice: T1∩T5, retaining only tactics with
eligible certified n1 supervision after exclusions.

**Internal motif targets.** In retrosynthetic direction, suppose a route is
`T -> A -> B -> C`. A composite replacing `A -> B -> C` should be recommended
when the current molecule is A. Its training input is A, although T is the
overall route target. Using only T would train root-starting tactics and omit
internal tactics needed later during MCTS. Confirmed choice: use all eligible
n1 motif targets, including internal molecules, with provenance and grouped
validation.

## Stock and terminal states

Export `n1.smi`, `n5.smi`, and `union.smi` from terminal molecule nodes, plus
targets and leaf provenance. Canonicalize and remove stereo consistently.
These plain SMILES files are readable by SynPlanner's stock loader. Use
`union.smi`, the deduplicated stereo-free union of cleaned n1+n5 leaves, as the
stock in both planning arms. The per-set files remain provenance outputs; a
separate-stock sensitivity analysis is optional and outside the primary protocol.

Use `min_mol_size=0` so a small non-stock fragment cannot count as a building
block. Report already-in-stock targets separately. Recheck stock after
unwrapping, including components omitted by the net-composite abstraction.

## Composite popularity experiment

The main setting is `pop_gt1`: retain merged composite labels with popularity
at least two. The additional `pop_ge1` setting includes all supported labels,
including popularity-one rules. Here popularity means unique prepared
`(product_smiles, merged rule)` policy pairs, as in the exported TSV; repeated
source occurrences of the same pair count once. It does not mean distinct
patents, distinct source routes, or number of tactic decompositions.

Compute support independently within each eligible n1 cohort, after E1-E3,
optional patent exclusion, preparation and mapping-equivalent merging. Never use
n5 frequencies for this threshold. Apply the threshold to merged labels, not
individual exact variants; retain all eligible n1 variants and decompositions
for each retained label. The criterion uses the full eligible n1 preparation
corpus before its grouped holdout. Thus >1 does not guarantee two examples in
the training partition. Training-frequency priors must use training rows only.

| Setting | Composite cohort | Minimum popularity | Role |
| --- | --- | --- | --- |
| B50 | None | — | Shared single-step baseline |
| Primary / pop_gt1 | E1-E3 | 2 | Main hybrid |
| Primary / pop_ge1 | E1-E3 | 1 | Singleton-inclusion sensitivity |
| Patent-disjoint / pop_gt1 | E1-E3 + patent exclusion | 2 | Patent sensitivity |
| Patent-disjoint / pop_ge1 | E1-E3 + patent exclusion | 1 | Combined sensitivity |

Freeze the full eligible cohort's molecule/route groups and split assignments
first, then derive both popularity settings from those same assignments. Do not
reshuffle surviving examples or break groups after filtering. Check retained
labels still have training support and that validation remains nonempty; report
achieved validation fraction, label coverage and common validation pairs.
Renumber labels and rebuild matched policy data, encoding caches and split
snapshots together, preserving source-to-arm label/row mappings. Use the same
model-seed list and training/tuning protocol across settings; calibrate each
hybrid on its eligible n1 development data only. Compare validation metrics on
a common retained subset as well as each setting's full holdout.

Current `data/composite_mapping_merged_v1/` descriptive counts (2026-10-27):

| Cohort | All labels | Labels >1 | Labels =1 | Pairs retained at >1 |
| --- | ---: | ---: | ---: | ---: |
| Primary | 2,094 | 741 | 1,353 | 2,872 |
| Patent-disjoint | 1,555 | 542 | 1,013 | 1,971 |

These are counts from the existing bundle, not completed filtered releases.
Recompute them after upstream recertification. Popularity filtering is an
experimental factor, not a repair for failed replay. Each final arm requires
its own complete replay audit; existing acceptance blockers still apply.

## Planning target population

Evaluate the same full list of cleaned n5 final/root targets in all five
settings, regardless of reference tactic detection or retained composite
support. The current export has 9,999 distinct prepared SMILES from 10,000 n5
route records. Preserve the mapping from each target to all its source routes;
apply the agreed stereo-free identity policy consistently and report any
additional identity collapse. Internal n1 motif targets are training inputs,
not the definition of the n5 planning population.

Report the full-n5 result first. Secondary reference-route strata are: retained
composite support, detected linear tactics without retained support, and no
detected linear tactics. Calculate coverage separately for each repertoire,
with a fixed common-covered subset for direct popularity-arm comparisons.
Retain route-level annotations where multiple references share one target;
use any-supported-reference coverage for target-level summaries and report
mixed reference strata. No detected tactic in a reference route does not
preclude composite use in an alternative generated route. Also report actual
composite use, without conditioning the main solve-rate denominator on it.
Reference-route annotations must never gate model calls or hybrid quotas.

## Comparison and recommendation budget

Compare B50 (50 single-step proposals) with each of the four hybrid settings
above. H40/10 (40 single-step plus 10 composite proposals) is the proposed common
hybrid allocation; allocation remains open. Freeze the same single-step
checkpoint, evaluator, stock, target list, and MCTS configuration across all
settings. Match search seeds and budgets, and do not retune allocation on n5
separately for each popularity setting.

The 50 slots count executable variants before reaction application. Failed
applications consume their slots; do not refill from lower ranks after seeing
chemistry failures. Deduplicate identical executable proposals without losing
their provenance. One family cannot execute arbitrarily many variants for one
slot. Apply the same outcome and mapping-work limits to both kinds.

SynPlanner's existing CompositePolicy merges ranking/filtering policies over
one vocabulary; it is not this hybrid. Priority-rule injection is also unsuitable
for the main comparison because it is additive and assigns different priors.
The future hybrid needs separate vocabularies and heads, a single budget,
calibrated priors, and stable action provenance. The zero-composite setting must
reproduce B50. Consider the existing fragment-count prior multiplier explicitly.

Keep macro action depth and explicit elementary chemical depth separately.
Match the chemical horizon across arms. Additional primitive chemistry in a
composite is an action-repertoire confound: audit constituent coverage in the
single-step vocabulary and report the overlap subset separately.

## Cost, validation, and diversity

The primary comparison is primary/pop_gt1 versus B50 on full n5; the other
cohort/popularity settings provide sensitivity analyses. Both actual model calls
and end-to-end wall time are required efficiency endpoints. Measure two separate
success events against each cost axis: any validated stock-reaching route, and
at least one validated route matching a cleaned n5 source RouteCGR for the target.
Report matched-budget success/recovery rates and cost/time to first occurrence;
include failures and timeouts rather than averaging only successful runs.
See [evaluation specifications](docs/EVALUATION.md) for counting, timing,
RouteCGR equality, and supplementary SB-CGR metrics.

Count RRS requests, cache hits, actual single-step/composite/value/gating/rollout
neural forwards, molecules scored, chemistry attempts, generated outcomes,
unwrapping attempts, and elapsed time by stage. Two heads can cost two neural
evaluations per decision. Fewer expansions alone do not prove lower model cost.
Reset molecule-dependent caches consistently between runs.

Replay composite-bearing solved and unsolved/partial candidates. Validate
explicit steps, compatible downstream reattachment and every terminal branch.
An intermediate in stock may terminate its branch early; preserve the full
original decomposition and validate the shortened route separately. Reusing a
compatible existing continuation can also recover a previously unsolved route.
Use only eligible n1-derived decompositions, and count all replay/reconciliation
costs. Do not accept approximate lineage projections or generated `in_stock=True`
flags as validation. Keep original search and final validation/solved statuses,
including invalid/inconclusive outcomes and enumeration caps. Additional search
to complete non-stock branches remains a separately budgeted protocol decision.

Report validated solve rate and solve-versus-cost curves first. Also report
unique explicit routes, root disconnections, building-block sets, fixed-method
route clusters, elementary depth/length, and exact RouteCGR reference recovery.
Supplement with per-target unique SB-CGR classes, class richness versus cost,
and overlap/unique classes between baseline and hybrid at matched budgets and
matched route counts. SB-CGR equality is coarser than exact route recovery. Separate
search-discovered routes from variants generated by decomposition enumeration.
Deduplicate atom-map variants and macro/elementary encodings of the same route.
Use a common ranking method on explicit routes; macro length must not give a
route an artificial ranking advantage.

Use paired targets and search seeds; report uncertainty at target/patent level.
Avoid success-only cost averages as the main result. Use full n5 as the primary
denominator and report reference-coverage strata secondarily. Estimate the
paired effect of singleton inclusion within each cohort, and patent exclusion
within each popularity setting. Report vocabulary/pair/coverage losses alongside
solve-versus-cost and diversity changes; do not compare only each arm's own
covered subset as if the target populations were identical.

## Phases

1. Project/environment and tested preparation adapters.
2. Consume refreshed n1/n5 publications, freeze their identities, and run the
   implemented E1-E3 selector plus the patent-disjoint sensitivity cohort.
3. Prepare single-step rules, composite supervision, and stock; derive the four
   cohort/popularity datasets with matched within-cohort splits and replay audits.
4. Train and validate the shared single-step MHN and four composite MHNs per
   model seed; freeze models and n1-only calibration.
5. Implement and test the hybrid on the separate SynPlanner branch.
6. Pilot on development data, freeze budgets, then evaluate paired full-n5
   runs for the shared baseline and all four cohort/popularity hybrid settings.
7. Unwrap solved/unsolved candidates, validate and deduplicate; measure
   stock-reaching success and exact RouteCGR recovery versus model calls and
   end-to-end time, then perform supplementary SB-CGR diversity analysis.

The self-contained dataset release, both composite cohorts and all three
InChI-grouped splits are complete and publicly verified. See
[cohort results](docs/COHORT_RELEASE.md) for counts, support losses and revisions.
Review the separate route-9035 granularity question in QUESTIONS.md. Production
model training and planning remain to be done; TODO.md tracks the remaining work.
