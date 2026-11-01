# Normalization repair and final-pair replay

Initial audit: 2026-10-25. Reaction-aware follow-up: 2026-10-26. Toolkit: pinned Chython/SynPlanner in `retrocomposite_env`.
No RDKit chemistry is used. Full stereo-free Standard InChI remains the identity
policy; this change does not redefine E1-E3 or modify cleaned source files.

## Targeted repair trial

The remaining **14 of 14** flagged rows passed complete-reaction normalization
followed by native rule re-extraction. The two previously investigated keto/enol
rows also passed: **16 of 16** known failures recovered their complete expected
prepared precursor multisets. Each final product also remained stable through
another normalization and encoder canonicalization and loaded as a molecular
graph. This trial used the same extraction configuration as the published data.

Evidence:

- `data/diagnostics/normalization-repair-trial-20261025/report.json`
- Per-case re-extracted TSVs and `reproduce.py` in that directory.
- Original investigation:
  `data/diagnostics/n1-route434-normalization-20261025/report.json`.

The trial does not by itself certify the rest of the corpus. It also does not
repair existing composite rules, whose certificates refer to their source
representation.

## Implemented preparation contract

Single-step preparation now removes stereo and normalizes all mapped reactants,
products and reagents **before rule extraction**. The old implementation
normalized only the duplicate key before extraction, retained the original
reaction for rule extraction, and changed the policy product afterward. That
could pair an aldehyde model input with a rule requiring its enol representation.

Policy: `stereo-free-complete-reaction-before-extraction/1`.

Original reactions and every source occurrence are retained alongside the
prepared extraction reaction. Changed occurrences have a before/after InChI
ledger. Heavy-atom maps and isotope inventory must survive normalization.
New valence errors are rejected. Existing source limitations remain evidence
for the replay audit rather than being silently corrected or removed.

`retrocomposite audit-pairs` reloads the final TSVs and uses SynPlanner's actual
reactor. Every policy row must recover every supporting expected precursor
multiset, with component multiplicity preserved. Single-step expected sides
follow native spectator removal. Composite expected sides use their certified
`synplanner_net_reactants_v1` boundary.

The audit checks final-input canonicalization, repeated normalization, encoder
stability, molecular graph loading, and one deterministic atom-renumbering probe.
The latter is a regression probe, not proof over all possible mappings.
Replay outcomes, supporting provenance and failure reasons are retained.

Limits: 100 outcomes and 100,000 mapping-work units per pair. A witness proves
replay within these limits; it does not imply recovery within the default
planning limit of five outcomes. Missing witnesses with exhausted limits are
inconclusive. No-outcome status describes the public reactor result; it does not
by itself distinguish input matching failure from rejected patched products.

Single-step preparation publishes usable assets only when every final pair
passes. Otherwise it preserves a marked diagnostic candidate plus its full
audit. No failing rows are automatically dropped. Existing public releases and
frozen splits are not overwritten.

## Full audits: normalization-only candidate (2026-10-25)

The normalized single-step candidate contains **11,208 rules and 57,381 pairs**
from 71,185 source reaction occurrences. Extraction retained all 57,381 unique
reactions with zero extraction errors. The normalization ledger records 177
changed occurrences, of which 34 change a full stereo-free InChI on at least
one reaction side. One native product still changes during final policy export.

Every final pair was audited, with **71,190 supporting-occurrence checks**
(including repeated support across duplicate product/rule rows):

| Result | Pairs |
| --- | ---: |
| Passed | 57,255 |
| No outcomes | 98 |
| Expected precursor multiset not recovered | 27 |
| Atom-renumbering normalization probe failed | 1 |
| Total | 57,381 |

The 126 failed pairs involve 89 vocabulary rules. None hit the declared outcome
or mapping-work limits. The representation failure is n5 route 1902, row 30016:
its exported target replays successfully, but renumbering atoms changes the
normalization result. This is why input stability is reported separately from
precursor recovery.

**All original 16 flagged rows pass in this complete candidate audit**, not only
in the isolated trial. Comparing each residual failure with its old released
rule and old exported target under the same precursor criterion finds:

- **124** also fail with the old released assets under this criterion.
- **2** previously pass and now fail: n5 route **4391** (row 4504) and n1 route
  **2887** (row 14768). Both were old rule 30 and become candidate rule 3438.
  Independent normalization introduces an additional remote tautomer edit
  alongside the amide transformation. The extracted SMARTS has two disconnected
  input patterns, while the actual target is one molecule. The current planning
  application supplies one molecule and obtains no outcomes.

Of the 98 no-outcome pairs, **91 have two input patterns** in the loaded reactor;
seven have one. This is a structural diagnosis, not proof that a single loader
change would repair all of them. These two regressions motivated the reaction-aware follow-up below.

Evidence:

- `data/diagnostics/final-pairs-normalized-v2-20261025/single_step/`
- `data/diagnostics/final-pairs-normalized-v2-20261025/residual_comparison/`
- `data/single_step_normalized_v2.candidate/` — marked `INCOMPLETE`, diagnostic
  only. Its files match the exact hashes in the final-pair audit.

No replacement single-step dataset or split was accepted or published.

Primary composites: **4,231 / 4,232 pairs passed**, covering 4,243 occurrence
supports. Row 384, rule 306, n1 route **166** produces no outcomes. Its exported
target is `c1ccccc1C(F)(F)C(NO)=N`; the composite pattern requires the alternative
amidoxime bond arrangement `C(=N-O)-N`. All representation-stability checks pass,
so an unchanged rule paired with a changed target remains an execution failure.
The corresponding single-step example was among the successful repair trials.

