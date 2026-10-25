"""Selection and exact chemistry checks using invented routes/certificates."""

from copy import deepcopy
import json
import re
from types import SimpleNamespace
from pathlib import Path

import pytest

from retrocomposite import preparation as prep
from retrocomposite.segments import Segment, adjacent_paths
from retrocomposite.selection import (
    route_patents,
    select_cohorts,
    shared_tactics,
)


def leaf(smi):
    return {"type": "mol", "smiles": smi}


@pytest.mark.parametrize(
    "patent",
    [
        "US04841062",
        "USRE037303E1",
        "USRE036736",
        "USH0002007H1",
        "USH0002007",
        "US20000001A1",
    ],
)
def test_valid_legacy_and_special_patent_formats_preserve_identity(patent):
    root = step(
        "CO",
        "[CH3:1][Cl:2].[OH2:3]>>[CH3:1][OH:3]",
        [leaf("CCl"), leaf("O")],
        patent=patent,
    )
    result = route_patents(root)
    assert result["complete"]
    assert result["ids"] == [patent]
    assert not result["unresolved"]


def step(product, reaction, children, patent="US20000001A1"):
    return {
        "type": "mol",
        "smiles": product,
        "children": [
            {
                "type": "reaction",
                "smiles": reaction,
                "metadata": {"ID": f"{patent};0001;example"} if patent else {},
                "children": children,
            }
        ],
    }


def chain(long=False, patent="US20000001A1"):
    prefix = "[CH3:10][CH2:1]" if long else "[CH3:1]"
    alcohol, halide, carbonyl = (
        ("CCCO", "CCCBr", "CCC=O") if long else ("CCO", "CCBr", "CC=O")
    )
    inner = step(
        alcohol,
        f"{prefix}[CH2:2][Br:4].[OH2:3]>>{prefix}[CH2:2][OH:3]",
        [leaf(halide), leaf("O")],
        patent,
    )
    return step(
        carbonyl, f"{prefix}[CH2:2][OH:3]>>{prefix}[CH:2]=[O:3]", [inner], patent
    )


def embedded():
    return step(
        "CC(=O)O",
        "[CH3:1][CH:2]=[O:3].[OH2:5]>>[CH3:1][C:2](=[O:3])[OH:5]",
        [chain(), leaf("O")],
        "US20000002A1",
    )


def motif_overlap():
    inner = step(
        "CCBr",
        "[CH3:1][CH3:2].[BrH:4]>>[CH3:1][CH2:2][Br:4]",
        [leaf("CC"), leaf("Br")],
        "US20000002A1",
    )
    return step(
        "CCO",
        "[CH3:1][CH2:2][Br:4].[OH2:3]>>[CH3:1][CH2:2][OH:3]",
        [inner, leaf("O")],
        "US20000002A1",
    )


def pair(root, paths=None, cap=256):
    first, second = paths or next(adjacent_paths(root))
    return Segment.from_route(root, first, second, {}, cap)


def record(rid, source, root, *, tactic="shared-2", paths=None, variant="v1"):
    if paths is None:
        paths = [(0,), (0, 0, 0)]
    return {
        "kind": "rrseq_cons",
        "dataset_id": "n1",
        "composite_identity_version": 3,
        "composite_rule": "[C:1]-[O:2]>>[C:1].[O:2]",
        "product_smiles": root["smiles"],
        "certificate": {
            key: True
            for key in (
                "source_occurrence_certified",
                "source_chemistry_equivalent",
                "source_mapping_consistent",
                "composite_chemistry_equivalent",
                "composite_mapping_consistent",
            )
        },
        "provenance": {
            "route_id": rid,
            "source_identity": "sha256:" + prep.digest(source),
            "reference_occurrence_id": "occ-" + rid,
            "tactic_entry_id": tactic,
            "composite_id": "family-1",
            "variant_id": variant,
            "selected_reaction_node_paths": paths,
        },
        "decomposition": {
            "raw_sequence": "invented-transport-fixture",
            "source_route": rid,
        },
    }


def shared():
    return {
        key: {
            "n1_entry_id": key,
            "n5_entry_ids": ["test-" + key],
            "n5_occurrences": [
                {"reference_occurrence_id": "test-occ-" + key, "route_id": "test-route"}
            ],
        }
        for key in ("shared-2", "shared-3")
    }


