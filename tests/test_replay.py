"""Chemical regression checks for pre-extraction normalization and release gating."""
import csv
import json
from pathlib import Path

import pytest

from retrocomposite import preparation as prep
from retrocomposite.identity import molecule_identity
from retrocomposite.replay import audit_training_pairs, precursor_ids, replay_pair

CONFIG = Path(__file__).resolve().parents[1] / "configs/rule_extraction.yaml"
FORMYLATION = "[CH3:1][C:2](=[O:3])[CH2:4][CH3:5].[CH:6](=[O:7])[O:8][CH2:9][CH3:10]>>[CH3:1][C:2](=[O:3])[C:4]([CH3:5])=[CH:6][OH:7]"


def source_file(tmp_path):
    from chython import smiles
    rxn = smiles(FORMYLATION)
    path = tmp_path / "source.json"
    prep.write_json(path, [{"type": "mol", "smiles": str(rxn.products[0]), "children": [
        {"type": "reaction", "smiles": FORMYLATION, "metadata": {"ID": "synthetic-formylation"},
         "children": [{"type": "mol", "smiles": str(m)} for m in rxn.reactants]}
    ]}])
    return path


def simple_reactor(tmp_path):
    from synplan.utils.loading import load_reaction_rules
    p = tmp_path / "toy.tsv"
    p.write_text("rule_smarts\tpopularity\treaction_indices\n[C:1]-[O:2]>>[C:1].[O:2]\t1\t0\n")
    return load_reaction_rules(str(p))[0]


def test_normalization_preserves_source_mapping_and_repairs_keto_enol():
    from chython import smiles
    source = smiles(FORMYLATION)
    before = format(source, "m")
    prepared = prep.normalize_mapped_reaction(source)
    assert format(source, "m") == before
    assert molecule_identity(source.products[0]) != molecule_identity(prepared.products[0])
    for old, new in zip(source.molecules(), prepared.molecules(), strict=True):
        assert {n: a.atomic_number for n, a in old.atoms()} == {n: a.atomic_number for n, a in new.atoms()}
    assert str(prep.normalize_mapped_reaction(prepared)) == str(prepared)


def test_final_export_replays_and_preserves_original_reaction(tmp_path):
    source = source_file(tmp_path)
    original_hash = prep.digest(source)
    out = tmp_path / "prepared"
    prep.prepare_single_step({"n1": source}, out, CONFIG)
    manifest = json.loads((out / "preparation.json").read_text())
    assert manifest["final_pair_replay"]["status"] == "passed"
    assert manifest["reaction_normalization"]["changed_occurrences"] == 1
    record = next(prep.read_records(out / "reaction_provenance.jsonl"))
    assert record["source_reactions"][0]["original_mapped"] != record["mapped"]
    assert record["source_reactions"][0]["normalized_mapped"] == record["mapped"]
    rows = list(prep.read_records(out / "replay_audit/pairs.jsonl"))
    assert len(rows) == 1 and rows[0]["status"] == "passed"
    assert rows[0]["support_matches"] == [True]
    assert prep.digest(source) == original_hash
    # New native products already use the same chemistry as the rules.
    assert not list(prep.read_records(out / "policy_product_normalization.jsonl"))


def test_old_extraction_order_blocks_publication_but_preserves_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(prep, "normalize_mapped_reaction", lambda reaction: reaction.copy())
    source = source_file(tmp_path)
    out = tmp_path / "bad"
    with pytest.raises(ValueError, match="Final-pair replay blocked"):
        prep.prepare_single_step({"n1": source}, out, CONFIG)
    assert not out.exists()
    assert (tmp_path / "bad.candidate/INCOMPLETE").exists()
    summary = json.loads((tmp_path / "bad.replay-audit/summary.json").read_text())
    assert summary["status"] == "blocked"
    assert summary["counts"] == {"no_outcomes": 1}


def test_every_expected_precursor_set_must_be_recovered(tmp_path):
    reactor = simple_reactor(tmp_path)
    expected = precursor_ids([prep.molecule("C"), prep.molecule("O")])
    impossible = precursor_ids([prep.molecule("N"), prep.molecule("O")])
    good = replay_pair("CO", reactor, [expected])
    assert good["status"] == "passed"
    bad = replay_pair("CO", reactor, [expected, impossible])
    assert bad["status"] == "precursor_mismatch"
    assert bad["support_matches"] == [True, False]


def test_precursor_multiplicity_is_not_collapsed(tmp_path):
    reactor = simple_reactor(tmp_path)
    expected = precursor_ids([prep.molecule("C"), prep.molecule("O"), prep.molecule("O")])
    assert replay_pair("CO", reactor, [expected])["status"] == "precursor_mismatch"