Patent-disjoint composites: **2,988 / 2,988 pairs passed**, covering 2,996
occurrence supports. These are direct composite applications against certified
net precursors. **Ordered unwrapping is not certified by this audit.**

Composite evidence is under
`data/diagnostics/final-pairs-normalized-v2-20261025/{primary,patent_disjoint}/`.
Each report includes `summary.json`, `pairs.jsonl`, `failures.jsonl` and file
hashes. The two reports retain the implementation hashes used for their runs.

## Pre-existing source valence flags

A scan of all 57,381 unique source reactions found two whose iodine-containing
reactant is flagged by Chython's valence check:

| Source reaction | Occurrences |
| --- | --- |
| `US20160031838A1;0090;1830982` | n5 route 3241 |
| `US07008940B1;0468;713309` | n1 route 7489; n5 route 7160 |

The structure is `O=I(=O)Cl` before and after normalization. This is a pre-existing
engine/source compatibility flag, not a valence change introduced by the
repair. Evidence:
`data/diagnostics/normalization-repair-trial-20261025/preexisting_valence_flags.json`.

## Reaction-aware follow-up (2026-10-26)

Implemented in `retrocomposite/reaction_aware.py`, policy
`source-unchanged-tautomer-alignment-with-replay/1`. Preparation retains the
original reaction, the fully normalized reaction and a separate extraction
view. The prepared product is unchanged. Only a source-unchanged remote region
may be aligned in the reactants, and only when all of these checks succeed:

- The change consists of single/double bond shifts, conserves hydrogens and
  preserves atom identity, charge, radicals, connectivity and valid valence.
- The precursor retains its full stereo-free Standard InChI and normalizes back
  to the same mapped molecular graph as the independent normalized reference.
- The serialized extracted rule passes input-stability and replay checks and
  recovers the exact prepared precursor structures.

Source-changed regions are protected. Unassessed proposals retain complete
normalization. Deduplication keeps its previous behavior for unaffected
reactions; only accepted alignment views add an extraction-view distinction.
This preserves the existing duplicate group for the differently represented
n1 4845 / n5 9035 nitro-reduction sources.

Across all 71,185 occurrences, three proposals were assessed: n1 2887 and n5
4391 were aligned; n1 4255 was retained because its proposed component did not
conserve hydrogens. No route or rule IDs control the implementation.

The candidate retains **57,381 unique reactions and policy rows**, with **11,207
rules**, zero extraction errors and 71,190 supporting-occurrence checks. Both
regressions now use the existing amide rule **30** (popularity 183); the extra
remote-tautomer rule disappears through normal native rule aggregation.

| Full single-step replay | Previous candidate | Reaction-aware candidate |
| --- | ---: | ---: |
| Passed | 57,255 | 57,257 |
| No outcomes | 98 | 96 |
| Precursor mismatch | 27 | 27 |
| Representation check failed | 1 | 1 |
| Total | 57,381 | 57,381 |

The complete comparison matches targets and every supporting normalized source
reaction and precursor reference, independently of rule IDs. **Both regressions
pass, all original 16 repaired cases pass, and there are zero new failures.**
Every previously passing pair still passes. The remaining 124 failures have the
same statuses as before. All **107 project tests pass**, including protection of
recorded source changes, atom-map renumbering, rejected unsafe alignments,
retention of duplicate groups and independent final-pair precursor references.

Both sorted composite cohorts were also re-audited against the final code:
primary remains **4,231/4,232** (the known route 166 failure); patent-disjoint
remains **2,988/2,988**. These are direct applications, not ordered unwrapping.

Evidence:

- `data/diagnostics/final-pairs-reaction-aware-v3-20261026/verification.json`
- `comparison.json` in that directory, with all 16 cases and both regressions;
  `compare.py` reproduces that comparison.
- `single_step/`, `primary/` and `patent_disjoint/` contain every replay row,
  all failures, summary counts and checked input hashes.
- `implementation/` preserves the exact preparation, alignment and replay code
  and extraction configuration used for these audits.
- `data/single_step_reaction_aware_v3.candidate/` retains the full diagnostic
  candidate and `reaction_alignment.jsonl`. Its `INCOMPLETE` marker remains:
  the 124 pre-existing failures still prevent release.

Source inputs and audit hashes were verified unchanged. No replacement training
release or checkpoint was published.

## Release implications

The initial normalization implementation passed **99 project tests**.
Tests include the old failure order, recovered chemistry, preservation of source
mapping, complete precursor multiplicity/support, blocked publication, bounded
replay diagnostics, pre-existing valence flags, and direct composite replay.

Reaction-aware extraction now resolves the two normalization-induced remote
tautomer regressions, as verified below. It does not repair general disconnected
query grouping in SynPlanner. The remaining 124 single-step failures still block
a replacement release; no source occurrence, policy pair or rule is silently
dropped to satisfy replay.

The primary composite dataset requires upstream recertification of the route
166 occurrence on the prepared representation. Library rebuilding remains in
RouteInspector; Retrocomposite does not replace certified composite SMARTS by
hand. Ordered replay/unwrapping and final stock checks remain separate work.

Resolve all residual single-step audit failures before accepting replacement
training assets. Then regenerate the exact ordered vocabulary, policy labels,
rule encodings and grouped splits together. Preserve old releases as historical
artifacts. Re-audit source and actual model-input overlaps before a replacement
composite release; the agreed InChI exclusion policy remains unchanged.
