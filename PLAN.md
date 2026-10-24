# General experiment plan

Updated: 2026-10-25. This file records scientific decisions and architecture;
execution status belongs in TODO.md and unresolved choices in QUESTIONS.md.

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

Composite supervision comes from n1 only. Audit its overlap with n5 separately:
the single-step exposure is deliberate, but duplicate-route exposure in the
composite head is still a distinct confound. Report the exact composite split
policy instead of describing the entire experiment as leakage-free.

## Confirmed decisions

- Separate Git project: `projects/retrocomposite`, initially located beside the
  existing RouteInspector and SynPlanner repositories.
- New isolated environment with RouteInspector and the full `SynPlanner[all]`
  dependency set. Pin installed dependencies and record source content/revisions.
- Rebuild standalone n1/n5 libraries in RouteInspector against the corrected
  source release and composite identity version 3. No rebuilding code here.
- Extract a single-step vocabulary and standard `*_policy_data.tsv` from
  cleaned n1+n5 reactions.
- MHN ranking architecture; `query_cgr_graph` rule encoding; GPS molecule
  encoder, and the supported GPS rule graph encoder.
- Adapt certified RouteInspector composites and associated motif products to
  the same SynPlanner training format, preserving executable variants.
- Linear consecutive `RRseq_cons` tactics only. Gapped and branched tactics are
  outside this first experiment.
- Derive stock from actual terminal molecule nodes in cleaned n1/n5 JSON.
  Do not use the original PaRoutes stock files or blindly trust `in_stock` flags.
- Ignore stereochemistry in exported model inputs, reactions, targets, stock,
  and planning evaluation; keep original sources unchanged.
- Implement the future hybrid policy on a separate SynPlanner branch.

## Data release and provenance

Freeze matching cleaned routes, reference libraries, and composite libraries
before producing production training assets. Check file hashes, library IDs,
processing profiles, and composite identity versions. Reject version-2
composite publications rather than silently treating them as refreshed.

The earlier corrected merged audit recorded 2,127 duplicate routes and 2,146
shared-target pairs. Those numbers are descriptive of that release, not
guaranteed counts for refreshed standalone publications. Recompute overlap
after refresh. Do not mix the older standalone hashes with the merged release.

Every generated asset receives a manifest with input hashes, configuration,
software versions, and output hashes. Preserve dataset, route, reaction-node
path, original reaction ID, reference occurrence, composite family, exact
variant, and decomposition provenance where applicable.

Decouple overlap assessment from merged-dataset publication. Reuse or extract
the merger's route-identity comparison into a read-only audit interface in
RouteInspector, then consume its membership/exclusion manifests here. Preserve
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
Verify compatibility with the refreshed extraction profile before a full run.

Composite export uses each certified link's exact mapped executable SMARTS,
not a family representative substituted for it. The product is the occurrence's
`motif_target_smiles`. Multiple observed labels for one molecule remain multiple
training rows. Exact duplicate product/rule pairs may be deduplicated while
retaining all occurrences in provenance. Unobserved rule applicability is not
claimed to have been exhaustively labelled.

The standard SynPlanner CLI currently makes its own ranking train/validation
split. CLI-compatible files do not by themselves implement route/patent-grouped
validation. A reproducible grouped split/training wrapper remains a task before
reportable composite-model evaluation. Keep n5 composite supervision out of
that model's training and tuning.

## Architecture inspected in the local repositories

The exact installed source-file hashes, Git revisions, and dirty status are in
`environment/sources.json`. The following entry points were inspected before
implementing these adapters; paths identify the current local checkouts.

| Finding | Source | Consequence |
| --- | --- | --- |
| Route merge uses a stereo-sensitive target bucket and exact ordered RouteCGR history, with intermediate states retained. | [merge.py](/Users/almazgil/Developer/projects/route-inspector/route_inspector/datasets/merge.py:25) | Separate audit from publication and add the experiment's stereo-free exclusion policy. |
| Composite libraries bind to a reference library and resolve an exact certified variant for each link. | [library.py](/Users/almazgil/Developer/projects/route-inspector/route_inspector/composite_rules/library.py:721), [certified_rule](/Users/almazgil/Developer/projects/route-inspector/route_inspector/composite_rules/library.py:815) | Verify matching publications and export the linked variant, preserving decomposition and provenance. |
| Reference occurrences record the molecule where the motif starts. | [models.py](/Users/almazgil/Developer/projects/route-inspector/route_inspector/reference_library/models.py:211) | Train on `motif_target_smiles`, including internal contexts. |
| Ranking data reads `product_smiles`/`rule_id`; its default split forces repeated products into training and stratifies remaining examples by rule. | [preprocessing.py](/Users/almazgil/Developer/projects/SynPlanner/synplan/ml/training/preprocessing.py:154), [supervised.py](/Users/almazgil/Developer/projects/SynPlanner/synplan/ml/training/supervised.py:43) | Native TSV compatibility is implemented; grouped experimental validation still needs a wrapper. |
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
selection rule was used. Do not silently decide this outstanding choice.

**Internal motif targets.** In retrosynthetic direction, suppose a route is
`T -> A -> B -> C`. A composite replacing `A -> B -> C` should be recommended
when the current molecule is A. Its training input is A, although T is the
overall route target. Using only T would train root-starting tactics and omit
internal tactics needed later during MCTS. Recommended default: use all eligible
n1 motif targets, with provenance and grouped validation.

## Stock and terminal states

Export `n1.smi`, `n5.smi`, and `union.smi` from terminal molecule nodes, plus
targets and leaf provenance. Canonicalize and remove stereo consistently.
These plain SMILES files are readable by SynPlanner's stock loader. Choose one
stock scope for the paired comparison; the n1+n5 union is the initial proposal,
not a settled scientific decision.

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
2. Consume refreshed n1/n5 publications, freeze release and overlap decisions.
3. Prepare single-step rules, composite supervision, and stock; validate assets.
4. Train and validate custom MHN models; freeze models and calibration.
5. Implement and test the hybrid on the separate SynPlanner branch.
6. Pilot on development data, freeze budgets, then evaluate paired n5 runs.
7. Unwrap, validate, deduplicate, measure cost/diversity, and publish the audit.

No production library construction, model training, or planning is implied by
creating this project. Those stages depend on refreshed inputs and the decisions
listed in QUESTIONS.md.
