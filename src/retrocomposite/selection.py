"""Frozen shared-tactic cohorts and exclusion audits; no model fitting."""

from collections import Counter, defaultdict
from contextlib import ExitStack
from dataclasses import dataclass, field
from importlib.metadata import version
from pathlib import Path
import json
import re

from retrocomposite import preparation as prep
from retrocomposite.identity import identity_metadata, molecule_identity
from retrocomposite.segments import Segment, adjacent_paths, node_at, ordered_paths

POLICY = "retrocomposite-cohort-selection/3"
SEGMENT_POLICY = "ordered-stereo-free-inchi-reaction-pair/1"
GRAPH_AUDIT_POLICY = "full-mapped-reaction-pair-with-all-intermediate-alignments/2"
PATENT_POLICY = "paroutes-document-identifiers-including-legacy-us-reissue-sir/2"


def witness(dataset, route_id, **details):
    return {"dataset_id": dataset, "route_id": str(route_id), **details}


def route_patents(root):
    """Parse original PaRoutes reaction IDs, including preprocessing split ancestry.

    Normalize formatting only; preserve publication kind codes. Missing or opaque
    IDs never establish disjointness. A route can have several source patents.
    """
    from route_inspector.datasets.source_ids import reaction_source_identifiers
    from route_inspector.routes.access import reaction_nodes

    evidence, missing = [], []
    for path, node in reaction_nodes(root):
        ids = reaction_source_identifiers(node, adapter="paroutes-semicolon-v1")
        normalized = re.sub(r"[\s/\-]", "", ids.source_document_id.upper())
        # Older US grants omit kind codes; reissues and statutory invention
        # registrations have RE/H number prefixes. Preserve the original ID,
        # including any supplied kind, rather than inventing a suffix or family.
        if not re.fullmatch(
            r"(?:[A-Z]{2}\d{4,}[A-Z]\d?|US\d{7,8}|USRE\d{5,6}(?:E\d?)?|USH\d{4,7}(?:H\d?)?)",
            normalized,
        ):
            missing.append(
                {"node_path": path, "source_record_id": ids.source_record_id}
            )
        else:
            evidence.append(
                {
                    "node_path": path,
                    "patent_id": normalized,
                    "source_record_id": ids.source_record_id,
                }
            )
    return {
        "ids": sorted({r["patent_id"] for r in evidence}),
        "complete": bool(evidence) and not missing,
        "evidence": evidence,
        "unresolved": missing,
    }


def shared_tactics(n1_entries, n5_entries):
    """Use lookup keys only as indexes; native exact identity decides membership."""
    by_key = defaultdict(list)
    for entry in n5_entries:
        by_key[entry.identity.lookup_key].append(entry)
    shared = {}
    for entry in sorted(n1_entries, key=lambda e: e.entry_id):
        matches = sorted(
            e.entry_id
            for e in by_key[entry.identity.lookup_key]
            if entry.identity.equivalent_to(e.identity)
        )
        if matches:
            shared[entry.entry_id] = {
                "n1_entry_id": entry.entry_id,
                "n5_entry_ids": matches,
                "identity": entry.identity.to_dict(),
            }
    return shared


@dataclass
class ReferenceIndex:
    targets: dict = field(default_factory=lambda: defaultdict(list))
    inputs: dict = field(default_factory=lambda: defaultdict(list))
    segments: dict = field(default_factory=lambda: defaultdict(list))
    patents: dict = field(default_factory=lambda: defaultdict(list))
    routes: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    patent_incomplete: list = field(default_factory=list)


