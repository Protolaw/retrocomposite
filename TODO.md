# Implementation TODO

## Project bootstrap

- [x] Separate general plan, implementation tasks, and open questions.
- [x] Initialize the standalone Git repository in `projects/retrocomposite`.
- [x] Create and verify the isolated environment with full SynPlanner extras.
- [x] Record upstream revisions, source hashes, and installed dependency pins.
- [x] Add and test cleaned-route reaction and leaf exporters.
- [x] Add and test certified linear-composite adapters for libraries and JSON.
- [x] Verify exported files with the current SynPlanner loader and MHN config.

Bootstrap checks use invented chemistry and adapter fixtures, including a real
MHN forward pass. Full refreshed-library export is pending the upstream input
release; transport tests do not establish chemistry certification of new data.

## Upstream prerequisite (owned by RouteInspector)

- [ ] Refreshed matching n1/n5 route/reference/composite publications are ready.

This is an input dependency only. Do not implement rebuilding in this project.

## Freeze experiment inputs

- [ ] Resolve composite vocabulary, occurrence-exclusion, and stock-scope questions.
- [ ] Recompute route, target, reaction, tactic, and model-input overlap audits.
- [ ] Separate read-only overlap auditing from merger publication; add an
      explicit stereo-free exclusion policy and preserve original memberships.
- [ ] Implement selection manifests for shared-tactic/target-filtered cohorts.
- [ ] Verify extraction profile matches the refreshed libraries.
- [ ] Prepare production rules, policy data, provenance, targets, and stock.
- [ ] Measure extraction errors, exclusions, duplicates, and retained coverage.

## Training

- [ ] Add explicit grouped validation and seed-controlled training wrapper.
- [ ] Train custom single-step MHN: QueryCGR rule graphs, GPS molecule encoder.
- [ ] Train composite MHN from allowed n1 motif inputs only.
- [ ] Record vocabularies, splits, seeds, metrics, hardware, and checkpoint hashes.
- [ ] Calibrate hybrid head priors on development data.

## SynPlanner branch (future upstream work)

- [ ] Create the agreed branch when hybrid implementation starts.
- [ ] Implement separate-vocabulary hybrid policy with one top-50 budget.
- [ ] Add action provenance and actual inference/caching counters.
- [ ] Track chemical depth separately from macro-action depth.
- [ ] Validate zero-composite equivalence to baseline.

## Planning and evaluation

- [ ] Freeze shared stock, stereo-off mode, `min_mol_size=0`, evaluator, budgets.
- [ ] Add strict composite replay/reattachment and post-unwrapping stock checks.
- [ ] Record enumeration truncation and classify invalid/inconclusive candidates.
- [ ] Pilot on development targets; lock configuration before final comparison.
- [ ] Run paired baseline/hybrid n5 experiments and allocation sensitivities.
- [ ] Deduplicate explicit routes and measure cost, recovery, and diversity.
- [ ] Produce target-level paired uncertainty estimates and final audit report.
