"""Small integration checks using invented chemistry, never benchmark records."""

import json
from pathlib import Path
import re

import pytest

from retrocomposite.preparation import (
    check_composite_record,
    digest,
    export_composites,
    inputs,
    library_records,
    molecule_key,
    prepare_single_step,
    prepare_stock,
    read_records,
    validate_training_assets,
    write_json,
)


def route():
    return {
        "type": "mol",
        "smiles": "CCO",
        "in_stock": True,
        "children": [
            {
                "type": "reaction",
                "smiles": "[CH3:1][CH2:2][Br:3].[OH2:4]>>[CH3:1][CH2:2][OH:4]",
                "metadata": {"ID": "invented-test"},
                "children": [
                    {"type": "mol", "smiles": "CCBr", "in_stock": False},
                    {"type": "mol", "smiles": "O", "in_stock": False},
                ],
            }
        ],
    }


def record():
    # Invented certificate tests transport validation only, not chemical proof.
    return {
        "kind": "rrseq_cons",
        "dataset_id": "n1",
        "composite_identity_version": 3,
        "composite_rule": "[C:1]-[O:2]>>[C:1].[O:2]",
        "product_smiles": "CCO",
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
        "provenance": {"reference_occurrence_id": "invented-1"},
        "decomposition": {"raw_sequence": "invented-test-only"},
    }


def test_stock_traverses_flags_and_collapses_stereo(tmp_path):
    from synplan.utils.loading import load_building_blocks

    a = route()
    a["children"][0]["children"] = [
        {"type": "mol", "smiles": "C[C@H](O)N"},
        {"type": "mol", "smiles": "C[C@@H](O)N"},
        {"type": "mol", "smiles": "O"},
    ]
    source = tmp_path / "n1.json"
    write_json(source, [a])
    before = digest(source)
    out = tmp_path / "stock"
    prepare_stock({"n1": source}, out)
    stock = load_building_blocks(out / "union.smi", standardize=False)
    assert len(stock) == 2
    assert (
        molecule_key("CCO") not in stock
    )  # root in_stock=True must not stop traversal
    assert molecule_key("C[C@@H](O)N") in stock
    assert len(list(read_records(out / "leaves.jsonl"))) == 3
    assert digest(source) == before
    with pytest.raises(FileExistsError):
        prepare_stock({"n1": source}, out)


def test_single_step_native_extraction_and_mapped_duplicate(tmp_path):
    a = route()
    b = json.loads(re.sub(r":(\d+)\]", lambda m: f":{int(m[1]) + 100}]", json.dumps(a)))
    source1, source5 = tmp_path / "n1.json", tmp_path / "n5.json"
    write_json(source1, [a])
    write_json(source5, {"other": b})
    config = Path(__file__).resolve().parents[1] / "configs/rule_extraction.yaml"
    out = tmp_path / "single"
    prepare_single_step({"n1": source1, "n5": source5}, out, config)
    manifest = json.loads((out / "preparation.json").read_text())
    assert manifest["reaction_occurrences"] == 2
    assert manifest["unique_reactions"] == 1
    assert manifest["policy_rows"] >= 1
    evidence = list(read_records(out / "reaction_provenance.jsonl"))
    assert {s["dataset"] for s in evidence[0]["sources"]} == {"n1", "n5"}
    assert validate_training_assets(out / "single_step.tsv")["rule_count"] >= 1


def test_composite_roundtrip_retains_occurrences_and_exact_variants(tmp_path):
    first = record()
    duplicate = {**first, "provenance": {"reference_occurrence_id": "invented-2"}}
    second = {**first, "composite_rule": "[O:2]-[C:1]>>[O:2].[C:1]"}
    source = tmp_path / "records.json"
    write_json(source, [first, duplicate, second])
    out = tmp_path / "composites"
    export_composites(read_records(source), out, inputs([source]))
    assert validate_training_assets(out / "composite.tsv") == {
        "rule_count": 2,
        "policy_rows": 2,
    }
    rows = list(read_records(out / "composite_records.jsonl"))
    assert len(rows) == 3
    out2 = tmp_path / "roundtrip"
    export_composites(rows, out2, inputs([out / "composite_records.jsonl"]))
    assert (out / "composite.tsv").read_bytes() == (out2 / "composite.tsv").read_bytes()
    assert (out / "composite_policy_data.tsv").read_bytes() == (
        out2 / "composite_policy_data.tsv"
    ).read_bytes()

    # Exercise the actual MHN training-side reader and both graph encoders.
    # This is a forward-pass smoke check, not a training experiment.
    import torch
    from torch_geometric.data import Batch
    from synplan.ml.config import PolicyNetworkConfig
    from synplan.ml.training.preprocessing import RankingPolicyDataset
    from synplan.ml.training.trainers import build_mhn_ranking_network

    dataset = RankingPolicyDataset(
        str(out / "composite_policy_data.tsv"), "", num_workers=1
    )
    config = PolicyNetworkConfig.from_dict(
        {
            "architecture": "mhn_ranking",
            "policy_type": "ranking",
            "embedder_type": "gps",
            "vector_dim": 16,
            "num_conv_layers": 1,
            "heads": 4,
            "association_dim": 16,
            "rule_embedding_type": "query_cgr_graph",
            "rule_embedder": {
                "embedder_type": "gps",
                "vector_dim": 16,
                "num_conv_layers": 1,
                "heads": 4,
            },
        }
    )
    network = build_mhn_ranking_network(config, dataset).eval()
    with torch.no_grad():
        logits = network.get_logits(Batch.from_data_list([dataset[0], dataset[1]]))
    assert logits.shape == (2, 2)
    assert torch.isfinite(logits).all()


