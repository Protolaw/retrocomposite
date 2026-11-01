"""Replay final policy pairs, with complete supporting-precursor evidence.

This audits executable representations. It never changes E1/E2/E3 identity,
filters examples, repairs rules, or certifies composite unwrapping.
"""

from collections import Counter, defaultdict
import csv
import json
from pathlib import Path

from retrocomposite import preparation as prep
from retrocomposite.identity import identity_metadata, molecule_identity


def _tsv(path):
    with Path(path).open(newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def precursor_ids(molecules):
    # A sorted list, not a set: repeated components must remain repeated.
    return sorted(molecule_identity(m) for m in molecules)


def _single_step_support(assets, rules, rows):
    from chython import smiles
    from synplan.chem.utils import unite_molecules
    from synplan.chem.reaction.curation.standardizing import RemoveReagentsStandardizer
    from retrocomposite.splitting import single_step_sources

    # Verify native-row normalization ledger, counts and every provenance link.
    single_step_sources(assets, rules, rows)
    native_path = assets / "single_step_policy_data.native.tsv"
    native = _tsv(native_path) if native_path.exists() else rows
    reactions = {
        record["input_index"]: record
        for record in prep.read_records(assets / "reaction_provenance.jsonl")
    }
    pairs = defaultdict(list)
    standardizer = RemoveReagentsStandardizer()
    for rule_id, rule in enumerate(rules):
        for index in map(int, rule["reaction_indices"].split(",")):
            record = reactions[index]
            source = smiles(record["mapped"])
            key = (molecule_identity(unite_molecules(source.products)), rule_id)
            variants = record.get("source_reactions", [])
            if variants and record["mapped"] not in {v.get("extraction_mapped", v["normalized_mapped"]) for v in variants}:
                raise ValueError("Extraction reaction is absent from its normalized source/extraction evidence")
            # Check every original occurrence, not merely the chosen duplicate
            # representative. Legacy assets retain one representative instead.
            witnesses = variants or [{"normalized_mapped": record["mapped"]}]
            for variant in witnesses:
                extraction = variant.get("extraction_mapped", variant["normalized_mapped"])
                if extraction != variant["normalized_mapped"]:
                    if str(prep.normalize_mapped_reaction(smiles(extraction))) != str(smiles(variant["normalized_mapped"])):
                        raise ValueError("Extraction view changes normalized source chemistry")
                witness = smiles(variant["normalized_mapped"])
                evidence = {
                    "input_index": index,
                    "sources": ([{k: variant[k] for k in ("dataset", "route_id", "node_path", "reaction_id")}]
                                if variants else record["sources"]),
                    "source_mapped": variant["normalized_mapped"],
                    "extraction_mapped": extraction,
                }
                try:
                    # Native extraction removes unchanged spectators first.
                    reaction = standardizer(witness.copy())
                    prepared = prep.normalize_mapped_reaction(reaction)
                    valence_flags = []
                    for component_index, mol in enumerate(prepared.reactants):
                        check = mol.copy()
                        check.kekule()
                        invalid = list(check.check_valence())
                        if invalid:
                            valence_flags.append({"component_index": component_index,
                                                  "atom_maps": invalid, "smiles": str(mol)})
                    evidence.update(
                        full_source_precursors=precursor_ids(witness.reactants),
                        expected_precursors=precursor_ids(prepared.reactants),
                        expected_precursor_valence_flags=valence_flags,
                    )
                    if prep.molecule_key(str(unite_molecules(witness.products))) != prep.molecule_key(str(unite_molecules(source.products))):
                        raise ValueError("Normalized source variant has a different model input")
                except Exception as error:
                    evidence["preparation_error"] = {"type": type(error).__name__, "message": str(error)}
                pairs[key].append(evidence)
    return [pairs[(molecule_identity(r["product_smiles"]), int(r["rule_id"]))]
            for r in native]


def _composite_support(assets, rules, rows):
    from retrocomposite.splitting import composite_sources

    composite_sources(assets, rules, rows)
    supports = [[] for _ in rows]
    for record in prep.read_records(assets / "composite_records.jsonl"):
        boundary = record["certificate"].get("abstraction_boundary", {})
        components = boundary.get("retained_components")
        if boundary.get("policy") != "synplanner_net_reactants_v1" or not components:
            raise ValueError("Composite needs explicit certified net-precursor boundary")
        supports[record["training_pair_index"]].append({
            "occurrence_id": record["provenance"]["reference_occurrence_id"],
            "certified_variant_smarts": record["composite_rule"],
            "sources": [record["provenance"]],
            "expected_precursors": precursor_ids(
                prep.molecule(c["mapped_smiles"]) for c in components
            ),
            "source_precursor_smiles": [c["mapped_smiles"] for c in components],
            "omitted_component_count": len(boundary.get("omitted_components", [])),
        })
    return supports


def replay_pair(product, reactor, expected_sets, *, max_outcomes=100, max_mapping_work=100_000):
    from chython import smiles
    from synplan.chem.reaction.reactor import apply_reaction_rule
    from synplan.ml.featurization.molecules import mol_to_numpy
    from synplan.chem.utils import safe_canonicalization

    target = smiles(product)
    target.clean_stereo()
    prepared = prep.molecule(product)
    encoded = target.copy()
    encoded.canonicalize()
    remapped = target.copy()
    numbers = list(remapped.atoms_numbers)
    remapped.remap(dict(zip(numbers, range(max(numbers) + len(numbers), max(numbers), -1))))
    checks = {
        "canonical_input": str(prepared) == str(target),
        "normalization_idempotent": str(prep.molecule(str(prepared))) == str(prepared),
        "encoder_preserves_structure": str(encoded) == str(target),
        "atom_renumbering_invariant": str(safe_canonicalization(remapped)) == str(prepared),
        "molecule_graph_loads": mol_to_numpy(target) is not None,
    }
    diagnostics = []
    outcomes = list(apply_reaction_rule(
        target, reactor, top_reactions_num=max_outcomes,
        max_mapping_work=max_mapping_work, diagnostics=diagnostics,
    ))
    identities = [precursor_ids(molecules) for molecules in outcomes]
    matches = [expected in identities for expected in expected_sets]
    capped = len(outcomes) >= max_outcomes
    if not all(checks.values()):
        status = "representation_failed"
    elif all(matches):
        status = "passed"
    elif diagnostics or capped:
        status = "inconclusive"
    elif not outcomes:
        status = "no_outcomes"
    else:
        status = "precursor_mismatch"
    result = {
        "status": status, "checks": checks, "outcome_count": len(outcomes),
        "support_matches": matches, "diagnostics": diagnostics, "outcome_cap_reached": capped,
    }
    if status == "passed":
        result["witnesses"] = [
            {"precursor_inchis": list(expected),
             "precursor_smiles": [str(m) for m in outcomes[identities.index(list(expected))]]}
            for expected in sorted({tuple(values) for values in expected_sets})
        ]
    else:
        result["observed_precursor_inchis"] = identities
        result["observed_precursor_smiles"] = [[str(m) for m in ms] for ms in outcomes]
    return result


def audit_training_pairs(assets, destination, *, max_outcomes=100, max_mapping_work=100_000, progress=None):
    """Audit every exported row and every associated source-precursor multiset.

    A blocked audit is still saved completely. It never implies permission to
    drop failing rows or publish a partial vocabulary. No model is trained.
    """
    from synplan.utils.loading import load_reaction_rules

    assets = Path(assets).resolve()
    implementation = {p.name: prep.digest(p) for p in
                      (Path(__file__), Path(prep.__file__), Path(__file__).with_name("reaction_aware.py"),
                       Path(__file__).with_name("composite_identity.py"), Path(__file__).with_name("splitting.py"))}
    if max_outcomes < 1 or max_mapping_work < 1:
        raise ValueError("Replay limits must be positive")
    stems = [stem for stem in ("single_step", "composite") if (assets / f"{stem}.tsv").is_file()]
    if len(stems) != 1:
        raise ValueError("Expected one single-step or composite vocabulary")
    stem = stems[0]
    rule_path, policy_path = assets / f"{stem}.tsv", assets / f"{stem}_policy_data.tsv"
    names = [rule_path.name, policy_path.name, f"{stem}.manifest.json"]
    names += (["reaction_provenance.jsonl", "single_step_policy_data.native.tsv", "policy_product_normalization.jsonl", "reaction_normalization.jsonl", "reaction_alignment.jsonl"]
              if stem == "single_step" else ["composite_records.jsonl", "composite_rule_mapping.json"])
    source_files = prep.inputs([assets / name for name in names if (assets / name).exists()])
    rules, rows = _tsv(rule_path), _tsv(policy_path)
    if not rules or not rows:
        raise ValueError("Empty training assets")
    if {int(r["rule_id"]) for r in rows} != set(range(len(rules))):
        raise ValueError("Invalid or unsupported vocabulary labels")
    reactors = load_reaction_rules(str(rule_path))
    if len(reactors) != len(rules):
        raise ValueError("Rule loading changed vocabulary size")
    if progress:
        progress(f"Loading provenance for {len(rows)} final pairs")
    supports = (_single_step_support if stem == "single_step" else _composite_support)(assets, rules, rows)
    counts, support_count = Counter(), 0
    with prep.publication(destination) as out:
        with (out / "pairs.jsonl").open("w") as all_rows, (out / "failures.jsonl").open("w") as failures:
            for index, (row, evidence) in enumerate(zip(rows, supports, strict=True)):
                if not evidence:
                    raise ValueError(f"Missing precursor evidence at row {index}")
                rule_id = int(row["rule_id"])
                item = {"row_index": index, "rule_id": rule_id, "product_smiles": row["product_smiles"],
                        "rule_smarts": rules[rule_id]["rule_smarts"], "supports": evidence}
                try:
                    if any("preparation_error" in e for e in evidence):
                        raise ValueError("Supporting reaction could not be prepared; see per-source errors")
                    item.update(replay_pair(row["product_smiles"], reactors[rule_id],
                                [e["expected_precursors"] for e in evidence],
                                max_outcomes=max_outcomes, max_mapping_work=max_mapping_work))
                except Exception as error:
                    item.update(status="error", error_type=type(error).__name__, error=str(error))
                line = json.dumps(item, sort_keys=True) + "\n"
                all_rows.write(line)
                if item["status"] != "passed":
                    failures.write(line)
                counts[item["status"]] += 1
                support_count += len(evidence)
                if progress and ((index + 1) % 1000 == 0 or index + 1 == len(rows)):
                    progress(f"Replayed {index + 1}/{len(rows)} pairs: {dict(counts)}")
        summary = {
            "schema": "retrocomposite-final-pair-replay/1",
            "status": "passed" if counts["passed"] == len(rows) else "blocked",
            "kind": stem, "policy_rows": len(rows), "rule_count": len(rules),
            "support_checks": support_count, "counts": dict(counts),
            "identity": identity_metadata(), "software": prep.software(),
            "max_outcomes": max_outcomes, "max_mapping_work": max_mapping_work,
            "scope": "final exported targets, molecule-encoder stability and direct rule replay; composite unwrapping is not certified",
            "precursor_policy": "full multiset after native extraction spectator removal, or certified composite net boundary; uniformly stereo-free normalized",
            "inputs": {Path(v["path"]).name: v["sha256"] for v in source_files},
            "implementation": implementation,
        }
        prep.write_json(out / "summary.json", summary)
        prep.finish(out, source_files, kind="final-pair-replay-audit", status=summary["status"])
    return summary
