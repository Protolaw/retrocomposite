"""Mapping-equivalent labels must preserve executable query semantics."""
import json

from chython import smarts
from chython.containers import ReactionContainer
from route_inspector.rules.canonical import _canonical_graph_certificate
from route_inspector.composite_rules.families import family_key_from_smarts
from retrocomposite.composite_identity import joint_query_graph, mapped_rule_identity
from retrocomposite import preparation as prep
from retrocomposite.splitting import composite_sources, read_tsv
from test_preparation import record
import pytest

RULES = (
    "[C:1]-[C:2]-[N:3](-[C:4])-[C:5]>>[N:3](-[C:4])-[C:5].[C:1]-[C:2]-[O:6]",
    "[C:1]-[N:2](-[C:3]-[C:4])-[C:5]>>[C:1]-[N:2]-[C:5].[C:3](-[C:4])-[O:6]",
    "[C:1]-[C:2]-[N:3](-[C:4])-[C:5]>>[C:1]-[C:2]-[O:6].[N:3](-[C:4])-[C:5]",
)


def test_reported_rules_merge_with_joint_correspondence():
    identities = [mapped_rule_identity(rule) for rule in RULES]
    assert len(set(identities)) == 1
    assert identities[0].status == "canonical"


def test_different_cross_side_correspondence_does_not_merge():
    a = "[C:1]-[C:2]-[O:3]>>[C:1]-[O:3].[C:2]"
    b = "[C:1]-[C:2]-[O:3]>>[C:2]-[O:3].[C:1]"
    assert family_key_from_smarts(a).encoding == family_key_from_smarts(b).encoding
    assert mapped_rule_identity(a).encoding != mapped_rule_identity(b).encoding


@pytest.mark.parametrize("other", [
    "[C;D2:1]-[O:2]>>[C:1].[O:2]",
    "[C+:1]-[O:2]>>[C:1].[O:2]",
    "[13C:1]-[O:2]>>[C:1].[O:2]",
    "[C:1]=[O:2]>>[C:1].[O:2]",
    "[C:1]-[O:2]>>[C:1].[O:3]",
    "[C:1]-[O:2]>>[C:1].[O:2].[O:3]",
])
def test_query_constraints_side_presence_and_multiplicity_are_preserved(other):
    assert mapped_rule_identity(other).encoding != mapped_rule_identity("[C:1]-[O:2]>>[C:1].[O:2]").encoding


def test_disconnected_single_pattern_is_not_two_input_patterns():
    a, b = smarts("[C:1]"), smarts("[O:2]")
    together = ReactionContainer([a | b], [a.copy(), b.copy()])
    separate = ReactionContainer([a, b], [a.copy(), b.copy()])
    assert _canonical_graph_certificate(joint_query_graph(together)) != _canonical_graph_certificate(joint_query_graph(separate))


def test_unsupported_predicates_fall_back_to_exact_text(monkeypatch):
    from retrocomposite import composite_identity as module
    def unsupported(query):
        raise NotImplementedError("future query predicate")
    monkeypatch.setattr(module, "joint_query_graph", unsupported)
    module.mapped_rule_identity.cache_clear()
    a, b = (module.mapped_rule_identity(r) for r in RULES[:2])
    assert a.status == b.status == "exact_representation"
    assert a.encoding != b.encoding
    module.mapped_rule_identity.cache_clear()


