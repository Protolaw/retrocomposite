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
MHN forward pass. Full refreshed-library export is pending the upstream input
release; transport tests do not establish chemistry certification of new data.

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
- [ ] Publish the first reviewed production dataset release and record its commit.
- [ ] Publish trained models with the matching dataset commit.
- [ ] Verify the full environment on the destination machine, preserving source hashes.

## Upstream prerequisite (owned by RouteInspector)

- [x] Freeze the selected existing n1/n5 source hashes and verify their reference
      libraries match those same files.
- [ ] Build a separate identity-v3 linear n1 composite publication from the
      selected source in RouteInspector; review all retained diagnostics.

This is an input dependency only. Do not implement rebuilding in this project.
The [readiness audit](docs/DATASET_READINESS.md) records exact evidence. Prepare
and upload single-step/stock independently of the composite-library refresh.
The alternative source-corrected merged release is not the selected input.

## Freeze experiment inputs

- [x] Select shared n1/n5 linear tactics, eligible n1 root/internal motif targets,
      and the union of cleaned n1+n5 leaves as the common stock.
- [x] Adopt E1 shared final-target route exclusion, E2 shared motif-input
      exclusion, and E3 exact concrete multistep-segment exclusion for primary
      composite training; adopt patent-disjointness as a sensitivity analysis.
- [x] Implement frozen n5 root, internal nonterminal molecule, and concrete
      consecutive-segment indexes with canonical stereo-free identities.
- [x] Implement E1 whole-route and E2 occurrence filters.
- [x] Implement and verify E3 exact concrete segment matching, including embedded
      segments of at least two reactions and their reactant/branch context.
- [x] Add checks for atom-map/stereo invariance, different-label shared inputs,
      abstract-tactic matches without concrete overlap, and embedded segments.
- [ ] Recompute route, target, reaction, tactic, and model-input overlap audits.
- [x] Implement read-only cohort auditing independently of merger publication,
      preserving original memberships and using a stereo-free exclusion policy.
- [x] Implement the shared-tactic intersection and agreed occurrence-exclusion
      manifests; retain eligible n1 examples and variants only, including
      internal motif targets, and report tactics lost after filtering.
- [x] Preserve every exclusion reason and n5 witness; report overlapping counts
      and quarantine unresolved comparison failures.
- [x] Rebuild eligible composite pairs, variant/decomposition support, and
      occurrence counts separately for both cohorts. Future validation splits
      and frequency priors must use only these retained assets.
- [x] Implement the additional patent-disjoint cohort, patent-ID normalization,
      provenance quarantine, and coverage/repertoire-loss reports.
- [x] Keep exclusion processing read-only with respect to cleaned source files;
      single-step and stock preparation remain separate and unfiltered.
- [ ] Run production cohort selection on refreshed matching publications and
      review all quarantines, support losses, and patent provenance gaps.
- [ ] Verify extraction profile matches the refreshed libraries.
- [ ] Prepare production rules, policy data, provenance, targets, and stock.
- [ ] Measure extraction errors, exclusions, duplicates, and retained coverage.

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
- [ ] Generate production split assignments in `data/splits/`; record training metrics,
      seeds, hardware, checkpoint hashes, and input-vocabulary hashes under
      `outputs/training/`.
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
