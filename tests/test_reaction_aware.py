"""Regression checks for normalization-only spectator tautomer changes."""
import json
from pathlib import Path

import pytest
from chython import smiles
from synplan.chem.reaction.rules.config import RuleExtractionConfig

from retrocomposite import preparation as prep
from retrocomposite import reaction_aware as aware

CONFIG = Path(__file__).resolve().parents[1] / "configs/rule_extraction.yaml"
CASES = json.loads((Path(__file__).parent / "fixtures/remote_tautomers.json").read_text())


@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c['dataset']}-{c['route_id']}")
def test_only_normalization_added_tautomer_is_aligned(case):
    original = smiles(case["original_mapped"])
    original.clean_stereo()
    normalized = prep.normalize_mapped_reaction(original)
    before = (format(original, "m"), format(normalized, "m"))
    aligned, report = aware.extraction_reaction(original, normalized, RuleExtractionConfig.from_yaml(CONFIG))
    assert (format(original, "m"), format(normalized, "m")) == before
    assert report["status"] == "aligned"
    assert report["aligned_atom_maps"] == [12, 13, 39]
    assert set((~aligned).center_atoms) == set((~original).center_atoms)
    assert str(aligned.products[0]) == str(normalized.products[0])
    assert all(r["status"] == "passed" and r["exact_prepared_precursors"] and r["input_patterns"] == 1
               for r in report["rule_replay"])
    assert str(prep.normalize_mapped_reaction(aligned)) == str(normalized)
    # The same graph changes explicitly present in the source must be kept.
    kept, evidence = aware.extraction_reaction(normalized, normalized, RuleExtractionConfig.from_yaml(CONFIG))
    assert str(kept) == str(normalized)
    assert evidence is None


def test_atom_map_labels_do_not_select_the_repair():
    original = smiles(CASES[0]["original_mapped"])
    original.clean_stereo()
    for m in original.molecules():
        m.remap({n: 500 - n for n in m.atoms_numbers})
    normalized = prep.normalize_mapped_reaction(original)
    aligned, report = aware.extraction_reaction(original, normalized, RuleExtractionConfig.from_yaml(CONFIG))
    assert report["status"] == "aligned"
    assert set(report["aligned_atom_maps"]) == {500 - n for n in (12, 13, 39)}
    assert set((~aligned).center_atoms) == set((~original).center_atoms)


def test_failed_rule_replay_retains_normalized_reaction(monkeypatch):
    original = smiles(CASES[0]["original_mapped"])
    normalized = prep.normalize_mapped_reaction(original)
    monkeypatch.setattr(aware, "_validate_rule", lambda *a: [{"status": "no_outcomes", "exact_prepared_precursors": False}])
    aligned, report = aware.extraction_reaction(original, normalized, RuleExtractionConfig.from_yaml(CONFIG))
    assert str(aligned) == str(normalized)
    assert report["status"] == "rejected"


def test_changed_normalized_graph_blocks_alignment(monkeypatch):
    original = smiles(CASES[0]["original_mapped"])
    normalized = prep.normalize_mapped_reaction(original)
    results = iter(["different", "graphs"])
    monkeypatch.setattr(aware, "_canonical_state", lambda *a: next(results))
    aligned, report = aware.extraction_reaction(original, normalized, RuleExtractionConfig.from_yaml(CONFIG))
    assert str(aligned) == str(normalized)
    assert report["status"] == "unchanged"
    assert "prepared mapped molecule" in report["components"][0]["reason"]


def test_final_pair_audit_uses_unaligned_source_reference(tmp_path):
    sources = {}
    for case in CASES:
        reaction = smiles(case["original_mapped"])
        path = tmp_path / f"{case['dataset']}.json"
        prep.write_json(path, [{"type": "mol", "smiles": str(reaction.products[0]), "children": [
            {"type": "reaction", "smiles": case["original_mapped"], "metadata": {"ID": case["reaction_id"]},
             "children": [{"type": "mol", "smiles": str(m)} for m in reaction.reactants]}
        ]}])
        sources[case["dataset"]] = path
    out = tmp_path / "prepared"
    prep.prepare_single_step(sources, out, CONFIG)
    manifest = json.loads((out / "preparation.json").read_text())
    assert manifest["reaction_extraction"]["counts"] == {"aligned": 2}
    assert manifest["final_pair_replay"]["status"] == "passed"
    records = list(prep.read_records(out / "reaction_provenance.jsonl"))
    assert len(records) == 2
    for r in records:
        assert r["mapped"] == r["source_reactions"][0]["extraction_mapped"]
        assert r["mapped"] != r["source_reactions"][0]["normalized_mapped"]
    rows = list(prep.read_records(out / "replay_audit/pairs.jsonl"))
    assert len(rows) == 2 and all(r["status"] == "passed" for r in rows)
    for row in rows:
        assert row["supports"][0]["source_mapped"] != row["supports"][0]["extraction_mapped"]


def test_unaligned_tautomer_duplicates_keep_the_existing_group(tmp_path):
    cases = json.loads((Path(__file__).parent / "fixtures/deduplication_tautomers.json").read_text())
    sources = {}
    for case in cases:
        reaction = smiles(case["original_mapped"])
        path = tmp_path / f"{case['dataset']}.json"
        prep.write_json(path, [{"type": "mol", "smiles": str(reaction.products[0]), "children": [
            {"type": "reaction", "smiles": case["original_mapped"], "metadata": {"ID": case["reaction_id"]},
             "children": [{"type": "mol", "smiles": str(m)} for m in reaction.reactants]}
        ]}])
        sources[case["dataset"]] = path
    out = tmp_path / "prepared"
    prep.prepare_single_step(sources, out, CONFIG)
    manifest = json.loads((out / "preparation.json").read_text())
    assert manifest["reaction_occurrences"] == 2
    assert manifest["unique_reactions"] == 1
    assert manifest["policy_rows"] == 1
    assert manifest["final_pair_replay"]["status"] == "passed"
    assert not list(prep.read_records(out / "reaction_alignment.jsonl"))
