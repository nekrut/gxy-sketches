---
name: data-sync-integrity-archival
description: Use when you need to synchronize sequencing data directories between
  storage locations, verify file integrity via checksums, and/or archive or flag aged
  datasets for deletion at a sequencing/data-processing facility. This is a sysops/automation
  workflow, not a biological analysis.
domain: other
organism_class:
- any
input_data:
- directory-tree
- samplesheet-csv
- yaml-include-exclude-rules
source:
  ecosystem: nf-core
  workflow: nf-core/datasync
  url: https://github.com/nf-core/datasync
  version: dev
  license: MIT
tools:
- sha256sum
- md5sum
- rsync
- multiqc
tags:
- sysops
- data-management
- checksum
- archival
- integrity
- sync
- automation
- facility
test_data: []
expected_output: []
---

# Data synchronization, integrity validation and archival

## When to use this sketch
- You operate a sequencing core or large data-processing facility and need to move run folders between a hot storage tier and a cold/archive tier.
- You need to generate and later re-verify checksums (sha256, md5, etc.) for arbitrary file trees to prove data integrity.
- You want to flag datasets as archivable based on rules like "checksum matches" and "mtime older than N days", optionally emitting deletion lists or dropping marker files (e.g. `SYNC_DONE`, empty stubs after archive).
- You want a MultiQC-style report documenting exactly which files were synced, validated, archived, or queued for deletion.
- The workflow is organism-agnostic — it manipulates files, not reads.

## Do not use when
- You actually need to process sequencing data (QC, alignment, variant calling, assembly, expression, etc.). Pick a domain-specific sketch instead (e.g. `haploid-variant-calling-bacterial`, `bulk-rna-seq-star-salmon`, `bacterial-assembly-short-read`).
- You just want a one-shot `rsync` or `aws s3 sync` — this workflow is overkill unless you need the reporting and rule engine.
- You need content-aware deduplication or backup versioning (use restic/borg/bacula instead).
- The pipeline is explicitly marked WIP/unstable upstream; do not rely on it for production archival without local validation.

## Analysis outline
1. Read a samplesheet / target directory listing describing the trees to operate on.
2. Optional `sync` subworkflow: walk the source tree, apply YAML include/exclude rules, optionally gate on checkpoint files (e.g. `DEMUX_DONE`), copy to the target, and compute checksums using the configured backend.
3. Optional `integrity` subworkflow: re-read files at a target location and compare against the checksum manifest produced earlier, emitting pass/fail per file.
4. Optional `archival` subworkflow: evaluate user-configurable rules (age threshold, checksum match, presence at both source and target) to decide whether a dataset is "archived"; drop `SYNC_DONE`/empty stub files and optionally delete or emit a deletion candidate list.
5. Aggregate per-subworkflow results into a MultiQC custom-content report documenting every action taken.

## Key parameters
- `--input` — CSV samplesheet describing datasets/paths to operate on (required).
- `--outdir` — absolute path for results and reports (required).
- `--sync` — enable the synchronization subworkflow.
- `--sync_backend` — checksum algorithm, e.g. `sha256`, `md5`.
- `--sync_done true` — drop a `SYNC_DONE` marker in each successfully processed folder.
- Include/exclude YAML — whitelist/blacklist patterns for which files/subfolders participate in the sync.
- Checkpoint-file gating — only sync folders that contain a sentinel such as `DEMUX_DONE`.
- Archival rules — minimum age in days, required checksum match, whether to delete-in-place vs. emit a deletion candidate list.
- `-profile` — container backend (`docker`, `singularity`, `conda`, institutional, etc.). Use `-profile test` for the bundled smoke test.

## Test data
The bundled `test` and `test_full` profiles currently point at the nf-core viralrecon Illumina amplicon samplesheets (`samplesheet_test_illumina_amplicon.csv` / `samplesheet_full_illumina_amplicon.csv`) and the `R64-1-1` iGenomes reference — these exist only to exercise the scaffolding while the sysops subworkflows are under development. A successful `nextflow run nf-core/datasync -profile test,docker --outdir results` should complete without error and produce a `multiqc/multiqc_report.html` plus a `pipeline_info/` directory containing execution reports and `software_versions.yml`. No biological assertions are expected from the test run.

## Reference workflow
nf-core/datasync (dev, version 1.0dev, MIT) — https://github.com/nf-core/datasync. Note: upstream README explicitly marks the pipeline as WORK IN PROGRESS and NOT YET STABLE; the sync/integrity/archival subworkflows described above reflect the stated design even though not all are fully implemented in the current codebase.