def test_budget_exhaustion_is_inconclusive(tmp_path, monkeypatch):
    from synplan.chem.reaction import reactor as backend
    def exhausted(*args, diagnostics, **kwargs):
        diagnostics.append({"reason": "mapping_budget_exceeded"})
        return iter(())
    monkeypatch.setattr(backend, "apply_reaction_rule", exhausted)
    result = replay_pair("CO", simple_reactor(tmp_path), [[molecule_identity("C")]])
    assert result["status"] == "inconclusive"


def test_outcome_cap_is_not_a_false_negative(tmp_path):
    result = replay_pair("CO", simple_reactor(tmp_path), [[molecule_identity("N")]], max_outcomes=1)
    assert result["status"] == "inconclusive"
    assert result["outcome_cap_reached"]


def test_actual_replay_rejects_wrong_source_precursors(tmp_path):
    source = source_file(tmp_path)
    out = tmp_path / "prepared"
    prep.prepare_single_step({"n1": source}, out, CONFIG)
    path = out / "reaction_provenance.jsonl"
    record = next(prep.read_records(path))
    # Keep the product and row join unchanged, corrupt only reaction evidence.
    record["mapped"] = "[NH3:99]>>" + record["mapped"].split(">>")[1]
    record["source_reactions"][0]["normalized_mapped"] = record["mapped"]
    record["source_reactions"][0]["extraction_mapped"] = record["mapped"]
    prep.write_jsonl(path, [record])
    result = audit_training_pairs(out, tmp_path / "audit")
    assert result["status"] == "blocked"


def test_invalid_audit_limits_rejected(tmp_path):
    with pytest.raises(ValueError, match="positive"):
        audit_training_pairs(tmp_path, tmp_path / "audit", max_outcomes=0)


def test_composite_direct_replay_uses_certified_net_boundary(tmp_path):
    record = {
        "kind": "rrseq_cons", "dataset_id": "n1", "composite_identity_version": 3,
        "composite_rule": "[C:1]-[O:2]>>[C:1].[O:2]", "product_smiles": "CO",
        "certificate": {
            **{k: True for k in ["source_occurrence_certified", "source_chemistry_equivalent",
                                 "source_mapping_consistent", "composite_chemistry_equivalent",
                                 "composite_mapping_consistent"]},
            "abstraction_boundary": {"policy": "synplanner_net_reactants_v1",
                                     "retained_components": [{"mapped_smiles": "[CH4:1]"}, {"mapped_smiles": "[OH2:2]"}],
                                     "omitted_components": []},
        },
        "provenance": {"route_id": "invented", "source_identity": "synthetic", "reference_occurrence_id": "toy"},
        "decomposition": {"raw_sequence": ["synthetic transport fixture"]},
    }
    assets = tmp_path / "composite"
    prep.export_composites([record], assets, [])
    result = audit_training_pairs(assets, tmp_path / "audit")
    assert result["status"] == "passed" and result["support_checks"] == 1
    assert "unwrapping is not certified" in result["scope"]
    # A source certificate alone is insufficient if the final target changes.
    p = assets / "composite_policy_data.tsv"
    p.write_text("product_smiles\trule_id\nCC\t0\n")
    record["product_smiles"] = "CC"
    record.update(rule_id=0, training_pair_index=0)
    prep.write_jsonl(assets / "composite_records.jsonl", [record])
    bad = audit_training_pairs(assets, tmp_path / "bad-audit")
    assert bad["counts"] == {"no_outcomes": 1}


def test_corrupted_duplicate_representative_is_rejected(tmp_path):
    source = source_file(tmp_path)
    assets = tmp_path / "assets"
    prep.prepare_single_step({"n1": source}, assets, CONFIG)
    path = assets / "reaction_provenance.jsonl"
    record = next(prep.read_records(path))
    record["source_reactions"][0]["extraction_mapped"] = FORMYLATION
    prep.write_jsonl(path, [record])
    with pytest.raises(ValueError, match="absent from its normalized source"):
        audit_training_pairs(assets, tmp_path / "audit")


def test_unchanged_source_valence_flags_are_preserved_for_replay_audit():
    from chython import smiles
    reaction = smiles("[O:1]=[I:2](=[O:3])[Cl:4].[CH3:5][OH:6]>>[CH2:5]=[O:6]")
    prepared = prep.normalize_mapped_reaction(reaction)
    assert str(prepared.reactants[0]) == str(reaction.reactants[0])
    assert prepared.reactants[0].check_valence()
