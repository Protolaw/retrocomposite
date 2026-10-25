"""Molecule identity, separate from model-input SMILES and exact reaction state."""

from functools import lru_cache

MOLECULE_IDENTITY_POLICY = "chython-standard-inchi-stereo-free/1"


def _from_molecule(molecule):
    from chython import to_inchi
    from chython.containers import MoleculeContainer

    if not isinstance(molecule, MoleculeContainer) or not len(molecule):
        raise ValueError("Molecule identity requires a nonempty molecule")
    # Do not run chemical canonicalization here: it can change tautomer state.
    # Chython/libINCHI works on a copy and omits atom maps and all stereo data.
    identifier = to_inchi(molecule, ignore_stereo=True, inplace=False)
    if not identifier.startswith("InChI=1S/"):
        raise ValueError("Expected a full Standard InChI identifier")
    return identifier


@lru_cache(maxsize=8192)
def _from_smiles(text):
    from chython import smiles

    return _from_molecule(smiles(text))


def molecule_identity(value):
    """Full stereo-free Standard InChI; preserve source containers unchanged.

    Standard InChI normalizes supported tautomers. It is a molecule identity
    filter, never sufficient evidence of identical concrete reaction states.
    Fail on unsupported chemistry or unavailable libINCHI; never fall back to
    SMILES, a truncated identifier, or an empty key.
    """
    return _from_smiles(value) if isinstance(value, str) else _from_molecule(value)


def identity_metadata():
    from hashlib import sha256
    from importlib.metadata import version
    from pathlib import Path
    from chython.files.libinchi.wrapper import lib

    if lib is None:
        raise ImportError("Chython libINCHI is required for molecule identity")
    binary = Path(lib._name)
    return {
        "policy": MOLECULE_IDENTITY_POLICY,
        "identifier": "full Standard InChI",
        "ignore_stereo": True,
        "tautomer_policy": "Standard InChI mobile-H normalization",
        "chython_synplan_version": version("chython-synplan"),
        "libinchi_binary": binary.name,
        "libinchi_sha256": sha256(binary.read_bytes()).hexdigest(),
    }
