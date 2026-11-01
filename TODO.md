# Implementation TODO

## Project bootstrap

- [x] Separate general plan, implementation tasks, and open questions.
- [x] Document preparation in three diagrams in one file, with separate training,
      planning, post-processing, and analysis workflows under `docs/diagrams/`.
- [x] Split post-processing into candidate preparation, the replay/reconciliation
      loop with intermediate stock checks, and final validation/export diagrams.
- [x] Establish `data/` for preparation artifacts and `outputs/` for training,
      planning, post-processing, and analysis results; document stage paths.
- [x] Initialize the standalone Git repository in `projects/retrocomposite`.
- [x] Create and verify the isolated environment with full SynPlanner extras.
- [x] Record upstream revisions, source hashes, and installed dependency pins.
- [x] Add and test cleaned-route reaction and leaf exporters.
- [x] Add and test certified linear-composite adapters for libraries and JSON.
- [x] Verify exported files with the current SynPlanner loader and MHN config.
- [x] Export composite vocabularies by descending popularity with deterministic
      SMARTS tie-breaking and consistent policy/provenance indices.
- [x] Re-export existing cohorts in popularity order and verify unchanged
      chemistry, occurrence support and frozen train/validation memberships
      under `data/composite_popularity_v1/`.
- [x] Merge mapping-equivalent composite training labels while preserving all
      original variants, certificates and tactic decompositions.
- [x] Add exact query/correspondence/pattern-grouping regression tests and an
      end-to-end two-cohort merge, split and replay check.
- [x] Rebuild both production cohorts under `data/composite_mapping_merged_v1/`,
      verify occurrence preservation and grouped splits, and compare full replay
      results against the previous audits. Primary: 2,094 rules, 4,225 pairs;
      patent-disjoint: 1,555 rules, 2,984 pairs. No new replay failures; the
      known n1 route 166 primary failure remains. See
      [merge results](docs/COMPOSITE_MERGING.md).

Bootstrap checks use invented chemistry and adapter fixtures, including a real
MHN forward pass. Production single-step assets are published. Composite cohort
export uses the corrected InChI identity and signature policy;
transport tests do not establish chemistry certification of new data.

## Portability

- [x] Publish the project under the public Protolaw GitHub account.
- [x] Create public Hugging Face repositories for datasets and model runs.
- [x] Add versioned uploads and checksum-verified downloads with commit receipts.
- [x] Bundle the exact 572 recorded RouteInspector/SynPlanner installation files,
      retain upstream licenses, and verify archives and individual source hashes.
- [x] Make setup default to the bundles and preserve baseline environment records;
      save actual per-installation pins/platform with subsequent training runs.
- [x] Audit available inputs and record the user's choice to use the existing
      `data/clean/n1_routes.json` and `n5_routes.json` as the experiment source.
- [x] Publish and anonymously verify `n1-n5-single-step-v1`: rules, pairs, stock,
      targets, provenance, and the grouped single-step split. Record its commit.
- [x] Publish the detailed input-readiness audit with all patent provenance and
      three mismatch witnesses; verify all five downloaded file hashes.
- [x] Publish eligible primary and patent-disjoint composite dataset releases.
- [ ] Update `retrocomposite_env` to consume the new upstream tactic-replay
      functionality. Refresh pinned RouteInspector/SynPlanner source bundles,
      dependency records and setup/conda instructions; verify the replay API and
      a portable clean installation. Keep upstream implementation in its own project.
- [ ] Publish trained models with the matching dataset commit.
- [ ] Verify the full environment on the destination machine, preserving source hashes.

## Upstream prerequisite (owned by RouteInspector)

- [x] Freeze the selected existing n1/n5 source hashes and verify their reference
      libraries match those same files.
- [x] Build a separate identity-v3 linear n1 composite publication from the
      selected source in RouteInspector: 13,121 certified links, with 1,043
      uncertified diagnostics retained and excluded from training.
- [x] Consume the user-updated standalone `outputs/composite_libraries/n1` v3
      publication for the current release, selecting its 13,121 linear links only.
- [x] Diagnose the three n5 mismatch false positives and replace molecular
      identity comparisons with Chython-generated stereo-free Standard InChI.
- [x] Rebuild the full n5 reference index: 10,000 routes, 28,958 adjacent pairs,
      zero reference errors and zero incomplete patent routes.
- [ ] Review route 9035 inferred tautomer-step granularity and its retained
      unresolved final-cyclization split separately from edge consistency.
