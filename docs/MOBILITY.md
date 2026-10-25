# Moving Retrocomposite between machines

| Location | Purpose |
| --- | --- |
| [GitHub: Protolaw/retrocomposite](https://github.com/Protolaw/retrocomposite) | Public source, configuration, documentation, tests, and environment records. |
| [HF: Protolaw/retrocomposite-data](https://huggingface.co/datasets/Protolaw/retrocomposite-data) | Prepared rules and corresponding training products, eligible composite cohorts, stock/targets, splits, and audits. |
| [HF: Protolaw/retrocomposite-models](https://huggingface.co/Protolaw/retrocomposite-models) | Complete trained model runs, checkpoints, logs, and metrics. |

The Hugging Face repositories start with introductory cards. Data releases await
refreshed publications; model releases await training. All three repositories
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

Artifact transfer and environment reconstruction are separate. The full stack
still uses the recorded local-source versions of RouteInspector and SynPlanner:

```sh
git clone https://github.com/Laboratoire-de-Chemoinformatique/route-inspector.git ../route-inspector
git -C ../route-inspector checkout f38f668a185801c37780f94db78fd76af1d4a122
git clone https://github.com/Laboratoire-de-Chemoinformatique/SynPlanner.git ../SynPlanner
git -C ../SynPlanner checkout 53ffed21794e829cd660b63effaaf4351e10cf95
python3.12 scripts/setup_environment.py \
  --route-inspector ../route-inspector --synplanner ../SynPlanner
source .venv/bin/activate
python -m pytest -q
```

`environment/sources.json` contains exact source-file hashes. The recorded
RouteInspector snapshot includes a local change to `route_inspector/gui/screens.py`,
so a clean checkout alone will not reproduce its complete source digest. For
exact reconstruction, transfer the matching upstream source snapshot separately.
Those upstream working-tree changes are not published in this repository.

If intentionally using the clean upstream checkouts or adapting to another
platform, run setup with `--refresh-lock` to accept and record the new environment,
then rerun the tests before production work. Keep the resulting environment
records with model runs. This creates a new reproducibility baseline rather than
claiming byte-identical reconstruction. Dependency pins were verified on the
original machine; accelerator/platform reproducibility needs its own check.

The helper uses Hugging Face's official [upload API](https://huggingface.co/docs/huggingface_hub/en/guides/upload)
and [revision-aware downloads](https://huggingface.co/docs/huggingface_hub/en/guides/download).
