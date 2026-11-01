# Preparation workflow

Preparation is split into three diagrams: shared data preparation, primary
occurrence exclusions, then composite cohorts and vocabulary audits. The export and cohort-selection tools are implemented;
production inputs are the existing standalone cleaned n1/n5 files selected by the user.
Library refreshing remains in RouteInspector. See [PLAN.md](../../PLAN.md#primary-occurrence-exclusions)
for exact exclusions and [preparation commands](../PREPARATION.md) for adapters.

## 1. Freeze inputs and prepare shared data

```mermaid
flowchart TD
    RI["RouteInspector: selected cleaned n1/n5 files<br/>Matching references and identity-v3 n1 composites"]
    RELEASE["Freeze cleaned routes, references and identity-v3 composites"]
    CHECK["Verify source hashes, identities, profiles and provenance"]
    REACTIONS["Cleaned n1+n5 reactions: remove stereo<br/>Normalize complete mapped sides before extraction"]
    ALIGN["Reaction-aware extraction view<br/>Align only source-unchanged remote tautomers<br/>Require identical prepared precursors and serialized-rule replay"]
    REPLAY["Extract candidate rules and serialize policy pairs<br/>Audit every final pair and all supporting precursors"]
    REPLAYOK{"Every final pair passes?"}
    REPLAYFAIL["data/ diagnostics and marked candidate<br/>Block release; retain every failure"]
    SINGLE["data/single_step/<br/>Rules, policy data and provenance"]
    LEAVES["Actual cleaned n1+n5 terminal leaves"]
    STOCK["data/stock/<br/>Stereo-free union stock and planning targets"]
    SHARED["Shared linear tactic identities<br/>and certified n1 root/internal occurrences"]
    REFERENCE["Frozen n5 roots, nonterminal inputs and ordered reaction signatures<br/>plus n1/n5 patent provenance"]
    RI --> RELEASE --> CHECK
    CHECK --> REACTIONS --> ALIGN --> REPLAY --> REPLAYOK
    REPLAYOK -->|yes| SINGLE
    REPLAYOK -->|no| REPLAYFAIL
    CHECK --> LEAVES --> STOCK
    CHECK --> SHARED
    CHECK --> REFERENCE
```

Shared tactics, certified occurrences, and frozen comparison indexes feed the
second diagram. Composite exclusions leave the single-step corpus and stock intact.

## 2. Apply the primary occurrence exclusions

```mermaid
flowchart TD
    N1["Certified n1 occurrences of shared linear tactics"]
    N5["Frozen n5 exclusion indexes<br/>Stereo-free InChI molecule identities"]
    READY{"Complete n5 E3 index?"}
    BLOCK["data/cohort_readiness/<br/>Input audit; no usable composite cohorts"]
    E1["E1: shared final target<br/>Exclude every occurrence in that n1 route"]
    E2["E2: shared n5 root/internal input<br/>Exclude the matching n1 occurrence"]
    E3["E3: ordered InChI reaction-pair match<br/>Exclude occurrences containing matching segments"]
    GRAPH["Exact graph audit of E3 matches<br/>Diagnostic only; no eligibility effect"]
    ELIGIBLE["Eligible n1 occurrences after E1-E3<br/>Continue to diagram 3"]
    AUDIT["data/cohorts/ audits<br/>All reasons, witnesses and quarantines"]
    N1 --> READY
    N5 --> READY
    READY -->|yes| E1 --> E2 --> E3
    READY -->|no| BLOCK
    N5 -.-> E1
    N5 -.-> E2
    N5 -.-> E3
    E1 -.-> AUDIT
    E2 -.-> AUDIT
    E3 -.-> GRAPH -.-> AUDIT
    E3 -->|eligible| ELIGIBLE
```

Evaluate all three predicates for audit purposes; the sequence does not discard
later reasons after the first match. Quarantine unresolved eligibility checks.
Graph audit results are match, different or unresolved; failures are diagnostic
only. Abstract tactic overlap alone is not E3: an ordered InChI reaction-pair
match embedded within a larger n1 occurrence also triggers E3. Incomplete n5
comparison indexes block both cohorts.

The retained occurrences feed both cohort definitions in the next diagram.

## 3. Build composite cohorts, vocabularies and audits

```mermaid
flowchart TD
    ELIGIBLE["Eligible n1 occurrences after E1-E3<br/>From diagram 2"]
    PRIMARY["data/cohorts/primary/<br/>Rebuild eligible pairs and decomposition support"]
    PATENTS["Frozen n1/n5 patent provenance"]
    PATENT["Additional patent exclusion<br/>Shared or unknown n1 IDs excluded; missing n5 IDs block"]
    SENS["data/cohorts/patent_disjoint/<br/>Rebuild eligible sensitivity assets"]
    MERGE["Merge mapping-equivalent labels per cohort<br/>Preserve variants, certificates and decompositions<br/>Count unique prepared target/rule pairs"]
    POP["Derive pop_gt1 main and pop_ge1 including singletons<br/>Keep matched full-cohort split assignments<br/>Export four settings with label/row lineage"]
    NETREPLAY["Audit every final composite pair<br/>against its certified net-precursor boundary"]
    AUDIT["data/ audits<br/>Patent exclusions, support losses and replay results"]
    ELIGIBLE --> PRIMARY
    ELIGIBLE --> PATENT --> SENS
    PATENTS --> PATENT
    PATENT -.-> AUDIT
    PRIMARY --> MERGE
    SENS --> MERGE
    MERGE --> POP --> NETREPLAY
    POP -.-> AUDIT
    NETREPLAY -.-> AUDIT
```

Rebuild all composite-derived support using only retained n1 occurrences, drop
unsupported tactics, and report lost n5 coverage. Unresolved n5 patent provenance
blocks the sensitivity cohort. Blocked cohorts have no trainable assets.

The popularity layer is planned, not yet exported. Count support after merging
within each eligible n1 cohort, before its grouped holdout. Freeze full-cohort
groups and assignments, then filter merged labels while preserving eligible
variants/decompositions. See the
[experiment matrix](../../PLAN.md#composite-popularity-experiment).

The earlier three n5 mismatch findings were false positives; the InChI-based
reference audit under `data/cohort_readiness_inchi/` passes all 10,000 routes.
The public release contains full occurrence filtering and supersedes the historical
source-error diagnosis; see [cohort results](../COHORT_RELEASE.md) and
[readiness](../DATASET_READINESS.md).

All preparation products remain under [data/](../../data/README.md). Next:
[training](training.md).
