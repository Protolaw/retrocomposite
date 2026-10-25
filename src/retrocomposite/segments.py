"""Exact concrete adjacent-step comparison, independent of atom-map numbering.

Each step retains both full molecular sides, component membership, bond states,
and within-reaction atom correspondence. All exact intermediate alignments are
enumerated, up to a declared bound; truncation is an error, never a non-match.
"""

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache

from retrocomposite.preparation import molecule_key


def node_at(root, path):
    node = root
    for index in path:
        if type(index) is not int or index < 0:
            raise ValueError("Invalid node path")
        node = node["children"][index]
    return node


def adjacent_paths(root):
    from route_inspector.routes.access import reaction_nodes

    for first, reaction in reaction_nodes(root):
        for i, molecule in enumerate(reaction.get("children") or []):
            for j, child in enumerate(molecule.get("children") or []):
                if child.get("type") != "reaction":
                    raise ValueError("Expected alternating molecule/reaction nodes")
                yield first, (*first, i, j)


def ordered_paths(paths):
    paths = sorted((tuple(p) for p in paths), key=lambda p: (len(p), p))
    if len(paths) < 2 or len(set(paths)) != len(paths):
        raise ValueError("A linear occurrence needs at least two distinct steps")
    for first, second in zip(paths, paths[1:]):
        if len(second) != len(first) + 2 or second[:-2] != first:
            raise ValueError("Selected steps are not one consecutive linear chain")
    return paths


def parse_step(root, path):
    from chython import smiles
    from chython.containers import ReactionContainer
    from route_inspector.routes.access import (
        molecule_node_smiles,
        reaction_smiles_from_node,
    )

    node = node_at(root, path)
    parent = node_at(root, path[:-1])
    if node.get("type") != "reaction" or parent.get("type") != "mol":
        raise ValueError("Reaction path does not resolve to a reaction and its product")
    reaction = smiles(reaction_smiles_from_node(node))
    if not isinstance(reaction, ReactionContainer) or len(reaction.products) != 1:
        raise ValueError("Concrete comparison requires one recorded product per step")
    for mol in (*reaction.reactants, *reaction.products, *reaction.reagents):
        mol.clean_stereo()
    for side in (reaction.reactants, reaction.products):
        atom_ids = [atom for mol in side for atom in mol]
        if len(atom_ids) != len(set(atom_ids)):
            raise ValueError("Atom maps overlap between components on a reaction side")
    product = molecule_key(str(reaction.products[0]))
    reactants = sorted(molecule_key(str(m)) for m in reaction.reactants)
    children = node.get("children") or []
    if not children or any(c.get("type") != "mol" for c in children):
        raise ValueError("Reaction must have molecule precursors")
    if product != molecule_key(molecule_node_smiles(parent)):
        raise ValueError("Reaction product disagrees with route molecule")
    if Counter(reactants) != Counter(
        molecule_key(molecule_node_smiles(c)) for c in children
    ):
        raise ValueError("Reaction reactants disagree with route precursor multiset")
    return reaction, (product, tuple(reactants))


def atom_state(atom):
    return [
        atom.atomic_number,
        atom.isotope,
        atom.charge,
        atom.is_radical,
        atom.implicit_hydrogens,
    ]


def reaction_graph(reaction, step, offset, continued_component=None):
    """One node per mapped atom per step; explicit side states and components."""
    sides = (reaction.reactants, reaction.products)
    states = [{i: atom_state(a) for m in side for i, a in m.atoms()} for side in sides]
    ids = {i: offset + j for j, i in enumerate(sorted(set(states[0]) | set(states[1])))}
    atoms = [
        {
            "node": ids[i],
            "label": {
                "type": "atom",
                "step": step,
                "states": [s.get(i) for s in states],
            },
        }
        for i in ids
    ]
    bond_states = [
        {tuple(sorted((a, b))): int(bond) for m in side for a, b, bond in m.bonds()}
        for side in sides
    ]
    bonds = [
        {
            "nodes": [ids[a], ids[b]],
            "label": {
                "type": "bond",
                "states": [s.get((a, b)) for s in bond_states],
            },
        }
        for a, b in sorted(set(bond_states[0]) | set(bond_states[1]))
    ]
    for side_number, side in enumerate(sides):
        for component, mol in enumerate(side):
            hub = offset + len(atoms)
            atoms.append(
                {
                    "node": hub,
                    "label": {
                        "type": "component",
                        "step": step,
                        "side": side_number,
                        "continuation": side_number == 0
                        and component == continued_component,
                    },
                }
            )
            bonds.extend(
                {"nodes": [hub, ids[i]], "label": {"type": "member"}} for i in mol
            )
    return atoms, bonds, ids