def build_reference_index(routes_path, max_alignments, progress=None):
    from route_inspector.routes.access import molecule_node_smiles, walk_route_nodes

    index = ReferenceIndex()
    seen = set()
    source_identity = "sha256:" + prep.digest(routes_path)
    for dataset, route_id, root in prep.route_sources({"n5": routes_path}):
        if route_id in seen:
            raise ValueError("Duplicate n5 route identifier")
        seen.add(route_id)
        if progress and len(seen) % 250 == 0:
            progress(f"Indexed {len(seen)} n5 routes")
        source = witness(dataset, route_id, source_identity=source_identity)
        patents = route_patents(root)
        index.routes.append({**source, "patents": patents})
        if not patents["complete"]:
            index.patent_incomplete.append(source)
        for patent in patents["ids"]:
            index.patents[patent].append(source)
        try:
            if root.get("type") != "mol":
                raise ValueError("Route root is not a molecule")
            key = molecule_identity(molecule_node_smiles(root))
            index.targets[key].append(source)
            for path, node in walk_route_nodes(root):
                if node.get("type") == "mol" and (not path or node.get("children")):
                    key = molecule_identity(molecule_node_smiles(node))
                    index.inputs[key].append({**source, "node_path": path})
            for first, second in adjacent_paths(root):
                pair_witness = {**source, "reaction_node_paths": [first, second]}
                segment = Segment.from_route(
                    root, first, second, pair_witness, max_alignments
                )
                index.segments[segment.signature].append(segment)
        except (ValueError, TypeError, KeyError, IndexError) as exc:
            index.errors.append({**source, "error": str(exc)})
    if not seen:
        raise ValueError("n5 reference corpus is empty")
    return index


def assess_occurrence(
    record, root, route_id, source_identity, index, shared, max_alignments
):
    from route_inspector.routes.access import molecule_node_smiles

    provenance = record.get("provenance", {})
    audit = {
        "dataset_id": "n1",
        "source_identity": source_identity,
        "reference_occurrence_id": provenance.get("reference_occurrence_id"),
        "route_id": route_id,
        "tactic_entry_id": provenance.get("tactic_entry_id"),
        "variant_id": provenance.get("variant_id"),
        "exclusions": {},
        "errors": [],
    }
    reasons = audit["exclusions"]
    # Compute E1/E2 independently of E3 so every known reason survives.
    try:
        key = molecule_identity(molecule_node_smiles(root))
        if key in index.targets:
            reasons["E1_SHARED_FINAL_TARGET"] = index.targets[key]
    except (ValueError, TypeError, KeyError) as exc:
        audit["errors"].append({"check": "E1", "error": str(exc)})
    try:
        key = molecule_identity(record["product_smiles"])
        if key in index.inputs:
            reasons["E2_SHARED_MOTIF_INPUT"] = index.inputs[key]
    except (ValueError, TypeError, KeyError) as exc:
        audit["errors"].append({"check": "E2", "error": str(exc)})
    if provenance.get("tactic_entry_id") not in shared:
        reasons["NOT_SHARED_TACTIC"] = []
    checked = None
    try:
        checked = prep.check_composite_record(record)
        if (
            provenance.get("source_identity") != source_identity
            or str(provenance.get("route_id")) != route_id
        ):
            raise ValueError("Occurrence source or route does not match cleaned n1")
        if any(
            not provenance.get(key)
            for key in ("reference_occurrence_id", "variant_id", "composite_id")
        ):
            raise ValueError("Occurrence, composite and exact variant IDs are required")
        paths = ordered_paths(provenance["selected_reaction_node_paths"])
        motif_key = molecule_identity(
            molecule_node_smiles(node_at(root, paths[0][:-1]))
        )
        if motif_key != molecule_identity(checked["product_smiles"]):
            raise ValueError("Motif input differs from the selected route occurrence")
        for first, second in zip(paths, paths[1:]):
            try:
                segment = Segment.from_route(
                    root,
                    first,
                    second,
                    witness("n1", route_id, reaction_node_paths=[first, second]),
                    max_alignments,
                )
                for reference in index.segments.get(segment.signature, []):
                    # Signature equality is sufficient. Exact graph differences or
                    # unresolved audits cannot rescue an overlapping occurrence.
                    reasons.setdefault("E3_SHARED_CONCRETE_SEGMENT", []).append(
                        {
                            "n1_reaction_node_paths": [first, second],
                            "n5": reference.witness,
                            "reaction_signature": segment.signature,
                            "exact_graph_audit": segment.audit_graph_match(reference),
                        }
                    )
            except (ValueError, TypeError, KeyError, IndexError) as exc:
                audit["errors"].append(
                    {
                        "check": "E3",
                        "reaction_node_paths": [first, second],
                        "error": str(exc),
                    }
                )
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        audit["errors"].append({"check": "occurrence", "error": str(exc)})
    if index.errors:
        audit["errors"].append(
            {
                "check": "n5_reference",
                "error": "Incomplete n5 reference index; see reference_errors.jsonl",
            }
        )
    audit["primary_status"] = (
        "excluded" if reasons else "quarantined" if audit["errors"] else "eligible"
    )
    return checked, audit


