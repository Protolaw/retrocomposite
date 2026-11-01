"""Align spectator tautomers for extraction without changing source chemistry.

The product keeps its model-input representation. Only normalization-added,
source-unchanged proton/bond-order shifts may be aligned in the reactants.
Normalized source molecules remain the independent replay reference.
"""

POLICY = "source-unchanged-tautomer-alignment-with-replay/1"


def _side(molecules):
    atoms, bonds, owners = {}, {}, {}
    for i, molecule in enumerate(molecules):
        for n, atom in molecule.atoms():
            if n in atoms:
                raise ValueError("Repeated atom map within a reaction side")
            atoms[n] = (atom.atomic_number, atom.isotope, atom.charge,
                        atom.is_radical, atom.implicit_hydrogens)
            owners[n] = i
        for n, m, bond in molecule.bonds():
            bonds[tuple(sorted((n, m)))] = bond.order
    return atoms, bonds, owners


def _changed(left, right):
    atoms = {n for n in left[0].keys() | right[0].keys()
             if left[0].get(n) != right[0].get(n)}
    for edge in left[1].keys() | right[1].keys():
        if left[1].get(edge) != right[1].get(edge):
            atoms.update(edge)
    return atoms


def _components(atoms, edges):
    adjacent = {n: set() for n in atoms}
    for n, m in edges:
        if n in atoms and m in atoms:
            adjacent[n].add(m)
            adjacent[m].add(n)
    remaining = set(atoms)
    while remaining:
        component = {min(remaining)}
        remaining -= component
        queue = list(component)
        while queue:
            neighbors = adjacent[queue.pop()] & remaining
            remaining -= neighbors
            component |= neighbors
            queue.extend(neighbors)
        yield component


def _canonical_state(molecule):
    from synplan.chem.utils import safe_canonicalization
    return _side((safe_canonicalization(molecule),))[:2]


def _validate_rule(extraction, normalized, config):
    from synplan.chem.reaction.curation.standardizing import RemoveReagentsStandardizer
    from synplan.chem.reaction.rules.extraction import extract_rules, _rule_to_reactor_smarts
    from synplan.chem.reaction.reactor import CanonicalRetroReactor
    from synplan.chem.utils import unite_molecules, safe_canonicalization
    from retrocomposite.replay import precursor_ids, replay_pair

    reference = RemoveReagentsStandardizer()(normalized.copy())
    expected = [safe_canonicalization(m) for m in reference.reactants]
    target = str(safe_canonicalization(unite_molecules(reference.products)))
    rules, skipped = extract_rules(config, extraction)
    if skipped or not rules:
        raise ValueError("Aligned extraction produced no rules")
    checks = []
    for rule in rules:
        text = _rule_to_reactor_smarts(rule)
        # Exercise the serialized pattern grouping, not only an in-memory query.
        reactor = CanonicalRetroReactor.from_smarts(text, delete_atoms=False)
        replay = replay_pair(target, reactor, [precursor_ids(expected)])
        exact = any(sorted(w["precursor_smiles"]) == sorted(map(str, expected))
                    for w in replay.get("witnesses", []))
        checks.append({"rule_smarts": text, "status": replay["status"],
                       "exact_prepared_precursors": exact,
                       "input_patterns": len(reactor._patterns)})
    return checks


