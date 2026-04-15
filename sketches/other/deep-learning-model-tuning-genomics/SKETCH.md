---
name: deep-learning-model-tuning-genomics
description: Use when you need to systematically benchmark, tune, and stress-test
  a user-supplied PyTorch deep learning model on tabular biological data (DNA sequences,
  RNA-seq labels, or similar) by combining data preprocessing, hyperparameter search
  with Ray Tune, and shuffle-based sanity checks. Suited for model developers who
  want reproducible training-set augmentation and hyperparameter sweeps rather than
  standard variant/assembly analyses.
domain: other
organism_class:
- eukaryote
- other
input_data:
- tabular-csv
- pytorch-model-py
- yaml-config
source:
  ecosystem: nf-core
  workflow: nf-core/deepmodeloptim
  url: https://github.com/nf-core/deepmodeloptim
  version: dev
  license: MIT
  slug: deepmodeloptim
tools:
- name: stimulus
- name: pytorch
- name: ray-tune
- name: nextflow
tags:
- deep-learning
- hyperparameter-tuning
- pytorch
- genomics-ml
- model-benchmarking
- stimulus
- ray-tune
test_data: []
expected_output: []
---

# Deep learning model tuning for genomics (STIMULUS)

## When to use this sketch
- The user has a PyTorch model (`.py` with a single `Model*` class and a `batch()` method) and wants to tune or benchmark it on tabular biological data.
- Inputs are provided as a CSV with typed columns (`name:type:class`, where `type` is `input`/`meta`/`label`) rather than raw FASTQ/BAM.
- Goal is hyperparameter search (Ray Tune), data-transformation experiments, or shuffle/noise sanity checks to assess whether the model is learning signal vs. memorizing.
- Use cases include regressing RNA-seq values from DNA k-mers, predicting binding from sequence, or any small-to-medium tabular ML task where training-set design matters more than the architecture.

## Do not use when
- You need a standard bioinformatics analysis (variant calling, assembly, RNA-seq quantification, single-cell clustering) — pick a domain-specific sketch instead.
- You only want to run inference with a pre-trained model and no tuning/evaluation loop.
- Your inputs are raw sequencing reads without a labeled tabular representation; preprocess first with the appropriate nf-core pipeline.
- You need distributed multi-node training of very large models — this pipeline targets single-host tuning with up to a handful of GPUs.

## Analysis outline
1. Validate inputs: parse the typed CSV header and the data/model YAML configs, confirm required columns exist.
2. Optional preprocessing: apply encoders for each declared data class (e.g. DNA one-hot), optionally extracting BED peaks of `bed_peak_size` (default 300 bp).
3. Model check: import the user `.py`, instantiate the single `Model*` class, and run one `batch()` forward pass (`check_model_num_samples` samples, default 3) to verify wiring.
4. Shuffle sanity check: retrain on label-shuffled data as a negative control (`shuffle` on by default) to confirm the model isn't learning from artifacts.
5. Hyperparameter tuning: launch Ray Tune with the search space from `model_config`, over `tune_trials_range` trials and `tune_replicates` repeats, optionally warm-started from `initial_weights`.
6. Evaluation / prediction: if `prediction_data` is supplied, run the tuned model on held-out CSV rows and emit predictions.
7. Reporting: collect per-trial metrics, best hyperparameters, and (if `save_data` is set) the transformed CSVs to `outdir`.

## Key parameters
- `--data` — typed input CSV with `name:type:class` headers (required).
- `--data_config` — YAML describing data transforms/encoders (required).
- `--model` — PyTorch `.py` file, exactly one `Model*` class, `forward()` arg names matching CSV input columns, and a `batch(x, y, loss_fn, optimizer=None)` method (required).
- `--model_config` — YAML with hyperparameter search space and Ray Tune directives (required).
- `--outdir` — results directory (required; use absolute paths on cloud).
- `--tune_trials_range` — `min,max,step` for Ray Tune trials (e.g. `5,10,5`); falls back to the value in `model_config`.
- `--tune_replicates` — number of independent tuning repeats (default `1`).
- `--shuffle` — run the label-shuffle negative control (default `true`).
- `--check_model` / `--check_model_num_samples` — pre-flight forward-pass check (default on, 3 samples).
- `--max_gpus` — GPU cap for Ray Tune workers (default `1`).
- `--preprocessing_config`, `--bed_peak_size` (default `300`) — optional preprocessing knobs when starting from BED regions.
- `--initial_weights` — optional warm-start checkpoint(s); one tuning run per file.
- `--save_data` — persist transformed CSVs alongside tuning results.

## Test data
The `test` profile pulls a toy Titanic dataset from `nf-core/test-datasets` (`deepmodeloptim/testdata/titanic/`): `titanic_stimulus.csv` as the typed input table, `titanic.yaml` as the data config, `titanic_model.py` as a minimal PyTorch classifier, and `titanic_model.yaml` as the Ray Tune search-space config. Running with `-profile test` should complete the model check, a shuffle sanity run, and a small Ray Tune sweep, writing transformed data (because `save_data = true`), per-trial metrics, and the best hyperparameter set to `--outdir`. It is a functional smoke test, not a biological benchmark.

## Reference workflow
nf-core/deepmodeloptim (dev, pre-1.0), https://github.com/nf-core/deepmodeloptim — wraps the STIMULUS framework with Ray Tune and PyTorch. License: MIT.
