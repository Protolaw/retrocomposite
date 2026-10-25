# Identity regressions

`n5_identity_regressions.json` retains only molecule/reaction type, current SMILES,
child structure, and source reaction ID from cleaned n5 routes 3032 and 9035.
Source SHA-256: `5a27be2e0199f2bacd66556122f50906a24e27946bb30b1d9472d55d725e71af`.
These fixtures reproduce actual identity comparison failures; they are not
training data. All extraction, parsing, identity checks, and rendering in the
updated workflow use Chython.
