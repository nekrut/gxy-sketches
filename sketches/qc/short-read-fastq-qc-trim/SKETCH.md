---
name: short-read-fastq-qc-trim
description: Use when you need a lightweight quality-control and adapter/quality trimming
  pass over Illumina short-read FASTQ files (single- or paired-end) and a consolidated
  MultiQC report, without any downstream alignment, assembly, or variant calling.
  Good entry point for inspecting new sequencing runs.
domain: qc
organism_class:
- any
input_data:
- short-reads-paired
- short-reads-single
source:
  ecosystem: nf-core
  workflow: nf-core/demo
  url: https://github.com/nf-core/demo
  version: 1.1.0
  license: MIT
tools:
- fastqc
- seqtk
- multiqc
tags:
- qc
- fastqc
- seqtk
- multiqc
- trimming
- illumina
- short-reads
- demo
test_data: []
expected_output: []
---

# Short-read FASTQ QC and trimming

## When to use this sketch
- You have Illumina short-read FASTQ files (single- or paired-end) and want a fast QC + light trimming pass.
- You need a single consolidated MultiQC HTML report across many samples.
- You are inspecting a new sequencing run before committing to a heavier downstream pipeline.
- You want an nf-core-style, container-reproducible entry point that runs on modest resources.
- The samplesheet uses the standard `sample,fastq_1,fastq_2` layout, with repeated `sample` rows auto-concatenated across lanes/runs.

## Do not use when
- You need alignment, variant calling, or assembly — this workflow stops at trimmed FASTQs + QC.
- You need adapter-aware trimming with adapter detection or UMI handling; `seqtk trimfq` does quality-based end trimming only. Prefer a fastp/Trim Galore-based sketch.
- Inputs are long reads (ONT/PacBio), 10x single-cell FASTQs, or already-aligned BAM/CRAM.
- You need per-tool biological outputs (counts, VCFs, MAGs). Route to the relevant domain sketch instead (rna-seq, variant-calling, metagenomics, etc.).

## Analysis outline
1. Parse samplesheet and merge multi-lane FASTQs per `sample` ID (pipeline-internal cat).
2. Raw-read QC with `FastQC` on each (merged) FASTQ.
3. Quality trimming with `seqtk trimfq` (skippable via `--skip_trim`).
4. Aggregate FastQC + tool version reports with `MultiQC` into a single HTML summary.

## Key parameters
- `--input` (required): path to CSV/TSV/YAML samplesheet with columns `sample,fastq_1,fastq_2`; `fastq_2` left empty marks single-end.
- `--outdir` (required): absolute output directory.
- `--skip_trim` (bool, default false): skip the `seqtk trimfq` step and run QC only.
- `--multiqc_title` / `--multiqc_config` / `--multiqc_logo` / `--multiqc_methods_description`: customise the final MultiQC report.
- `--email` / `--email_on_fail`: optional completion notifications.
- `-profile` (Nextflow, single hyphen): pick a container engine, e.g. `docker`, `singularity`, `podman`, `conda`, or stack with `test` for the bundled minimal run.
- Reference-genome parameters (`--genome`, `--fasta`, `--igenomes_ignore`) are exposed by the schema but are not used by any process in this pipeline; leave unset.

## Test data
The `test` profile points `--input` at `samplesheet_test_illumina_amplicon.csv` from the `nf-core/test-datasets` (viralrecon branch), which lists a handful of small paired-end Illumina amplicon FASTQs downloaded over HTTPS. Running `nextflow run nf-core/demo -profile test,docker --outdir results` is expected to produce per-sample `FastQC` HTML/zip reports, trimmed gzipped FASTQs under `fq/`, and a top-level `multiqc/multiqc_report.html` aggregating FastQC stats and software versions, plus the standard `pipeline_info/` execution reports. Resources are capped at 2 CPUs / 4 GB / 1 h by the test profile so the run completes in minutes on a laptop.

## Reference workflow
nf-core/demo v1.1.0 (https://github.com/nf-core/demo) — FastQC + seqtk trimfq + MultiQC. Built on the nf-core 3.5.1 template; requires Nextflow ≥ 25.10.2.
