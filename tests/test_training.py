"""Grouping and tiny CPU fitting checks on invented chemistry, never PaRoutes."""

import json
from pathlib import Path

import pytest

from retrocomposite import preparation as prep
from retrocomposite.splitting import assign_groups, create_split, load_split, read_tsv
from retrocomposite.training import train


def example(molecule, label, *routes, patent=None):
    return {
        "product_smiles": molecule,
        "rule_id": label,
        "routes": list(routes),
        "patents": [patent] if patent else [],
        "patents_complete": bool(patent),
    }


def test_transitive_groups_keep_multilabel_products_and_all_routes_together():
    rows = [
        example("CCO", 0, "a", "b"),
        example("CCO", 1, "c"),
        example("CCN", 1, "b"),
        example("CCC", 0, "d"),
        example("CCCC", 1, "e"),
        example("CCCO", 0, "f"),
    ]
    a, report = assign_groups(rows, 42, 0.3, "route")
    assert len({r["group_id"] for r in a[:3]}) == 1
    assert len({r["partition"] for r in a[:3]}) == 1
    assert report["status"] == "ready"
    assert not any(report["overlap"].values())
    assert assign_groups(rows, 42, 0.3, "route") == (a, report)
    assert {r["rule_id"] for r in a if r["partition"] == "train"} == {0, 1}


def test_rare_rule_remains_train_and_giant_component_blocks():
    rows = [example("CCO", 0, "a"), example("CCN", 0, "b"), example("CCC", 1, "rare")]
    assignments, report = assign_groups(rows, 7, 0.5, "route")
    assert assignments[2]["partition"] == "train"
    assert report["rules_without_validation"] == [1]
    for row in rows:
        row["routes"].append("connected")
    _, report = assign_groups(rows, 7, 0.5, "route")
    assert report["status"] == "blocked"
    assert report["validation_rows"] == 0


def test_patents_merge_routes_and_unknown_provenance_blocks_strict_holdout():
    rows = [
        example("CCO", 0, "a", patent="US20000001A1"),
        example("CCN", 0, "b", patent="US20000001A1"),
        example("CCC", 0, "c", patent="US20000002A1"),
        example("CCCC", 0, "d", patent="US20000003A1"),
    ]
    assignments, report = assign_groups(rows, 42, 0.25, "patent")
    assert assignments[0]["group_id"] == assignments[1]["group_id"]
    assert report["status"] == "ready"
    rows[-1]["patents_complete"] = False
    _, report = assign_groups(rows, 42, 0.25, "patent")
    assert report["status"] == "blocked"
    assert report["missing_patent_rows_forced_train"] > 0


def test_seed_changes_assignment_without_changing_constraints():
    rows = [example("C" * (i + 2), i % 2, str(i)) for i in range(30)]
    first, _ = assign_groups(rows, 42, 0.2, "route")
    other, _ = assign_groups(rows, 11, 0.2, "route")
    assert [a["partition"] for a in first] != [a["partition"] for a in other]
    for invalid in (-1, 2**32):
        with pytest.raises(ValueError):
            assign_groups(rows, invalid, 0.2, "route")


@pytest.fixture
def cohort(tmp_path):
    from test_preparation import record

    parent = tmp_path / "cohorts"
    parent.mkdir()
    records = []
    for length in range(2, 8):
        for hetero in ("O", "N"):
            row = record()
            row["product_smiles"] = prep.molecule_key("C" * length + hetero)
            row["composite_rule"] = f"[C:1]-[{hetero}:2]>>[C:1].[{hetero}:2]"
            row["provenance"] = {
                "source_identity": "invented-transport-test-only",
                "route_id": str(length),
                "reference_occurrence_id": f"occ-{length}-{hetero}",
            }
            records.append(row)
    assets = parent / "primary"
    prep.export_composites(records, assets, [])
    prep.write_json(assets / "support.json", {"status": "ready"})
    prep.write_json(
        parent / "selection.json", {"cohorts": {"primary": {"status": "ready"}}}
    )
    prep.write_jsonl(
        parent / "route_audit.jsonl",
        [
            {
                "dataset_id": "n1",
                "route_id": str(i),
                "patents": {"ids": [f"US2000000{i}A1"], "complete": True},
            }
            for i in range(2, 8)
        ],
    )
    prep.finish(parent, [], kind="cohort-selection")
    return assets


