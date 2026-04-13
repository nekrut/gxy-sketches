---
name: fastq-repair-gz-recovery
description: Use when you have corrupted or truncated FASTQ.gz files, malformed/non-compliant
  FASTQ reads, broken paired-end synchronization, or interleaving problems that need
  to be salvaged before downstream analysis. Produces clean, well-formed FASTQ files
  plus a FastQC/MultiQC report.
domain: qc
organism_class:
- any
input_data:
- short-reads-single
- short-reads-paired
- fastq-gz-corrupted
source:
  ecosystem: nf-core
  workflow: nf-core/fastqrepair
  url: https://github.com/nf-core/fastqrepair
  version: 1.0.0
  license: MIT
tools:
- gzrt
- wipertools
- fastqwiper
- bbmap-repair
- fastqc
- multiqc
tags:
- fastq
- repair
- recovery
- corrupted
- gzip
- qc
- paired-end
- preprocessing
test_data: []
expected_output: []
---

# FASTQ.gz corruption recovery and repair

## When to use this sketch
- A FASTQ.gz file fails to decompress cleanly (truncated archive, CRC errors) and you need to salvage as many reads as possible before continuing.
- Downstream tools reject reads due to malformed records (bad SEQ/QUAL lines, illegal characters, header/quality length mismatches).
- Paired-end R1/R2 files have become desynchronized, contain orphan reads, or need to be re-interleaved/re-paired.
- You want a single pass that emits repaired FASTQs plus FastQC/MultiQC reports so you can verify the recovery worked.
- Works for any organism / any library type — the pipeline is sequence-content agnostic; pick it whenever the problem is *file integrity*, not biology.

## Do not use when
- Your FASTQs are structurally fine and you just want trimming, adapter removal, or quality filtering — use a standard read-preprocessing sketch (fastp / Trim Galore) instead.
- You need contamination screening, host removal, or taxonomic QC — use a dedicated QC/decontamination sketch.
- You are starting from BAM/CRAM — convert with samtools first, then apply this sketch only if the resulting FASTQ is broken.
- You have long reads (ONT/PacBio) with basecalling problems — this pipeline targets short-read FASTQ structural issues and uses BBMap repair semantics.

## Analysis outline
1. Parse the input samplesheet (`sample,fastq_1,fastq_2`) and auto-detect single- vs paired-end per row.
2. Recover as many intact gzip blocks as possible from corrupted `.fastq.gz` files using `gzrt`.
3. Split each recovered FASTQ into `num_splits` chunks and run `wipertools` (fastqwiper) in parallel to drop/fix non-compliant reads, filtering SEQ lines against the allowed `alphabet`.
4. For paired-end samples, re-synchronize mates and separate orphans with `bbmap/repair.sh` (unless `--skip_bbmap_repair` is set).
5. Run `FastQC` on the repaired FASTQs to characterize the salvaged data.
6. Aggregate per-sample QC and per-step cleaning summaries with `MultiQC`.

## Key parameters
- `input`: CSV samplesheet with columns `sample,fastq_1,fastq_2`; R2 optional; both mates in a row must share the same extension (`.fastq`, `.fastq.gz`, `.fq`, `.fq.gz`).
- `outdir`: absolute output path; final files land under `<outdir>/repaired/` with companion `*.report` cleaning summaries, plus `<outdir>/QC/{fastqc,multiqc}/`.
- `num_splits` (default `2`, must be ≥1): number of chunks per FASTQ for parallel wipertools processing — raise on large files.
- `qin` (default `33`; allowed `33` or `64`): ASCII quality offset passed to BBMap (33=Sanger/Illumina 1.8+, 64=old Solexa/Illumina 1.3–1.7).
- `alphabet` (default `ACGTN`): characters permitted in SEQ lines; reads with any other character are discarded by wipertools.
- `skip_bbmap_repair` (default `false`): set `true` for single-end-only runs or when you want the wipertools output verbatim without mate re-pairing.
- `publish_all_tools` (default `false`): set `true` to also publish intermediate gzrt/wipertools/bbmap outputs for debugging.

## Test data
The bundled `test` profile points at `fastqrepair/testdata/samplesheet_30reads.csv` from the nf-core test-datasets repo, a tiny samplesheet referencing ~30-read FASTQs (including deliberately corrupted and empty files) used to exercise the gzrt → wipertools → bbmap repair path end-to-end. Running `-profile test,docker --outdir results` is expected to complete with `num_splits=2`, emit repaired FASTQs and `.report` cleaning summaries under `results/repaired/`, and produce `results/QC/fastqc/*_fastqc.{html,zip}` plus a `results/QC/multiqc/multiqc_report.html`. The `test_full` profile reuses the same 30-read dataset as a smoke-test for full-size CI. No reference genome or organism-specific assertions are involved; success is structural (files exist, MultiQC parses, pipeline exits 0).

## Reference workflow
nf-core/fastqrepair v1.0.0 — https://github.com/nf-core/fastqrepair (Zenodo DOI 10.5281/zenodo.14796348). Designed and maintained by Tommaso Mazza; implemented in Nextflow DSL2 (≥24.04.2).
