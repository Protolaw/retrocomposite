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
