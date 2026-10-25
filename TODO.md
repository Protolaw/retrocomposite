# Implementation TODO

## Project bootstrap

- [x] Separate general plan, implementation tasks, and open questions.
- [x] Document preparation in two diagrams in one file, with separate training,
      planning, post-processing, and analysis workflows under `docs/diagrams/`.
- [x] Establish `data/` for preparation artifacts and `outputs/` for training,
      planning, post-processing, and analysis results; document stage paths.
- [x] Initialize the standalone Git repository in `projects/retrocomposite`.
- [x] Create and verify the isolated environment with full SynPlanner extras.
- [x] Record upstream revisions, source hashes, and installed dependency pins.
- [x] Add and test cleaned-route reaction and leaf exporters.
- [x] Add and test certified linear-composite adapters for libraries and JSON.
- [x] Verify exported files with the current SynPlanner loader and MHN config.

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

## Training

- [x] Add molecule/route connected-component splits with optional patent grouping,
      train-label coverage, explicit blocked audits, and immutable split snapshots.
- [x] Add seed-controlled MHN training, native checkpoints, local logs/metrics,
      failure manifests, and repeated-seed CPU verification.
- [ ] Review production group sizes, holdout fraction, and per-rule coverage;
      freeze validation settings and model-seed budget before full training.
- [ ] Train custom single-step MHN: QueryCGR rule graphs, GPS molecule encoder.
- [ ] Train composite MHN for shared tactics from eligible n1 root/internal
      motif inputs only, after E1-E3.
- [ ] Train a separate composite MHN on the additional patent-disjoint cohort,
      using the same validation/tuning procedure on that cohort's eligible data.
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
- [ ] Add action provenance and actual inference/caching counters.
- [ ] Track chemical depth separately from macro-action depth.
- [ ] Validate zero-composite equivalence to baseline.

## Planning

- [ ] Freeze the union-stock artifact hash, stereo-off mode, `min_mol_size=0`,
      evaluator, and budgets.
- [ ] Pilot on development targets; lock configuration before final comparison.
- [ ] Run paired baseline/hybrid n5 experiments and allocation sensitivities.
- [ ] Evaluate the patent-disjoint composite model with the same single-step
      checkpoint, n5 targets, stock, and matched search settings.
- [ ] Save candidate routes, run configurations, and search/inference costs
      under `outputs/planning/`, including unsuccessful runs.

## Post-processing

- [ ] Add strict composite replay/reattachment and post-unwrapping stock checks.
- [ ] Record enumeration truncation and classify invalid/inconclusive candidates.
- [ ] Deduplicate validated explicit routes while retaining candidate provenance.
- [ ] Save explicit routes, validation reports, and replay costs under
      `outputs/postprocessing/`.

## Analysis

- [ ] Audit overlap with search-generated molecules without retroactively
      changing the frozen training cohort.
- [ ] Measure solve-versus-cost, reference recovery, and explicit-route diversity.
- [ ] Produce target-level paired uncertainty estimates and final audit report
      under `outputs/analysis/`, including patent-cohort support losses.

Verified production counts and public revisions: [cohort release](docs/COHORT_RELEASE.md).
