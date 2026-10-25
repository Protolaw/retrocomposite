# Dataset inputs and publication status

The user selected the existing standalone files under RouteInspector's
`data/clean/` on 2026-10-25. Each contains 10,000 routes:

| File, relative to RouteInspector | SHA-256 |
| --- | --- |
| `data/clean/n1_routes.json` | `c1e396cd71228e3ab113412428571d223ef943835c3793f91b994b3341359439` |
| `data/clean/n5_routes.json` | `5a27be2e0199f2bacd66556122f50906a24e27946bb30b1d9472d55d725e71af` |

The existing n1/n5 reference libraries match these exact source hashes and use
the same extraction profile and tactic identity version 4. Their older composite
companions use identity version 2. A new linear n1 companion was constructed
in RouteInspector at `outputs/composite_libraries/n1-retrocomposite-v3-20261025`;
the experiment requires composite identity version 3. n5 composites are not
needed for shared-tactic selection. The new library contains 8,279 composite
identities and 13,121 certified links from 14,164 attempted occurrences. All
1,043 uncertified attempts remain in its diagnostics and are excluded from
training. Exact variants number 10,764; every variant uses identity version 3.

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

## Single-step release

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

## Composite readiness: blocked by three source inconsistencies

The new identity-v3 n1 library is available, but the complete n5 E3 comparison
index cannot be constructed. Three mapped reactions disagree with their route
precursor multisets after the agreed stereo-free normalization:

| n5 route | Reaction-node path | Source reaction ID |
| --- | --- | --- |
| `3032` | `[0]` | `US20150225423A1;0414;1736056` |
| `9035` | `[0,0,0,0,0]` | `US05109001;;249758` |
| `9035` | `[0,0,0,0,0,0,0]` | `US05109001;;249757` |

The exact reaction strings, conflicting molecules, node paths, and all 20,000
routes' patent provenance are in the public
[input-readiness audit](https://huggingface.co/datasets/Protolaw/retrocomposite-data/tree/3b5089c2c72dc3a5aba2574360d751fd682dfd33/audits/n1-n5-input-readiness-v1). Its five files passed anonymous download
and SHA-256 verification. The receipt is
[`environment/cohort_readiness_publication.json`](../environment/cohort_readiness_publication.json).
This is a diagnostic publication, not an eligible composite training release.

Both primary and patent-disjoint cohorts remain blocked: incomplete n5 indexing
cannot establish absence of E3 overlap. Full occurrence filtering was stopped
after establishing this global blocker and has **not completed**. There are no
production composite training TSVs, composite splits, or final exclusion/support
counts. Do not infer an empty eligible cohort from this blocked result.

These structures appear to differ in tautomer representations; this is an
interpretation of the witnesses, not an authorized normalization policy.
Stereochemistry removal does not resolve them. Reconcile the source reaction
and route representations in RouteInspector under an explicit chemistry policy,
publish matching source/library revisions, and rerun selection. The chosen source
files remain unchanged. Do not silently drop the affected n5 routes or weaken E3.
If sources change, version and rebuild any affected single-step, stock, and split
artifacts as well; the present release remains an immutable record of its inputs.

The single-step release passed extraction/loading checks, which do not certify
agreement between mapped reactions and every route-tree precursor. This known
source limitation therefore accompanies that release too.

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
The sensitivity cohort remains blocked by the same incomplete E3 index.
