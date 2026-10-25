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
This repository is initialized as the destination for versioned data releases.
Available releases will appear under `releases/`.

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
