# Moving Retrocomposite between machines

| Location | Purpose |
| --- | --- |
| [GitHub: Protolaw/retrocomposite](https://github.com/Protolaw/retrocomposite) | Public source, configuration, documentation, tests, and environment records. |
| [HF: Protolaw/retrocomposite-data](https://huggingface.co/datasets/Protolaw/retrocomposite-data) | Prepared rules and corresponding training products, eligible composite cohorts, stock/targets, splits, and audits. |
| [HF: Protolaw/retrocomposite-models](https://huggingface.co/Protolaw/retrocomposite-models) | Complete trained model runs, checkpoints, logs, and metrics. |

Production data use the existing standalone n1/n5 files selected on 2026-10-25.
See [dataset readiness](DATASET_READINESS.md) for release contents and revisions.
Model releases await training. All three repositories
are public. Credentials stay in the local Hugging Face/GitHub authentication
stores, outside the project.

## On another machine

```sh
git clone https://github.com/Protolaw/retrocomposite.git
cd retrocomposite
python3 -m venv ../retrocomposite-transfer-env
source ../retrocomposite-transfer-env/bin/activate
python -m pip install -e '.[hub]'
```

This small transfer environment only needs Hugging Face Hub; it can upload or
download artifacts without installing the chemistry/ML stack. Public downloads
need no login. For uploads, authenticate locally with `hf auth login` using an
account/token with write access to the destination repository.

## Publish a prepared dataset release

After preparing and reviewing the files under `data/`:

```sh
python scripts/hub_artifacts.py upload --kind dataset \
  --source data --release n1-n5-v1
```

The helper collects manifest-listed artifacts from `single_step/`, `stock/`,
`cohorts/`, and each `splits/` subdirectory. This includes the native rule TSVs,
policy-data TSVs with corresponding molecule/rule pairs, provenance,
decompositions, and split snapshots. Raw unfiltered adapter exports and unrelated
files are outside this upload layout. Missing/mismatched hashes or incomplete
publications stop the upload.

Each release is stored under `releases/<name>/`, with `release.json` and a
`payload/` tree. Upload prints the immutable commit SHA: save that as the dataset
revision for training/model releases. A release name cannot be overwritten by
the helper. New versions use a new name. The helper snapshots files locally
before upload, so allow temporary disk space comparable to the release size.

## Download and train from an exact dataset revision

Replace `DATASET_COMMIT_SHA` with the revision printed by upload:

```sh
python scripts/hub_artifacts.py download --kind dataset \
  --release n1-n5-v1 --revision DATASET_COMMIT_SHA \
  --output data/releases/n1-n5-v1
```

The helper downloads only that release, verifies each SHA-256 hash, and publishes
it to a new destination. The restored layout includes `single_step/`, `stock/`,
`cohorts/`, and `splits/` as provided. `hub-release.json` records repository,
commit, and file hashes. Existing destinations are never overwritten. A branch
or tag is accepted and resolved once to a commit; pin the commit for experiments.

With the full environment installed, a restored split is directly usable:

```sh
retrocomposite train --split data/releases/n1-n5-v1/splits/primary \
  --config configs/mhn_querycgr_gps.yaml --seed 17 --accelerator cuda \
  --output outputs/training/primary/seed_17
```

## Publish and restore a trained model

Use a completed training run and the exact dataset commit containing its matching
ordered vocabulary and split. The supplied dataset commit is recorded alongside
the model; selecting the corresponding release remains the uploader's responsibility.

```sh
python scripts/hub_artifacts.py upload --kind model \
  --source outputs/training/primary/seed_17 \
  --release primary-seed17-v1 --dataset-revision DATASET_COMMIT_SHA

python scripts/hub_artifacts.py download --kind model \
  --release primary-seed17-v1 --revision MODEL_COMMIT_SHA \
  --output outputs/training/imported/primary-seed17-v1
```

Only `status: complete` runs are accepted. The run manifest defines the files to
upload, including best/final checkpoints, configuration, logs, metrics, and
environment records. SHA-256 verification preserves their association. Native
SynPlanner checkpoint loading still needs the matching ordered vocabulary; these
are not Transformers models. Restored provenance retains the original machine's
paths as historical information, while split snapshots use relative paths for
their actual training inputs.

## Recreate the full training environment

Clone this repository and use Python 3.12:

```sh
python3.12 scripts/setup_environment.py --verify-only
python3.12 scripts/setup_environment.py
source .venv/bin/activate
python -m pytest -q
```

Setup reads `environment/source_snapshots/` by default. Its two compressed
archives contain the 572 software/build files recorded in
`environment/sources.json`: SynPlanner's package and scripts, RouteInspector's
package, and their build metadata, README files, and MIT licenses. The recorded
RouteInspector GUI edit is included. Total compressed size is about 1.5 MB.
Two generated GUI TLS files (certificate and private key) captured by the old
recursive inventory are excluded. `manifest.json` records their names/hashes and
a separate bundled-content digest; every software file retains its original
hash. No upstream clone or Git executable is needed for installation.

Before building, setup verifies both archive hashes, the complete file sets, and
every recorded file hash. Extraction rejects unexpected paths, links, duplicate
members, and modified files. The baseline `sources.json` and dependency lock
remain unchanged. Dependencies still require package-index access; the source
archives are not an offline wheelhouse.

The default environment is `.venv`; use `--environment /path/to/new/venv` to
choose another new location. Existing environments are never overwritten.
Each successful installation saves `retrocomposite-environment.json` and
`requirements.resolved.txt` inside that environment, including its platform,
source digests, dependency mode, and actual installed versions. Training copies
these alongside its baseline environment records.

The baseline was recreated on macOS arm64 with all 172 installed package versions
matching and package/import/configuration checks passing. Linux/CUDA portability
still requires installation and hardware checks on that platform. Package pins
constrain applicable dependencies; they do not make different accelerators
numerically identical. If a different platform needs a deliberate dependency
refresh, use `--refresh-lock` with a new environment. This preserves the exact
source bundles, resolves dependencies without baseline constraints, and records
the resulting versions only in the new environment. Review and test that new
baseline before training.

For maintainers, `scripts/source_snapshots.py` packages files from the recorded
source locations and refuses modified files or an existing bundle destination.
`--route-inspector` and `--synplanner` can explicitly select matching local
sources for setup; both must be supplied, and the same file hashes are enforced.
A future hybrid SynPlanner branch requires a deliberate new source receipt and
bundle release, rather than `--refresh-lock` silently accepting code changes.

The helper uses Hugging Face's official [upload API](https://huggingface.co/docs/huggingface_hub/en/guides/upload)
and [revision-aware downloads](https://huggingface.co/docs/huggingface_hub/en/guides/download).
