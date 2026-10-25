# Dataset inputs and publication status

The user selected the existing standalone files under RouteInspector's
`data/clean/` on 2026-10-25. Each contains 10,000 routes:

| File, relative to RouteInspector | SHA-256 |
| --- | --- |
| `data/clean/n1_routes.json` | `c1e396cd71228e3ab113412428571d223ef943835c3793f91b994b3341359439` |
| `data/clean/n5_routes.json` | `5a27be2e0199f2bacd66556122f50906a24e27946bb30b1d9472d55d725e71af` |

The n1/n5 reference libraries match these exact source hashes and use the same
extraction profile and tactic identity version 4. The user-updated standalone
`outputs/composite_libraries/n1` now uses composite identity version 3 and is the
source for this release. It contains 13,445 certified links: 13,121 linear
`rrseq_cons` links and 324 branched links. Only the linear links enter selection.
The complete upstream publication has 8,552 identities, 11,076 exact variants,
and 1,074 uncertified construction attempts retained as diagnostics. Those
uncertified attempts do not enter supervision. n5 composites are not required.
The earlier linear-only v3 publication remains recorded as historical provenance.

The alternative merged publication was built from source hashes beginning
`9902ff12` and `fb8bf966`. Its source directory is absent from the local checkout.
That alternative is excluded from this release following the user's input
choice. The merged library is not substituted for standalone n1 supervision.

Hugging Face authentication and both public Protolaw repositories have been
verified. Preparation, scientific validation, and immutable release upload are
separate steps. The first verified release is [n1-n5-single-step-v1](https://huggingface.co/datasets/Protolaw/retrocomposite-data/tree/4ba2b7f366ea881825fbebe343ccefdd7899af42/releases/n1-n5-single-step-v1).
Its revision is `4ba2b7f366ea881825fbebe343ccefdd7899af42`. Anonymous downloads, all file hashes,
and relocated split loading have been verified.

The common stock has been prepared from all 20,000 selected routes: 13,308 n1
and 13,195 n5 unique stereo-free leaves, giving 20,087 molecules in the union.
Original stock flags do not affect traversal. Single-step preparation uses the
same files and retains the complete deduplicated reaction provenance.

Use `--workers 1` with the pinned SynPlanner snapshot: its parallel extraction
initializer rejects functional-group query objects during configuration
deserialization. The failed parallel attempt published no artifacts. Sequential
extraction uses the same profile and preserves the exact software snapshot.

## Historical single-step release (version 1)

- 71,185 reaction occurrences yield 57,381 unique reactions and training pairs.
- 11,209 rules pass native loading and QueryCGR graph encoding; zero extraction
  failures or excluded reactions were recorded.
- 22 native product strings were normalized to the shared model/stock identity
  convention. Original rows and a change ledger are included.
- The seed-42, molecule-plus-route split has 51,642 training and 5,739 validation
  rows across 14,832 connected groups. Largest group: 54 rows. Molecule, route,
  and group overlap between partitions are all zero.
- 9,267 rules have no validation support under this split. Interpret validation
  metrics over observed classes; review this coverage before model selection.
- Each dataset has 9,999 unique stereo-free targets. Thirteen n1 and eight n5
  targets are already in the union stock; retain and flag them in planning analysis.

Dataset and split manifests are in the release. Compact checked counts and
revision receipts are tracked under `environment/`.

## Composite reference indexing: corrected and ready

The earlier public input-readiness audit reported three precursor mismatches in
n5 routes 3032 and 9035. That source-error diagnosis was incorrect: each stored
mapped reaction precursor equals its route child exactly. Retrocomposite's
asymmetric extra chemical canonicalization introduced different tautomers.

The user selected Chython-generated stereo-free Standard InChI for identity
checks. The new full n5 index contains 10,000 routes, 28,958 adjacent pairs,
9,999 target identities, and 36,223 nonterminal identities, with zero reference
errors and zero incomplete patent routes. New local audit:
`data/cohort_readiness_inchi/`. Input source hashes remain unchanged.

See [molecule identity and exact reaction states](MOLECULE_IDENTITY.md) for the
implementation. E3 uses ordered InChI reaction signatures; exact graph matching
is diagnostic only and cannot change exclusion decisions.
The original public audit and its immutable receipts remain historical.
The [verified composite release](COHORT_RELEASE.md) publishes both eligible cohorts,
all three InChI-grouped splits and the correction of that source-error diagnosis.

Route 9035's inferred tautomer-only step and unresolved final-cyclization split
are separate granularity findings to review upstream. No change to the three
stored precursor edges is needed to resolve the false mismatch.

## Patent provenance is resolved

The earlier parser incorrectly rejected legacy US grants and special RE/H
identifiers. Policy
`paroutes-document-identifiers-including-legacy-us-reissue-sir/2` recognizes
these documented forms while retaining the supplied identifier and any kind code.
No kind code or patent family is inferred. All 10,000 n1 and 10,000 n5 routes
now have complete recognized provenance; 1,113 n5 false-negative routes were
corrected. Missing patent IDs are no longer a blocker. This audit checks
identifier extraction and format, not independent patent-registry verification.

See the [USPTO kind-code documentation](https://www.uspto.gov/learning-and-resources/support-centers/electronic-business-center/kind-codes-included-uspto-patent)
and [USPTO number-format help](https://patentsgazette.uspto.gov/week27/OG/help/help.html).
The full n1 occurrence-selection run also passes. Both cohorts have published,
verified training assets; see [results and remaining limitations](COHORT_RELEASE.md).

## Complete current training release

The [verified composite release](https://huggingface.co/datasets/Protolaw/retrocomposite-data/tree/e4e575d7a9e066eca65f43fc3fde5b905b0cf309/releases/n1-n5-composites-inchi-v1) is **`n1-n5-composites-inchi-v1`**, pinned at
`e4e575d7a9e066eca65f43fc3fde5b905b0cf309`. It contains both composite cohorts, unchanged single-step data and
union stock, new InChI-grouped splits, and complete selection/support audits.
All 62 payload files passed anonymous download and SHA-256 checks; all three
relocated splits loaded successfully. The full code suite passes 80 tests.

| Cohort | Rules | Product/rule pairs | Train | Validation |
| --- | ---: | ---: | ---: | ---: |
| Single-step | 11,209 | 57,381 | 51,642 | 5,739 |
| Primary composites | 3,185 | 4,232 | 3,809 | 423 |
| Patent-disjoint composites | 2,322 | 2,988 | 2,689 | 299 |
