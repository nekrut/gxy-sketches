---
name: illumina-bcl-demultiplexing
description: Use when you have a raw Illumina sequencer run directory (BCL files)
  and need to convert it to per-sample FASTQ files with demultiplexing, adapter trimming,
  and QC. Handles multi-flowcell, multi-lane runs and produces downstream-pipeline-ready
  samplesheets. Also supports Element AVITI, Singular Genomics, MGI, and 10x Genomics
  instruments via sibling demultiplexers.
domain: qc
organism_class:
- any
input_data:
- illumina-run-directory
- flowcell-samplesheet
source:
  ecosystem: nf-core
  workflow: nf-core/demultiplex
  url: https://github.com/nf-core/demultiplex
  version: 1.7.0
  license: MIT
  slug: demultiplex
tools:
- name: bcl-convert
- name: bcl2fastq
- name: bases2fastq
- name: sgdemux
  version: 1.1.1
- name: fqtk
  version: 0.2.1
- name: mkfastq
- name: mgikit
- name: samshee
- name: fastp
- name: falco
  version: 1.2.1
- name: checkqc
- name: kraken2
- name: multiqc
tags:
- demultiplex
- bcl
- fastq
- illumina
- flowcell
- samplesheet
- preprocessing
- sequencing-facility
test_data: []
expected_output: []
---

# Illumina BCL demultiplexing to FASTQ

## When to use this sketch
- You have a raw Illumina sequencer output directory (e.g. `DDMMYY_SERIAL_FC/`) containing BCL/CBCL files plus a facility-provided `SampleSheet.csv` and need per-sample FASTQs.
- You are running a sequencing core and need a reproducible, containerised demultiplexing step with QC reports (Falco/FastQC, fastp, MultiQC) and MD5 checksums before delivering FASTQs to downstream analysis.
- You need downstream-pipeline-ready samplesheets (nf-core/rnaseq, sarek, atacseq, methylseq, taxprofiler) auto-generated from the demultiplexed output.
- You are processing multiple flowcells and/or restricting demultiplexing to specific lanes in a single pipeline run.
- Optional: you want post-run QC thresholding (CheckQC, bcl2fastq only) or contamination screening via Kraken2 against a user-supplied DB.

## Do not use when
- You already have demultiplexed FASTQs and only need trimming/QC — use a dedicated QC/trimming workflow instead.
- Your data comes from an Element Biosciences AVITI, Singular Genomics, MGI, or 10x Chromium `mkfastq` workflow and you want a sketch tuned to that instrument — this pipeline supports them too via `--demultiplexer {bases2fastq,sgdemux,mgikit,mkfastq,fqtk}`, but the canonical path documented here is Illumina BCL. Pick a sibling sketch if one exists for the non-Illumina instrument.
- You need variant calling, alignment, or quantification — this is a preprocessing-only pipeline; hand its output (and the auto-generated samplesheets) to nf-core/rnaseq, sarek, etc.

## Analysis outline
1. Validate the Illumina v2 (or v1 with `--v1_schema`) flowcell `SampleSheet.csv` with **samshee**, optionally applying a custom JSON schema.
2. Strip adapter sequences from the `[Settings]` section of the samplesheet (controlled by `remove_samplesheet_adapter`, default true) so the BCL converter does not pre-trim.
3. Convert BCL → FASTQ and demultiplex with **bcl-convert** (default) or **bcl2fastq**, honoring optional per-row `lane` filtering.
4. (bcl2fastq only) Run **CheckQC** against Illumina run-folder quality thresholds, emitting `checkqc_report.json`.
5. Adapter and quality trim each demultiplexed FASTQ with **fastp** (unless `--trim_fastq false`).
6. Run raw-read QC with **Falco** (FastQC-compatible) on the untrimmed FASTQs.
7. Optionally subsample reads and screen for contamination with **Kraken2** against `--kraken_db`.
8. Generate per-file **MD5** checksums.
9. Emit downstream-ready samplesheets for nf-core/rnaseq, sarek, atacseq, methylseq, and taxprofiler (respecting `--strandedness` for rnaseq).
10. Aggregate all reports into a single **MultiQC** HTML report under `multiqc/`.

## Key parameters
- `--input samplesheet.csv` — pipeline samplesheet with columns `id,samplesheet,lane,flowcell` (add `per_flowcell_manifest` for fqtk). One row per (flowcell, lane) to demultiplex.
- `--outdir <path>` — results directory (absolute path required on cloud).
- `--demultiplexer bclconvert` — default; set to `bcl2fastq`, `bases2fastq`, `sgdemux`, `fqtk`, `mkfastq`, or `mgikit` to switch instruments.
- `--trim_fastq true` — run fastp trimming (default true).
- `--skip_tools` — comma list from `{fastp,fastqc,kraken,multiqc,checkqc,falco,md5sum,samshee}` to disable individual steps.
- `--remove_samplesheet_adapter true` — strip `[Settings]` adapters so fastp (not the BCL converter) does trimming; aligns with 10x Genomics guidance.
- `--v1_schema false` — set true if feeding an Illumina v1 sample sheet to samshee.
- `--json_schema_validator` / `--name_schema_validator` / `--file_schema_validator` — custom samshee validation rules.
- `--checkqc_config` — optional path to a CheckQC YAML threshold config.
- `--kraken_db` + `--sample_size 100000` — enable contamination screening and set the per-sample read subsample size.
- `--strandedness auto` — value written into the generated nf-core/rnaseq samplesheet (`unstranded|auto|reverse|forward`); does not alter demultiplexing.
- `-profile docker|singularity|conda|<institutional>` — container/runtime profile (required for reproducibility).

## Test data
The pipeline's `test` profile (conf/test.config) points `--input` at `nf-core/test-datasets:demultiplex/samplesheet/1.3.0/flowcell_input.csv`, a small pipeline samplesheet referencing a miniature Illumina run directory and `b2fq-samplesheet.csv` flowcell samplesheet. It runs with `--demultiplexer bclconvert` and `--skip_tools samshee`, restricted via `ext.args` to `--first-tile-only` so the test completes in minutes. Expected outputs include per-flowcell directories under `<outdir>/<id>/` containing demultiplexed `*.fastq.gz`, `InterOp/` binaries, bcl-convert `Reports/`, fastp HTML/JSON, Falco FastQC reports, `.md5` files, and a top-level `multiqc/multiqc_report.html`. The `test_full` profile uses `samplesheet_full.csv` with `--demultiplexer bcl2fastq` and `--v1_schema true` to exercise the full bcl2fastq + CheckQC path on real-sized data.

## Reference workflow
nf-core/demultiplex v1.7.0 — https://github.com/nf-core/demultiplex (DOI 10.5281/zenodo.7153103). Default demultiplexer is `bclconvert`; see `nextflow_schema.json` and `docs/usage.md` for the full parameter set and per-demultiplexer flowcell samplesheet formats.
