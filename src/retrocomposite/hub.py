"""Versioned Hugging Face transfers without loading chemistry or ML packages."""

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile

from retrocomposite import preparation as prep

REPOS = {
    "dataset": "Protolaw/retrocomposite-data",
    "model": "Protolaw/retrocomposite-models",
}
SCHEMA = "retrocomposite-hub-release/1"


def safe_relative(name):
    path = PurePosixPath(name)
    if (
        not name
        or not path.parts
        or path.is_absolute()
        or ".." in path.parts
        or "\\" in name
        or str(path) != name
    ):
        raise ValueError(f"Unsafe artifact path: {name}")
    return path


def release_prefix(release):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", release):
        raise ValueError("Release name must be a simple identifier, not a path")
    return f"releases/{release}"


def verified_files(root, manifest_name):
    root = Path(root)
    manifest = json.loads((root / manifest_name).read_text())
    if (root / "INCOMPLETE").exists() or not manifest.get("outputs"):
        raise ValueError(f"Incomplete artifact: {root}")
    if manifest_name == "run.json" and manifest.get("status") != "complete":
        raise ValueError("Only complete training runs may be uploaded")
    files = {manifest_name: root / manifest_name}
    for name, expected in manifest["outputs"].items():
        safe_relative(name)
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Artifact symlink escapes its source: {name}")
        if prep.digest(path) != expected:
            raise ValueError(f"Artifact hash mismatch: {name}")
        files[name] = path
    return files


def collect_files(source, kind):
    """Upload only manifest-listed artifacts, never an arbitrary project tree."""
    source = Path(source).resolve()
    if kind == "model":
        return verified_files(source, "run.json")
    files = {}
    for name in ("single_step", "stock", "cohorts", "splits"):
        directory = source / name
        if not directory.exists():
            continue
        roots = sorted(directory.iterdir()) if name == "splits" else [directory]
        for root in roots:
            if not root.is_dir() or root.name.startswith("."):
                continue
            for relative, path in verified_files(root, "preparation.json").items():
                files[f"{root.relative_to(source).as_posix()}/{relative}"] = path
    if not files:
        raise ValueError(
            "No prepared artifacts found: expected single_step/, stock/, cohorts/, or splits/"
        )
    return files


def upload(source, kind, release, repo_id=None, dataset_revision=None, api=None):
    from huggingface_hub import CommitOperationAdd, HfApi

    api = api or HfApi()
    repo_id = repo_id or REPOS[kind]
    prefix = release_prefix(release)
    files = collect_files(source, kind)
    dataset = None
    if kind == "model":
        if not dataset_revision or not re.fullmatch(r"[0-9a-f]{40}", dataset_revision):
            raise ValueError(
                "Model uploads require the exact 40-character --dataset-revision commit"
            )
        info = api.repo_info(
            REPOS["dataset"], repo_type="dataset", revision=dataset_revision
        )
        if info.sha != dataset_revision:
            raise ValueError("Dataset revision did not resolve to the requested commit")
        dataset = {"repo_id": REPOS["dataset"], "revision": info.sha}
    head = api.repo_info(repo_id, repo_type=kind).sha
    existing = api.list_repo_files(repo_id, repo_type=kind, revision=head)
    if any(name == prefix or name.startswith(prefix + "/") for name in existing):
        raise FileExistsError(f"Release already exists: {repo_id}/{prefix}")
    # Upload an immutable local snapshot; original files may belong to another job.
    with tempfile.TemporaryDirectory(prefix="retrocomposite-hub-") as temporary:
        staging = Path(temporary)
        hashes = {}
        for name, path in sorted(files.items()):
            safe_relative(name)
            destination = staging / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
            hashes[name] = prep.digest(destination)
            if hashes[name] != prep.digest(path):
                raise ValueError(f"Source changed during snapshot: {name}")
        # Recheck the source's own hash contracts after snapshotting as well.
        collect_files(source, kind)
        collect_files(staging, kind)
        manifest = {
            "schema": SCHEMA,
            "kind": kind,
            "release": release,
            "dataset": dataset,
            "files": hashes,
        }
        operations = [
            CommitOperationAdd(
                path_in_repo=f"{prefix}/payload/{name}", path_or_fileobj=staging / name
            )
            for name in sorted(hashes)
        ]
        operations.append(
            CommitOperationAdd(
                path_in_repo=f"{prefix}/release.json",
                path_or_fileobj=(
                    json.dumps(manifest, indent=2, sort_keys=True) + "\n"
                ).encode(),
            )
        )
        commit = api.create_commit(
            repo_id,
            repo_type=kind,
            operations=operations,
            parent_commit=head,
            commit_message=f"Publish {release}",
        )
    return {
        "repo_id": repo_id,
        "repo_type": kind,
        "release": release,
        "revision": commit.oid,
        "url": commit.commit_url,
        "file_count": len(hashes),
    }


def download(
    kind, release, destination, revision="main", repo_id=None, api=None, downloader=None
):
    from huggingface_hub import HfApi, snapshot_download

    api = api or HfApi()
    downloader = downloader or snapshot_download
    repo_id = repo_id or REPOS[kind]
    prefix = release_prefix(release)
    destination = Path(destination).resolve()
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite {destination}")
    # Resolve a tag/branch once, then fetch and record that exact immutable commit.
    sha = api.repo_info(repo_id, repo_type=kind, revision=revision).sha
    snapshot = Path(
        downloader(
            repo_id, repo_type=kind, revision=sha, allow_patterns=[prefix + "/*"]
        )
    )
    root = snapshot / prefix
    manifest = json.loads((root / "release.json").read_text())
    if (
        manifest.get("schema") != SCHEMA
        or manifest.get("kind") != kind
        or manifest.get("release") != release
    ):
        raise ValueError("Unexpected Hub release manifest")
    if not manifest.get("files"):
        raise ValueError("Empty Hub release")
    with prep.publication(destination) as out:
        for name, expected in manifest["files"].items():
            safe_relative(name)
            if name == "hub-release.json":
                raise ValueError("Reserved artifact receipt path")
            path = root / "payload" / name
            if prep.digest(path) != expected:
                raise ValueError(f"Downloaded checksum mismatch: {name}")
            target = out / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            if prep.digest(target) != expected:
                raise ValueError(f"Copied checksum mismatch: {name}")
        collect_files(out, kind)
        receipt = {**manifest, "repo_id": repo_id, "revision": sha}
        prep.write_json(out / "hub-release.json", receipt)
    return {
        "repo_id": repo_id,
        "revision": sha,
        "destination": str(destination),
        "file_count": len(manifest["files"]),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("upload", "download"):
        child = commands.add_parser(command)
        child.add_argument("--kind", choices=tuple(REPOS), required=True)
        child.add_argument("--release", required=True)
        child.add_argument("--repo", help="Override the default Protolaw repository")
        if command == "upload":
            child.add_argument("--source", type=Path, required=True)
            child.add_argument(
                "--dataset-revision",
                help="Exact dataset commit associated with a model",
            )
        else:
            child.add_argument("--output", type=Path, required=True)
            child.add_argument("--revision", default="main")
    args = parser.parse_args(argv)
    if args.command == "upload":
        result = upload(
            args.source, args.kind, args.release, args.repo, args.dataset_revision
        )
    else:
        result = download(
            args.kind, args.release, args.output, args.revision, args.repo
        )
    print(json.dumps(result, indent=2))
