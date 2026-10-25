# General experiment plan

Updated: 2026-10-25. This file records scientific decisions and architecture;
execution status belongs in TODO.md and unresolved choices in QUESTIONS.md.
Workflow diagrams: [preparation](docs/diagrams/preparation.md),
[training](docs/diagrams/training.md), [planning](docs/diagrams/planning.md),
[post-processing](docs/diagrams/postprocessing.md), and
[analysis](docs/diagrams/analysis.md). Preparation has two diagrams in the
same file: shared data preparation, then composite cohort filtering.

## Objective and interpretation

Measure whether learned linear composite actions improve MCTS planning cost,
validated solve rate, and explicit-route diversity over a shared single-step
reaction recommendation system (RRS).

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
- Use the union of actual terminal molecule nodes in cleaned n1+n5 JSON as
  the stock for both planning arms.
  Do not use the original PaRoutes stock files or blindly trust `in_stock` flags.
- Ignore stereochemistry in exported model inputs, reactions, targets, stock,
  and planning evaluation; keep original sources unchanged.
- Implement the future hybrid policy on a separate SynPlanner branch.

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

Single-step extraction delegates chemistry to SynPlanner's current extraction
API. The checked-in extraction configuration starts from RouteInspector's
functional-group configuration, with stereo ignored and minimum popularity 1.
The extraction settings have been checked against both selected reference
profiles. Any later source/profile release requires a new compatibility check.

Composite export uses each certified link's exact mapped executable SMARTS,
not a family representative substituted for it. The product is the occurrence's
`motif_target_smiles`. Multiple observed labels for one molecule remain multiple
training rows. Exact duplicate product/rule pairs may be deduplicated while
retaining all occurrences in provenance. Unobserved rule applicability is not
claimed to have been exhaustively labelled.

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
| Route merge uses a stereo-sensitive target bucket and exact ordered RouteCGR history, with intermediate states retained. | [merge.py](/Users/almazgil/Developer/projects/route-inspector/route_inspector/datasets/merge.py:25) | Separate audit from publication and add the experiment's stereo-free exclusion policy. |
| Composite libraries bind to a reference library and resolve an exact certified variant for each link. | [library.py](/Users/almazgil/Developer/projects/route-inspector/route_inspector/composite_rules/library.py:721), [certified_rule](/Users/almazgil/Developer/projects/route-inspector/route_inspector/composite_rules/library.py:815) | Verify matching publications and export the linked variant, preserving decomposition and provenance. |
| Reference occurrences record the molecule where the motif starts. | [models.py](/Users/almazgil/Developer/projects/route-inspector/route_inspector/reference_library/models.py:211) | Train on `motif_target_smiles`, including internal contexts. |
| Ranking data reads `product_smiles`/`rule_id`; its default split forces repeated products into training and stratifies remaining examples by rule. | [preprocessing.py](/Users/almazgil/Developer/projects/SynPlanner/synplan/ml/training/preprocessing.py:154), [supervised.py](/Users/almazgil/Developer/projects/SynPlanner/synplan/ml/training/supervised.py:43) | Retrocomposite freezes grouped assignments and bypasses the native split while using the native dataset/model/checkpoint interfaces. |
| The molecule encoder defaults to GCN unless explicitly configured. | [config.py](/Users/almazgil/Developer/projects/SynPlanner/synplan/ml/config.py:60) | Set GPS explicitly for the molecule and QueryCGR rule graph encoders. |
| Existing `CompositePolicy` merges filtering/ranking logits over one rule vocabulary; priority rules are additive with prior 1.0. | [composite.py](/Users/almazgil/Developer/projects/SynPlanner/synplan/mcts/policy/composite.py:17), [tree.py](/Users/almazgil/Developer/projects/SynPlanner/synplan/mcts/tree.py:541) | Implement the separate-vocabulary hybrid on the future SynPlanner branch, with one shared quota. |
| Policy molecules remove stereo; small non-stock molecules can be assumed trivial at positive `min_mol_size`. | [precursor.py](/Users/almazgil/Developer/projects/SynPlanner/synplan/chem/precursor.py:64), [termination](/Users/almazgil/Developer/projects/SynPlanner/synplan/chem/precursor.py:101) | Use stereo-free identities consistently and set `min_mol_size=0`. |
| RouteInspector pins an older SynPlanner Git revision. | [pyproject.toml](/Users/almazgil/Developer/projects/route-inspector/pyproject.toml:41) | The isolated setup explicitly overrides that one pin with the inspected local snapshot and records the override. |

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

## Comparison and recommendation budget

Primary proposed arms: B50 (50 single-step proposals) and H40/10 (40 single-step
plus 10 composite proposals). Freeze the same single-step checkpoint, evaluator,
stock, target list, and MCTS configuration in both arms. Allocation remains open.

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

Count RRS requests, cache hits, actual single-step/composite/value/gating/rollout
neural forwards, molecules scored, chemistry attempts, generated outcomes,
unwrapping attempts, and elapsed time by stage. Two heads can cost two neural
evaluations per decision. Fewer expansions alone do not prove lower model cost.
Reset molecule-dependent caches consistently between runs.

A candidate macro route counts as solved only after all composites are replayed
into explicit single-step routes, exact downstream branches reattach, and all
terminal molecules satisfy the selected stock. Use only n1-derived decomposition
alternatives. Do not accept approximate lineage projections or generated
`in_stock=True` flags as validation. Report invalid and inconclusive outcomes,
including enumeration caps. Decide separately whether non-stock precursors
exposed during unwrapping should fail or trigger additional charged search.

Report validated solve rate and solve-versus-cost curves first. Also report
unique explicit routes, root disconnections, building-block sets, fixed-method
route clusters, elementary depth/length, and reference-route recovery. Separate
search-discovered routes from variants generated by decomposition enumeration.
Deduplicate atom-map variants and macro/elementary encodings of the same route.
Use a common ranking method on explicit routes; macro length must not give a
route an artificial ranking advantage.

Use paired targets and search seeds; report uncertainty at target/patent level.
Avoid success-only cost averages as the main result. Full n5 and shared-tactic
cohorts should both be reported under the selected vocabulary protocol.

## Phases

1. Project/environment and tested preparation adapters.
2. Consume refreshed n1/n5 publications, freeze their identities, and run the
   implemented E1-E3 selector plus the patent-disjoint sensitivity cohort.
3. Prepare single-step rules, composite supervision, and stock; validate assets.
4. Train and validate the shared single-step MHN and separate primary/sensitivity
   composite MHNs; freeze models and calibration.
5. Implement and test the hybrid on the separate SynPlanner branch.
6. Pilot on development data, freeze budgets, then evaluate paired n5 runs for
   the primary and patent-disjoint composite models.
7. Unwrap, validate, deduplicate, measure cost/diversity, and publish the audit.

The self-contained dataset release, both composite cohorts and all three
InChI-grouped splits are complete and publicly verified. See
[cohort results](docs/COHORT_RELEASE.md) for counts, support losses and revisions.
Review the separate route-9035 granularity question in QUESTIONS.md. Production
model training and planning remain to be done; TODO.md tracks the remaining work.
