---
name: xenium-spatial-transcriptomics-qc
description: Use when you need to process and quality-control 10x Genomics Xenium
  in situ spatial transcriptomics data, running baseline read QC and aggregate reporting
  as a scaffold for downstream spatial analysis. Targets Xenium outputs rather than
  sequencing-based spatial assays like Visium or Slide-seq.
domain: single-cell
organism_class:
- eukaryote
- vertebrate
input_data:
- xenium-output
- short-reads-paired
source:
  ecosystem: nf-core
  workflow: nf-core/spatialxe
  url: https://github.com/nf-core/spatialxe
  version: dev
  license: MIT
  slug: spatialxe
tools:
- name: fastqc
- name: multiqc
  version: '1.13'
- name: nextflow
tags:
- spatial-transcriptomics
- xenium
- in-situ
- 10x-genomics
- qc
- imaging
test_data: []
expected_output: []
---

# Xenium spatial transcriptomics QC

## When to use this sketch
- Input is 10x Genomics Xenium in situ spatial transcriptomics data (imaging-based, sub-cellular resolution transcript detections).
- You want a reproducible, containerized Nextflow pipeline to run baseline QC (FastQC) and aggregate a MultiQC report across one or more Xenium samples.
- You need a scaffold to stage Xenium experiments before downstream spatial analysis (cell segmentation review, cell typing, neighborhood analysis).
- The analysis target is vertebrate tissue sections (e.g., human or mouse FFPE/fresh-frozen) profiled with a Xenium gene panel.

## Do not use when
- Data are from 10x Visium or Visium HD spot-based spatial transcriptomics — use a Visium-oriented sketch (e.g. `nf-core/spatialvi`) instead.
- Data are from MERFISH, CosMx, Slide-seq, Stereo-seq, or other non-Xenium spatial platforms — those need platform-specific segmentation and decoding pipelines.
- Data are dissociated single-cell or single-nucleus RNA-seq (10x Chromium, Smart-seq) — use an scRNA-seq sketch.
- You need full downstream spatial analysis (cell typing, niche detection, differential expression across regions) — this pipeline is QC-focused and currently in development; pair it with a spatial analysis sketch (Squidpy/Scanpy, Seurat, Giotto).
- You need variant calling, bulk RNA-seq quantification, or assembly — completely different domains.

## Analysis outline
1. Parse the samplesheet CSV (`sample,fastq_1,fastq_2`) and concatenate lanes per sample.
2. Run FastQC on raw reads to produce per-sample quality metrics.
3. Aggregate FastQC output and tool versions with MultiQC into a single HTML report.
4. Emit a `pipeline_info/` directory with Nextflow execution reports, DAG, and software versions for provenance.

## Key parameters
- `--input`: path to the samplesheet CSV (required; must match `assets/schema_input.json`).
- `--outdir`: absolute output directory (required).
- `--genome` / `--fasta`: reference selection, e.g. `--genome GRCh38` via iGenomes, or a custom `--fasta` path.
- `-profile`: execution/container profile — `docker`, `singularity`, `podman`, `conda`, or `test` for the bundled minimal run.
- `--max_cpus`, `--max_memory`, `--max_time`: resource caps (defaults 16 CPU / 128 GB / 240 h).
- `--multiqc_title`, `--multiqc_config`: customize the aggregated QC report.

## Test data
The `test` profile wires up a minimal placeholder samplesheet (currently borrowed from the nf-core/viralrecon test-datasets bucket) with the `R64-1-1` (S. cerevisiae) iGenomes reference and resource caps of 2 CPUs / 6 GB / 6 h so the pipeline can execute on GitHub Actions. Running `nextflow run nf-core/spatialxe -profile test,docker --outdir results` is expected to complete end-to-end and produce FastQC HTML/zip outputs under `results/fastqc/`, a MultiQC report at `results/multiqc/multiqc_report.html`, and Nextflow execution reports plus `software_versions.yml` under `results/pipeline_info/`. A full-size Xenium test dataset is not yet wired up — the `test_full` profile is a placeholder during pipeline development.

## Reference workflow
nf-core/spatialxe (dev branch, https://github.com/nf-core/spatialxe), MIT-licensed. The pipeline is explicitly marked as under development: the current release implements the QC scaffold (FastQC + MultiQC + pipeline_info reporting) of the planned Xenium processing metromap, with additional Xenium-specific modules to follow in future releases.
