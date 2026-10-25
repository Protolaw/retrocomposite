"""Portable source integrity, deterministic packaging, and safe extraction."""

import importlib.util
import io
import json
from pathlib import Path
import shutil
import tarfile

import pytest

spec = importlib.util.spec_from_file_location(
    "source_snapshots",
    Path(__file__).resolve().parents[1] / "scripts/source_snapshots.py",
)
snapshots = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshots)


@pytest.fixture
def project(tmp_path):
    project = tmp_path / "project"
    (project / "environment").mkdir(parents=True)
    root = tmp_path / "upstream"
    root.mkdir()
    (root / "LICENSE").write_text("MIT test license\n")
    (root / "module.py").write_text("# recorded local change\n")
    (root / "unrecorded.txt").write_text("must not be packaged")
    files = {
        f.name: snapshots.digest(f.read_bytes())
        for f in root.iterdir()
        if f.name != "unrecorded.txt"
    }
    source = {
        "path": str(root),
        "source_files": files,
        "source_digest": snapshots.digest(json.dumps(files, sort_keys=True).encode()),
        "git_commit": "abc",
    }
    (project / "environment/sources.json").write_text(
        json.dumps({"sources": {"Example": source}})
    )
    return project, root


def test_exact_and_deterministic_without_original_checkout(project, tmp_path):
    project, root = project
    first = snapshots.pack(project)
    shutil.rmtree(project / "environment/source_snapshots")
    assert snapshots.pack(project) == first
    shutil.rmtree(root)
    snapshots.unpack(project, tmp_path / "restored")
    assert sorted(p.name for p in (tmp_path / "restored/Example").iterdir()) == [
        "LICENSE",
        "module.py",
    ]
    assert (
        tmp_path / "restored/Example/module.py"
    ).read_text() == "# recorded local change\n"


def test_changed_source_cannot_be_packaged(project):
    project, root = project
    (root / "module.py").write_text("changed")
    with pytest.raises(ValueError, match="Source hash mismatch"):
        snapshots.pack(project)
    assert not (project / "environment/source_snapshots").exists()


def test_generated_tls_files_are_never_packaged(project, tmp_path):
    project, root = project
    receipt = project / "environment/sources.json"
    metadata = json.loads(receipt.read_text())
    source = metadata["sources"].pop("Example")
    metadata["sources"]["route-inspector"] = source
    tls = "route_inspector/outputs/gui/tls/server.key"
    (root / tls).parent.mkdir(parents=True)
    (root / tls).write_text("fixture runtime key, never publish")
    source["source_files"][tls] = snapshots.digest((root / tls).read_bytes())
    source["source_digest"] = snapshots.digest(
        json.dumps(source["source_files"], sort_keys=True).encode()
    )
    receipt.write_text(json.dumps(metadata))
    manifest = snapshots.pack(project)["sources"]["route-inspector"]
    assert list(manifest["excluded_runtime_files"]) == [tls]
    assert manifest["source_digest"] != manifest["bundled_source_digest"]
    snapshots.unpack(project, tmp_path / "restored")
    assert not (tmp_path / "restored/route-inspector" / tls).exists()


def test_archive_corruption_rejected_before_extraction(project, tmp_path):
    project, _ = project
    manifest = snapshots.pack(project)
    archive = (
        project
        / "environment/source_snapshots"
        / manifest["sources"]["Example"]["archive"]
    )
    archive.write_bytes(archive.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="Archive hash mismatch"):
        snapshots.unpack(project, tmp_path / "restored")
    assert not (tmp_path / "restored").exists()


@pytest.mark.parametrize(
    "member_name,symlink",
    [("../escape", False), ("module.py", True), ("module.py", False)],
)
def test_tampered_members_rejected_even_with_updated_archive_hash(
    project, tmp_path, member_name, symlink
):
    project, _ = project
    manifest = snapshots.pack(project)
    directory = project / "environment/source_snapshots"
    record = manifest["sources"]["Example"]
    archive = directory / record["archive"]
    with tarfile.open(archive, "w:gz") as tar:
        member = tarfile.TarInfo(member_name)
        if symlink:
            member.type = tarfile.SYMTYPE
            member.linkname = "/tmp/escape"
            tar.addfile(member)
        else:
            data = b"tampered"
            member.size = len(data)
            tar.addfile(member, io.BytesIO(data))
    record["archive_sha256"] = snapshots.digest(archive.read_bytes())
    (directory / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        snapshots.unpack(project, tmp_path / "restored")
    assert not (tmp_path / "restored").exists()
