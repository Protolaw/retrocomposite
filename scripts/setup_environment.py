"""Install isolated local-source snapshots and all SynPlanner extras.

Only the new project's environment and metadata are written. Builds run from
temporary source copies, so setuptools cannot alter either upstream checkout.
"""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tomllib
import venv


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def copy_source(repo, target, packages):
    target.mkdir()
    for name in ("pyproject.toml", "README.md", "LICENSE", *packages):
        source = repo / name
        if source.is_dir():
            shutil.copytree(
                source,
                target / name,
                ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", "*.egg-info", ".DS_Store"
                ),
            )
        elif source.exists():
            shutil.copy2(source, target / name)
    files = {
        str(p.relative_to(target)): sha256(p.read_bytes()).hexdigest()
        for p in sorted(target.rglob("*"))
        if p.is_file()
    }
    return {
        "path": str(repo),
        "git_commit": git(repo, "rev-parse", "HEAD"),
        "git_status": git(repo, "status", "--short"),
        "source_files": files,
        "source_digest": sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
    }


def main():
    project = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--route-inspector", type=Path, default=project.parent / "route-inspector"
    )
    parser.add_argument(
        "--synplanner", type=Path, default=project.parent / "SynPlanner"
    )
    parser.add_argument(
        "--refresh-lock",
        action="store_true",
        help="Intentionally accept changed upstream sources and resolve dependency versions again",
    )
    args = parser.parse_args()
    ri = args.route_inspector.resolve()
    syn = args.synplanner.resolve()
    environment = project / ".venv"
    if environment.exists():
        raise FileExistsError(
            "The project .venv already exists; it will not be overwritten"
        )
    ri_metadata = tomllib.loads((ri / "pyproject.toml").read_text())
    dependencies = ri_metadata["project"]["dependencies"]
    override = [d for d in dependencies if re.match(r"(?i)^synplanner(?:\W|$)", d)]
    other_dependencies = [d for d in dependencies if d not in override]
    python = environment / "bin/python"
    uv = shutil.which("uv")
    installer = (
        [uv, "pip", "install", "--python", python]
        if uv
        else [python, "-m", "pip", "install"]
    )
    print(
        "Installing complete SynPlanner extras from a recorded local source snapshot.",
        flush=True,
    )
    with tempfile.TemporaryDirectory(prefix="retrocomposite-sources-") as temporary:
        root = Path(temporary)
        sources = {
            "SynPlanner": copy_source(syn, root / "SynPlanner", ("synplan", "scripts")),
            "route-inspector": copy_source(
                ri, root / "route-inspector", ("route_inspector",)
            ),
        }
        metadata = project / "environment"
        receipt = metadata / "sources.json"
        lock = metadata / "requirements.lock.txt"
        if receipt.exists() and not args.refresh_lock:
            previous = json.loads(receipt.read_text())["sources"]
            for name, item in sources.items():
                if previous[name]["source_digest"] != item["source_digest"]:
                    raise ValueError(
                        f"{name} source differs from the saved snapshot; review then use --refresh-lock"
                    )
        constraints = (
            ["--constraint", lock] if lock.exists() and not args.refresh_lock else []
        )
        venv.EnvBuilder(with_pip=True).create(environment)
        run(
            *installer,
            *constraints,
            str(root / "SynPlanner") + "[all]",
            *other_dependencies,
            "pytest>=8,<10",
        )
        # Intentional override: using the inspected local SynPlanner snapshot
        # instead of RouteInspector's direct Git requirement, with all other
        # RouteInspector dependencies installed above.
        run(*installer, "--no-deps", root / "route-inspector")
        run(*installer, "--no-deps", "-e", project)
    run(python, "-m", "pip", "check")
    check = "from synplan.ml.config import PolicyNetworkConfig; c=PolicyNetworkConfig.from_yaml('configs/mhn_querycgr_gps.yaml'); assert c.embedder_type=='gps' and c.rule_embedding_type=='query_cgr_graph'; import route_inspector; import retrocomposite; print('Imports and MHN configuration verified')"
    subprocess.run([str(python), "-c", check], cwd=project, check=True)
    installed = json.loads(
        subprocess.check_output(
            [str(python), "-m", "pip", "list", "--format=json"], text=True
        )
    )
    metadata = project / "environment"
    metadata.mkdir(exist_ok=True)
    excluded = {"synplanner", "route-inspector", "retrocomposite"}
    (metadata / "requirements.lock.txt").write_text(
        "# Installed dependency pins; install local source snapshots separately.\n"
        + "".join(
            f"{p['name']}=={p['version']}\n"
            for p in sorted(installed, key=lambda p: p["name"].lower())
            if p["name"].lower().replace("_", "-") not in excluded
        )
    )
    (metadata / "sources.json").write_text(
        json.dumps(
            {
                "sources": sources,
                "overridden_route_inspector_requirements": override,
                "override_reason": "Use inspected local SynPlanner with all extras and current MHN interfaces",
                "python": subprocess.check_output(
                    [str(python), "--version"], text=True
                ).strip(),
                "installed": installed,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(f"Environment ready: {environment}")


if __name__ == "__main__":
    main()
