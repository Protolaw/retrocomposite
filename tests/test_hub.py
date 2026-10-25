"""Artifact transfer contracts tested against a local fake Hub, without network."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from retrocomposite import preparation as prep
from retrocomposite.hub import collect_files, download, safe_relative, upload


class FakeHub:
    def __init__(self, root):
        self.root = root
        self.files = []

    def repo_info(self, repo_id, **kwargs):
        return SimpleNamespace(sha="a" * 40)

    def list_repo_files(self, repo_id, **kwargs):
        return self.files

    def create_commit(self, repo_id, operations, **kwargs):
        assert kwargs["parent_commit"] == "a" * 40
        for operation in operations:
            path = self.root / operation.path_in_repo
            path.parent.mkdir(parents=True, exist_ok=True)
            value = operation.path_or_fileobj
            path.write_bytes(
                value if isinstance(value, bytes) else Path(value).read_bytes()
            )
            self.files.append(operation.path_in_repo)
        return SimpleNamespace(oid="b" * 40, commit_url="https://example.test/commit")

    def snapshot(self, repo_id, **kwargs):
        assert kwargs["revision"] == "a" * 40
        return str(self.root)


def dataset(root):
    directory = root / "single_step"
    directory.mkdir(parents=True)
    (directory / "single_step.tsv").write_text("invented fixture\n")
    prep.finish(directory, [], kind="single-step")
    (root / "do-not-upload.txt").write_text("unrelated local file")
    return root


def test_upload_and_download_preserve_files_and_pin_revision(tmp_path):
    source = dataset(tmp_path / "data")
    api = FakeHub(tmp_path / "remote")
    result = upload(source, "dataset", "v1", api=api)
    assert result["revision"] == "b" * 40
    assert result["file_count"] == 2
    assert not any("do-not-upload" in name for name in api.files)
    destination = tmp_path / "restored"
    received = download("dataset", "v1", destination, api=api, downloader=api.snapshot)
    assert received["revision"] == "a" * 40
    assert (destination / "single_step/single_step.tsv").read_bytes() == (
        source / "single_step/single_step.tsv"
    ).read_bytes()
    receipt = json.loads((destination / "hub-release.json").read_text())
    assert receipt["repo_id"] == "Protolaw/retrocomposite-data"
    with pytest.raises(FileExistsError):
        upload(source, "dataset", "v1", api=api)
    with pytest.raises(FileExistsError):
        download("dataset", "v1", destination, api=api, downloader=api.snapshot)


def test_hash_failures_do_not_publish_a_download(tmp_path):
    source = dataset(tmp_path / "data")
    api = FakeHub(tmp_path / "remote")
    upload(source, "dataset", "v1", api=api)
    (api.root / "releases/v1/payload/single_step/single_step.tsv").write_text("changed")
    with pytest.raises(ValueError, match="checksum mismatch"):
        download("dataset", "v1", tmp_path / "bad", api=api, downloader=api.snapshot)
    assert not (tmp_path / "bad").exists()
    (source / "single_step/single_step.tsv").write_text("changed")
    with pytest.raises(ValueError, match="hash mismatch"):
        collect_files(source, "dataset")


def test_models_require_completed_run_and_exact_dataset_revision(tmp_path):
    model = tmp_path / "model"
    model.mkdir()
    (model / "weights.ckpt").write_bytes(b"test fixture")
    manifest = {
        "status": "failed",
        "outputs": {"weights.ckpt": prep.digest(model / "weights.ckpt")},
    }
    prep.write_json(model / "run.json", manifest)
    api = FakeHub(tmp_path / "remote")
    with pytest.raises(ValueError, match="complete training"):
        upload(model, "model", "v1", dataset_revision="a" * 40, api=api)
    manifest["status"] = "complete"
    prep.write_json(model / "run.json", manifest)
    with pytest.raises(ValueError, match="exact 40-character"):
        upload(model, "model", "v1", dataset_revision="main", api=api)
    upload(model, "model", "v1", dataset_revision="a" * 40, api=api)
    release = json.loads((api.root / "releases/v1/release.json").read_text())
    assert release["dataset"]["revision"] == "a" * 40


@pytest.mark.parametrize(
    "path", ["../secret", "/absolute", "a/../b", "a\\b", "", "./a"]
)
def test_reject_unsafe_paths(path):
    with pytest.raises(ValueError):
        safe_relative(path)
