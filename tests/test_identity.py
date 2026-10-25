"""Chython/libINCHI regressions for molecular identity and exact E3 states."""

from copy import deepcopy
import json
from pathlib import Path
import random

import pytest
from chython import smiles

from retrocomposite.identity import molecule_identity
from retrocomposite.segments import Segment, adjacent_paths, node_at, parse_step
from retrocomposite.selection import build_reference_index
from retrocomposite.splitting import assign_groups
from route_inspector.routes.access import reaction_nodes

FIXTURE = Path(__file__).parent / "fixtures/n5_identity_regressions.json"


def test_inchi_ignores_atom_maps_serialization_and_stereo_but_keeps_isotopes_charge():
    assert molecule_identity("[CH3:52][OH:14]") == molecule_identity("OC")
    assert molecule_identity("C[C@H](O)N") == molecule_identity("C[C@@H](O)N")
    assert molecule_identity("F/C=C/F") == molecule_identity("F/C=C\\F")
    assert molecule_identity("[13CH3]O") != molecule_identity("CO")
    assert molecule_identity("C[NH3+]") != molecule_identity("CN")
    assert molecule_identity("CCO") != molecule_identity("COC")
    assert molecule_identity("O.O") != molecule_identity("O")
    assert molecule_identity("[Na+].[Cl-]") == molecule_identity("[Cl-].[Na+]")


@pytest.mark.parametrize(
    "route_id,path,index",
    [
        ("3032", (0,), 1),
        ("9035", (0, 0, 0, 0, 0), 0),
        ("9035", (0, 0, 0, 0, 0, 0, 0), 0),
    ],
)
def test_actual_mismatch_precursors_have_one_nonmutating_map_invariant_inchi(
    route_id, path, index
):
    node = node_at(json.loads(FIXTURE.read_text())[route_id], path)
    mol = smiles(node["smiles"]).reactants[index]
    original = format(mol, "m")
    expected = molecule_identity(mol)
    assert expected.startswith("InChI=1S/")
    assert molecule_identity(node["children"][index]["smiles"]) == expected
    assert molecule_identity(str(mol)) == expected
    for seed in range(20):
        clone = mol.copy()
        ids = list(clone)
        permuted = list(ids)
        random.Random(seed).shuffle(permuted)
        clone.remap(dict(zip(ids, permuted)))
        assert molecule_identity(clone) == expected
        assert molecule_identity(format(clone, "m")) == expected
    assert format(mol, "m") == original


def test_both_n5_routes_and_all_six_adjacent_pairs_pass():
    routes = json.loads(FIXTURE.read_text())
    pairs = 0
    for root in routes.values():
        for path, _node in reaction_nodes(root):
            parse_step(root, path)
        for first, second in adjacent_paths(root):
            segment = Segment.from_route(root, first, second, {})
            assert segment.graphs
            assert segment.equivalent_to(segment)
            pairs += 1
    assert pairs == 6
    reference = build_reference_index(FIXTURE, 256)
    assert not reference.errors
    assert all(key.startswith("InChI=1S/") for key in reference.inputs)


def test_same_inchi_excludes_despite_different_exact_reaction_states():
    root = json.loads(FIXTURE.read_text())["9035"]
    first, second = (0, 0, 0), (0, 0, 0, 0, 0)
    original = Segment.from_route(root, first, second, {})
    changed = deepcopy(root)
    node = node_at(changed, second)
    product = node["smiles"].split(">")[-1]
    # Replace the recorded tautomerization by an identity transformation.
    # E3 signatures match while the exact graph audit retains the difference.
    node["smiles"] = product + ">>" + product
    node["children"][0]["smiles"] = product
    alternative = Segment.from_route(changed, first, second, {})
    assert original.matches_signature(alternative)
    assert original.audit_graph_match(alternative) == {"status": "different"}
    assert not original.equivalent_to(alternative)


def test_inchi_equivalent_tautomers_stay_in_one_validation_group():
    texts = ["Cc1cc(O)nc(S)n1", "N1C(=S)NC(=CC1=O)C", "CCO", "CCN"]
    rows = [
        {
            "product_smiles": text,
            "rule_id": 0,
            "routes": [str(i)],
            "patents": [],
            "patents_complete": False,
        }
        for i, text in enumerate(texts)
    ]
    assignments, _ = assign_groups(rows, 42, 0.25, "route")
    assert assignments[0]["molecule_inchi"] == assignments[1]["molecule_inchi"]
    assert assignments[0]["group_id"] == assignments[1]["group_id"]
    assert assignments[0]["partition"] == assignments[1]["partition"]


def test_invalid_identity_fails_without_smiles_fallback():
    for text in ("", "not a molecule", "CO>>C=O"):
        with pytest.raises((ValueError, TypeError)):
            molecule_identity(text)


def test_identity_backend_failure_is_not_silently_accepted(monkeypatch):
    import chython

    def fail(*args, **kwargs):
        raise ValueError("INCHI generation failed")

    monkeypatch.setattr(chython, "to_inchi", fail)
    with pytest.raises(ValueError, match="INCHI generation failed"):
        molecule_identity(smiles("CCCCO"))
