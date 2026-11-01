"""Auditable adapters; chemistry extraction remains owned by SynPlanner."""

from collections import defaultdict
from contextlib import contextmanager
import csv
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import tempfile


def digest(path):
    h = sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_jsonl(path, values):
    with Path(path).open("w") as stream:
        for value in values:
            stream.write(json.dumps(value, sort_keys=True, default=str) + "\n")


def software():
    result = {}
    for name in ("retrocomposite", "route-inspector", "SynPlanner", "chython-synplan"):
        try:
            result[name] = version(name)
        except PackageNotFoundError:
            result[name] = "not-installed"
    return result


def inputs(paths):
    return [{"path": str(p), "sha256": digest(p)} for p in paths]


def finish(root, source_files, **details):
    for item in source_files:
        if digest(item["path"]) != item["sha256"]:
            raise ValueError(f"Input changed during export: {item['path']}")
    write_json(
        root / "preparation.json",
        {
            "schema": "retrocomposite-preparation/1",
            "inputs": source_files,
            "software": software(),
            "stereo": "ignored",
            **details,
            "outputs": {
                str(p.relative_to(root)): digest(p)
                for p in sorted(root.rglob("*"))
                if p.is_file()
            },
        },
    )


@contextmanager
def publication(destination):
    destination = Path(destination).resolve()
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".retrocomposite-", dir=destination.parent
    ) as tmp:
        root = Path(tmp) / "publication"
        root.mkdir()
        yield root
        # Reserve the destination exclusively before moving files; no existing
        # publication is ever replaced, including a concurrent creator's.
        destination.mkdir()
        marker = destination / "INCOMPLETE"
        marker.write_text("Publication in progress; do not consume.\n")
        try:
            for file in sorted(
                root.iterdir(), key=lambda p: p.name == "preparation.json"
            ):
                os.replace(file, destination / file.name)
            marker.unlink()
        except BaseException:
            (destination / "INCOMPLETE").write_text(
                "Publication interrupted; do not consume.\n"
            )
            raise


def molecule(text):
    from chython import smiles
    from chython.containers import MoleculeContainer
    from synplan.chem.utils import safe_canonicalization

    mol = smiles(text)
    if not isinstance(mol, MoleculeContainer) or not len(mol):
        raise ValueError("Expected a nonempty molecule")
    mol.clean_stereo()
    return safe_canonicalization(mol)


def molecule_key(text):
    return str(molecule(text))


def route_sources(sources):
    from route_inspector.routes.io import iter_route_json_file

    if not sources or set(sources) - {"n1", "n5"}:
        raise ValueError("Route inputs must be labelled n1 and/or n5")
    for dataset, path in sorted(sources.items()):
        for route_id, root in iter_route_json_file(path):
            yield dataset, str(route_id), root


def prepare_stock(sources, destination):
    from route_inspector.routes.access import molecule_node_smiles, walk_route_nodes

    source_files = inputs(sources.values())
    stocks = {label: set() for label in sources}
    targets = {label: set() for label in sources}
    counts = defaultdict(int)
    with publication(destination) as out:
        with (out / "leaves.jsonl").open("w") as evidence:
            for dataset, route_id, root in route_sources(sources):
                counts[dataset] += 1
                targets[dataset].add(molecule_key(molecule_node_smiles(root)))
                for path, node in walk_route_nodes(root):
                    if node.get("type") != "mol" or node.get("children"):
                        continue
                    key = molecule_key(molecule_node_smiles(node))
                    stocks[dataset].add(key)
                    evidence.write(
                        json.dumps(
                            {
                                "dataset": dataset,
                                "route_id": route_id,
                                "node_path": path,
                                "smiles": key,
                            }
                        )
                        + "\n"
                    )
        for label, values in sorted(stocks.items()):
            (out / f"{label}.smi").write_text("".join(s + "\n" for s in sorted(values)))
            (out / f"{label}_targets.smi").write_text(
                "".join(s + "\n" for s in sorted(targets[label]))
            )
        union = set().union(*stocks.values())
        if not union:
            raise ValueError("No terminal molecules found")
        (out / "union.smi").write_text("".join(s + "\n" for s in sorted(union)))
        finish(
            out,
            source_files,
            kind="leaf-stock",
            routes=dict(counts),
            stock_counts={k: len(v) for k, v in stocks.items()},
            union_count=len(union),
            terminal_policy="molecule node without children; ignore stored stock flags",
        )