def test_shared_tactics_use_native_equivalence_not_dataset_entry_ids():
    from route_inspector.reference_library.models import TacticIdentity

    def entry(name, keys, version=2):
        return SimpleNamespace(
            entry_id=name,
            identity=TacticIdentity(
                kind="rrseq_cons",
                identity_version=version,
                equivalence_payload={
                    "family": "rrseq",
                    "variant": "cons",
                    "query_cgr_keys": keys,
                },
            ),
        )

    first = entry("n1-local", ["a", "b"])
    other = entry("n5-other-id", ["a", "b"])
    mismatch = entry("n1-local", ["b", "a"])
    result = shared_tactics([first], [other, mismatch])
    assert result["n1-local"]["n5_entry_ids"] == ["n5-other-id"]
    # A locator collision alone must never count as equality.
    forged = SimpleNamespace(
        entry_id="collision",
        identity=SimpleNamespace(lookup_key=first.identity.lookup_key),
    )
    assert shared_tactics([first], [forged]) == {}


def test_pair_equivalence_ignores_maps_and_component_order_but_preserves_chemistry():
    original = chain()
    shifted = json.loads(
        re.sub(r":(\d+)\]", lambda m: f":{int(m[1]) + 200}]", json.dumps(original))
    )
    shifted["children"][0]["children"][0]["children"][0]["children"].reverse()
    assert pair(original).equivalent_to(pair(shifted))
    # Different map namespaces in the two steps also preserve identity.
    inner = shifted["children"][0]["children"][0]["children"][0]
    inner["smiles"] = re.sub(
        r":(\d+)\]", lambda m: f":{int(m[1]) + 400}]", inner["smiles"]
    )
    assert pair(original).equivalent_to(pair(shifted))
    assert not pair(original).equivalent_to(pair(chain(long=True)))
    changed = deepcopy(original)
    second = changed["children"][0]["children"][0]["children"][0]
    second["smiles"] = second["smiles"].replace("[Br:4]", "[Cl:4]")
    second["children"][0]["smiles"] = "CCCl"
    assert not pair(original).equivalent_to(pair(changed))


def test_pair_preserves_within_reaction_atom_correspondence():
    original = chain()
    changed = deepcopy(original)
    first = changed["children"][0]
    first["smiles"] = "[CH3:1][CH2:2][OH:3]>>[CH3:2][CH:1]=[O:3]"
    assert pair(original).context == pair(changed).context
    assert not pair(original).equivalent_to(pair(changed))


def symmetric_chain():
    # Two possible atom correspondences through the ethane intermediate.
    inner = step("CC", "[CH2:1]=[CH2:2]>>[CH3:1][CH3:2]", [leaf("C=C")])
    return step(
        "CCCl", "[CH3:1][CH3:2].[ClH:3]>>[CH3:1][CH2:2][Cl:3]", [inner, leaf("Cl")]
    )


def test_symmetry_is_enumerated_and_truncation_is_not_a_nonmatch():
    example = symmetric_chain()
    assert len(pair(example).graphs) == 2
    assert pair(example).equivalent_to(pair(example))
    with pytest.raises(ValueError, match="enumeration exceeded"):
        pair(example, cap=1).equivalent_to(pair(example))


def test_stereo_is_ignored_and_isotopes_retained():
    def stereo_chain(stereo):
        inner = step(
            f"C[C{stereo}H](O)CBr",
            f"[CH3:1][C{stereo}H:2]([OH:3])[CH2:4][Cl:5].[BrH:6]>>[CH3:1][C{stereo}H:2]([OH:3])[CH2:4][Br:6]",
            [leaf(f"C[C{stereo}H](O)CCl"), leaf("Br")],
        )
        return step(
            f"C[C{stereo}H](O)CO",
            f"[CH3:1][C{stereo}H:2]([OH:3])[CH2:4][Br:6].[OH2:7]>>[CH3:1][C{stereo}H:2]([OH:3])[CH2:4][OH:7]",
            [inner, leaf("O")],
        )

    assert pair(stereo_chain("@")).equivalent_to(pair(stereo_chain("@@")))
    isotope = json.loads(
        json.dumps(chain()).replace("[CH3:1]", "[13CH3:1]").replace('"CC', '"[13CH3]C')
    )
    assert not pair(chain()).equivalent_to(pair(isotope))


