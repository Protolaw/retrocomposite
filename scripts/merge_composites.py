"""Merge mapping-equivalent composite labels, rebuild splits, and audit all pairs."""

import argparse
import json
import sys
from pathlib import Path
from retrocomposite.composite_merging import merge_cohorts

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("cohorts", "splits", "output"):
        parser.add_argument("--" + flag, type=Path, required=True)
    args = parser.parse_args()
    report = merge_cohorts(args.cohorts, args.splits, args.output,
                          progress=lambda message: print(message, file=sys.stderr, flush=True))
    compact = {**report, "cohorts": {
        name: {k: v for k, v in values.items() if not k.startswith("old_to_new")}
        for name, values in report["cohorts"].items()}}
    print(json.dumps(compact, indent=2))
    if report["status"] != "passed":
        raise SystemExit(2)