def support(records):
    tactics, variants, pairs = defaultdict(list), defaultdict(list), set()
    for record in records:
        p = record["provenance"]
        occurrence = p["reference_occurrence_id"]
        tactics[p["tactic_entry_id"]].append(occurrence)
        variants[(p["composite_id"], p["variant_id"], record["composite_rule"])].append(
            occurrence
        )
        pairs.add((record["product_smiles"], record["composite_rule"]))
    return {
        "occurrences": len(records),
        "training_pairs": len(pairs),
        "rules": len({r["composite_rule"] for r in records}),
        "tactics": {k: sorted(v) for k, v in sorted(tactics.items())},
        "variants": [
            {
                "composite_id": key[0],
                "variant_id": key[1],
                "composite_rule": key[2],
                "occurrences": sorted(values),
            }
            for key, values in sorted(variants.items())
        ],
    }


def publish_cohort(out, records, shared, source_files, blocked=False):
    records.sort(
        key=lambda r: (
            r["provenance"]["reference_occurrence_id"],
            r["provenance"]["variant_id"],
        )
    )
    if records:
        prep.export_composites(records, out, source_files)
    else:
        out.mkdir()
        prep.write_jsonl(out / "composite_records.jsonl", [])
    supported = support(records)
    n5_entry_ids = sorted(
        {entry for key in supported["tactics"] for entry in shared[key]["n5_entry_ids"]}
    )
    n5_occurrences = {
        o["reference_occurrence_id"]: o
        for key in supported["tactics"]
        for o in shared[key].get("n5_occurrences", [])
    }
    result = {
        "status": "blocked" if blocked else "ready" if records else "empty",
        **supported,
        "retained_n5_entry_ids": n5_entry_ids,
        "n5_covered_occurrences": len(n5_occurrences),
        "n5_covered_routes": sorted({o["route_id"] for o in n5_occurrences.values()}),
        "dropped_shared_tactics": sorted(set(shared) - set(supported["tactics"])),
    }
    prep.write_json(out / "support.json", result)
    return result