def test_patents_use_split_ancestry_and_reject_opaque_ids():
    example = chain(patent=None)
    reaction = example["children"][0]
    reaction["metadata"] = {
        "ID": "generated",
        "route_preprocessing_split": {
            "original_source_record_id": "us-20000001-a1;01;record"
        },
    }
    result = route_patents(example)
    assert result["ids"] == ["US20000001A1"]
    assert not result["complete"]  # Other step lacks provenance.
    example["children"][0]["children"][0]["children"][0]["metadata"] = {"ID": "opaque"}
    assert not route_patents(example)["complete"]


def test_primary_and_patent_cohorts_full_audit_and_support_rebuild(tmp_path):
    routes = {
        "same": chain(),
        "motif": motif_overlap(),
        "embedded": embedded(),
        "keep": chain(True, "US20000002A1"),
        "same-patent": chain(True),
        "unknown-patent": chain(True, None),
        "not-shared": chain(True, "US20000003A1"),
    }
    n1, n5 = tmp_path / "n1.json", tmp_path / "n5.json"
    prep.write_json(n1, routes)
    prep.write_json(n5, {"test": chain()})
    before = (prep.digest(n1), prep.digest(n5))
    records = [
        record(
            rid,
            n1,
            root,
            tactic="unshared"
            if rid == "not-shared"
            else "shared-3"
            if rid == "embedded"
            else "shared-2",
            paths=[(0,), (0, 0, 0), (0, 0, 0, 0, 0)] if rid == "embedded" else None,
        )
        for rid, root in routes.items()
    ]
    out = tmp_path / "selection"
    report = select_cohorts(n1, n5, records, shared(), out)
    assert report["cohorts"]["primary"]["occurrences"] == 3
    assert report["cohorts"]["primary"]["training_pairs"] == 1
    assert report["cohorts"]["patent_disjoint"]["occurrences"] == 1
    assert report["cohorts"]["patent_disjoint"]["status"] == "ready"
    assert report["cohorts"]["primary"]["dropped_shared_tactics"] == ["shared-3"]
    audits = {
        r["route_id"]: r for r in prep.read_records(out / "occurrence_audit.jsonl")
    }
    assert set(audits["same"]["exclusions"]) == {
        "E1_SHARED_FINAL_TARGET",
        "E2_SHARED_MOTIF_INPUT",
        "E3_SHARED_CONCRETE_SEGMENT",
    }
    assert set(audits["embedded"]["exclusions"]) == {"E3_SHARED_CONCRETE_SEGMENT"}
    assert set(audits["motif"]["exclusions"]) == {"E2_SHARED_MOTIF_INPUT"}
    assert audits["same-patent"]["sensitivity_status"] == "excluded"
    assert audits["unknown-patent"]["sensitivity_status"] == "quarantined"
    kept = list(prep.read_records(out / "patent_disjoint/composite_records.jsonl"))
    assert [r["decomposition"]["source_route"] for r in kept] == ["keep"]
    assert len(report["cohorts"]["patent_disjoint"]["variants"]) == 1
    manifest = json.loads((out / "preparation.json").read_text())
    assert "primary/support.json" in manifest["outputs"]
    for name, digest in manifest["outputs"].items():
        assert prep.digest(out / name) == digest
    assert (prep.digest(n1), prep.digest(n5)) == before
    with pytest.raises(FileExistsError):
        select_cohorts(n1, n5, records, shared(), out)
    # Deterministic publication despite record order.
    out2 = tmp_path / "selection2"
    select_cohorts(n1, n5, list(reversed(records)), shared(), out2)
    for path in out.rglob("*"):
        if path.is_file():
            assert path.read_bytes() == (out2 / path.relative_to(out)).read_bytes()


def test_n5_unknown_patent_blocks_only_sensitivity(tmp_path):
    n1, n5 = tmp_path / "n1.json", tmp_path / "n5.json"
    prep.write_json(n1, {"keep": chain(True, "US20000002A1")})
    prep.write_json(n5, [chain(patent=None)])
    report = select_cohorts(
        n1, n5, [record("keep", n1, chain(True))], shared(), tmp_path / "out"
    )
    assert report["cohorts"]["primary"]["status"] == "ready"
    assert report["cohorts"]["patent_disjoint"]["status"] == "blocked"
    assert not (tmp_path / "out/patent_disjoint/composite.tsv").exists()


