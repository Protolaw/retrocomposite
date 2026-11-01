"""Re-export existing cohorts by popularity and rebuild matching frozen splits.

Preserves exact rule/product pairs, occurrence records, selection audits and
train/validation memberships. Writes a new local bundle; never overwrites one.
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import shutil

from retrocomposite import preparation as prep
from retrocomposite.splitting import (
    create_split,
    load_split,
    read_json,
    read_tsv,
    verify_publication,
)

COHORTS = ("primary", "patent_disjoint")


def pair_keys(rules, rows):
    return [(r["product_smiles"], rules[int(r["rule_id"])]["rule_smarts"]) for r in rows]


def occurrence_payloads(path):
    return Counter(
        json.dumps({k: v for k, v in r.items() if k not in {"rule_id", "training_pair_index"}}, sort_keys=True)
        for r in prep.read_records(path)
    )


def reorder(cohorts, splits, destination):
    cohorts, splits, destination = (Path(p).resolve() for p in (cohorts, splits, destination))
    source = verify_publication(cohorts)
    if source["kind"] != "cohort-selection":
        raise ValueError("Expected an audited cohort-selection publication")
    frozen = {}
    for name in COHORTS:
        verify_publication(cohorts / name)
        frozen[name] = load_split(splits / name)
        for suffix in (".tsv", "_policy_data.tsv", ".manifest.json"):
            filename = f"composite{suffix}"
            if prep.digest(cohorts / name / filename) != prep.digest(splits / name / "assets" / filename):
                raise ValueError(f"Source split vocabulary/pairs differ from cohort: {name}")
    source_files = prep.inputs(
        [cohorts / "preparation.json"] + [splits / name / "preparation.json" for name in COHORTS]
    )
    destination.mkdir(parents=True, exist_ok=False)
    marker = destination / "INCOMPLETE"
    marker.write_text("Reordering in progress; do not consume.\n")
    reports = {}
    with prep.publication(destination / "cohorts") as out:
        # These audits contain identities and source witnesses, not rule IDs.
        for path in cohorts.iterdir():
            if path.is_file() and path.name != "preparation.json":
                shutil.copy2(path, out / path.name)
        for name in COHORTS:
            old, new = cohorts / name, out / name
            records = old / "composite_records.jsonl"
            prep.export_composites(prep.read_records(records), new, prep.inputs([records, old / "preparation.json"]), merge_equivalent=False)
            old_rules, new_rules = (read_tsv(p / "composite.tsv") for p in (old, new))
            old_rows, new_rows = (read_tsv(p / "composite_policy_data.tsv") for p in (old, new))
            old_pairs, new_pairs = pair_keys(old_rules, old_rows), pair_keys(new_rules, new_rows)
            if Counter(old_pairs) != Counter(new_pairs):
                raise ValueError(f"Reordering changed product/rule pairs: {name}")
            if occurrence_payloads(records) != occurrence_payloads(new / records.name):
                raise ValueError(f"Reordering changed occurrence evidence: {name}")
            old_support = {r["rule_smarts"]: int(r["popularity"]) for r in old_rules}
            if old_support != {r["rule_smarts"]: int(r["popularity"]) for r in new_rules}:
                raise ValueError(f"Reordering changed rule popularity: {name}")
            new_ids = {r["rule_smarts"]: i for i, r in enumerate(new_rules)}
            new_indices = {pair: i for i, pair in enumerate(new_pairs)}
            reports[name] = {
                "rules": len(new_rules),
                "pairs": len(new_rows),
                "occurrences": sum(occurrence_payloads(records).values()),
                "old_to_new_rule_ids": [new_ids[r["rule_smarts"]] for r in old_rules],
                "old_to_new_pair_indices": [new_indices[pair] for pair in old_pairs],
                "source_rules_sha256": prep.digest(old / "composite.tsv"),
                "sorted_rules_sha256": prep.digest(new / "composite.tsv"),
                "pairs_and_occurrences_preserved": True,
            }
            shutil.copy2(old / "support.json", new / "support.json")
        prep.write_json(out / "vocabulary_reordering.json", {
            "schema": "retrocomposite-vocabulary-reordering/1",
            "rule_order": prep.COMPOSITE_RULE_ORDER,
            "source_cohorts": str(cohorts),
            "cohorts": reports,
        })
        prep.finish(out, source_files, kind="cohort-selection", policy=source.get("policy"),
                    operation="vocabulary-reordering", chemistry_replay_revalidated=False)

    # Build after publishing cohorts so split provenance uses permanent paths.
    for name in COHORTS:
        metadata, old_assignments = frozen[name]
        target = destination / "splits" / name
        create_split(destination / "cohorts" / name, target,
                     metadata["seed"], metadata["requested_validation_fraction"], metadata["grouping"])
        _, new_assignments = load_split(target)
        old_rules = read_tsv(cohorts / name / "composite.tsv")
        new_rules = read_tsv(destination / "cohorts" / name / "composite.tsv")
        def memberships(rules, assignments):
            return {pair: {k: a[k] for k in ("partition", "group_id", "routes", "patents")}
                    for pair, a in zip(pair_keys(rules, assignments), assignments, strict=True)}
        if memberships(old_rules, old_assignments) != memberships(new_rules, new_assignments):
            raise ValueError(f"Reordering changed frozen memberships: {name}")
        reports[name]["split_memberships_preserved"] = True
    verify_publication(cohorts)
    for name in COHORTS:
        verify_publication(splits / name)
    prep.write_json(destination / "reordering.json", {
        "schema": "retrocomposite-vocabulary-reordering/1",
        "rule_order": prep.COMPOSITE_RULE_ORDER,
        "chemistry_replay_revalidated": False,
        "cohorts": reports,
    })
    marker.unlink()
    try:
        prep.finish(destination, source_files, kind="composite-vocabulary-reordering",
                    implementation={"reorder_composites.py": prep.digest(__file__),
                                    "preparation.py": prep.digest(prep.__file__)})
    except BaseException:
        marker.write_text("Reordering verification failed; do not consume.\n")
        raise
    return {name: {k: v for k, v in report.items() if not k.startswith("old_to_new")}
            for name, report in reports.items()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohorts", type=Path, required=True)
    parser.add_argument("--splits", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(reorder(args.cohorts, args.splits, args.output), indent=2))
