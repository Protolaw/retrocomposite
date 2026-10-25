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
separate steps. Completed releases will be recorded here with exact revisions.

The common stock has been prepared from all 20,000 selected routes: 13,308 n1
and 13,195 n5 unique stereo-free leaves, giving 20,087 molecules in the union.
Original stock flags do not affect traversal. Single-step preparation uses the
same files and retains the complete deduplicated reaction provenance.

Use `--workers 1` with the pinned SynPlanner snapshot: its parallel extraction
initializer rejects functional-group query objects during configuration
deserialization. The failed parallel attempt published no artifacts. Sequential
extraction uses the same profile and preserves the exact software snapshot.