def extraction_reaction(original, normalized, config):
    """Return an extraction view plus a ledger; inputs are never modified.

    Uncertain candidates retain complete normalization and remain subject to
    the mandatory full final-pair audit. Never drop a source reaction or use
    route IDs, rule IDs or evaluation outcomes to choose a repair.
    """
    from chython.containers import ReactionContainer
    from retrocomposite.identity import molecule_identity

    source_left, source_right = _side(original.reactants), _side(original.products)
    left, right = _side(normalized.reactants), _side(normalized.products)
    protected = _changed(source_left, source_right)
    changed = _changed(left, right)
    candidates = [c for c in _components(changed, left[1].keys() | right[1].keys())
                  if c.isdisjoint(protected)]
    if not candidates or not protected:
        return normalized, None
    ledger = {"policy": POLICY, "source_changed_atoms": sorted(protected),
              "status": "unchanged", "components": []}
    reactants = [m.copy() for m in normalized.reactants]
    accepted = set()
    for component in candidates:
        item = {"atom_maps": sorted(component), "status": "retained"}
        ledger["components"].append(item)
        try:
            if not component <= (left[0].keys() & right[0].keys()):
                raise ValueError("Atoms added or removed")
            if len({left[2][n] for n in component}) != 1 or len({right[2][n] for n in component}) != 1:
                raise ValueError("Change spans distinct molecules")
            # Identity, charge and radicals must agree; only implicit H may move.
            if any(left[0][n][:-1] != right[0][n][:-1] or
                   left[0][n][-1] is None or right[0][n][-1] is None for n in component):
                raise ValueError("Change is not an assessed proton/bond-order shift")
            if sum(left[0][n][-1] for n in component) != sum(right[0][n][-1] for n in component):
                raise ValueError("Component does not conserve hydrogens")
            edits = []
            for edge in left[1].keys() | right[1].keys():
                before, after = left[1].get(edge), right[1].get(edge)
                if component.intersection(edge) and before != after:
                    if not set(edge) <= component or {before, after} != {1, 2}:
                        raise ValueError("Connectivity or unsupported bond-order change")
                    edits.append((edge, before, after))
            if not edits:
                raise ValueError("No transferable single/double bond shifts")
            owner = left[2][next(iter(component))]
            # Require the same reactant to participate in recorded chemistry.
            if not protected.intersection(normalized.reactants[owner]):
                raise ValueError("Tautomer-only spectator molecule")
            candidate = reactants[owner].copy()
            for (n, m), before, after in edits:
                candidate.delete_bond(n, m, _skip_calculation=True)
                candidate.add_bond(n, m, after, _skip_calculation=True)
            candidate.fix_structure()
            actual = _side((candidate,))
            expected_atoms = dict(_side((reactants[owner],))[0])
            expected_atoms.update({n: right[0][n] for n in component})
            if actual[0] != expected_atoms:
                raise ValueError("Alignment changed atom states outside the proposed shift")
            check = candidate.copy()
            check.kekule()
            if check.check_valence():
                raise ValueError("Aligned molecule has invalid valence")
            reference = normalized.reactants[owner]
            if molecule_identity(candidate) != molecule_identity(reference):
                raise ValueError("Alignment changes stereo-free Standard InChI")
            if _canonical_state(candidate) != _canonical_state(reference):
                raise ValueError("Alignment changes the prepared mapped molecule")
            reactants[owner] = candidate
            accepted |= component
            item.update(status="aligned", bonds=[{"atoms": list(edge), "before": a, "after": b}
                                                  for edge, a, b in sorted(edits)])
        except (ValueError, KeyError) as error:
            item["reason"] = str(error)
    if not accepted:
        return normalized, ledger
    aligned = ReactionContainer(tuple(reactants), tuple(m.copy() for m in normalized.products),
                               tuple(m.copy() for m in normalized.reagents))
    try:
        if _changed(_side(aligned.reactants), _side(aligned.products)) != changed - accepted:
            raise ValueError("Alignment changed additional reaction edits")
        checks = _validate_rule(aligned, normalized, config)
        ledger["rule_replay"] = checks
        if not all(c["status"] == "passed" and c["exact_prepared_precursors"] for c in checks):
            raise ValueError("Serialized aligned rule did not recover exact prepared precursors")
    except Exception as error:
        ledger.update(status="rejected", reason=f"{type(error).__name__}: {error}")
        return normalized, ledger
    ledger.update(status="aligned", aligned_atom_maps=sorted(accepted))
    return aligned, ledger