def test_e2_excludes_same_input_with_different_composite_label(tmp_path):
    n1, n5 = tmp_path / "n1.json", tmp_path / "n5.json"
    root = motif_overlap()
    prep.write_json(n1, {"candidate": root})
    prep.write_json(n5, [chain()])
    item = record("candidate", n1, root)
    item["composite_rule"] = "[C:1]-[O:2]>>[C:1]=[O:2]"
    out = tmp_path / "out"
    select_cohorts(n1, n5, [item], shared(), out)
    (audit,) = list(prep.read_records(out / "occurrence_audit.jsonl"))
    assert audit["primary_status"] == "excluded"
    assert set(audit["exclusions"]) == {"E2_SHARED_MOTIF_INPUT"}


def test_n5_invalid_chemistry_blocks_safe_publication(tmp_path):
    n1, n5 = tmp_path / "n1.json", tmp_path / "n5.json"
    prep.write_json(n1, {"keep": chain(True)})
    broken = chain()
    broken["children"][0]["smiles"] = "not a reaction"
    prep.write_json(n5, [broken])
    out = tmp_path / "out"
    report = select_cohorts(n1, n5, [record("keep", n1, chain(True))], shared(), out)
    assert report["cohorts"]["primary"]["status"] == "blocked"
    assert report["primary_status_counts"] == {"quarantined": 1}
    assert not (out / "primary/composite.tsv").exists()


@pytest.mark.parametrize(
    "change", ["gapped", "source", "product", "certificate", "orphan"]
)
def test_invalid_n1_occurrences_are_quarantined(tmp_path, change):
    n1, n5 = tmp_path / "n1.json", tmp_path / "n5.json"
    prep.write_json(n1, {"keep": chain(True)})
    prep.write_json(n5, [chain()])
    item = record("keep", n1, chain(True))
    if change == "gapped":
        item["provenance"]["selected_reaction_node_paths"] = [[0], [0, 0, 0, 0, 0]]
    elif change == "source":
        item["provenance"]["source_identity"] = "sha256:wrong"
    elif change == "product":
        item["product_smiles"] = "CCCCO"
    elif change == "certificate":
        item["certificate"] = {}
    else:
        item["provenance"]["route_id"] = "missing"
    report = select_cohorts(n1, n5, [item], shared(), tmp_path / "out")
    assert report["primary_status_counts"] == {"quarantined": 1}
    assert report["cohorts"]["primary"]["status"] == "empty"


def test_root_exclusion_applies_to_internal_occurrences_and_eligible_internal_survives(
    tmp_path,
):
    n1, n5 = tmp_path / "n1.json", tmp_path / "n5.json"
    internal = chain(True, "US20000002A1")
    excluded = step(
        "CC=O", "[CH3:1][CH2:2][CH:3]=[O:4]>>[CH3:2][CH:3]=[O:4]", [internal]
    )
    kept = step(
        "CCC(=O)O",
        "[CH3:1][CH2:2][CH:3]=[O:4].[OH2:5]>>[CH3:1][CH2:2][C:3](=[O:4])[OH:5]",
        [deepcopy(internal), leaf("O")],
        "US20000002A1",
    )
    prep.write_json(n1, {"remove": excluded, "keep": kept})
    prep.write_json(n5, [chain()])
    records = [
        record(rid, n1, internal, paths=[(0, 0, 0), (0, 0, 0, 0, 0)])
        for rid in ("remove", "keep")
    ]
    out = tmp_path / "out"
    report = select_cohorts(n1, n5, records, shared(), out)
    audits = {
        a["route_id"]: a for a in prep.read_records(out / "occurrence_audit.jsonl")
    }
    assert set(audits["remove"]["exclusions"]) == {"E1_SHARED_FINAL_TARGET"}
    assert report["cohorts"]["primary"]["occurrences"] == 1
    assert report["cohorts"]["patent_disjoint"]["occurrences"] == 1