- [x] Publish a versioned correction of the earlier public readiness diagnosis.

This is an input dependency only. Do not implement rebuilding in this project.
The [readiness audit](docs/DATASET_READINESS.md) records exact evidence. Prepare
and upload single-step/stock independently of the composite-library refresh.
The alternative source-corrected merged release is not the selected input.

## Freeze experiment inputs

- [x] Select shared n1/n5 linear tactics, eligible n1 root/internal motif targets,
      and the union of cleaned n1+n5 leaves as the common stock.
- [x] Adopt E1 shared final-target route exclusion, E2 shared motif-input
      exclusion, and E3 ordered InChI reaction-signature exclusion for primary
      composite training; adopt patent-disjointness as a sensitivity analysis.
- [x] Implement frozen n5 root, internal nonterminal molecule, and concrete
      consecutive-segment indexes with stereo-free Standard InChI molecule identities
      and diagnostic exact reaction-state graphs.
- [x] Implement E1 whole-route and E2 occurrence filters.
- [x] Implement and verify E3 ordered InChI signatures, including embedded
      segments, reaction order, side roles and full reactant multiplicity.
- [x] Retain exact graph matching only as an audit; graph differences and
      unresolved alignment enumeration never override signature exclusions.
- [x] Add checks for atom-map/stereo invariance, different-label shared inputs,
      abstract-tactic matches without concrete overlap, and embedded segments.
- [ ] Recompute route, target, reaction, tactic, and model-input overlap audits.
- [x] Implement read-only cohort auditing independently of merger publication,
      preserving original memberships and using a stereo-free exclusion policy.
- [x] Implement the shared-tactic intersection and agreed occurrence-exclusion
      manifests; retain eligible n1 examples and variants only, including
      internal motif targets, and report tactics lost after filtering.
- [x] Preserve every exclusion reason and n5 witness; report overlapping counts
      and quarantine unresolved eligibility failures. Graph-audit failures are
      recorded separately and do not change exclusions.
- [x] Implement rebuilding of eligible composite pairs, variant/decomposition
      support, and occurrence counts separately for both cohorts. Production
      outputs are published and verified; splits and priors use retained assets only.
- [x] Implement the additional patent-disjoint cohort, patent-ID normalization,
      provenance quarantine, and coverage/repertoire-loss reports.
- [x] Keep exclusion processing read-only with respect to cleaned source files;
      single-step and stock preparation remain separate and unfiltered.
- [x] Run production cohort selection on refreshed matching publications and
      review all quarantines, support losses, and patent provenance gaps.
- [x] Verify extraction settings match both selected reference-library profiles.
- [x] Prepare and validate production single-step rules, policy data, provenance,
      targets, and stock: 11,209 rules, 57,381 pairs, 20,087 stock molecules.
- [x] Measure single-step extraction errors/exclusions (zero), duplicates
      (13,804), retained coverage, and 22 normalized native product strings.
- [x] Recognize legacy US/RE/H patent identifiers; all 20,000 routes have complete
      recognized provenance under the versioned policy.
- [x] Preserve the historical n5 diagnostic and publish its corrected source-error
      interpretation alongside the successful full selection release.
- [x] Complete production occurrence filtering and review final exclusions,
      support losses, quarantines, and composite coverage using the InChI policy.

## Normalization repair and release gate

- [x] Test complete-reaction normalization and re-extraction on the remaining
      14 flagged rows; all pass. Recheck the original two cases; both pass.
- [x] Normalize mapped reactions before single-step extraction and retain every
      original occurrence plus before/after normalization evidence.
- [x] Implement final-pair replay auditing, full precursor multiplicity,
      every supporting occurrence, representation checks and bounded diagnostics.
- [x] Make failed single-step replay block publication while retaining a marked
      diagnostic candidate and full audit manifests.
- [x] Audit all 4,232 primary and 2,988 patent-disjoint composite pairs:
      primary has one no-outcome case (n1 route 166); sensitivity passes all.
- [x] Complete the full normalized single-step candidate audit: 57,255/57,381
      pairs pass; 98 no outcomes, 27 precursor mismatches, one mapping-sensitive
      normalization result. All original 16 repaired cases pass.
- [x] Compare residual failures with old assets: 124 also fail under the same
      criterion; two regressions introduce disconnected multi-pattern rules.
- [x] Repair normalization-induced remote tautomer edits in n5 route 4391
      and n1 route 2887 with a source-aware extraction view and independent
      normalized precursor references.
