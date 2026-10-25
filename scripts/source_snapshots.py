"""Package and verify the exact installation sources in environment/sources.json."""

import argparse
import gzip
from hashlib import sha256
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
import tempfile


SCHEMA = "retrocomposite-source-bundles/1"
# Generated GUI credentials were accidentally captured by the original recursive
# source inventory. They are runtime state, never portable software sources.
RUNTIME_EXCLUSIONS = {
    "route-inspector": {
        "route_inspector/outputs/gui/tls/server.key",
        "route_inspector/outputs/gui/tls/server.crt",
    }
}


def digest(data):
    return sha256(data).hexdigest()


def safe_name(name):
    path = PurePosixPath(name)
    if (
        not path.parts
        or path.is_absolute()
        or ".." in path.parts
        or "\\" in name
        or ":" in name
        or str(path) != name
    ):
        raise ValueError(f"Unsafe source path: {name}")
    return path


def expected_files(source, project_name):
    files = source["source_files"]
    if (
        not files
        or digest(json.dumps(files, sort_keys=True).encode()) != source["source_digest"]
    ):
        raise ValueError("Invalid recorded source digest")
    for name in files:
        safe_name(name)
    excluded = RUNTIME_EXCLUSIONS.get(project_name, set())
    return {name: value for name, value in files.items() if name not in excluded}


def portable_metadata(sources):
    return {
        name: {
            **source,
            "bundled_source_digest": digest(
                json.dumps(expected_files(source, name), sort_keys=True).encode()
            ),
        }
        for name, source in sources.items()
    }


def pack(project, roots=None):
    """Only recorded files are packaged, including recorded working-tree edits."""
    project = Path(project)
    sources = json.loads((project / "environment/sources.json").read_text())["sources"]
    destination = project / "environment/source_snapshots"
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite {destination}")
    manifest = {"schema": SCHEMA, "sources": {}}
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        staging = Path(tmp)
        for name, source in sorted(sources.items()):
            root = Path((roots or {}).get(name, source["path"]))
            files = expected_files(source, name)
            bundled_digest = digest(json.dumps(files, sort_keys=True).encode())
            filename = f"{name}-{bundled_digest[:16]}.tar.gz"
            archive = staging / filename
            with archive.open("wb") as raw:
                with gzip.GzipFile(
                    filename="", fileobj=raw, mode="wb", mtime=0
                ) as compressed:
                    with tarfile.open(
                        fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT
                    ) as tar:
                        for relative, expected in sorted(files.items()):
                            data = (root / relative).read_bytes()
                            if digest(data) != expected:
                                raise ValueError(
                                    f"Source hash mismatch: {name}/{relative}"
                                )
                            info = tarfile.TarInfo(relative)
                            info.size = len(data)
                            info.mode = 0o644
                            tar.addfile(info, io.BytesIO(data))
            manifest["sources"][name] = {
                "archive": filename,
                "archive_sha256": digest(archive.read_bytes()),
                "source_digest": source["source_digest"],
                "bundled_source_digest": bundled_digest,
                "excluded_runtime_files": {
                    p: h for p, h in source["source_files"].items() if p not in files
                },
                "git_commit": source["git_commit"],
                "file_count": len(files),
                "size_bytes": archive.stat().st_size,
            }
        (staging / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )
        # An exclusive destination prevents accidental replacement of an old bundle.
        destination.mkdir()
        marker = destination / "INCOMPLETE"
        marker.write_text("Packaging in progress\n")
        for path in staging.iterdir():
            path.replace(destination / path.name)
        marker.unlink()
    return manifest


def unpack(project, destination):
    """Verify archive and every file before writing; never use tar.extractall."""
    project, destination = Path(project), Path(destination)
    sources = json.loads((project / "environment/sources.json").read_text())["sources"]
    bundle = project / "environment/source_snapshots"
    manifest = json.loads((bundle / "manifest.json").read_text())
    if (bundle / "INCOMPLETE").exists() or manifest.get("schema") != SCHEMA:
        raise ValueError("Incomplete or unsupported source bundle")
    if set(manifest["sources"]) != set(sources):
        raise ValueError("Source bundle names differ from sources.json")
    for name, source in sources.items():
        safe_name(name)
        record = manifest["sources"][name]
        files = expected_files(source, name)
        if record["source_digest"] != source["source_digest"]:
            raise ValueError(f"Bundle source digest mismatch: {name}")
        if record["bundled_source_digest"] != digest(
            json.dumps(files, sort_keys=True).encode()
        ):
            raise ValueError(f"Portable source digest mismatch: {name}")
        if record["excluded_runtime_files"] != {
            p: h for p, h in source["source_files"].items() if p not in files
        }:
            raise ValueError(f"Runtime exclusions differ: {name}")
        archive = bundle / safe_name(record["archive"])
        if digest(archive.read_bytes()) != record["archive_sha256"]:
            raise ValueError(f"Archive hash mismatch: {name}")
        contents = {}
        with tarfile.open(archive, "r:gz") as tar:
            for member in tar:
                safe_name(member.name)
                if (
                    not member.isfile()
                    or member.name in contents
                    or member.name not in files
                ):
                    raise ValueError(f"Unexpected archive member: {member.name}")
                stream = tar.extractfile(member)
                data = stream.read()
                if digest(data) != files[member.name]:
                    raise ValueError(
                        f"Bundled file hash mismatch: {name}/{member.name}"
                    )
                contents[member.name] = data
        if set(contents) != set(files) or len(contents) != record["file_count"]:
            raise ValueError(f"Bundle file set mismatch: {name}")
        root = destination / name
        root.mkdir(parents=True, exist_ok=False)
        for relative, data in contents.items():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    return portable_metadata(sources)


def copy_verified(project, destination, roots):
    """Explicit local checkout alternative, with the same exact file contract."""
    sources = json.loads((Path(project) / "environment/sources.json").read_text())[
        "sources"
    ]
    for name, source in sources.items():
        root = Path(destination) / name
        root.mkdir()
        for relative, expected in expected_files(source, name).items():
            data = (Path(roots[name]) / relative).read_bytes()
            if digest(data) != expected:
                raise ValueError(f"Source hash mismatch: {name}/{relative}")
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    return portable_metadata(sources)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--route-inspector", type=Path)
    parser.add_argument("--synplanner", type=Path)
    args = parser.parse_args()
    roots = {}
    if args.route_inspector:
        roots["route-inspector"] = args.route_inspector
    if args.synplanner:
        roots["SynPlanner"] = args.synplanner
    print(json.dumps(pack(args.project, roots), indent=2))


if __name__ == "__main__":
    main()
