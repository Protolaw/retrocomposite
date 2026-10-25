# Molecule identity and reaction-signature exclusions

Confirmed on 2026-10-25: molecular identity checks use full stereo-free Standard
InChI strings, generated through Chython's `to_inchi(molecule,
ignore_stereo=True, inplace=False)`. Policy:
`chython-standard-inchi-stereo-free/1`. No RDKit conversion, InChIKey truncation,
SMILES fallback, or preliminary chemical canonicalization is used. Errors remain
errors. Chython and bundled libINCHI binary/version evidence is recorded in new
cohort and split manifests; setup checks that InChI generation works.

Standard InChI normalizes supported tautomers and retains its charge/protonation
and isotope layers. This is an intentional identity-policy change, not merely a
new string encoding. Fixed-H InChI is not used. See the
[InChI Trust technical FAQ](https://www.inchi-trust.org/technical-faq/).

## Where identity is used

- E1 final targets and E2 root/internal motif inputs.
- Reaction/route product and precursor identity checks, motif provenance checks,
  and E3 context indexing and intermediate candidate selection.
- Molecular connected components in new train/validation splits, and the
  single-step native-product/rule provenance join (followed through the saved
  normalization ledger to the actual model-input row).

E3 now uses ordered InChI reaction signatures: each step has a product identity
and the complete reactant identity multiset. A shared adjacent pair is sufficient
to exclude an occurrence, including when exact bond states or atom correspondence
differ. The old stable reason code `E3_SHARED_CONCRETE_SEGMENT` is interpreted
under the new versioned policy. Exact graphs only annotate matching witnesses as
`match`, `different`, or `unresolved`; graph audit errors never change eligibility.
A regression replaces a tautomer-change step by an identity transformation:
the signatures match (E3 overlap), while the graph audit reports a difference.

Training TSVs and stock files remain SMILES. Their serialization and preparation
are separate from comparison identifiers; existing artifacts are not rewritten.
The stock/planning integration must adopt the same declared membership policy
when the planning stage is implemented. Native rule identities and exact reaction
deduplication are not replaced by InChI molecule identity.

## Versions and existing releases

New cohort audits use `retrocomposite-cohort-selection/3`; exclusion policy is
`ordered-stereo-free-inchi-reaction-pair/1`. Exact graph auditing retains
`full-mapped-reaction-pair-with-all-intermediate-alignments/2` and explicitly
records `affects_eligibility: false`. New grouped splits
use `retrocomposite-grouped-split/2`, record a `molecule_inchi` on each assignment,
and count molecular overlap using InChI. Existing version-1 splits remain
loadable and are checked using their original SMILES grouping, without changing
assignments or claiming they used InChI. Regenerate splits under a new path/release
before comparing results under the updated policy.

## Corrected n5 diagnosis

The earlier three precursor mismatch witnesses in routes 3032 and 9035 were
false positives: their stored mapped precursor strings are identical to their
route children. Retrocomposite re-canonicalized reaction molecules after removing
maps but canonicalized route molecules with maps retained. In pinned
chython-synplan 1.108, that extra standardization can select different tautomers.

Repeating preprocessing canonicalization with the original maps is stable for
all three witnesses. Mapped and unmapped serialization alone preserve their
chemical graph. A further canonicalization after an unmapped round trip changes
the tautomer. The new InChI check avoids this asymmetric extra preparation.

With the new code, all 10,000 n5 routes index successfully: 28,958 adjacent pairs,
9,999 target identities, 36,223 nonterminal identities, zero reference errors,
and zero incomplete patent-provenance routes. The audit is saved locally under
`data/cohort_readiness_inchi/`. The subsequent [full cohort release](COHORT_RELEASE.md) verifies n1 occurrence
selection, support rebuilding and all three frozen splits, and provides the public
correction of the historical source-error diagnosis.

Route 9035's separate inferred tautomer-only split and retained unresolved final
cyclization split remain preprocessing/granularity questions. They do not
constitute the reported precursor mismatch.
