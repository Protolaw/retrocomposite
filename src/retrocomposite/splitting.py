"""Frozen molecule/route connected-component splits with complete provenance."""

from collections import Counter, defaultdict
import csv
from hashlib import sha256
import json
from pathlib import Path
import shutil

from retrocomposite import preparation as prep
from retrocomposite.identity import (
    MOLECULE_IDENTITY_POLICY,
    identity_metadata,
    molecule_identity,
)

SCHEMA = "retrocomposite-grouped-split/2"
LEGACY_SCHEMA = "retrocomposite-grouped-split/1"


def read_json(path):
    return json.loads(Path(path).read_text())


def read_tsv(path):
    with Path(path).open(newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def verify_publication(root):
    """Verify all published bytes, including nested cohort audit files."""
    root = Path(root).resolve()
    if (root / "INCOMPLETE").exists():
        raise ValueError(f"Incomplete publication: {root}")
    manifest = read_json(root / "preparation.json")
    if not manifest.get("outputs"):
        raise ValueError(f"Missing output hashes: {root}")
    for name, expected in manifest["outputs"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or prep.digest(path) != expected:
            raise ValueError(f"Publication hash mismatch: {name}")
    return manifest


def route_key(dataset, route_id):
    if dataset not in {"n1", "n5"} or route_id is None:
        raise ValueError("Missing dataset/route provenance")
    return json.dumps([dataset, str(route_id)], separators=(",", ":"))


def single_step_sources(assets, rules, rows):
    """Join by product/rule, retaining ALL supporting deduplicated reactions.

    Native extraction may reorder rows. Never infer reaction provenance from
    policy row positions, or choose one occurrence of a repeated product/rule.
    """
    from chython import smiles
    from synplan.chem.utils import unite_molecules

    # Join the native products back to their reactions before applying the
    # recorded model-input normalization. Some keto/enol changes made during
    # preparation are not merged by Standard InChI. Their row provenance still
    # comes from the original product, while grouping uses the exported input.
    provenance_rows = rows
    native = assets / "single_step_policy_data.native.tsv"
    ledger = assets / "policy_product_normalization.jsonl"
    if native.exists():
        provenance_rows = read_tsv(native)
        if len(provenance_rows) != len(rows):
            raise ValueError("Native and normalized policy row counts differ")
        expected_changes = []
        for index, (original, normalized) in enumerate(
            zip(provenance_rows, rows, strict=True)
        ):
            if original["rule_id"] != normalized["rule_id"]:
                raise ValueError("Normalization changed a policy rule label")
            if original["product_smiles"] != normalized["product_smiles"]:
                expected_changes.append(
                    {
                        "row_index": index,
                        "rule_id": int(original["rule_id"]),
                        "original": original["product_smiles"],
                        "canonical": normalized["product_smiles"],
                    }
                )
        if not ledger.is_file() or list(prep.read_records(ledger)) != expected_changes:
            raise ValueError("Policy normalization ledger does not match native rows")
    elif ledger.exists():
        raise ValueError("Policy normalization ledger has no native rows")
    reactions = {}
    for record in prep.read_records(assets / "reaction_provenance.jsonl"):
        index = record["input_index"]
        if index in reactions or not record.get("sources"):
            raise ValueError("Duplicate or unsupported reaction provenance")
        rxn = smiles(record["mapped"])
        product = molecule_identity(unite_molecules(rxn.products))
        routes = {route_key(s["dataset"], s["route_id"]) for s in record["sources"]}
        reactions[index] = (product, routes)
    pairs, counts = defaultdict(set), Counter()
    for rule_id, rule in enumerate(rules):
        for value in rule["reaction_indices"].split(","):
            product, routes = reactions[int(value)]
            pair = (product, rule_id)
            pairs[pair].update(routes)
            counts[pair] += 1
    observed = Counter(
        (molecule_identity(r["product_smiles"]), int(r["rule_id"]))
        for r in provenance_rows
    )
    if observed != counts:
        raise ValueError("Policy rows do not match reaction/rule provenance")
    return [
        sorted(pairs[(molecule_identity(r["product_smiles"]), int(r["rule_id"]))])
        for r in provenance_rows
    ]


def composite_sources(assets, rules, rows):
    routes = [set() for _ in rows]
    for record in prep.read_records(assets / "composite_records.jsonl"):
        if record.get("dataset_id") != "n1":
            raise ValueError("Composite supervision must be n1-only")
        index = record["training_pair_index"]
        if not isinstance(index, int) or not 0 <= index < len(rows):
            raise ValueError("Composite pair index is out of range")
        row = rows[index]
        rule_id = int(row["rule_id"])
        if (
            record["product_smiles"] != row["product_smiles"]
            or record["rule_id"] != rule_id
            or record["composite_rule"] != rules[rule_id]["rule_smarts"]
        ):
            raise ValueError("Composite record does not match its training pair")
        provenance = record["provenance"]
        if not provenance.get("source_identity"):
            raise ValueError("Missing composite source identity")
        routes[index].add(route_key("n1", provenance["route_id"]))
    if not all(routes):
        raise ValueError("Missing composite occurrence provenance")
    return [sorted(values) for values in routes]


def patent_sources(assets, kind, sources, manifest):
    if kind == "linear-composites":
        rows = prep.read_records(assets.parent / "route_audit.jsonl")
        return {
            route_key(r["dataset_id"], r["route_id"]): r["patents"] for r in rows
        }, []
    from retrocomposite.selection import route_patents

    if not sources:
        raise ValueError("Patent grouping of single-step data needs --n1 and --n5")
    known = {item["sha256"] for item in manifest["inputs"]}
    source_files = prep.inputs(sources.values())
    if any(item["sha256"] not in known for item in source_files):
        raise ValueError("Patent route sources differ from the preparation inputs")
    patents = {}
    for dataset, route_id, root in prep.route_sources(sources):
        key = route_key(dataset, route_id)
        if key in patents:
            raise ValueError("Duplicate route ID in patent source")
        patents[key] = route_patents(root)
    return patents, source_files


def assign_groups(
    examples, seed, validation_fraction, grouping, *, legacy_smiles=False
):
    """Union overlapping provenance, then select whole groups with train coverage."""
    if grouping not in {"route", "patent"}:
        raise ValueError("grouping must be route or patent")
    if not 0 < validation_fraction < 1 or not 0 <= seed < 2**32:
        raise ValueError("Require 0 < validation_fraction < 1 and a uint32 seed")
    if not examples:
        raise ValueError("No examples to split")
    if not legacy_smiles:
        examples = [
            {**example, "molecule_inchi": molecule_identity(example["product_smiles"])}
            for example in examples
        ]
    parents = list(range(len(examples)))

    def find(i):
        while i != parents[i]:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    tokens, owner = [], {}
    for i, example in enumerate(examples):
        if not example["routes"]:
            raise ValueError("Every row needs route provenance")
        keys = {
            "molecule:"
            + example["product_smiles" if legacy_smiles else "molecule_inchi"]
        }
        keys.update("route:" + r for r in example["routes"])
        if grouping == "patent":
            keys.update("patent:" + p for p in example["patents"])
        tokens.append(keys)
        for key in sorted(keys):
            if key in owner:
                parents[find(i)] = find(owner[key])
            else:
                owner[key] = i
    components = defaultdict(list)
    for i in range(len(examples)):
        components[find(i)].append(i)
    groups = []
    for indices in components.values():
        identity = "\n".join(sorted(set().union(*(tokens[i] for i in indices))))
        group_id = sha256(identity.encode()).hexdigest()
        groups.append(
            {
                "group_id": group_id,
                "indices": indices,
                "rule_counts": Counter(examples[i]["rule_id"] for i in indices),
                "forced_train": grouping == "patent"
                and any(not examples[i]["patents_complete"] for i in indices),
            }
        )
    groups.sort(key=lambda g: sha256(f"{seed}:{g['group_id']}".encode()).hexdigest())
    remaining = Counter(e["rule_id"] for e in examples)
    target = len(examples) * validation_fraction
    validation = set()

    def eligible(group):
        return not group["forced_train"] and all(
            remaining[k] - count >= 1 for k, count in group["rule_counts"].items()
        )

    for group in groups:
        size = len(group["indices"])
        if eligible(group) and abs(target - len(validation) - size) < abs(
            target - len(validation)
        ):
            validation.update(group["indices"])
            remaining.subtract(group["rule_counts"])
    if not validation:
        candidates = [g for g in groups if eligible(g)]
        if candidates:
            group = min(candidates, key=lambda g: abs(target - len(g["indices"])))
            validation.update(group["indices"])
    assignments = []
    for group in groups:
        partition = "validation" if group["indices"][0] in validation else "train"
        for i in group["indices"]:
            assignments.append(
                {
                    "row_index": i,
                    **examples[i],
                    "group_id": group["group_id"],
                    "partition": partition,
                    "forced_train_missing_patent": group["forced_train"],
                }
            )
    assignments.sort(key=lambda a: a["row_index"])
    counts = {
        part: Counter(a["rule_id"] for a in assignments if a["partition"] == part)
        for part in ("train", "validation")
    }
    missing_patents = sum(a["forced_train_missing_patent"] for a in assignments)
    overlap = {}
    for label, field in (
        ("molecules", "product_smiles" if legacy_smiles else "molecule_inchi"),
        ("routes", "routes"),
        ("groups", "group_id"),
        ("known_patents", "patents"),
    ):
        if label == "known_patents" and grouping != "patent":
            continue
        sets = {}
        for part in ("train", "validation"):
            values = [a[field] for a in assignments if a["partition"] == part]
            sets[part] = (
                set().union(*(set(v) for v in values))
                if field in {"routes", "patents"}
                else set(values)
            )
        overlap[label] = len(sets["train"] & sets["validation"])
    if any(overlap.values()):
        raise AssertionError("Connected-component split leaked grouping identities")
    blocked_reason = None
    if not validation:
        blocked_reason = "No whole group can be held out while retaining training support for every rule"
    if missing_patents:
        blocked_reason = "Incomplete patent provenance cannot establish a patent-disjoint holdout; resolve it or explicitly use route grouping"
    report = {
        "status": "blocked" if blocked_reason else "ready",
        "blocked_reason": blocked_reason,
        "rows": len(examples),
        "groups": len(groups),
        "largest_group_rows": max(len(g["indices"]) for g in groups),
        "train_rows": len(examples) - len(validation),
        "validation_rows": len(validation),
        "actual_validation_fraction": len(validation) / len(examples),
        "rules_without_validation": sorted(
            set(counts["train"]) - set(counts["validation"])
        ),
        "rule_counts": counts,
        "missing_patent_rows_forced_train": missing_patents,
        "overlap": overlap,
    }
    return assignments, report


def create_split(
    assets,
    destination,
    seed=42,
    validation_fraction=0.1,
    grouping="route",
    sources=None,
):
    assets = Path(assets).resolve()
    metadata = verify_publication(assets)
    kind = metadata["kind"]
    if kind not in {"single-step", "linear-composites"}:
        raise ValueError("Expected single-step or eligible composite assets")
    source_paths = [assets / "preparation.json"]
    if kind == "linear-composites":
        parent = verify_publication(assets.parent)
        support = read_json(assets / "support.json")
        selection = read_json(assets.parent / "selection.json")
        if (
            parent["kind"] != "cohort-selection"
            or assets.name not in {"primary", "patent_disjoint"}
            or support["status"] != "ready"
            or selection["cohorts"][assets.name]["status"] != "ready"
        ):
            raise ValueError("Use a ready, audited composite cohort")
        source_paths += [assets.parent / "preparation.json", assets / "support.json"]
    stem = "single_step" if kind == "single-step" else "composite"
    rule_path, policy_path = assets / f"{stem}.tsv", assets / f"{stem}_policy_data.tsv"
    rules, rows = read_tsv(rule_path), read_tsv(policy_path)
    if not rules or not rows:
        raise ValueError("Empty training assets")
    for row in rows:
        if (
            not 0 <= int(row["rule_id"]) < len(rules)
            or prep.molecule_key(row["product_smiles"]) != row["product_smiles"]
        ):
            raise ValueError("Invalid rule label or noncanonical molecule")
    if {int(r["rule_id"]) for r in rows} != set(range(len(rules))):
        raise ValueError("Every vocabulary rule must have training support")
    row_routes = (single_step_sources if kind == "single-step" else composite_sources)(
        assets, rules, rows
    )
    patents, extra_sources = ({}, [])
    if grouping == "patent":
        patents, extra_sources = patent_sources(assets, kind, sources, metadata)
        missing = set().union(*(set(r) for r in row_routes)) - set(patents)
        if missing:
            raise ValueError(
                f"Missing route provenance for patent grouping: {sorted(missing)[:5]}"
            )
    examples = []
    for row, routes in zip(rows, row_routes, strict=True):
        examples.append(
            {
                "product_smiles": row["product_smiles"],
                "rule_id": int(row["rule_id"]),
                "routes": routes,
                "patents": sorted(
                    {p for r in routes for p in patents.get(r, {}).get("ids", [])}
                ),
                "patents_complete": bool(patents)
                and all(patents[r]["complete"] for r in routes),
            }
        )
    assignments, report = assign_groups(examples, seed, validation_fraction, grouping)
    source_files = prep.inputs(source_paths + [rule_path, policy_path]) + extra_sources
    with prep.publication(destination) as out:
        (out / "assets").mkdir()
        for suffix in (".tsv", "_policy_data.tsv", ".manifest.json"):
            shutil.copy2(assets / f"{stem}{suffix}", out / "assets" / f"{stem}{suffix}")
        prep.write_jsonl(out / "assignments.jsonl", assignments)
        for part in ("train", "validation"):
            with (out / f"{part}.tsv").open("w", newline="") as stream:
                writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
                writer.writerow(["product_smiles", "rule_id"])
                writer.writerows(
                    (a["product_smiles"], a["rule_id"])
                    for a in assignments
                    if a["partition"] == part
                )
        result = {
            "schema": SCHEMA,
            "molecule_identity": identity_metadata(),
            "seed": seed,
            "grouping": grouping,
            "requested_validation_fraction": validation_fraction,
            "kind": kind,
            "cohort": assets.name if kind == "linear-composites" else "single_step",
            "policy_data": f"assets/{stem}_policy_data.tsv",
            "rules": f"assets/{stem}.tsv",
            "source_assets": str(assets),
            "source_manifest_sha256": prep.digest(assets / "preparation.json"),
            "algorithm": "seeded component order; greedy row-fraction approximation; at least one training row per rule",
            **report,
        }
        prep.write_json(out / "split.json", result)
        # Detect changes to any provenance sidecar during selection too.
        verify_publication(assets)
        if kind == "linear-composites":
            verify_publication(assets.parent)
        prep.finish(
            out,
            source_files,
            kind="grouped-split",
            implementation={
                "splitting.py": prep.digest(__file__),
                "identity.py": prep.digest(Path(__file__).with_name("identity.py")),
            },
        )
    return result


def load_split(path):
    """Fail closed on tampering, empty holdouts, index drift, or group overlap."""
    path = Path(path).resolve()
    verify_publication(path)
    metadata = read_json(path / "split.json")
    if (
        metadata.get("schema") not in {SCHEMA, LEGACY_SCHEMA}
        or metadata["status"] != "ready"
    ):
        raise ValueError("Training requires a ready grouped split with validation rows")
    if metadata["schema"] == SCHEMA and (
        metadata.get("molecule_identity", {}).get("policy") != MOLECULE_IDENTITY_POLICY
    ):
        raise ValueError("Unsupported split molecule identity policy")
    rows = read_tsv(path / metadata["policy_data"])
    assignments = list(prep.read_records(path / "assignments.jsonl"))
    if [a["row_index"] for a in assignments] != list(range(len(rows))):
        raise ValueError("Split row indices are not complete and ordered")
    rebuilt, report = assign_groups(
        assignments,
        metadata["seed"],
        metadata["requested_validation_fraction"],
        metadata["grouping"],
        legacy_smiles=metadata["schema"] == LEGACY_SCHEMA,
    )
    if rebuilt != assignments or report["status"] != "ready":
        raise ValueError("Split assignments do not match the frozen grouping policy")
    for a, row in zip(assignments, rows, strict=True):
        if (a["product_smiles"], a["rule_id"]) != (
            row["product_smiles"],
            int(row["rule_id"]),
        ):
            raise ValueError("Split row contents differ from policy data")
    for key in ("train_rows", "validation_rows", "groups"):
        if report[key] != metadata[key]:
            raise ValueError("Split manifest counts disagree with assignments")
    return metadata, assignments