def prepare_single_step(sources, destination, config_path, workers=1):
    from chython import smiles
    from chython.containers import ReactionContainer
    from route_inspector.routes.access import reaction_nodes, reaction_smiles_from_node
    from synplan.chem.reaction.rules.config import RuleExtractionConfig
    from synplan.chem.reaction.rules.extraction import extract_rules_from_reactions

    if workers < 1:
        raise ValueError("workers must be positive")
    config = RuleExtractionConfig.from_yaml(config_path)
    if not config.ignore_stereo or not config.reverse_rule:
        raise ValueError("Extraction must be retrospective with ignore_stereo=true")
    source_files = inputs([*sources.values(), config_path])
    records = {}
    occurrence_count = 0
    for dataset, route_id, root in route_sources(sources):
        for path, node in reaction_nodes(root):
            text = reaction_smiles_from_node(node)
            rxn = smiles(text)
            if (
                not isinstance(rxn, ReactionContainer)
                or not rxn.reactants
                or not rxn.products
            ):
                raise ValueError(f"Invalid reaction in {dataset}:{route_id}:{path}")
            for mol in (*rxn.reactants, *rxn.products, *rxn.reagents):
                mol.clean_stereo()
            # Direction is the cleaned route's forward reaction. Do not reverse
            # recorded mapping; SynPlanner's reverse_rule handles retro extraction.
            key = (
                tuple(sorted(molecule_key(str(m)) for m in rxn.reactants)),
                tuple(sorted(molecule_key(str(m)) for m in rxn.products)),
            )
            mapped = format(rxn, "m")
            record = records.setdefault(key, {"mapped": mapped, "sources": []})
            record["mapped"] = min(record["mapped"], mapped)
            record["sources"].append(
                {
                    "dataset": dataset,
                    "route_id": route_id,
                    "node_path": path,
                    "reaction_id": (node.get("metadata") or {}).get("ID"),
                }
            )
            occurrence_count += 1
    if not records:
        raise ValueError("No reactions found")
    ordered = [records[k] for k in sorted(records)]
    with publication(destination) as out:
        reaction_file = out / "reactions.smi"
        reaction_file.write_text("".join(r["mapped"] + "\n" for r in ordered))
        write_jsonl(
            out / "reaction_provenance.jsonl",
            (
                {"input_index": i, "input_line": i + 1, **r}
                for i, r in enumerate(ordered)
            ),
        )
        extract_rules_from_reactions(
            config=config,
            reaction_data_path=str(reaction_file),
            reaction_rules_path=str(out / "single_step.tsv"),
            num_cpus=workers,
            batch_size=100,
            ignore_errors=False,
            error_file_path=out / "single_step.errors.tsv",
            audit_file_path=out / "single_step.audit.tsv",
        )
        # Native manifests can contain staging paths. Keep the published artifact portable.
        manifest_path = out / "single_step.manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["source_stereo_file"] = "single_step.stereo.jsonl"
        write_json(manifest_path, manifest)
        normalization = normalize_policy_products(out / "single_step_policy_data.tsv")
        summary = validate_training_assets(out / "single_step.tsv")
        with (out / "single_step.tsv").open() as stream:
            retained = {
                int(index)
                for row in csv.DictReader(stream, delimiter="\t")
                for index in row["reaction_indices"].split(",")
                if index
            }
        if not retained.issubset(range(len(ordered))):
            raise ValueError("Rule provenance points outside the exported reactions")
        finish(
            out,
            source_files,
            kind="single-step",
            reaction_occurrences=occurrence_count,
            unique_reactions=len(ordered),
            duplicates=occurrence_count - len(ordered),
            retained_reaction_count=len(retained),
            excluded_reaction_count=len(ordered) - len(retained),
            deduplication="stereo-free reactant/product multisets; reagents excluded",
            config=digest(config_path),
            workers=workers,
            policy_product_normalization=normalization,
            **summary,
        )


