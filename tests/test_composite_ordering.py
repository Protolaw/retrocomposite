"""Vocabulary order must preserve the meaning of every training label."""

import json

from retrocomposite import preparation as prep
from retrocomposite.splitting import read_tsv
from retrocomposite.composite_identity import mapped_rule_identity
from test_preparation import record


def test_popularity_sort_preserves_labels_support_and_determinism(tmp_path):
    specs = [
        ("[C:1]-[O:2]>>[C:1].[O:2]", ["CCO"]),
        ("[N:2]-[C:1]>>[N:2].[C:1]", ["CCN", "CCCN"]),
        ("[O:2]-[C:1]>>[O:2].[C:1]", ["CCO", "CCCO"]),
        ("[S:2]-[C:1]>>[S:2].[C:1]", ["CCS", "CCCS", "CCCCS"]),
    ]
    records = []
    for rule, products in specs:
        for product in products:
            records.append({**record(), "composite_rule": rule, "product_smiles": product,
                            "rule_id": 99, "training_pair_index": 99})
    # Many occurrences for a single pair must not move this rule to the top.
    for i in range(5):
        records.append({**records[0], "provenance": {"reference_occurrence_id": f"duplicate-{i}"}})
    out = tmp_path / "sorted"
    prep.export_composites(records, out, [])
    rules = read_tsv(out / "composite.tsv")
    rows = read_tsv(out / "composite_policy_data.tsv")
    assert [r["rule_smarts"] for r in rules] == [specs[i][0] for i in (3, 0, 1)]
    assert [int(r["popularity"]) for r in rules] == [3, 2, 2]
    expected_pairs = {(prep.molecule_key(r["product_smiles"]), mapped_rule_identity(r["composite_rule"]).encoding) for r in records}
    assert {(r["product_smiles"], mapped_rule_identity(rules[int(r["rule_id"])]["rule_smarts"]).encoding) for r in rows} == expected_pairs
    for rule_id, rule in enumerate(rules):
        assert list(map(int, rule["reaction_indices"].split(","))) == [
            i for i, row in enumerate(rows) if int(row["rule_id"]) == rule_id
        ]
    witnesses = list(prep.read_records(out / "composite_records.jsonl"))
    assert len(witnesses) == len(records)
    for witness in witnesses:
        pair = rows[witness["training_pair_index"]]
        assert witness["product_smiles"] == pair["product_smiles"]
        assert witness["rule_id"] == int(pair["rule_id"])
        assert mapped_rule_identity(witness["composite_rule"]) == mapped_rule_identity(rules[witness["rule_id"]]["rule_smarts"])
    manifest = json.loads((out / "composite.manifest.json").read_text())
    assert manifest["rules_sha256"] == prep.digest(out / "composite.tsv")
    assert manifest["rule_order"] == prep.COMPOSITE_RULE_ORDER
    other = tmp_path / "shuffled"
    prep.export_composites(reversed(records), other, [])
    for name in ("composite.tsv", "composite_policy_data.tsv", "composite_records.jsonl", "composite.manifest.json", "composite_rule_mapping.json"):
        assert (out / name).read_bytes() == (other / name).read_bytes()
