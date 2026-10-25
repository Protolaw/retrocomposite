---
tags:
  - chemistry
  - retrosynthesis
  - synplanner
  - modern-hopfield-network
datasets:
  - Protolaw/retrocomposite-data
---

# Retrocomposite models

Model-run storage for [Protolaw/retrocomposite](https://github.com/Protolaw/retrocomposite).
This repository is initialized for future trained checkpoints. Available releases
will appear under `releases/`; initialization does not imply any trained model or
performance result.

Each release contains one complete training run: native SynPlanner best/final
checkpoints, configuration, seed/split information, logs, validation metrics,
provenance, and hashes. Release names distinguish the single-step, primary
composite, and patent-disjoint composite models and their seeds.

The intended architecture is MHN ranking with QueryCGR rule graphs and GPS
encoders. These are native SynPlanner checkpoints, not Transformers models.
Download the associated exact ordered rule vocabulary and data split from the
dataset commit recorded in the release manifest.

See the [mobility guide](https://github.com/Protolaw/retrocomposite/blob/main/docs/MOBILITY.md)
for upload/download commands and source/environment requirements. The associated
data repository is [Protolaw/retrocomposite-data](https://huggingface.co/datasets/Protolaw/retrocomposite-data).
