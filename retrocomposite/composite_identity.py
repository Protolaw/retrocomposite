"""Exact mapped query identity for training labels, independent of tactic families.

The joint graph retains both query sides, atom correspondence, every query
predicate and membership in each input/output pattern. Unsupported predicates
retain exact SMARTS identity. Original executable variants are never rewritten.
"""

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import json

POLICY = "joint-query-correspondence-and-patterns/1"


@dataclass(frozen=True)
class RuleIdentity:
    encoding: str
    status: str
    reason: str = ""

    @property
    def id(self):
        return "mapped_rule_" + sha256(self.encoding.encode()).hexdigest()


def joint_query_graph(query):
    from route_inspector.rules.graph import GRAPH_SCHEMA_VERSION
    from route_inspector.rules.transformation import _predicates, _value

    if query.reagents:
        raise ValueError("Reaction-agent queries require exact representation")
    atoms, bonds, maps = [], [], []
    for side, patterns in (("target", query.reactants), ("precursor", query.products)):
        numbers = {}
        for pattern in patterns:
            membership = len(atoms)
            atoms.append({"node": membership, "label": {"kind": "pattern", "side": side}})
            for number, atom in pattern.atoms():
                if number in numbers:
                    raise ValueError("Repeated atom map on one query side")
                node = len(atoms)
                numbers[number] = node
                atoms.append({"node": node, "label": {
                    "kind": "atom", "side": side,
                    "element": _value(atom.atomic_number), "symbol": atom.atomic_symbol,
                    "predicates": _predicates(atom),
                }})
                bonds.append({"nodes": [membership, node], "label": {"kind": "membership"}})
            for a, b, bond in pattern.bonds():
                bonds.append({"nodes": sorted((numbers[a], numbers[b])),
                              "label": {"kind": "bond", "predicates": _predicates(bond)}})
        maps.append(numbers)
    for number in maps[0].keys() & maps[1].keys():
        bonds.append({"nodes": [maps[0][number], maps[1][number]],
                      "label": {"kind": "correspondence"}})
    return {"graph_schema_version": GRAPH_SCHEMA_VERSION, "atoms": atoms, "bonds": bonds}


@lru_cache(maxsize=16384)
def mapped_rule_identity(rule):
    from chython import smarts
    from route_inspector.rules.canonical import _canonical_graph_certificate

    normalized = "".join(rule.split())
    try:
        certificate = _canonical_graph_certificate(joint_query_graph(smarts(normalized)))
        payload = {"policy": POLICY, "graph": certificate}
        status, reason = "canonical", ""
    except (ValueError, TypeError, AttributeError, KeyError, NotImplementedError) as error:
        payload = {"policy": POLICY, "exact_representation": normalized}
        status, reason = "exact_representation", f"{type(error).__name__}: {error}"
    return RuleIdentity(json.dumps(payload, sort_keys=True, separators=(",", ":")), status, reason)