def test_composite_split_snapshots_keep_vocabulary_and_supporting_occurrences(
    cohort, tmp_path
):
    split = tmp_path / "split"
    result = create_split(cohort, split, 42, 0.25)
    assert result["status"] == "ready"
    meta, assignments = load_split(split)
    assert meta["cohort"] == "primary"
    assert (split / "assets/composite.tsv").read_bytes() == (
        cohort / "composite.tsv"
    ).read_bytes()
    assert (
        len(read_tsv(split / "train.tsv")) + len(read_tsv(split / "validation.tsv"))
        == 12
    )
    by_route = {}
    for a in assignments:
        for r in a["routes"]:
            by_route.setdefault(r, set()).add(a["partition"])
    assert all(len(v) == 1 for v in by_route.values())
    with pytest.raises(FileExistsError):
        create_split(cohort, split)
    assert (
        create_split(cohort, tmp_path / "patents", grouping="patent")["status"]
        == "ready"
    )
    (split / "assignments.jsonl").write_text("{}\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        load_split(split)


def test_raw_composites_are_not_accepted_as_a_cohort(cohort, tmp_path):
    (cohort / "support.json").write_text('{"status":"blocked"}')
    with pytest.raises(ValueError, match="hash mismatch"):
        create_split(cohort, tmp_path / "bad")


def test_ready_cohort_cannot_import_n5_composite_labels(cohort, tmp_path):
    records_path = cohort / "composite_records.jsonl"
    records = list(prep.read_records(records_path))
    records[0]["dataset_id"] = "n5"
    prep.write_jsonl(records_path, records)
    # Rehash to test the semantic gate rather than only byte-integrity checking.
    for root in (cohort, cohort.parent):
        path = root / "preparation.json"
        manifest = json.loads(path.read_text())
        for name in manifest["outputs"]:
            manifest["outputs"][name] = prep.digest(root / name)
        prep.write_json(path, manifest)
    with pytest.raises(ValueError, match="n1-only"):
        create_split(cohort, tmp_path / "bad-n5")


def test_split_revalidates_group_assignments_after_hash_refresh(cohort, tmp_path):
    split = tmp_path / "split"
    create_split(cohort, split)
    rows = list(prep.read_records(split / "assignments.jsonl"))
    rows[0]["partition"] = "validation" if rows[0]["partition"] == "train" else "train"
    prep.write_jsonl(split / "assignments.jsonl", rows)
    path = split / "preparation.json"
    manifest = json.loads(path.read_text())
    manifest["outputs"]["assignments.jsonl"] = prep.digest(split / "assignments.jsonl")
    prep.write_json(path, manifest)
    with pytest.raises(ValueError, match="frozen grouping policy"):
        load_split(split)


def test_single_step_join_retains_all_duplicate_route_sources(tmp_path):
    from test_preparation import route

    n1, n5 = tmp_path / "n1.json", tmp_path / "n5.json"
    a, b = route(), route()
    b["children"][0]["smiles"] = "[CH3:1][CH2:2][I:3].[OH2:4]>>[CH3:1][CH2:2][OH:4]"
    b["children"][0]["children"][0]["smiles"] = "CCI"
    prep.write_json(n1, {"a": a, "b": b})
    prep.write_json(n5, {"duplicate": a})
    assets = tmp_path / "single_step"
    config = Path(__file__).resolve().parents[1] / "configs/rule_extraction.yaml"
    prep.prepare_single_step({"n1": n1, "n5": n5}, assets, config)
    result = create_split(assets, tmp_path / "split")
    assert result["status"] == "blocked"  # all examples share CCO
    rows = list(prep.read_records(tmp_path / "split/assignments.jsonl"))
    assert any('["n5","duplicate"]' in r["routes"] for r in rows)
    assert len({r["group_id"] for r in rows}) == 1
    with pytest.raises(ValueError, match="ready grouped split"):
        load_split(tmp_path / "split")


def small_config(tmp_path):
    import yaml

    values = yaml.safe_load(
        (
            Path(__file__).resolve().parents[1] / "configs/mhn_querycgr_gps.yaml"
        ).read_text()
    )
    values.update(
        vector_dim=16, num_conv_layers=1, association_dim=16, num_epoch=2, batch_size=4
    )
    values["rule_embedder"].update(vector_dim=16, num_conv_layers=1)
    path = tmp_path / "tiny.yaml"
    path.write_text(yaml.safe_dump(values))
    return path


def test_seeded_training_repeats_weights_and_native_checkpoint_loads(cohort, tmp_path):
    import torch
    from synplan.ml.networks.checkpoint import load_policy_network_from_checkpoint

    split = tmp_path / "split"
    create_split(cohort, split, 42, 0.25)
    config = small_config(tmp_path)
    runs = []
    for name, seed in (("first", 17), ("repeat", 17), ("other", 18)):
        output = tmp_path / name
        result = train(split, config, output, seed)
        assert result["status"] == "complete"
        assert result["split_seed"] == 42
        assert result["seed"] == seed
        assert (output / "logs/metrics/metrics.csv").is_file()
        assert (output / "console.log").is_file()
        assert (output / "checkpoints/last.ckpt").is_file()
        metrics = json.loads((output / "metrics.json").read_text())
        assert metrics["validation_rows"] > 0
        assert metrics["epochs_completed"] == 2
        assert metrics["validation_loss"] == pytest.approx(
            metrics["best_monitored_validation_loss"], abs=1e-6
        )
        model = load_policy_network_from_checkpoint(output / metrics["checkpoint"])
        assert model.n_rules == 2
        assert model.rule_vocabulary_digest == prep.digest(
            split / "assets/composite.tsv"
        )
        assert (
            json.loads((output / "graph_alignment.json").read_text())["status"]
            == "verified"
        )
        runs.append((model.state_dict(), metrics))
    assert all(torch.equal(runs[0][0][k], runs[1][0][k]) for k in runs[0][0])
    assert runs[0][1]["validation_loss"] == runs[1][1]["validation_loss"]
    assert any(not torch.equal(runs[0][0][k], runs[2][0][k]) for k in runs[0][0])
    with pytest.raises(FileExistsError):
        train(split, config, tmp_path / "first", 17)


def test_failed_training_keeps_error_manifest_and_console_log(cohort, tmp_path):
    import yaml

    split = tmp_path / "split"
    create_split(cohort, split)
    config = small_config(tmp_path)
    values = yaml.safe_load(config.read_text())
    values["trainer"] = {"limit_val_batches": 0}
    config.write_text(yaml.safe_dump(values))
    output = tmp_path / "failed"
    with pytest.raises(RuntimeError, match="worker exited"):
        train(split, config, output, 17)
    assert json.loads((output / "run.json").read_text())["status"] == "failed"
    assert "Unsupported trainer overrides" in (output / "console.log").read_text()


def test_native_join_keeps_provenance_across_non_inchi_equivalent_normalization(
    tmp_path,
):
    from retrocomposite.identity import molecule_identity
    from retrocomposite.splitting import single_step_sources

    assert molecule_identity("C=CO") != molecule_identity("CC=O")
    native = tmp_path / "single_step_policy_data.native.tsv"
    native.write_text("product_smiles\trule_id\nC=CO\t0\nCC=O\t0\n")
    rows = [{"product_smiles": "CC=O", "rule_id": "0"}] * 2
    changes = [{"row_index": 0, "rule_id": 0, "original": "C=CO", "canonical": "CC=O"}]
    prep.write_jsonl(tmp_path / "policy_product_normalization.jsonl", changes)
    prep.write_jsonl(
        tmp_path / "reaction_provenance.jsonl",
        [
            {
                "input_index": 0,
                "mapped": "C=CO>>C=CO",
                "sources": [{"dataset": "n1", "route_id": "enol"}],
            },
            {
                "input_index": 1,
                "mapped": "CC=O>>CC=O",
                "sources": [{"dataset": "n1", "route_id": "keto"}],
            },
        ],
    )
    rules = [{"reaction_indices": "0,1"}]
    assert single_step_sources(tmp_path, rules, rows) == [
        ['["n1","enol"]'],
        ['["n1","keto"]'],
    ]
    prep.write_jsonl(tmp_path / "policy_product_normalization.jsonl", [])
    with pytest.raises(ValueError, match="normalization ledger"):
        single_step_sources(tmp_path, rules, rows)