def test_alignment_limit_is_audit_only_for_embedded_occurrence(tmp_path):
    n1, n5 = tmp_path / "n1.json", tmp_path / "n5.json"
    root = step(
        "CCBr",
        "[CH3:1][CH2:2][Cl:3].[BrH:4]>>[CH3:1][CH2:2][Br:4]",
        [symmetric_chain(), leaf("Br")],
    )
    prep.write_json(n1, {"candidate": root})
    prep.write_json(n5, [symmetric_chain()])
    item = record("candidate", n1, root, paths=[(0,), (0, 0, 0), (0, 0, 0, 0, 0)])
    out = tmp_path / "out"
    report = select_cohorts(n1, n5, [item], shared(), out, max_alignments=1)
    assert report["primary_status_counts"] == {"excluded": 1}
    assert report["reason_counts"] == {"E3_SHARED_CONCRETE_SEGMENT": 1}
    assert report["links_with_errors"] == 0
    assert report["exact_graph_audit"]["status_counts"] == {"unresolved": 1}
    assert "enumeration exceeded" in (out / "occurrence_audit.jsonl").read_text()


@pytest.fixture
def native_libraries(tmp_path, request):
    """Build only tiny invented fixtures; never refresh a production publication."""
    from route_inspector.workflows.reference_library import (
        build_reference_library,
        route_tactic_processor_from_config,
    )
    from route_inspector.workflows.composites import publish_composite_library
    from route_inspector.workflows.requests import BuildCompositeLibraryRequest

    inner = step("C=C", "[CH:1]#[CH:2]>>[CH2:1]=[CH2:2]", [leaf("C#C")])
    root = step("CC", "[CH2:1]=[CH2:2]>>[CH3:1][CH3:2]", [inner])
    config = Path(__file__).resolve().parents[1] / "configs/rule_extraction.yaml"
    for dataset in ("n1", "n5"):
        source_root = deepcopy(root)
        if dataset == "n5" and getattr(request, "param", False):
            source_root["children"][0]["metadata"] = {}
        source = tmp_path / f"{dataset}.json"
        prep.write_json(source, {"sample": source_root})
        processor = route_tactic_processor_from_config(
            config,
            source_id_adapter="paroutes-semicolon-v1",
            rrseq_max_length=2,
            rrsubtree_max_size=3,
        )
        built = build_reference_library(
            [("sample", source_root)],
            processor,
            reference_id=dataset,
            source_identity="sha256:" + prep.digest(source),
            corpus_sha256=prep.digest(source),
        )
        built.library.save(tmp_path / f"{dataset}-reference")
    result = publish_composite_library(
        BuildCompositeLibraryRequest(
            reference_library=tmp_path / "n1-reference",
            routes_json=tmp_path / "n1.json",
            output_dir=tmp_path / "n1-composites",
            config=config,
            kinds=["rrseq_cons"],
            single_step_overlap=False,
            n_cpu=1,
            progress_interval=0,
        )
    )
    assert result.certified_links == 1
    return tmp_path, getattr(request, "param", False)


@pytest.mark.filterwarnings("ignore:Pydantic serializer warnings:UserWarning")
@pytest.mark.parametrize("native_libraries", [False, True], indirect=True)
def test_real_certified_library_to_cli_and_mismatched_release(native_libraries, capsys):
    from retrocomposite.cli import main

    root, blocked = native_libraries
    args = [
        "select-cohorts",
        "--n1",
        str(root / "n1.json"),
        "--n5",
        str(root / "n5.json"),
        "--n1-reference",
        str(root / "n1-reference"),
        "--n5-reference",
        str(root / "n5-reference"),
        "--n1-composites",
        str(root / "n1-composites"),
        "--output",
        str(root / "selected"),
    ]
    if blocked:
        with pytest.raises(SystemExit) as exc:
            main(args)
        assert exc.value.code == 2
    else:
        main(args)
    assert '"status": "empty"' in capsys.readouterr().out
    report = json.loads((root / "selected/selection.json").read_text())
    assert report["shared_tactic_count"] == 1
    assert report["reason_counts"] == {
        "E1_SHARED_FINAL_TARGET": 1,
        "E2_SHARED_MOTIF_INPUT": 1,
        "E3_SHARED_CONCRETE_SEGMENT": 1,
    }
    assert report["primary_status_counts"] == {"excluded": 1}
    # Fresh paths with source content changed cannot reuse the certified release.
    source = root / "n5.json"
    source.write_text(source.read_text() + "\n")
    args[-1] = str(root / "wrong-source")
    with pytest.raises(ValueError, match="standalone cleaned source"):
        main(args)
    assert not (root / "wrong-source").exists()