def select_cohorts(
    n1_routes,
    n5_routes,
    records,
    shared,
    destination,
    *,
    source_files=None,
    library_metadata=None,
    max_alignments=256,
    progress=None,
):
    """Select from verified library records; writes both cohorts and full audits.

    The public CLI verifies libraries first. This core is separately testable
    with explicit records, without fabricating certified production libraries.
    """
    if max_alignments < 1:
        raise ValueError("max_alignments must be positive")
    if Path(destination).exists():
        raise FileExistsError(f"Refusing to overwrite {destination}")
    n1_routes, n5_routes = Path(n1_routes).resolve(), Path(n5_routes).resolve()
    source_files = source_files or prep.inputs([n1_routes, n5_routes])
    source_identity = "sha256:" + prep.digest(n1_routes)
    if progress:
        progress("Indexing the frozen n5 reference corpus")
    index = build_reference_index(n5_routes, max_alignments, progress)
    by_route = defaultdict(list)
    unique = set()
    for record in records:
        p = record["provenance"]
        key = (p["reference_occurrence_id"], p.get("variant_id"))
        if key in unique:
            raise ValueError("Duplicate occurrence/variant link")
        unique.add(key)
        by_route[str(p["route_id"])].append(record)
    primary, sensitivity, audits, route_audits = [], [], [], []
    if progress:
        progress("Applying primary and patent exclusions to n1 occurrences")
    seen = set()
    for _, route_id, root in prep.route_sources({"n1": n1_routes}):
        if route_id in seen:
            raise ValueError("Duplicate n1 route identifier")
        seen.add(route_id)
        if progress and len(seen) % 250 == 0:
            progress(
                f"Assessed {len(seen)} n1 routes; {len(primary)} primary links retained"
            )
        patents = route_patents(root)
        overlap = {p: index.patents[p] for p in patents["ids"] if p in index.patents}
        route_audits.append(
            {
                **witness("n1", route_id, source_identity=source_identity),
                "patents": patents,
                "n5_patent_matches": overlap,
            }
        )
        for record in by_route.pop(route_id, []):
            checked, audit = assess_occurrence(
                record, root, route_id, source_identity, index, shared, max_alignments
            )
            audit["patent_exclusions"] = {}
            if overlap:
                audit["patent_exclusions"]["SHARED_PATENT"] = overlap
            if not patents["complete"]:
                audit["patent_exclusions"]["UNRESOLVED_N1_PATENT"] = patents[
                    "unresolved"
                ]
            if index.patent_incomplete:
                audit["patent_exclusions"]["INCOMPLETE_N5_PATENTS"] = {
                    "unresolved_route_count": len(index.patent_incomplete),
                    "witness_file": "route_audit.jsonl",
                    "dataset_id": "n5",
                }
            audit["sensitivity_status"] = audit["primary_status"]
            if audit["primary_status"] == "eligible":
                # Never carry old row indices or excluded occurrence evidence into a cohort.
                checked = {
                    k: v
                    for k, v in checked.items()
                    if k not in {"rule_id", "training_pair_index"}
                }
                primary.append(checked)
                if audit["patent_exclusions"]:
                    audit["sensitivity_status"] = (
                        "excluded" if overlap else "quarantined"
                    )
                else:
                    sensitivity.append(checked)
            audits.append(audit)
    for route_id, orphaned in by_route.items():
        for record in orphaned:
            audits.append(
                {
                    "reference_occurrence_id": record["provenance"][
                        "reference_occurrence_id"
                    ],
                    "route_id": route_id,
                    "variant_id": record["provenance"].get("variant_id"),
                    "tactic_entry_id": record["provenance"].get("tactic_entry_id"),
                    "exclusions": {},
                    "patent_exclusions": {},
                    "errors": [
                        {"check": "source_route", "error": "Missing cleaned n1 route"}
                    ],
                    "primary_status": "quarantined",
                    "sensitivity_status": "quarantined",
                }
            )
    audits.sort(key=lambda a: (a["reference_occurrence_id"], a.get("variant_id") or ""))
    if progress:
        progress("Publishing cohort assets, support and audit manifests")
    with prep.publication(destination) as out:
        prep.write_json(
            out / "shared_tactics.json", {"schema": POLICY, "tactics": shared}
        )
        prep.write_jsonl(out / "occurrence_audit.jsonl", audits)
        prep.write_jsonl(
            out / "route_audit.jsonl",
            sorted(
                route_audits + index.routes,
                key=lambda r: (r["dataset_id"], r["route_id"]),
            ),
        )
        prep.write_jsonl(out / "reference_errors.jsonl", index.errors)
        prep.write_jsonl(
            out / "n5_molecule_index.jsonl",
            (
                {"kind": kind, "molecule": key, "witnesses": values}
                for kind, entries in (
                    ("target", index.targets),
                    ("model_input", index.inputs),
                )
                for key, values in sorted(entries.items())
            ),
        )
        prep.write_jsonl(
            out / "n5_segment_index.jsonl",
            (
                {
                    "reaction_signature": signature,
                    "witnesses": [s.witness for s in values],
                }
                for signature, values in sorted(index.segments.items())
            ),
        )
        cohorts = {
            "primary": publish_cohort(
                out / "primary", primary, shared, source_files, bool(index.errors)
            ),
            "patent_disjoint": publish_cohort(
                out / "patent_disjoint",
                sensitivity,
                shared,
                source_files,
                bool(index.errors or index.patent_incomplete),
            ),
        }
        report = {
            "schema": POLICY,
            "segment_identity": SEGMENT_POLICY,
            "molecule_identity": identity_metadata(),
            "patent_identity": "PaRoutes original reaction IDs; uppercase; remove whitespace/slash/hyphen; retain kind code",
            "patent_identity_policy": PATENT_POLICY,
            "max_alignments": max_alignments,
            "exact_graph_audit": {
                "policy": GRAPH_AUDIT_POLICY,
                "matcher": "NetworkX VF2 with complete atom and bond labels",
                "networkx_version": version("networkx"),
                "affects_eligibility": False,
                "scope": "Every E3 signature-match witness; repeated witnesses count per occurrence/variant link",
                "status_counts": dict(
                    sorted(
                        Counter(
                            match["exact_graph_audit"]["status"]
                            for audit in audits
                            for match in audit["exclusions"].get(
                                "E3_SHARED_CONCRETE_SEGMENT", []
                            )
                        ).items()
                    )
                ),
            },
            "shared_tactic_count": len(shared),
            "libraries": library_metadata or {},
            "cohorts": cohorts,
            "occurrence_links": len(audits),
            "counting_unit": "certified reference-occurrence / exact-variant link",
            "unique_occurrences": len({a["reference_occurrence_id"] for a in audits}),
            "links_with_errors": sum(bool(a["errors"]) for a in audits),
            "n1_patent_complete_routes": sum(
                r["patents"]["complete"] for r in route_audits
            ),
            "n1_patent_incomplete_routes": sum(
                not r["patents"]["complete"] for r in route_audits
            ),
            "patent_reason_counts": dict(
                sorted(
                    Counter(k for a in audits for k in a["patent_exclusions"]).items()
                )
            ),
            "reason_counts": dict(
                sorted(Counter(k for a in audits for k in a["exclusions"]).items())
            ),
            "reason_combinations": dict(
                sorted(
                    Counter(
                        "|".join(sorted(a["exclusions"])) or "NONE" for a in audits
                    ).items()
                )
            ),
            "primary_status_counts": dict(Counter(a["primary_status"] for a in audits)),
            "sensitivity_status_counts": dict(
                Counter(a["sensitivity_status"] for a in audits)
            ),
            "n5_reference_errors": len(index.errors),
            "n5_patent_incomplete_routes": len(index.patent_incomplete),
            "unchanged_inputs": ["single-step n1+n5 corpus", "union leaf stock"],
            "e3_coverage": "All adjacent ordered InChI reaction pairs in all n5 routes; any repeated sequence of length >=2 contains a matching pair",
            "reagent_policy": "Compare full participating reactants/products; ignore reaction middle-field reagents",
        }
        prep.write_json(out / "selection.json", report)
        prep.finish(
            out,
            source_files,
            kind="cohort-selection",
            policy=POLICY,
            implementation={
                p.name: prep.digest(p)
                for p in (
                    Path(__file__),
                    Path(__file__).with_name("segments.py"),
                    Path(__file__).with_name("identity.py"),
                    Path(prep.__file__),
                )
            },
        )
    return report


