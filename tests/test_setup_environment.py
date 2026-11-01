"""Check that Conda setup targets only the explicitly activated interpreter."""

import importlib.util
from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location(
    "retrocomposite_setup", SCRIPTS / "setup_environment.py"
)
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)
sys.path.pop(0)


@pytest.fixture
def activated(tmp_path, monkeypatch):
    prefix = tmp_path / "retrocomposite_env"
    (prefix / "conda-meta").mkdir(parents=True)
    monkeypatch.setenv("CONDA_PREFIX", str(prefix))
    monkeypatch.setenv("CONDA_DEFAULT_ENV", "retrocomposite_env")
    monkeypatch.setattr(setup.sys, "prefix", str(prefix))
    monkeypatch.setattr(setup.sys, "base_prefix", str(prefix))
    return prefix


def test_selects_activated_conda_interpreter(activated):
    assert setup.active_conda_environment() == activated


def test_rejects_unactivated_environment(monkeypatch):
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    with pytest.raises(ValueError, match="Activate"):
        setup.active_conda_environment()


def test_rejects_base(activated, monkeypatch):
    monkeypatch.setenv("CONDA_DEFAULT_ENV", "base")
    with pytest.raises(ValueError, match="not base"):
        setup.active_conda_environment()


def test_rejects_base_activated_by_path(activated):
    (activated / "condabin").mkdir()
    with pytest.raises(ValueError, match="not base"):
        setup.active_conda_environment()


def test_rejects_different_python(activated, monkeypatch, tmp_path):
    monkeypatch.setattr(setup.sys, "prefix", str(tmp_path / "another-env"))
    with pytest.raises(ValueError, match="activated Conda"):
        setup.active_conda_environment()


def test_rejects_nested_venv(activated, monkeypatch):
    monkeypatch.setattr(setup.sys, "base_prefix", str(activated.parent))
    with pytest.raises(ValueError, match="activated Conda"):
        setup.active_conda_environment()


def test_rejects_directory_without_conda_metadata(activated):
    (activated / "conda-meta").rmdir()
    with pytest.raises(ValueError, match="not in a Conda"):
        setup.active_conda_environment()
