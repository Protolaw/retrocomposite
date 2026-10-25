"""Seeded, single-device MHN training on frozen grouped assignments."""

import argparse
from collections import Counter
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import traceback

from retrocomposite import preparation as prep
from retrocomposite.splitting import load_split, read_tsv


def seed_worker(_worker_id):
    import random
    import numpy as np
    import torch

    seed = torch.initial_seed() % 2**32
    random.seed(seed)
    np.random.seed(seed)


def train(
    split,
    config,
    output,
    seed,
    accelerator="cpu",
    device=0,
    workers=0,
    threads=1,
    determinism="strict",
):
    """Start a fresh interpreter so hash and accelerator seeds precede imports."""
    split, config, output = (Path(p).resolve() for p in (split, config, output))
    if not 0 <= seed < 2**32 or workers < 0 or threads < 1 or device < 0:
        raise ValueError("Invalid seed, worker count, thread count, or device")
    if accelerator not in {"cpu", "cuda", "mps"} or determinism not in {
        "strict",
        "warn",
    }:
        raise ValueError("Unsupported accelerator or determinism mode")
    metadata, _ = load_split(split)
    source_files = prep.inputs([split / "preparation.json", config])
    environment = Path(__file__).resolve().parents[2] / "environment"
    environment_files = [
        environment / name
        for name in ("sources.json", "requirements.lock.txt")
        if (environment / name).is_file()
    ]
    source_files += prep.inputs(environment_files)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    output.mkdir(parents=True)
    shutil.copy2(config, output / "config.yaml")
    shutil.copy2(split / "split.json", output / "split.json")
    if environment_files:
        (output / "environment").mkdir()
        for path in environment_files:
            shutil.copy2(path, output / "environment" / path.name)
    record = {
        "schema": "retrocomposite-training/1",
        "status": "running",
        "split": str(split),
        "split_seed": metadata["seed"],
        "cohort": metadata["cohort"],
        "seed": seed,
        "accelerator": accelerator,
        "device": device,
        "workers": workers,
        "threads": threads,
        "determinism": determinism,
        "inputs": source_files,
        "rule_vocabulary_sha256": prep.digest(split / metadata["rules"]),
        "software": {
            **prep.software(),
            **{
                name: version(name)
                for name in ("torch", "torch-geometric", "pytorch-lightning", "numpy")
            },
        },
        "python": sys.version,
        "platform": platform.platform(),
        "implementation": {
            p.name: prep.digest(p)
            for p in (
                Path(__file__),
                Path(__file__).with_name("splitting.py"),
                Path(prep.__file__),
            )
        },
    }
    prep.write_json(output / "run.json", record)
    env = {
        **os.environ,
        "PYTHONHASHSEED": str(seed),
        "PYTHONUNBUFFERED": "1",
        "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
        "OMP_NUM_THREADS": str(threads),
        "MKL_NUM_THREADS": str(threads),
        "MPLCONFIGDIR": str(output / "runtime_cache" / "matplotlib"),
    }
    started = time.monotonic()
    try:
        print(
            f"Training {metadata['cohort']} with seed {seed}; log: {output / 'console.log'}",
            flush=True,
        )
        with (output / "console.log").open("w") as log:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "retrocomposite.training",
                    "--worker",
                    str(output),
                ],
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
        if completed.returncode:
            raise RuntimeError(
                f"Training worker exited {completed.returncode}; see {output / 'console.log'}"
            )
        for source in source_files:
            if prep.digest(source["path"]) != source["sha256"]:
                raise ValueError("Training inputs changed during the run")
        load_split(split)
        if not (output / "metrics.json").is_file():
            raise RuntimeError("Training worker did not publish metrics")
        record["status"] = "complete"
    except BaseException as exc:
        record["status"] = "failed"
        record["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        record["elapsed_seconds"] = time.monotonic() - started
        record["outputs"] = {
            str(p.relative_to(output)): prep.digest(p)
            for p in sorted(output.rglob("*"))
            if p.is_file() and p.name != "run.json"
        }
        prep.write_json(output / "run.json", record)
    return record


def worker(output):
    # This process inherits PYTHONHASHSEED and CUBLAS settings before torch import.
    import torch
    from torch.nn.functional import cross_entropy
    from torch.utils.data import Subset
    from torch_geometric.loader import DataLoader
    from pytorch_lightning import Trainer, seed_everything
    from pytorch_lightning.callbacks import ModelCheckpoint
    from pytorch_lightning.loggers import CSVLogger
    from synplan.ml.config import PolicyNetworkConfig
    from synplan.ml.training.preprocessing import RankingPolicyDataset
    from synplan.ml.training.trainers import (
        LitMHNRanking,
        build_mhn_ranking_network,
        rebind_training_rules,
    )
    from synplan.ml.training.lightning import GradNormLogger
    from synplan.ml.networks.checkpoint import load_policy_network_from_checkpoint
    from synplan.chem.reaction.rules.vocabulary import bind_training_vocabulary

    output = Path(output).resolve()
    run = json.loads((output / "run.json").read_text())
    if os.environ.get("PYTHONHASHSEED") != str(run["seed"]):
        raise ValueError("Training must run in the seed-controlled subprocess")
    torch.set_num_threads(run["threads"])
    torch.set_num_interop_threads(run["threads"])
    seed_everything(run["seed"], workers=True)
    strict = run["determinism"] == "strict"
    torch.use_deterministic_algorithms(True, warn_only=not strict)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    split = Path(run["split"])
    metadata, assignments = load_split(split)
    if prep.digest(split / "preparation.json") != run["inputs"][0]["sha256"]:
        raise ValueError("Split changed before training")
    if prep.digest(output / "config.yaml") != run["inputs"][1]["sha256"]:
        raise ValueError("Config changed before training")
    config = PolicyNetworkConfig.from_yaml(output / "config.yaml")
    if (
        config.architecture != "mhn_ranking"
        or config.policy_type != "ranking"
        or config.embedder_type != "gps"
        or config.rule_embedding_type != "query_cgr_graph"
        or config.rule_embedder.embedder_type != "gps"
        or config.weights_path is not None
    ):
        raise ValueError(
            "Use a fresh MHN ranking model with GPS molecules and QueryCGR/GPS rules"
        )
    extra = config.trainer or {}
    allowed = {
        "precision",
        "accumulate_grad_batches",
        "gradient_clip_val",
        "gradient_clip_algorithm",
    }
    if set(extra) - allowed:
        raise ValueError(
            f"Unsupported trainer overrides: {sorted(set(extra) - allowed)}"
        )
    # The wrapper always owns logging, checkpoints, determinism, and full validation.
    config.logger = {"type": "csv"}
    prep.write_json(output / "effective_config.json", config.model_dump(mode="json"))
    policy_path = split / metadata["policy_data"]
    rows = read_tsv(policy_path)
    dataset = RankingPolicyDataset(str(policy_path), "", num_workers=1)
    expected = [(r["product_smiles"], int(r["rule_id"])) for r in rows]
    observed = list(
        zip(dataset._product_keys, dataset._data.y_rules.view(-1).tolist(), strict=True)
    )
    counts = Counter(observed)
    missing = []
    for index, pair in enumerate(expected):
        if counts[pair]:
            counts[pair] -= 1
        else:
            missing.append(index)
    prep.write_json(
        output / "graph_alignment.json",
        {
            "status": "verified" if expected == observed else "failed",
            "expected_rows": len(expected),
            "graph_rows": len(observed),
            "missing_row_indices": missing,
            "first_order_mismatch": next(
                (i for i, (a, b) in enumerate(zip(expected, observed)) if a != b), None
            ),
        },
    )
    if expected != observed:
        raise ValueError("Graph preprocessing dropped or reordered frozen policy rows")
    loaders = {}
    for offset, partition in enumerate(("train", "validation")):
        indices = [a["row_index"] for a in assignments if a["partition"] == partition]
        loaders[partition] = DataLoader(
            Subset(dataset, indices),
            batch_size=config.batch_size,
            shuffle=partition == "train",
            drop_last=False,
            num_workers=run["workers"],
            worker_init_fn=seed_worker,
            generator=torch.Generator().manual_seed((run["seed"] + offset) % 2**32),
            persistent_workers=False,
        )

    class GroupedMHNTrainer(LitMHNRanking):
        """Weight loss/accuracy by actual rows, including the last partial batch."""

        def step(self, batch, stage):
            labels = batch.y_rules.long().view(-1)
            logits = self.network.get_logits(batch)
            loss = cross_entropy(logits, labels)
            self.log(
                f"{stage}_loss",
                loss,
                on_step=stage == "train",
                on_epoch=True,
                batch_size=len(labels),
            )
            accuracy = (logits.argmax(-1) == labels).float().mean()
            self.log(
                f"{stage}_top1_accuracy",
                accuracy,
                on_step=False,
                on_epoch=True,
                batch_size=len(labels),
            )
            return loss

        def training_step(self, batch, batch_idx):
            return self.step(batch, "train")

        def validation_step(self, batch, batch_idx):
            self.step(batch, "val")

    network = bind_training_vocabulary(
        build_mhn_ranking_network(config, dataset), dataset
    )
    network.hparams["retrocomposite"] = {
        "seed": run["seed"],
        "split_sha256": prep.digest(split / "preparation.json"),
        "cohort": metadata["cohort"],
    }
    module = GroupedMHNTrainer(network)
    checkpoint = ModelCheckpoint(
        dirpath=output / "checkpoints",
        filename="best",
        monitor="val_loss",
        mode="min",
        save_top_k=1,
        save_last=True,
        enable_version_counter=False,
    )
    callbacks = [checkpoint]
    if config.log_grad_norm:
        callbacks.append(GradNormLogger())
    logger = CSVLogger(str(output), name="logs", version="metrics")
    trainer = Trainer(
        accelerator=run["accelerator"],
        devices=[run["device"]] if run["accelerator"] == "cuda" else 1,
        max_epochs=config.num_epoch,
        callbacks=callbacks,
        logger=logger,
        default_root_dir=output,
        deterministic=True if strict else "warn",
        benchmark=False,
        enable_progress_bar=False,
        log_every_n_steps=1,
        num_sanity_val_steps=0,
        **{"gradient_clip_val": 1.0, **extra},
    )
    trainer.fit(
        module,
        train_dataloaders=loaders["train"],
        val_dataloaders=loaders["validation"],
    )
    if trainer.interrupted or not checkpoint.best_model_path:
        raise RuntimeError("Training interrupted or no validated checkpoint saved")
    # Native checkpoints intentionally contain bare-network weights. Reload using
    # SynPlanner's inference loader, not Lightning's trainer-resume interface.
    best = load_policy_network_from_checkpoint(checkpoint.best_model_path)
    rebind_training_rules(best, policy_path)
    device = module.device
    best = best.to(device).eval()
    support = torch.zeros(best.n_rules, dtype=torch.long)
    correct = torch.zeros_like(support)
    top = {k: 0 for k in (1, 5, 10, 50) if k <= best.n_rules}
    loss_sum, count = 0.0, 0
    with torch.inference_mode():
        for batch in loaders["validation"]:
            batch = batch.to(device)
            labels = batch.y_rules.long().view(-1)
            logits = best.get_logits(batch)
            if not torch.isfinite(logits).all():
                raise ValueError("Nonfinite validation logits")
            loss_sum += cross_entropy(logits, labels, reduction="sum").item()
            count += len(labels)
            support += torch.bincount(labels.cpu(), minlength=best.n_rules)
            matched = labels[logits.argmax(-1) == labels].cpu()
            correct += torch.bincount(matched, minlength=best.n_rules)
            for k in top:
                top[k] += (
                    (logits.topk(k, dim=-1).indices == labels[:, None])
                    .any(-1)
                    .sum()
                    .item()
                )
    observed = support > 0
    summary = {
        "checkpoint": str(Path(checkpoint.best_model_path).relative_to(output)),
        "checkpoint_sha256": prep.digest(checkpoint.best_model_path),
        "rule_vocabulary_sha256": run["rule_vocabulary_sha256"],
        "split_sha256": run["inputs"][0]["sha256"],
        "validation_rows": count,
        "validation_loss": loss_sum / count,
        "validation_topk_accuracy": {str(k): value / count for k, value in top.items()},
        "validation_macro_recall_observed_rules": (
            correct[observed].double() / support[observed]
        )
        .mean()
        .item(),
        "validation_observed_rules": int(observed.sum()),
        "best_monitored_validation_loss": float(checkpoint.best_model_score),
        "epochs_completed": trainer.current_epoch,
        "global_steps": trainer.global_step,
        "hardware": {
            "device": str(device),
            "cuda": torch.version.cuda,
            "cudnn": torch.backends.cudnn.version(),
            "name": torch.cuda.get_device_name(device)
            if device.type == "cuda"
            else platform.processor(),
        },
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        "determinism": run["determinism"],
    }
    prep.write_json(output / "metrics.json", summary)
    # Retain the exact training interface sources, not only package versions.
    import inspect
    from synplan.ml.training import trainers, lightning, preprocessing
    from synplan.ml.networks.policy import mhnreact

    prep.write_json(
        output / "runtime_sources.json",
        {
            m.__name__: {
                "path": inspect.getfile(m),
                "sha256": prep.digest(inspect.getfile(m)),
            }
            for m in (trainers, lightning, preprocessing, mhnreact)
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=Path, required=True)
    args = parser.parse_args()
    try:
        worker(args.worker)
    except BaseException:
        traceback.print_exc()
        raise SystemExit(1)