- [x] Repeat the complete replay audits: both regressions and all original 16
      cases pass; no new failures. Single-step results are 57,257/57,381, with
      the same 124 existing failures. All 107 project tests pass.
- [ ] Triage the remaining 124 existing execution/representation failures.
- [ ] Resolve residual execution failures before producing replacement datasets,
      vocabularies and grouped splits; do not silently discard failures.
- [ ] Recertify the route 166 composite on the actual prepared target in
      RouteInspector before rebuilding the primary composite dataset.
- [ ] Complete ordered composite unwrapping validation separately from the
      direct net-precursor replay audit.

Evidence and current blockers: [normalization/replay](docs/NORMALIZATION_REPLAY.md).

## Composite popularity experiment

- [x] Set popularity >1 as the main setting and >=1 (including singletons) as
      the additional setting, crossed with primary/patent-disjoint cohorts.
- [ ] After upstream recertification, recompute unique prepared target/rule
      popularity after eligibility filtering and mapping-equivalent merging.
- [ ] Export four cohort/popularity datasets under `data/experiments/`, retaining
      eligible variants/decompositions and source-to-arm label/row mappings.
- [ ] Freeze full-cohort groups/assignments; derive matched popularity splits
      without reshuffling. Audit train support, holdout coverage and common pairs.
- [ ] Audit every final training pair in each setting; keep replay blockers
      separate from the popularity criterion and record all support losses.
- [ ] Build full-n5 target-to-reference provenance and per-setting reference
      coverage strata, including no-tactic targets and a common-covered subset.

## Training

- [x] Add molecule/route connected-component splits with optional patent grouping,
      train-label coverage, explicit blocked audits, and immutable split snapshots.
- [x] Add seed-controlled MHN training, native checkpoints, local logs/metrics,
      failure manifests, and repeated-seed CPU verification.
- [ ] Review production group sizes, holdout fraction, and per-rule coverage;
      freeze validation settings and model-seed budget before full training.
- [ ] Train custom single-step MHN: QueryCGR rule graphs, GPS molecule encoder.
- [ ] Train four composite MHNs per model seed: primary/patent-disjoint crossed
      with pop_gt1/pop_ge1, using eligible n1 root/internal motif inputs only.
      Main comparison uses primary/pop_gt1; match seed lists and tuning protocol.
- [ ] Save each setting's checkpoints, logs, metrics and calibration under
      `outputs/training/<cohort>/<popularity>/seed_<seed>/`.
- [x] Generate the seed-42 production single-step split under `data/splits/`:
      51,642 train / 5,739 validation rows, no molecule/route/group overlap.
- [x] Use InChI molecular components in new version-2 splits; preserve legacy
      version-1 split loading and its original grouping checks.
- [x] Regenerate the production single-step split under the InChI policy:
      51,642 train / 5,739 validation rows, with zero molecule/route/group overlap.
      Join native products through the preserved normalization ledger before
      grouping actual training inputs; unchanged single-step files are reused.
- [x] Generate primary and sensitivity composite splits after eligible selection.
- [ ] Record training metrics, seeds, hardware, checkpoint hashes, and input
      vocabulary hashes under `outputs/training/`.
- [ ] Calibrate hybrid head priors on development data.

## SynPlanner branch (future upstream work)

- [ ] Create the agreed branch when hybrid implementation starts.
- [ ] Implement separate-vocabulary hybrid policy with one top-50 budget.
- [ ] Add action provenance and actual per-network inference/caching counters,
      molecules scored, batch sizes and synchronized timing; count all later
      completion-stage model calls too, without counting nested network layers twice.
- [ ] Track chemical depth separately from macro-action depth.
- [ ] Validate zero-composite equivalence to baseline.

## Planning

- [ ] Freeze the union-stock artifact hash, stereo-off mode, `min_mol_size=0`,
      evaluator, and budgets.
- [ ] Pilot on development targets; lock configuration before final comparison,
      including call/time budget checkpoints, candidate-retention/replay caps,
      batching/cache policy, warm-up convention and event timestamp schema.
- [ ] Run the baseline and four cohort/popularity hybrids on the same full-n5
      target list, including no-tactic targets, with matched search seeds/budgets.
- [ ] Reuse the single-step checkpoint, stock, evaluator and allocation protocol;
      preserve cohort/popularity IDs in planning and post-processing manifests.