def test_signature_preserves_order_sides_and_reactant_multiplicity():
    from dataclasses import replace

    original = pair(chain())
    one, two, intermediate = original.context
    assert not original.matches_signature(
        replace(original, context=(two, one, intermediate))
    )
    duplicate = (two[0], tuple(sorted((*two[1], two[1][0]))))
    assert not original.matches_signature(
        replace(original, context=(one, duplicate, intermediate))
    )
    reversed_side = (one[1][0], (one[0],))
    assert not original.matches_signature(
        replace(original, context=(reversed_side, two, intermediate))
    )


def test_e3_excludes_mapping_differences_without_e1_or_e2(tmp_path):
    root = embedded()
    first = root["children"][0]["children"][0]["children"][0]
    first["smiles"] = "[CH3:1][CH2:2][OH:3]>>[CH3:2][CH:1]=[O:3]"
    n1, n5 = tmp_path / "n1.json", tmp_path / "n5.json"
    prep.write_json(n1, {"embedded": root})
    prep.write_json(n5, {"test": chain()})
    paths = [(0,), (0, 0, 0), (0, 0, 0, 0, 0)]
    report = select_cohorts(
        n1, n5, [record("embedded", n1, root, paths=paths)], shared(), tmp_path / "out"
    )
    assert report["reason_counts"] == {"E3_SHARED_CONCRETE_SEGMENT": 1}
    assert report["primary_status_counts"] == {"excluded": 1}
    assert report["links_with_errors"] == 0
    assert report["exact_graph_audit"]["status_counts"] == {"different": 1}
    assert not report["exact_graph_audit"]["affects_eligibility"]


def test_unresolved_graph_audit_does_not_change_e3_exclusion(tmp_path):
    root = symmetric_chain()
    n1, n5 = tmp_path / "n1.json", tmp_path / "n5.json"
    prep.write_json(n1, {"same": root})
    prep.write_json(n5, {"test": root})
    report = select_cohorts(
        n1, n5, [record("same", n1, root)], shared(), tmp_path / "out", max_alignments=1
    )
    assert report["reason_counts"]["E3_SHARED_CONCRETE_SEGMENT"] == 1
    assert report["links_with_errors"] == 0
    assert report["exact_graph_audit"]["status_counts"] == {"unresolved": 1}
    audit = next(prep.read_records(tmp_path / "out/occurrence_audit.jsonl"))
    graph = audit["exclusions"]["E3_SHARED_CONCRETE_SEGMENT"][0]["exact_graph_audit"]
    assert "enumeration exceeded" in graph["error"]
    assert audit["primary_status"] == "excluded"


def test_accelerated_graph_audit_matches_native_labelled_isomorphism():
    from retrocomposite.segments import exact_graphs_match, graph_label_counts
    from route_inspector.rules.graph import labelled_graphs_are_isomorphic

    original = chain()
    renumbered = json.loads(
        re.sub(r":(\d+)\]", lambda m: f":{1000 - int(m[1])}]", json.dumps(original))
    )
    left, right = pair(original).graphs[0][1], pair(renumbered).graphs[0][1]
    assert labelled_graphs_are_isomorphic(left, right)
    assert exact_graphs_match(left, right)

    # Same coarse label counts, different placement of bond states around a ring.
    def cycle(labels):
        return {
            "graph_schema_version": 1,
            "atoms": [{"node": i, "label": {"type": "atom"}} for i in range(4)],
            "bonds": [
                {"nodes": [i, (i + 1) % 4], "label": {"state": label}}
                for i, label in enumerate(labels)
            ],
        }

    adjacent, alternating = cycle([1, 1, 2, 2]), cycle([1, 2, 1, 2])
    assert graph_label_counts(adjacent) == graph_label_counts(alternating)
    assert not labelled_graphs_are_isomorphic(adjacent, alternating)
    assert not exact_graphs_match(adjacent, alternating)
