---
pretty_name: Retrocomposite experiment data
tags:
  - chemistry
  - retrosynthesis
  - synplanner
  - reaction-rules
---

# Retrocomposite datasets

Prepared data for [Protolaw/retrocomposite](https://github.com/Protolaw/retrocomposite).
The first verified release is **`n1-n5-single-step-v1`**, at immutable revision
`4ba2b7f366ea881825fbebe343ccefdd7899af42`. It contains 11,209 single-step rules, 57,381 associated
training pairs, and the 20,087-molecule common leaf stock. The seed-42 grouped
split has 51,642 training rows and 5,739 validation rows, with zero molecule or
source-route overlap. All 26 files passed anonymous download/checksum verification
and the relocated split loaded successfully.

Composite data will be published separately after shared-tactic/exclusion checks
pass. No trained model weights are included in this release.

Each release can contain the single-step rule vocabulary and corresponding
product/rule training pairs, primary and patent-disjoint composite cohorts with
their product/rule pairs and decomposition support, union stock, planning targets,
frozen grouped splits, and audit manifests. Inputs are derived from the standalone cleaned PaRoutes n1/n5 files selected by
the user on 2026-10-25, using RouteInspector and SynPlanner. Source SHA-256 hashes
start with `c1e396cd` (n1) and `5a27be2e` (n5); these differ from the later merged
publication's input release.

Single-step supervision intentionally uses cleaned n1+n5 reactions. Composite
supervision uses eligible n1 occurrences of linear tactics shared with n5, after
the documented exclusions. This is a controlled action-space comparison, not
an unseen-molecule or standard held-out PaRoutes benchmark claim.

Upload and download using the [mobility guide](https://github.com/Protolaw/retrocomposite/blob/main/docs/MOBILITY.md).
Transfers preserve ordered vocabularies and row IDs, verify SHA-256 hashes, and
record the exact Hub commit. Use a commit revision for reproducible retrieval.

Models are stored separately at
[Protolaw/retrocomposite-models](https://huggingface.co/Protolaw/retrocomposite-models).
No original source dataset license is replaced by this repository; provenance
and source terms belong with each data release.

## Current composite preparation blocker

The [public input-readiness audit](https://huggingface.co/datasets/Protolaw/retrocomposite-data/tree/3b5089c2c72dc3a5aba2574360d751fd682dfd33/audits/n1-n5-input-readiness-v1) contains the exact chemistry
mismatch witnesses and extracted patent provenance for all 20,000 source routes.
All five audit files passed anonymous download/checksum verification. It is a
blocked-input diagnostic, not a composite training release.

The identity-v3 linear n1 library has 13,121 certified links (1,043 uncertified
attempts retained as diagnostics). However, three mapped-reaction/route-precursor
mismatches in n5 routes 3032 and 9035 prevent a complete E3 exclusion index.
Full occurrence filtering has not completed, so neither composite cohort has
eligible training assets or final support counts. Source files remain unchanged;
resolving the representations upstream requires matching new source/library
versions and regeneration of any affected prepared data.

Legacy US/RE/H patent identifier handling is fixed: all 20,000 routes have
recognized provenance. Patent extraction is no longer a blocker; this does not
constitute independent patent-registry verification or patent-family matching.
The single-step release passed extraction/loading checks, which do not prove
agreement between every mapped reaction and its route-tree precursors. The
source inconsistencies above remain a documented limitation of those inputs.
