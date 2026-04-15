---
name: umi-consensus-reads-fgbio
description: Use when you have UMI-tagged Illumina short-read sequencing data (single-UMI,
  dual-UMI, or Duplex-Sequencing) and need to produce error-corrected consensus reads
  following the fgbio Best Practices FASTQ-to-Consensus pipeline. Typical applications
  include cfDNA/ctDNA, low-frequency somatic variant detection, and duplex sequencing
  where raw UMIs must be extracted, reads grouped by source molecule, and consensus
  reads called, filtered, and realigned.
domain: variant-calling
organism_class:
- eukaryote
- vertebrate
input_data:
- short-reads-paired
- umi-tagged-fastq
- reference-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/fastquorum
  url: https://github.com/nf-core/fastquorum
  version: 1.2.0
  license: MIT
  slug: fastquorum
tools:
- name: fgbio
- name: bwa-mem
- name: samtools
- name: fastqc
  version: 0.12.1
- name: multiqc
  version: '1.27'
tags:
- umi
- consensus
- duplex-sequencing
- cfdna
- ctdna
- low-frequency-variants
- fgbio
- molecular-barcodes
test_data: []
expected_output: []
---

# UMI consensus read calling with fgbio

## When to use this sketch
- Illumina short-read libraries that carry unique molecular identifiers (UMIs) inline in R1/R2, in index reads, or both, and you need error-corrected consensus reads before variant calling.
- Low-frequency somatic / cfDNA / ctDNA / MRD workflows where duplicate collapsing by coordinate alone is insufficient.
- Duplex Sequencing data (e.g. TwinStrand, IDT xGen Prism, Agilent SureSelect XT HS2) where both strands of the source molecule are sequenced and duplex consensus calling is required.
- Verified / commonly used kit read structures include Twist UMI Adapter System (`5M2S+T 5M2S+T`), NEBNext UDI-UMI, IDT xGen, Illumina TSO, Agilent SureSelect XT HS/HS2, TwinStrand AML MRD / Mutagenesis.
- You want an end-to-end FASTQ -> grouped BAM -> consensus BAM -> filtered, realigned consensus BAM following the [fgbio Best Practices FASTQ-to-Consensus Pipeline](https://github.com/fulcrumgenomics/fgbio/blob/main/docs/best-practice-consensus-pipeline.md).

## Do not use when
- Reads have no UMIs at all — use a standard short-read alignment + MarkDuplicates workflow instead.
- You only need raw read QC / trimming with no consensus step.
- Your data are long reads (PacBio HiFi, ONT) — use a long-read variant-calling sketch.
- You need downstream somatic variant calling and annotation in the same pipeline; this sketch stops at filtered, realigned consensus BAMs and leaves variant calling to a downstream workflow.
- Your UMIs are already pre-extracted into read headers by another tool and you want UMI-aware dedup without consensus calling (consider a UMI-tools based workflow).

## Analysis outline
1. Raw FASTQ QC with `FastQC`.
2. Convert FASTQ to unmapped BAM and extract UMIs into the `RX` SAM tag using `fgbio FastqToBam`, driven by a per-sample `read_structure` (e.g. `5M2S+T 5M2S+T`). 1–4 FASTQs per sample are supported (R1, optional R2, optional I1, optional I2).
3. Align raw reads with `bwa mem`, re-merge UMI tags from the unmapped BAM with `fgbio ZipperBam`, and template-coordinate sort with `samtools sort`.
4. Group reads originating from the same source molecule with `fgbio GroupReadsByUmi` (`MI` tag), emitting a tag-family-size metrics file.
5. Call consensus reads:
   - Duplex sequencing (`--duplex_seq true`): `fgbio CallDuplexConsensusReads` plus `fgbio CollectDuplexSeqMetrics`.
   - Otherwise: `fgbio CallMolecularConsensusReads` (single-strand consensus).
6. Realign the consensus reads with `bwa mem` and re-attach tags with `fgbio ZipperBam`.
7. Filter consensus reads with `fgbio FilterConsensusReads` (per-base masking and whole-read filtering). In `--mode ht` (High Throughput) filtering is fused with calling and alignment happens after filtering; in `--mode rd` (R&D) intermediate pre-filter consensus BAMs are retained so parameters can be swept.
8. Aggregate QC across steps with `MultiQC`.

## Key parameters
- `--input`: CSV samplesheet with columns `sample,fastq_1[,fastq_2[,fastq_3[,fastq_4]]],read_structure`. Rows with the same `sample` are merged; `read_structure` must match the number of FASTQs (one read-structure segment per FASTQ).
- `--mode`: `rd` (default, flexible, keeps intermediates for parameter sweeps) or `ht` (high-throughput production, fuses consensus call+filter).
- `--duplex_seq`: `true` for Duplex-Sequencing libraries; switches to `CallDuplexConsensusReads` and enables `CollectDuplexSeqMetrics`.
- `--groupreadsbyumi_strategy`: `Paired` (auto-default when `duplex_seq=true`) or `Adjacency` (auto-default otherwise); other options `Identity`, `Edit`. Must match library chemistry.
- `--groupreadsbyumi_edits`: maximum UMI edit distance when grouping.
- `--call_min_reads` / `--call_min_baseq`: minimum raw-read support and input base quality for `CallMolecularConsensusReads` / `CallDuplexConsensusReads`. In HT mode keep these equal to the filter thresholds.
- `--filter_min_reads` / `--filter_min_baseq` / `--filter_max_base_error_rate`: thresholds for `FilterConsensusReads`. `filter_min_reads` accepts up to three values for duplex data (total / per-strand A / per-strand B).
- Reference: `--genome` (iGenomes key, e.g. `GRCh38`) OR explicit `--fasta`, optional `--fasta_fai`, `--dict`, `--bwa`; use `--save_reference` to cache generated indices.
- `-profile`: one of `docker`, `singularity`, `podman`, `conda`, etc.; chain with `test` for the bundled test profile.

## Test data
The pipeline ships a `test` profile (`conf/test.config`) that points `--input` at `samplesheet.tiny.csv` from the `nf-core/test-datasets` `fastquorum` branch and `--fasta` at a chr17 subset (`references/chr17.fa`). A companion `test_full` profile uses `samplesheet.full.csv` against the same chr17 reference for fuller AWS CI runs. Both profiles cap resources at 2 CPU / 6 GB / 6 h and exercise the full FASTQ→consensus path: FastQC reports, `*.unmapped.bam` from FastqToBam (with `RX` tags), a grouped BAM plus `*.grouped-family-sizes.txt` from GroupReadsByUmi, a `*.cons.unmapped.bam` from consensus calling, and a `*.cons.filtered.bam` (plus `.bai` in HT mode) after FilterConsensusReads, finishing with a combined MultiQC report.

## Reference workflow
[nf-core/fastquorum](https://github.com/nf-core/fastquorum) v1.2.0 — implements the [fgbio Best Practices FASTQ to Consensus Pipeline](https://github.com/fulcrumgenomics/fgbio/blob/main/docs/best-practice-consensus-pipeline.md) by Fulcrum Genomics.
