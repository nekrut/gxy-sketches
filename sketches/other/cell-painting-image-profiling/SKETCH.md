---
name: cell-painting-image-profiling
description: "Use when you have high-content microscopy images from a Cell Painting\
  \ (or related multi-channel fluorescence) assay and need to run CellProfiler-based\
  \ image-based profiling \u2014 illumination correction, segmentation, and per-cell\
  \ morphological feature extraction across plates and wells."
domain: other
organism_class:
- eukaryote
- cell-culture
input_data:
- microscopy-images-tiff
- cellprofiler-load-data-csv
- cellprofiler-pipeline-cppipe
source:
  ecosystem: nf-core
  workflow: nf-core/cellpainting
  url: https://github.com/nf-core/cellpainting
  version: dev
  license: MIT
tools:
- cellprofiler
- multiqc
- nextflow
tags:
- cell-painting
- image-based-profiling
- high-content-screening
- microscopy
- cellprofiler
- morphological-profiling
- phenotypic-screening
test_data: []
expected_output: []
---

# Cell Painting image-based profiling

## When to use this sketch
- You have raw multi-channel fluorescence microscopy images (typically 5-channel Cell Painting: DNA, ER, RNA/nucleoli, AGP, mito) from a plate-based screen and need to extract per-cell morphological features.
- You want a reproducible CellProfiler orchestration that runs illumination correction, then an analysis (or assay-development) pipeline across many wells/sites/plates.
- Input is organised as a CellProfiler `load_data.csv` describing image file locations per well/site/channel, plus one or more `.cppipe` CellProfiler pipelines.
- You need MultiQC-style aggregated QC over the resulting image/feature outputs.
- Assay development: you are tuning a CellProfiler pipeline on a small pilot plate before scaling.

## Do not use when
- Your raw data is sequencing reads (FASTQ/BAM) — this is an imaging pipeline, not a genomics one. For RNA-seq-based perturbation profiling use an `rna-seq` sketch instead.
- You need single-cell RNA-seq / Perturb-seq analysis — use a `single-cell` sketch.
- You only need classical image segmentation without the Cell Painting five-channel morphological feature battery — a bespoke CellProfiler run outside nf-core may be simpler.
- You want deep-learning-based cell segmentation (e.g. Cellpose, StarDist) as the primary segmenter; this pipeline is built around CellProfiler `.cppipe` modules.

## Analysis outline
1. Parse the input samplesheet / `load_data.csv` describing plates, wells, sites, and per-channel image paths.
2. Run CellProfiler in illumination-correction mode using `illumination.cppipe` to produce per-plate illumination function images.
3. Run CellProfiler in analysis mode (`analysis.cppipe`) — segmentation of nuclei/cells/cytoplasm and extraction of per-object morphological, intensity, texture, and neighbour features.
4. Alternatively run in `assay_development` mode with `assaydevelopment.cppipe` for pilot/tuning runs on small test plates.
5. Aggregate per-plate CellProfiler outputs (object CSVs / SQLite / image QC metrics).
6. Collate run-level QC into a MultiQC report alongside Nextflow execution reports.

## Key parameters
- `input`: path to samplesheet / `load_data.csv` (CSV, required).
- `outdir`: absolute output directory (required).
- `cellprofiler_mode`: one of `analysis` (default, full feature extraction), `illumination` (illumination correction only), `assay_development` (pilot tuning), or `complete` to run end-to-end.
- `cellprofiler_illumination_cppipe`: path to the illumination-correction `.cppipe` (defaults to the bundled `assets/cellprofiler/illumination.cppipe`).
- `cellprofiler_analysis_cppipe`: path to the analysis `.cppipe` (defaults to `assets/cellprofiler/analysis.cppipe`).
- `cellprofiler_assaydevelopment_cppipe`: path to the assay-development `.cppipe`.
- `stop_after`: checkpoint to halt the workflow early (default `complete`); useful to stop after illumination when iterating.
- `-profile`: pick `docker`, `singularity`, `conda`, etc. for reproducibility; combine with `test` for the bundled minimal dataset.

## Test data
The bundled `test` profile points `input` at `assets/samplesheet.csv` — a minimal pilot load-data CSV shipped with the repository — and forces `cellprofiler_mode = assay_development` so the run exercises the assay-development `.cppipe` on a tiny image set suitable for CI (resource cap: 4 CPU / 15 GB / 1 h). The `test_full` profile instead pulls a `complete_plate_dataset/load_data.csv` from the `nf-core/test-datasets` repo under `cellpainting/` to run a full-size plate end-to-end. Expected outputs are CellProfiler per-object feature tables plus a MultiQC HTML report and Nextflow `pipeline_info/` execution traces under `--outdir`.

## Reference workflow
[nf-core/cellpainting](https://github.com/nf-core/cellpainting) (version `1.0.0dev`, template 3.3.2). This pipeline is in active development; consult `docs/development_plan.md`, `docs/architecture.md`, and `docs/data_contracts.md` in the repo for the current module map and data contracts before relying on specific outputs.