@pytest.mark.parametrize(
    "field,value",
    [
        ("kind", "rrseq_gap"),
        ("kind", "rrsubtree_cons"),
        ("dataset_id", "n5"),
        ("composite_identity_version", 2),
        ("certificate", {}),
        ("decomposition", {}),
        ("provenance", {}),
    ],
)
def test_composite_rejects_wrong_scope_or_missing_evidence(field, value):
    with pytest.raises(ValueError):
        check_composite_record({**record(), field: value})


def test_old_library_rejected_before_opening(tmp_path):
    write_json(tmp_path / "manifest.json", {"library_format_version": 2})
    with pytest.raises(ValueError, match="Refresh"):
        list(library_records(tmp_path, tmp_path, tmp_path / "missing.json"))


def test_library_join_uses_motif_product_and_certified_variant(tmp_path, monkeypatch):
    from contextlib import nullcontext
    from types import SimpleNamespace
    from route_inspector.reference_library import ReferenceTacticLibrary
    from route_inspector.composite_rules.library import CompositeDecompositionLibrary

    routes = tmp_path / "routes.json"
    write_json(routes, [route()])
    source_identity = "sha256:" + digest(routes)
    write_json(
        tmp_path / "manifest.json",
        {"library_format_version": 3, "source_routes_sha256": digest(routes)},
    )
    example = record()
    link = SimpleNamespace(
        dataset_id="n1",
        route_id="0",
        source_identity=source_identity,
        reference_occurrence_id="occ-1",
        tactic_entry_id="tactic-1",
        composite_id="family-1",
        variant_id="exact-variant",
        kind="rrseq_cons",
        certificate=example["certificate"],
    )
    occurrence = SimpleNamespace(
        route=SimpleNamespace(
            dataset_id="n1", route_id="0", source_identity=source_identity
        ),
        route_target_smiles="CCCC",
        motif_target_smiles="CCO",
        selected_reaction_node_paths=((0, 0, 0), (0, 0, 0, 0, 0)),
        native_payload=example["decomposition"],
    )
    reference = SimpleNamespace(
        library_id="ref-1", get_occurrence=lambda _id: occurrence
    )
    entry = SimpleNamespace(
        composite_id="family-1",
        identity_version=3,
        composite_rule="[C:1]>>[C:1]-[Cl:2]",
    )
    composites = SimpleNamespace(
        library_id="comp-1",
        assert_reference_library=lambda _ref: None,
        entries=lambda **_kw: [entry],
        links_for_entry=lambda *_a, **_kw: [link],
        certified_rule=lambda _link: example["composite_rule"],
    )
    monkeypatch.setattr(
        ReferenceTacticLibrary, "load", lambda *_a, **_kw: nullcontext(reference)
    )
    monkeypatch.setattr(
        CompositeDecompositionLibrary,
        "load",
        lambda *_a, **_kw: nullcontext(composites),
    )
    (row,) = list(library_records(tmp_path, tmp_path, routes))
    assert row["product_smiles"] == "CCO"  # Not the final route target CCCC.
    assert (
        row["composite_rule"] == example["composite_rule"]
    )  # Not the family representative.
    assert row["provenance"]["variant_id"] == "exact-variant"
    link.dataset_id = "n5"
    with pytest.raises(ValueError, match="standalone n1"):
        list(library_records(tmp_path, tmp_path, routes))


def test_config_explicitly_uses_requested_encoders():
    from synplan.ml.config import PolicyNetworkConfig

    config = PolicyNetworkConfig.from_yaml(
        Path(__file__).resolve().parents[1] / "configs/mhn_querycgr_gps.yaml"
    )
    assert config.architecture == "mhn_ranking"
    assert config.embedder_type == "gps"
    assert config.rule_embedding_type == "query_cgr_graph"
    assert config.rule_embedder.embedder_type == "gps"