@dataclass
class Segment:
    first: str
    second: str
    context: tuple
    witness: dict
    max_alignments: int = 256

    @classmethod
    def from_route(cls, root, first, second, witness, max_alignments=256):
        ordered_paths([first, second])
        r1, context1 = parse_step(root, first)
        r2, context2 = parse_step(root, second)
        # The second product must be the actual selected first-step precursor.
        from route_inspector.routes.access import molecule_node_smiles

        intermediate = molecule_key(molecule_node_smiles(node_at(root, second[:-1])))
        if intermediate != context2[0] or intermediate not in context1[1]:
            raise ValueError("Intermediate does not connect the selected reactions")
        return cls(
            format(r1, "m"),
            format(r2, "m"),
            (context1, context2, intermediate),
            witness,
            max_alignments,
        )

    @property
    def graphs(self):
        return aligned_graphs(
            self.first, self.second, self.context[2], self.max_alignments
        )

    def equivalent_to(self, other):
        from route_inspector.rules.graph import labelled_graphs_are_isomorphic

        if self.context != other.context:
            return False
        # Force complete enumeration before accepting any match.
        left, right = self.graphs, other.graphs
        return any(
            lkey == rkey and labelled_graphs_are_isomorphic(lgraph, rgraph)
            for lkey, lgraph in left
            for rkey, rgraph in right
        )


@lru_cache(maxsize=8)
def aligned_graphs(first_text, second_text, intermediate, max_alignments):
    """Bound graph memory while retaining compact text for the full n5 index."""
    from chython import smiles
    from route_inspector.rules.graph import graph_coarse_signature

    if max_alignments < 1:
        raise ValueError("max_alignments must be positive")
    first, second = smiles(first_text), smiles(second_text)
    alignments = []
    product = second.products[0]
    product_atoms = dict(product.atoms())
    for component, reactant in enumerate(first.reactants):
        if molecule_key(str(reactant)) != intermediate:
            continue
        reactant_atoms = dict(reactant.atoms())
        for mapping in product.get_mapping(
            reactant, automorphism_filter=False, match_stereo=False
        ):
            if len(mapping) != len(product) or len(set(mapping.values())) != len(
                reactant
            ):
                continue
            if any(
                atom_state(product_atoms[a]) != atom_state(reactant_atoms[b])
                for a, b in mapping.items()
            ):
                continue
            if len(alignments) >= max_alignments:
                raise ValueError(
                    "Intermediate alignment enumeration exceeded max_alignments"
                )
            alignments.append((component, mapping))
    if not alignments:
        raise ValueError("No exact intermediate atom correspondence")
    # Discover truncation before allocating any potentially large graph family.
    result = []
    for component, mapping in alignments:
        atoms1, bonds1, ids1 = reaction_graph(first, 0, 0, component)
        atoms2, bonds2, ids2 = reaction_graph(second, 1, len(atoms1))
        graph = {
            "graph_schema_version": 1,
            "atoms": deepcopy(atoms1 + atoms2),
            "bonds": deepcopy(bonds1 + bonds2)
            + [
                {"nodes": [ids2[a], ids1[b]], "label": {"type": "continuity"}}
                for a, b in mapping.items()
            ],
        }
        result.append((graph_coarse_signature(graph), graph))
    return result