def test_merge_preserves_variant_certificates_and_unions_all_source_routes(tmp_path):
    records = [{**record(), "composite_rule": rule, "provenance": {
        "route_id": str(i), "source_identity": "synthetic-source", "variant_id": f"v{i}",
        "tactic_entry_id": f"t{i}", "reference_occurrence_id": f"o{i}"},
        "decomposition": {"raw_sequence": [f"step-{i}"]}} for i, rule in enumerate(RULES)]
    out = tmp_path / "merged"
    prep.export_composites(records, out, [])
    rules, rows = read_tsv(out / "composite.tsv"), read_tsv(out / "composite_policy_data.tsv")
    assert len(rules) == len(rows) == 1
    witnesses = list(prep.read_records(out / "composite_records.jsonl"))
    for original in records:
        assert any(all(w[k] == v for k, v in original.items()) for w in witnesses)
    assert len(composite_sources(out, rules, rows)[0]) == 3
    mapping = json.loads((out / "composite_rule_mapping.json").read_text())
    assert len(mapping["rules"][0]["variants"]) == 3
    assert mapping["rules"][0]["popularity"] == 1
    witnesses[0]["composite_rule"] = "[C:1]-[N:2]>>[C:1].[N:2]"
    prep.write_jsonl(out / "composite_records.jsonl", witnesses)
    with pytest.raises(ValueError, match="training pair"):
        composite_sources(out, rules, rows)


def test_both_cohorts_merge_rebuild_splits_and_replay_every_occurrence(tmp_path):
    from retrocomposite.composite_merging import merge_cohorts
    from retrocomposite.splitting import create_split, load_split, verify_publication

    cohorts = tmp_path / "source_cohorts"
    cohorts.mkdir()
    variants = ("[C:1]-[O:2]>>[C:1].[O:2]", "[O:9]-[C:8]>>[O:9].[C:8]")
    for name in ("primary", "patent_disjoint"):
        records = []
        for length in range(2, 6):
            for variant, rule in enumerate(variants):
                row = record()
                row.update(product_smiles="C" * length + "O", composite_rule=rule)
                row["provenance"] = {"route_id": str(length), "source_identity": "synthetic-source",
                                     "reference_occurrence_id": f"o{length}-{variant}",
                                     "variant_id": f"v{variant}", "tactic_entry_id": f"t{variant}"}
                row["certificate"]["abstraction_boundary"] = {
                    "policy": "synplanner_net_reactants_v1",
                    "retained_components": [{"mapped_smiles": "C" * length}, {"mapped_smiles": "O"}],
                }
                records.append(row)
        prep.export_composites(records, cohorts / name, [], merge_equivalent=False)
        prep.write_json(cohorts / name / "support.json", {"status": "ready"})
    prep.write_json(cohorts / "selection.json", {"cohorts": {
        name: {"status": "ready"} for name in ("primary", "patent_disjoint")}})
    prep.finish(cohorts, [], kind="cohort-selection")
    for name in ("primary", "patent_disjoint"):
        create_split(cohorts / name, tmp_path / "old_splits" / name, 17, 0.25)
    output = tmp_path / "merged_bundle"
    report = merge_cohorts(cohorts, tmp_path / "old_splits", output)
    assert report["status"] == "passed"
    for name, cohort in report["cohorts"].items():
        assert (cohort["old_rules"], cohort["rules"]) == (2, 1)
        assert (cohort["old_pairs"], cohort["pairs"], cohort["occurrences"]) == (8, 4, 8)
        assert cohort["replay"]["support_checks"] == 8
        assert cohort["replay"]["counts"] == {"passed": 4}
        metadata, _ = load_split(output / "splits" / name)
        assert metadata["seed"] == 17
        assert not any(metadata["overlap"].values())
        assert len(set(cohort["old_to_new_rule_ids"])) == 1
    assert verify_publication(output)["status"] == "passed"
    with pytest.raises(FileExistsError):
        merge_cohorts(cohorts, tmp_path / "old_splits", output)


def test_fresh_selection_support_counts_match_merged_labels():
    from retrocomposite.selection import support
    records = [{**record(), "composite_rule": rule, "provenance": {
        "composite_id": "family", "variant_id": f"v{i}", "tactic_entry_id": f"t{i}",
        "reference_occurrence_id": f"o{i}"}} for i, rule in enumerate(RULES)]
    report = support(records)
    assert report["rules"] == report["training_pairs"] == 1
    assert report["exact_variant_rules"] == report["exact_variant_training_pairs"] == 3
    assert len(report["variants"]) == len(report["tactics"]) == report["occurrences"] == 3