def select_from_libraries(
    n1_routes,
    n5_routes,
    n1_reference,
    n5_reference,
    n1_composites,
    destination,
    max_alignments=256,
    progress=None,
):
    from route_inspector.reference_library import ReferenceTacticLibrary

    if Path(destination).exists():
        raise FileExistsError(f"Refusing to overwrite {destination}")
    if max_alignments < 1:
        raise ValueError("max_alignments must be positive")
    if progress:
        progress("Verifying source publications and shared tactic identities")
    paths = [
        Path(p).resolve()
        for p in (n1_routes, n5_routes, n1_reference, n5_reference, n1_composites)
    ]
    n1_routes, n5_routes, n1_reference, n5_reference, n1_composites = paths
    # Snapshot all library files as well as routes; finish() rechecks every hash.
    files = [n1_routes, n5_routes]
    for directory in paths[2:]:
        if not (directory / "manifest.json").is_file():
            raise FileNotFoundError(directory / "manifest.json")
        files.extend(sorted(p for p in directory.rglob("*") if p.is_file()))
    source_files = prep.inputs(files)
    with ExitStack() as stack:
        refs = [
            stack.enter_context(ReferenceTacticLibrary.load(p, verification="full"))
            for p in (n1_reference, n5_reference)
        ]
        for dataset, reference, routes in zip(
            ("n1", "n5"), refs, (n1_routes, n5_routes)
        ):
            corpora = reference.manifest.reference_corpora
            expected = (dataset, "sha256:" + prep.digest(routes))
            if (
                len(corpora) != 1
                or (corpora[0]["dataset_id"], corpora[0]["source_identity"]) != expected
            ):
                raise ValueError(
                    f"{dataset} reference library does not match the standalone cleaned source"
                )
            route_ids = {rid for _, rid, _ in prep.route_sources({dataset: routes})}
            if len(route_ids) != corpora[0]["route_count"] or (
                "route_ids" in corpora[0] and route_ids != set(corpora[0]["route_ids"])
            ):
                raise ValueError(
                    f"{dataset} reference route roster differs from cleaned source"
                )
        refs[0].processing_profile.assert_compatible(refs[1].processing_profile)
        entries = [ref.entries(kind="rrseq_cons") for ref in refs]
        configurations = [dict(ref.manifest.identity_configuration) for ref in refs]
        if configurations[0] != configurations[1] or any(
            e.identity.identity_version != conf["tactic_identity_version"]
            for es, conf in zip(entries, configurations)
            for e in es
        ):
            raise ValueError("Reference tactic identity configurations differ")
        shared = shared_tactics(*entries)
        # Record test-side occurrence membership only as overlap/coverage evidence.
        for row in shared.values():
            row["n5_occurrences"] = [
                {
                    "reference_occurrence_id": o.reference_occurrence_id,
                    **o.route.to_dict(),
                }
                for entry_id in row["n5_entry_ids"]
                for o in refs[1].iter_occurrences(entry_id)
            ]
        records = list(prep.library_records(n1_reference, n1_composites, n1_routes))
        for record in records:
            p = record["provenance"]
            occurrence = refs[0].get_occurrence(p["reference_occurrence_id"])
            entry = refs[0].get_entry(p["tactic_entry_id"])
            if not occurrence.identity.equivalent_to(entry.identity):
                raise ValueError(
                    "Composite link's tactic entry differs from its occurrence"
                )
            record["tactic_identity"] = occurrence.identity.to_dict()
        metadata = {
            dataset: {
                "reference_library_id": ref.library_id,
                "processing_profile": ref.processing_profile.to_dict(),
                "tactic_count": len(es),
                "identity_configuration": dict(ref.manifest.identity_configuration),
                "reference_statistics": dict(ref.manifest.statistics),
            }
            for dataset, ref, es in zip(("n1", "n5"), refs, entries)
        }
        composite_manifest = json.loads((n1_composites / "manifest.json").read_text())
        metadata["n1_composites"] = {
            key: composite_manifest[key]
            for key in (
                "library_id",
                "library_format_version",
                "source_reference_library_id",
                "source_routes_sha256",
                "statistics",
            )
        }
        metadata["n1_composites"]["selected_kind"] = "rrseq_cons"
        return select_cohorts(
            n1_routes,
            n5_routes,
            records,
            shared,
            destination,
            source_files=source_files,
            library_metadata=metadata,
            max_alignments=max_alignments,
            progress=progress,
        )
