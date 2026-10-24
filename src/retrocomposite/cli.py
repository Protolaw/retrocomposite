"""Command-line entry points; full experiments are deliberately separate."""

import argparse
import json
from pathlib import Path

from retrocomposite import preparation as prep


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    subs = root.add_subparsers(dest="command", required=True)
    for name in ("single-step", "stock"):
        command = subs.add_parser(name)
        command.add_argument("--n1", type=Path, required=True)
        command.add_argument("--n5", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        if name == "single-step":
            command.add_argument("--config", type=Path, required=True)
            command.add_argument("--workers", type=int, default=1)
    command = subs.add_parser("composite-library")
    command.add_argument("--reference-library", type=Path, required=True)
    command.add_argument("--composite-library", type=Path, required=True)
    command.add_argument("--routes-json", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    command = subs.add_parser("composite-json")
    command.add_argument("--records", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    command = subs.add_parser("validate")
    command.add_argument("--rules", type=Path, required=True)
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    if args.command == "single-step":
        prep.prepare_single_step(
            {"n1": args.n1, "n5": args.n5}, args.output, args.config, args.workers
        )
    elif args.command == "stock":
        prep.prepare_stock({"n1": args.n1, "n5": args.n5}, args.output)
    elif args.command == "composite-library":
        files = prep.inputs(
            [
                args.routes_json,
                args.reference_library / "manifest.json",
                args.composite_library / "manifest.json",
            ]
        )
        prep.export_composites(
            prep.library_records(
                args.reference_library, args.composite_library, args.routes_json
            ),
            args.output,
            files,
        )
    elif args.command == "composite-json":
        prep.export_composites(
            prep.read_records(args.records), args.output, prep.inputs([args.records])
        )
    else:
        print(json.dumps(prep.validate_training_assets(args.rules), indent=2))
