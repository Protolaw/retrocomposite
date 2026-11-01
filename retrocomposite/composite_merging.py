"""Rebuild audited composite cohorts with merged mapped-query training labels."""

from collections import Counter
import json
from pathlib import Path
import shutil

from retrocomposite import preparation as prep
from retrocomposite.composite_identity import POLICY, mapped_rule_identity
from retrocomposite.replay import audit_training_pairs
from retrocomposite.splitting import create_split, load_split, read_tsv, verify_publication

COHORTS = ("primary", "patent_disjoint")


def pair_keys(rules, rows):
    return [(row["product_smiles"], mapped_rule_identity(rules[int(row["rule_id"])]["rule_smarts"]).encoding)
            for row in rows]


def occurrence_payloads(path):
    derived = {"rule_id", "training_pair_index", "training_rule_identity"}
    return Counter(json.dumps({k: v for k, v in record.items() if k not in derived}, sort_keys=True)
                   for record in prep.read_records(path))


def merge_cohorts(cohorts, splits, destination, *, progress=None):
    cohorts, splits, destination = (Path(p).resolve() for p in (cohorts, splits, destination))
    source = verify_publication(cohorts)
    if source["kind"] != "cohort-selection":
        raise ValueError("Expected an audited cohort-selection publication")
    frozen = {}
    for name in COHORTS:
        verify_publication(cohorts / name)
        frozen[name] = load_split(splits / name)
        for suffix in (".tsv", "_policy_data.tsv", ".manifest.json"):
            filename = "composite" + suffix
            if prep.digest(cohorts / name / filename) != prep.digest(splits / name / "assets" / filename):
                raise ValueError(f"Source split vocabulary/pairs differ from cohort: {name}")
    source_files = prep.inputs([cohorts / "preparation.json"] +
                              [splits / name / "preparation.json" for name in COHORTS])
    destination.mkdir(parents=True, exist_ok=False)
    marker = destination / "INCOMPLETE"
    marker.write_text("Composite merge and replay in progress; do not consume.\n")
    reports = {}
    with prep.publication(destination / "cohorts") as out:
        for path in cohorts.iterdir():
            if path.is_file() and path.name != "preparation.json":
                # Preserve historical metadata under its original name; the new
                # vocabulary mapping lives in the bundle-level merging report.
                shutil.copy2(path, out / path.name)
        for name in COHORTS:
            if progress:
                progress(f"Merging {name} vocabulary")
            old, new = cohorts / name, out / name
            records = old / "composite_records.jsonl"
            prep.export_composites(prep.read_records(records), new,
                                   prep.inputs([records, old / "preparation.json"]))
            old_rules, new_rules = (read_tsv(p / "composite.tsv") for p in (old, new))
            old_rows, new_rows = (read_tsv(p / "composite_policy_data.tsv") for p in (old, new))
            old_pairs, new_pairs = pair_keys(old_rules, old_rows), pair_keys(new_rules, new_rows)
            if set(old_pairs) != set(new_pairs) or len(set(new_pairs)) != len(new_pairs):
                raise ValueError(f"Merge changed mapped-query/product support: {name}")
            before, after = occurrence_payloads(records), occurrence_payloads(new / records.name)
            if before != after:
                raise ValueError(f"Merge changed original occurrence evidence: {name}")
            new_ids = {mapped_rule_identity(r["rule_smarts"]).encoding: i for i, r in enumerate(new_rules)}
            if len(new_ids) != len(new_rules):
                raise ValueError("Duplicate mapped-query training labels")
            new_indices = {pair: i for i, pair in enumerate(new_pairs)}
            reports[name] = {
                "old_rules": len(old_rules), "rules": len(new_rules),
                "old_pairs": len(old_rows), "pairs": len(new_rows),
                "occurrences": sum(before.values()),
                "old_to_new_rule_ids": [new_ids[mapped_rule_identity(r["rule_smarts"]).encoding] for r in old_rules],
                "old_to_new_pair_indices": [new_indices[pair] for pair in old_pairs],
                "source_rules_sha256": prep.digest(old / "composite.tsv"),
                "merged_rules_sha256": prep.digest(new / "composite.tsv"),
                "all_original_variants_certificates_decompositions_preserved": True,
                "mapped_query_product_support_preserved": True,
            }
            shutil.copy2(old / "support.json", new / "support.json")
        prep.finish(out, source_files, kind="cohort-selection", policy=source.get("policy"),
                    operation="mapped-query-vocabulary-merging", rule_identity=POLICY,
                    selection_audits="unchanged source occurrence/tactic/family support; training-label counts are in merging.json")

    for name in COHORTS:
        metadata, old_assignments = frozen[name]
        target = destination / "splits" / name
        result = create_split(destination / "cohorts" / name, target,
                              metadata["seed"], metadata["requested_validation_fraction"], metadata["grouping"])
        _, new_assignments = load_split(target)
        transitions = Counter()
        for old, new_index in zip(old_assignments, reports[name]["old_to_new_pair_indices"], strict=True):
            new = new_assignments[new_index]
            if old["group_id"] != new["group_id"] or not set(old["routes"]) <= set(new["routes"]):
                raise ValueError("Merge changed connected group identity or lost routes")
            transitions[old["partition"] + "->" + new["partition"]] += 1
        reports[name]["split"] = {
            **{k: result[k] for k in ("seed", "grouping", "requested_validation_fraction", "train_rows",
                                      "validation_rows", "groups", "overlap")},
            "connected_group_identities_preserved": True,
            "old_pair_partition_transitions": dict(transitions),
        }
        if progress:
            progress(f"Replaying every merged {name} pair against all original occurrence boundaries")
        replay = audit_training_pairs(destination / "cohorts" / name,
                                      destination / "replay" / name, progress=progress)
        reports[name]["replay"] = {k: replay[k] for k in ("status", "counts", "support_checks", "policy_rows")}
    verify_publication(cohorts)
    for name in COHORTS:
        verify_publication(cohorts / name)
        verify_publication(splits / name)
    report = {"schema": "retrocomposite-composite-merging/1", "rule_identity": POLICY,
              "rule_order": prep.COMPOSITE_RULE_ORDER,
              "status": "passed" if all(r["replay"]["status"] == "passed" for r in reports.values()) else "blocked",
              "cohorts": reports}
    prep.write_json(destination / "merging.json", report)
    implementation = destination / "implementation"
    implementation.mkdir()
    for filename in ("composite_identity.py", "composite_merging.py", "preparation.py", "splitting.py", "replay.py"):
        shutil.copy2(Path(__file__).with_name(filename), implementation / filename)
    # The completed bundle can be inspected even when chemistry replay blocks
    # training. Read merging.json/replay summaries; INCOMPLETE means interrupted.
    marker.unlink()
    try:
        prep.finish(destination, source_files, kind="composite-vocabulary-merging",
                    status=report["status"], rule_identity=POLICY,
                    implementation={p.name: prep.digest(p) for p in implementation.iterdir()})
    except BaseException:
        marker.write_text("Composite merge verification failed; do not consume.\n")
        raise
    return report
