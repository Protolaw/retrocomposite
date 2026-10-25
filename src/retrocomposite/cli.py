"""Command-line entry points; full experiments are deliberately separate."""

import argparse
import json
import sys
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
    command = subs.add_parser(
        "select-cohorts",
        help="Select shared tactics and publish primary/patent-disjoint cohorts",
    )
    for flag in ("n1", "n5", "n1-reference", "n5-reference", "n1-composites", "output"):
        command.add_argument("--" + flag, type=Path, required=True)
    command.add_argument(
        "--max-alignments",
        type=int,
        default=256,
        help="Intermediate alignment limit for exact graph auditing only; never changes E3 exclusion",
    )
    command = subs.add_parser(
        "split",
        help="Freeze molecule/route grouped training and validation assignments",
    )
    command.add_argument("--assets", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    command.add_argument("--seed", type=int, default=42)
    command.add_argument("--validation-fraction", type=float, default=0.1)
    command.add_argument("--grouping", choices=("route", "patent"), default="route")
    command.add_argument(
        "--n1", type=Path, help="Cleaned n1 routes for single-step patent grouping"
    )
    command.add_argument(
        "--n5", type=Path, help="Cleaned n5 routes for single-step patent grouping"
    )
    command = subs.add_parser(
        "train", help="Train a fresh MHN with a frozen split and explicit model seed"
    )
    command.add_argument("--split", type=Path, required=True)
    command.add_argument("--config", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    command.add_argument("--seed", type=int, required=True)
    command.add_argument("--accelerator", choices=("cpu", "cuda", "mps"), default="cpu")
    command.add_argument(
        "--device", type=int, default=0, help="CUDA device index; one device per run"
    )
    command.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Seeded data-loader workers; preprocessing is serial",
    )
    command.add_argument("--threads", type=int, default=1)
    command.add_argument("--determinism", choices=("strict", "warn"), default="strict")
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
    elif args.command == "select-cohorts":
        from retrocomposite.selection import select_from_libraries

        report = select_from_libraries(
            args.n1,
            args.n5,
            args.n1_reference,
            args.n5_reference,
            args.n1_composites,
            args.output,
            args.max_alignments,
            progress=lambda message: print(message, file=sys.stderr, flush=True),
        )
        print(
            json.dumps(
                {
                    "output": str(args.output),
                    "cohorts": {
                        name: {
                            key: value[key]
                            for key in ("status", "occurrences", "rules")
                        }
                        for name, value in report["cohorts"].items()
                    },
                },
                indent=2,
            )
        )
        if any(c["status"] == "blocked" for c in report["cohorts"].values()):
            raise SystemExit(2)
    elif args.command == "split":
        from retrocomposite.splitting import create_split

        result = create_split(
            args.assets,
            args.output,
            args.seed,
            args.validation_fraction,
            args.grouping,
            {k: v for k, v in (("n1", args.n1), ("n5", args.n5)) if v},
        )
        print(json.dumps(result, indent=2))
        if result["status"] != "ready":
            raise SystemExit(2)
    elif args.command == "train":
        from retrocomposite.training import train

        result = train(
            args.split,
            args.config,
            args.output,
            args.seed,
            args.accelerator,
            args.device,
            args.workers,
            args.threads,
            args.determinism,
        )
        print(
            json.dumps(
                {"status": result["status"], "output": str(args.output)}, indent=2
            )
        )
    else:
        print(json.dumps(prep.validate_training_assets(args.rules), indent=2))
