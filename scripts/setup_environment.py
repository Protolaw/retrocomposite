"""Recreate the full environment using bundled, hash-verified source snapshots.

Requires Python 3.12 and package-index access; no upstream checkout is needed.
The baseline source receipt and dependency pins are never overwritten by setup.
"""

import argparse
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import venv

from source_snapshots import copy_verified, digest, unpack


def run(*args, **kwargs):
    subprocess.run([str(a) for a in args], check=True, **kwargs)


def main():
    project = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", type=Path, default=project / ".venv")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify bundled source files without installing anything",
    )
    parser.add_argument(
        "--route-inspector",
        type=Path,
        help="Optional exact local source; requires --synplanner",
    )
    parser.add_argument(
        "--synplanner",
        type=Path,
        help="Optional exact local source; requires --route-inspector",
    )
    parser.add_argument(
        "--refresh-lock",
        action="store_true",
        help="Resolve dependencies without baseline constraints; record a new baseline inside the new environment",
    )
    args = parser.parse_args()
    if bool(args.route_inspector) != bool(args.synplanner):
        parser.error("Supply both local source paths, or neither to use the bundles")
    environment = args.environment.resolve()
    if not args.verify_only and sys.version_info[:2] != (3, 12):
        parser.error("Use Python 3.12 to recreate this recorded environment")
    if not args.verify_only and environment.exists():
        raise FileExistsError(
            f"Existing environment will not be overwritten: {environment}"
        )
    lock = project / "environment/requirements.lock.txt"
    with tempfile.TemporaryDirectory(prefix="retrocomposite-sources-") as temporary:
        root = Path(temporary)
        sources = (
            copy_verified(
                project,
                root,
                {
                    "route-inspector": args.route_inspector,
                    "SynPlanner": args.synplanner,
                },
            )
            if args.route_inspector
            else unpack(project, root)
        )
        print("Verified exact source snapshots: " + ", ".join(sources), flush=True)
        if args.verify_only:
            return
        dependencies = tomllib.loads(
            (root / "route-inspector/pyproject.toml").read_text()
        )["project"]["dependencies"]
        override = [d for d in dependencies if re.match(r"(?i)^synplanner(?:\W|$)", d)]
        other_dependencies = [d for d in dependencies if d not in override]
        python = environment / (
            "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
        )
        uv = shutil.which("uv")
        installer = (
            [uv, "pip", "install", "--python", python]
            if uv
            else [python, "-m", "pip", "install"]
        )
        constraints = [] if args.refresh_lock else ["--constraint", lock]
        venv.EnvBuilder(with_pip=True).create(environment)
        receipt_path = environment / "retrocomposite-environment.json"
        receipt = {
            "schema": "retrocomposite-environment/1",
            "status": "installing",
            "sources": {
                name: {
                    key: value[key]
                    for key in ("git_commit", "source_digest", "bundled_source_digest")
                }
                for name, value in sources.items()
            },
            "source_mode": "local-verified" if args.route_inspector else "bundled",
            "dependency_mode": "refreshed" if args.refresh_lock else "constrained",
            "baseline_lock_sha256": digest(lock.read_bytes()),
            "python": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "overridden_route_inspector_requirements": override,
        }

        def save():
            receipt_path.write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n"
            )

        save()
        try:
            run(
                *installer,
                *constraints,
                str(root / "SynPlanner") + "[all]",
                *other_dependencies,
                "pytest>=8,<10",
                "huggingface_hub>=1.0,<3",
            )
            # Replace only RouteInspector's SynPlanner Git pin with our verified source.
            run(*installer, "--no-deps", root / "route-inspector")
            run(*installer, "--no-deps", "-e", project)
            run(python, "-m", "pip", "check")
            check = "from synplan.ml.config import PolicyNetworkConfig; c=PolicyNetworkConfig.from_yaml('configs/mhn_querycgr_gps.yaml'); assert c.embedder_type=='gps' and c.rule_embedding_type=='query_cgr_graph'; import route_inspector; import retrocomposite; import huggingface_hub; print('Imports and MHN configuration verified')"
            run(python, "-c", check, cwd=project)
            receipt["installed"] = json.loads(
                subprocess.check_output(
                    [str(python), "-m", "pip", "list", "--format=json"], text=True
                )
            )
            excluded = {"synplanner", "route-inspector", "retrocomposite"}
            (environment / "requirements.resolved.txt").write_text(
                "".join(
                    f"{p['name']}=={p['version']}\n"
                    for p in sorted(
                        receipt["installed"], key=lambda p: p["name"].lower()
                    )
                    if p["name"].lower().replace("_", "-") not in excluded
                )
            )
            receipt["status"] = "complete"
        except BaseException as error:
            receipt.update(status="failed", error=f"{type(error).__name__}: {error}")
            raise
        finally:
            save()
    print(f"Environment ready: {environment}")
    print(f"Installation receipt: {receipt_path}")


if __name__ == "__main__":
    main()