def normalize_policy_products(path):
    """Align native product strings with the shared model/stock identity policy.

    SynPlanner emits the parsed product spelling, which can still be Kekule or
    otherwise unprepared for its own molecule encoder. Preserve the native rows
    and a change ledger; keep row order, multiplicity, and rule IDs unchanged.
    """
    path = Path(path)
    native = path.with_suffix(".native.tsv")
    if native.exists():
        raise FileExistsError(native)
    path.rename(native)
    changed = []
    count = 0
    with native.open(newline="") as source, path.open("w", newline="") as output:
        reader = csv.DictReader(source, delimiter="\t")
        if reader.fieldnames != ["product_smiles", "rule_id"]:
            raise ValueError("Unexpected policy-data columns")
        writer = csv.DictWriter(
            output, fieldnames=reader.fieldnames, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        for index, row in enumerate(reader):
            original = row["product_smiles"]
            canonical = molecule_key(original)
            if canonical != original:
                changed.append(
                    {
                        "row_index": index,
                        "rule_id": int(row["rule_id"]),
                        "original": original,
                        "canonical": canonical,
                    }
                )
            writer.writerow({**row, "product_smiles": canonical})
            count += 1
    write_jsonl(path.parent / "policy_product_normalization.jsonl", changed)
    return {
        "policy": "retrocomposite.molecule_key; same as stock and grouped splitting",
        "rows": count,
        "changed_rows": len(changed),
        "native_rows": native.name,
    }


def validate_training_assets(rules_path):
    from synplan.utils.loading import load_reaction_rules
    from synplan.chem.reaction.rules.representation import rule_smarts_from_reactors
    from synplan.ml.featurization.rules import query_cgr_graphs_from_smarts

    rules_path = Path(rules_path)
    rules = load_reaction_rules(str(rules_path))
    if not rules:
        raise ValueError("Empty rule vocabulary")
    # Validate the requested rule graph encoding, not only the TSV syntax.
    graphs = query_cgr_graphs_from_smarts(
        rule_smarts_from_reactors(rules), schema_version="1"
    )
    if len(graphs) != len(rules):
        raise ValueError("QueryCGR graph count differs from the vocabulary")
    policy_path = rules_path.with_name(rules_path.stem + "_policy_data.tsv")
    row_count = 0
    used = set()
    with policy_path.open(newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if reader.fieldnames != ["product_smiles", "rule_id"]:
            raise ValueError("Unexpected policy-data columns")
        for row in reader:
            rule_id = int(row["rule_id"])
            if not 0 <= rule_id < len(rules):
                raise ValueError("Out-of-range rule ID")
            if molecule_key(row["product_smiles"]) != row["product_smiles"]:
                raise ValueError("Product must be canonical, unmapped and stereo-free")
            used.add(rule_id)
            row_count += 1
    if used != set(range(len(rules))):
        raise ValueError("Some rules have no training products")
    return {"rule_count": len(rules), "policy_rows": row_count}


def read_records(path):
    path = Path(path)
    if path.suffix == ".jsonl":
        with path.open() as stream:
            for line in stream:
                if line.strip():
                    yield json.loads(line)
    else:
        data = json.loads(path.read_text())
        if not isinstance(data, list):
            raise ValueError(
                "Composite JSON must be a list of explicit product/rule records"
            )
        yield from data


def check_composite_record(record):
    from chython import smarts

    if record.get("kind") != "rrseq_cons":
        raise ValueError("Only consecutive linear tactics are supported")
    if record.get("dataset_id") != "n1":
        raise ValueError("Composite supervision must come from n1")
    if record.get("composite_identity_version") != 3:
        raise ValueError("Composite identity version 3 is required")
    certificate = record.get("certificate", {})
    required = (
        "source_occurrence_certified",
        "source_chemistry_equivalent",
        "source_mapping_consistent",
        "composite_chemistry_equivalent",
        "composite_mapping_consistent",
    )
    if not all(certificate.get(key) is True for key in required):
        raise ValueError("Missing successful source and composite replay certificate")
    if not record.get("provenance") or not record.get("decomposition"):
        raise ValueError("Occurrence provenance and decomposition are required")
    rule = "".join(record["composite_rule"].split())
    query = smarts(rule)
    if not query.reactants or not query.products:
        raise ValueError("Composite must have a target and precursor side")
    if "@" in rule or "/" in rule or "\\" in rule:
        raise ValueError(
            "Stereo-constrained composite rules are outside this experiment"
        )
    return {
        **record,
        "composite_rule": rule,
        "product_smiles": molecule_key(record["product_smiles"]),
    }


def export_composites(records, destination, source_files):
    grouped = defaultdict(list)
    for record in records:
        checked = check_composite_record(record)
        grouped[(checked["composite_rule"], checked["product_smiles"])].append(checked)
    if not grouped:
        raise ValueError("No eligible linear composite records")
    rules = sorted({r for r, _p in grouped})
    ids = {rule: i for i, rule in enumerate(rules)}
    pairs = sorted(grouped, key=lambda key: (ids[key[0]], key[1]))
    with publication(destination) as out:
        indices = defaultdict(list)
        for index, (rule, _product) in enumerate(pairs):
            indices[rule].append(index)
        with (out / "composite.tsv").open("w", newline="") as stream:
            writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
            writer.writerow(["rule_smarts", "popularity", "reaction_indices"])
            for rule in rules:
                writer.writerow(
                    [rule, len(indices[rule]), ",".join(map(str, indices[rule]))]
                )
        with (out / "composite_policy_data.tsv").open("w", newline="") as stream:
            writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
            writer.writerow(["product_smiles", "rule_id"])
            writer.writerows((product, ids[rule]) for rule, product in pairs)
        write_jsonl(
            out / "composite_records.jsonl",
            (
                {**r, "rule_id": ids[rule], "training_pair_index": i}
                for i, (rule, product) in enumerate(pairs)
                for r in sorted(
                    grouped[(rule, product)],
                    key=lambda r: json.dumps(r, sort_keys=True),
                )
            ),
        )
        write_json(
            out / "composite.manifest.json",
            {
                "schema": "synplan-rules/2",
                "stereo_schema": 1,
                "preserve_stereo": False,
                "rules_sha256": digest(out / "composite.tsv"),
                "rule_count": len(rules),
                "input_sha256": digest(out / "composite_records.jsonl"),
                "policy_compatibility": "requires this exact ordered vocabulary",
                "reaction_indices_semantics": "zero-based unique product/rule training-pair indices",
            },
        )
        summary = validate_training_assets(out / "composite.tsv")
        finish(
            out,
            source_files,
            kind="linear-composites",
            training_dataset="n1",
            occurrence_count=sum(map(len, grouped.values())),
            **summary,
        )


def library_records(reference_path, composite_path, routes_path):
    from route_inspector.reference_library import ReferenceTacticLibrary
    from route_inspector.composite_rules.library import CompositeDecompositionLibrary

    # Fail early on old publications, before an expensive library audit.
    raw = json.loads((Path(composite_path) / "manifest.json").read_text())
    if raw.get("library_format_version") != 3:
        raise ValueError(
            "Refresh the composite library in RouteInspector: format/identity v3 required"
        )
    if raw["source_routes_sha256"] != digest(routes_path):
        raise ValueError("Cleaned routes hash differs from composite library source")
    with ReferenceTacticLibrary.load(reference_path, verification="full") as reference:
        with CompositeDecompositionLibrary.load(
            composite_path, verification="full"
        ) as composites:
            composites.assert_reference_library(reference)
            for entry in composites.entries(kind="rrseq_cons"):
                for link in composites.links_for_entry(
                    entry.composite_id, kind="rrseq_cons"
                ):
                    if link.dataset_id != "n1":
                        raise ValueError(
                            "Use a standalone n1 publication, not n5 or merged supervision"
                        )
                    occurrence = reference.get_occurrence(link.reference_occurrence_id)
                    if (
                        occurrence.route.source_identity
                        != "sha256:" + raw["source_routes_sha256"]
                    ):
                        raise ValueError("Occurrence source differs from cleaned input")
                    if (
                        occurrence.route.route_id != link.route_id
                        or occurrence.route.dataset_id != link.dataset_id
                        or occurrence.route.source_identity != link.source_identity
                    ):
                        raise ValueError("Link and occurrence routes differ")
                    yield {
                        "kind": link.kind,
                        "dataset_id": link.dataset_id,
                        "composite_identity_version": entry.identity_version,
                        "composite_rule": composites.certified_rule(link),
                        "product_smiles": occurrence.motif_target_smiles,
                        "certificate": dict(link.certificate),
                        "provenance": {
                            "route_id": link.route_id,
                            "source_identity": link.source_identity,
                            "reference_library_id": reference.library_id,
                            "composite_library_id": composites.library_id,
                            "reference_occurrence_id": link.reference_occurrence_id,
                            "tactic_entry_id": link.tactic_entry_id,
                            "composite_id": link.composite_id,
                            "variant_id": link.variant_id,
                            "selected_reaction_node_paths": occurrence.selected_reaction_node_paths,
                        },
                        "decomposition": dict(occurrence.native_payload),
                    }
