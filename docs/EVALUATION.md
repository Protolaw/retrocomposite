# Evaluation specifications

Updated: 2026-10-28. This is the intended evaluation protocol; the instrumented
hybrid, route post-processing and analysis runners remain to be implemented.
See [PLAN.md](../PLAN.md#cost-validation-and-diversity) and [TODO.md](../TODO.md).

## Outcomes and efficiency claims

The main contrast is primary/pop_gt1 hybrid versus B50. Apply the same protocol
to the other three cohort/popularity hybrids. All use the same full-n5 target
list, single-step checkpoint, stock, evaluator, hardware and paired search seeds.
Retain the model-seed identity in each comparison. Report already-in-stock
targets separately so zero-step solutions do not drive the efficiency result.

| Quantity | Operational definition |
| --- | --- |
| Validated solve rate | Fraction of evaluation targets with at least one validated explicit route whose required terminal molecules are all in union stock. |
| Source-route recovery rate | Fraction with at least one such route whose full RouteCGR matches a cleaned n5 source route for that target under the frozen equality policy. |
| Model-call efficiency | Each of the two success rates versus a common budget of actual neural forwards; calls to first validated solution and first recovered reference. |
| Time efficiency | Each of the two success rates versus common end-to-end wall-clock budgets; elapsed time to first validated solution and first recovered reference. |

The desired outcome is higher solve/recovery rates with fewer calls and less
elapsed time. This is a hypothesis, not an assumed consequence of macro actions.
If quality and cost move in opposite directions, report that tradeoff. A valid
alternative synthesis is successful even when it does not recover the source.
A route ending early at an in-stock intermediate can therefore be solved without
matching the complete source RouteCGR.

Use equal-budget solve/recovery curves as the main efficiency evidence. Freeze
model-call and wall-clock checkpoints before evaluating n5; retain a common
safety limit for the other resources and identify runs stopped by that limit.
Report both target-level and source-route-level recovery where a target has
multiple reference routes, but do not duplicate targets in the main denominator.
Also report reference hit@1, @5 and @10 using one reference-independent ranking
of deduplicated explicit routes. Reference identity must not guide search,
ranking, replay scheduling, checkpoint selection or stopping.

Failures and timeouts remain in the denominator, and unobserved first-success
events remain censored/unsuccessful at the achieved budget, never zero-cost
successes. Paired cost ratios on targets solved by both arms are secondary and
must state that subset's size. Use paired target/patent uncertainty estimates;
model/search seeds are repeated measurements, not extra independent targets.

## Count actual inference work

Record separately logical RRS requests, cache hits, and actual forwards through
the single-step, composite, value, gating and rollout networks. The headline
call count is the sum of actual network forwards over search and any subsequent
completion/replay stage that invokes a model. Count at network inference entry
points, without double-counting nested encoder/layer calls. Two independently
executed policy networks ordinarily count as two calls, even for one MCTS
expansion. Cache hits and purely chemical tactic replay add no neural calls.

Record batch size, molecules scored per network, cache policy and actual neural
time as well. Freeze batching and cache-reset conventions across arms; fewer
calls caused by larger batches are not evidence of less molecular scoring.
If an implementation genuinely shares computation, record the shared and
head-specific work explicitly. Include failed applications and unsuccessful
searches. Training cost is reported separately from inference efficiency.

## End-to-end time and post-processing

Measure monotonic wall time from target processing to delivery of validated
explicit routes. Include target/feature preparation, policy inference, MCTS
chemistry, tactic replay, enumeration of alternative decompositions, compatible
node/branch reuse, stock checks, validation, deduplication and output ranking.
Include necessary output serialization; record logging overhead consistently.
Measure overall elapsed time directly rather than summing overlapping stage
timers. Keep hardware, concurrency and accelerator synchronization consistent.
Report model-loading/warm-up separately, use a fixed convention for the primary
warm-service measurement, and include startup in total campaign runtime.

Replay both solved and retained unsolved candidates, using the same fixed
retention/enumeration budget. Check new intermediates against stock and existing
compatible continuations; every required branch must validate and terminate in
stock before the result counts as solved. Save search status, final status and
whether recovery required replay, stock termination or continuation reuse.

Record cumulative actual calls and elapsed time when each validated route first
becomes available. Reference matching can identify recovery retrospectively from
these events. If replay is only performed after a whole search run, do not
backdate a validated result to the earlier macro-route discovery. For results at
budget checkpoints, charge all work needed to produce and validate those results;
post-processing is not a free step outside the time budget.

Offline reference comparison and supplementary diversity calculations are
analysis overhead: report their runtime separately. They do not supply an oracle
to the planner. Reuse of a previously searched continuation does not erase its
original inference/time cost; new completion search must be explicitly budgeted.

## Exact source-route recovery using RouteCGR

Compare final explicit elementary routes with the cleaned n5 source routes for
the same target, after the same frozen stereo-free normalization and composition
profile. Use complete RouteCGR graphs, independent of atom-map numbering and
macro encoding. Keep transient bonds and intermediate-state history; graph
isomorphism decides equality, with hashes/buckets only used for indexing.
Source references and generated candidates must use the same implementation.

The proposed strict primary policy retains step order/history, consistent with
the existing RouteInspector dataset-merger comparator. Its current target bucket
is stereo-sensitive and must not be copied unchanged into this stereo-free
experiment. Freeze and test branch-order handling before evaluation; report
order-agnostic RouteCGR equivalence separately as a sensitivity, never silently
substitute it for the strict recovery metric. Audit normalization and composition
failures as unresolved rather than declaring a chemically distinct route. Keep
those targets visible in full-n5 reporting and additionally state the evaluable
reference coverage and confirmed recovery lower bound.

Local implementation references: RouteInspector
[`datasets/merge.py`](/Users/almazgil/Developer/projects/route-inspector/route_inspector/datasets/merge.py)
constructs the ordered, history-preserving graph and confirms exact isomorphism;
SynPlanner
[`representation/hash.py`](/Users/almazgil/Developer/projects/SynPlanner/synplan/chem/reaction/routes/representation/hash.py)
provides order-aware and order-agnostic RouteCGR identities. Native hash labels
alone do not preserve every intermediate-state field of the merger's comparator.
These are adapter starting points; no new recovery evaluator has been implemented.

## Supplementary SB-CGR diversity

After explicit-route validation and deduplication, derive SB-CGRs and group them
within each target. Use a frozen stereo-free, map-independent identity and test
invariance to remapping/serialization. SB-CGR equality represents a coarser
strategic-bond class; it does not establish exact source-route recovery.

Report per target:

- Number of distinct SB-CGR classes among validated stock-reaching routes,
  including zero classes for unsolved targets in full-population summaries.
- Class richness versus actual model calls and end-to-end time, at matched budgets.
- Shared, hybrid-only and baseline-only SB-CGR classes, and whether the source
  reference's class was found. Define empty-set cases explicitly for overlap ratios.
- Class richness at matched numbers of unique explicit routes (fixed top-K and,
  where useful, seeded equal-size subsampling); state eligible-target counts so
  producing more routes alone does not explain every diversity increase.

Separate search-discovered routes from decomposition-generated alternatives,
stock-truncated routes and reused-continuation combinations. Keep unresolved or
non-stock-reaching partial-route diversity in a separate exploratory report.
Do not pool SB-CGR identities from unrelated targets into a target-level diversity
claim. Preserve membership maps so each class traces to its explicit routes.

SynPlanner already provides
[`compose_sb_cgr`](/Users/almazgil/Developer/projects/SynPlanner/synplan/chem/reaction/routes/representation/sb_cgr.py),
[`cluster_routes`](/Users/almazgil/Developer/projects/SynPlanner/synplan/chem/reaction/routes/clustering/core.py)
and [`compare_sb_cgr_clusters`](/Users/almazgil/Developer/projects/SynPlanner/synplan/chem/reaction/routes/analysis.py).
Their current clustering uses SB-CGR string identities; verify the frozen runtime's
mapping/normalization behavior before adopting them for this experiment.

## Saved evidence

Keep event counters/timestamps and candidate provenance in `outputs/planning/`,
explicit routes and original/final statuses in `outputs/postprocessing/`, and
solve/recovery curves, RouteCGR comparison audits and SB-CGR class tables/figures
in `outputs/analysis/`. Record target, cohort/popularity, model/search seeds,
source/vocabulary/stock hashes and evaluator versions throughout. Replay failures,
limits and uncomparable references remain in manifests and reports.