- [ ] Run any preregistered allocation sensitivities separately.
- [ ] Save candidate routes, run configurations, and search/inference costs
      under `outputs/planning/`, including unsuccessful runs.
- [ ] Retain composite-bearing partial routes/search branches from unsolved and
      timed-out runs, with frontier states, node/action identities and parent links,
      so post-processing can replay them and find compatible single-step continuations.
      Record retention/enumeration limits rather than silently dropping partial results.

## Post-processing

- [ ] Integrate the updated tactic-replay API and record the actual runtime/source
      hashes used for each replay run; keep this route-level stage distinct from
      the final training-pair replay audit.
- [ ] Replay composite actions in both search-solved candidates and retained
      unsolved/partial candidates, including timed-out searches. Do not gate replay
      on the planner's solved flag. Use only the matching model's eligible n1
      variants/decompositions; preserve the original search status.
- [ ] Add strict composite replay and downstream reattachment. Match newly
      introduced intermediates against existing single-step and composite-generated
      molecules using the agreed stereo-free identity policy, then verify exact
      executable graph/atom-correspondence compatibility before reusing a branch.
      InChI equality alone does not certify interchangeable replay states.
- [ ] Reconcile duplicate intermediates and reuse compatible continuations within
      the same target/run. Preserve alternative reactions, precursor multiplicity,
      parent context and action provenance; prevent cycles and duplicate routes.
      A matching molecule must not automatically merge entire search states or
      transfer MCTS visits/value statistics. Keep baseline and hybrid searches isolated.
- [ ] Check every newly created intermediate against the frozen union stock during
      replay. An in-stock intermediate may terminate that branch and yield a shorter
      explicit route; retain the original full decomposition as provenance and
      validate the shortened route separately, including all required co-precursors.
      Keep `min_mol_size=0` and the same stereo-free stock policy as planning.
- [ ] Recompute route status after replay, compatible branch reuse and stock
      termination: solved only when every required terminal branch is in stock
      and explicit chemistry/connectivity validate. Preserve valid-but-unsolved,
      invalid and inconclusive results; one stock intermediate does not solve a route.
- [ ] Record enumeration truncation and replay/reattachment/reuse costs. Any new
      completion search or model inference must be separately budgeted and charged;
      reusing a previously searched continuation retains its original search cost.
- [ ] Deduplicate validated explicit routes while retaining candidate provenance,
      including routes shared between composite replay and ordinary single-step paths.
- [ ] Verify solved and unsolved composite candidates, identical intermediates
      from both heads, incompatible same-InChI states, cycle prevention, and stock
      intermediates with unresolved co-precursors using focused regression fixtures.
- [ ] Save explicit routes, original/final statuses, validation reports, node/route
      reconciliation maps, stock-termination events and replay costs under
      `outputs/postprocessing/`.

## Analysis

- [ ] Report search-solved versus post-processing-solved outcomes separately,
      including unsolved-to-solved recovery through stock intermediates or reused
      continuations. Count unique explicit routes and include all replay costs in
      end-to-end comparisons; apply common identity/stock/validation checks to baseline.
- [ ] Audit overlap with search-generated molecules without retroactively
      changing the frozen training cohort.
- [ ] Implement the [evaluation specifications](docs/EVALUATION.md): validated
      stock-reaching solve rate and source-route recovery versus both actual
      neural forwards and end-to-end time, including tactic replay and validation.
      Record calls/time to first validated solution and first source recovery;
      retain unsuccessful targets/timeouts in full-n5 summaries.
- [ ] Freeze and test the stereo-free, map-independent, full-history RouteCGR
      source comparator and branch-order policy; audit composition failures.
      Report strict recovery, hit@1/5/10 and separate order-agnostic sensitivity.
- [ ] Add supplementary SB-CGR analysis: unique classes per target, richness
      versus call/time budgets, baseline/hybrid/source class overlap and matched
      route-count comparisons. Validate map invariance and preserve class membership.
- [ ] Report reference-coverage strata secondarily; separate source recovery from
      alternative valid solutions and SB-CGR class recovery.
- [ ] Compare singleton inclusion within each cohort and patent exclusion within
      each popularity setting, with paired uncertainty and support/coverage losses.
      Use fixed/common-covered targets for direct subset comparisons.
- [ ] Produce target-level paired uncertainty estimates and final audit report
      under `outputs/analysis/`, including patent-cohort support losses.

Verified production counts and public revisions: [cohort release](docs/COHORT_RELEASE.md).
