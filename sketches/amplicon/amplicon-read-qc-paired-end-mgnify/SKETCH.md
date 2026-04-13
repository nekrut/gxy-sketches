---
name: amplicon-read-qc-paired-end-mgnify
description: Use when you need to quality-control paired-end Illumina amplicon (16S/18S/ITS)
  FASTQ reads before downstream ASV/OTU calling or taxonomic profiling, following
  the MGnify v5 amplicon pipeline conventions (fastp + SeqPrep merge + Trimmomatic
  + length/ambiguity filters + MultiQC).
domain: amplicon
organism_class:
- microbial
- metagenome
input_data:
- short-reads-paired
source:
  ecosystem: iwc
  workflow: MGnify's amplicon pipeline v5.0 - Quality control PE
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/amplicon/amplicon-mgnify/mgnify-amplicon-pipeline-v5-quality-control-paired-end
  version: '0.3'
  license: Apache-2.0
tools:
- fastp
- seqprep
- trimmomatic
- fastq_filter
- prinseq
- fastqc
- multiqc
tags:
- amplicon
- 16s
- 18s
- its
- metagenomics
- quality-control
- read-merging
- mgnify
- microgalaxy
test_data:
- role: paired_end_reads__err2715528__forward
  url: https://zenodo.org/records/13710235/files/ERR2715528_forward.fastqsanger.gz
  sha1: 3defa3fafb76470cce8f37eaf725c80f155c6ac2
- role: paired_end_reads__err2715528__reverse
  url: https://zenodo.org/records/13710235/files/ERR2715528_reverse.fastqsanger.gz
  sha1: 38ca7f72b64c1b27367b61084e95797c4c97bfd5
expected_output:
- role: paired_end_multiqc_report
  description: Content assertions for `Paired-end MultiQC report`.
  assertions:
  - 'that: has_text'
  - 'text: ERR2715528_ambiguous_base_filtering'
  - 'that: has_text'
  - 'text: ERR2715528_initial_reads'
  - 'that: has_text'
  - 'text: ERR2715528_length_filtering'
  - 'that: has_text'
  - 'text: ERR2715528_trimming'
  - 'that: has_text'
  - 'text: 92.2'
  - 'that: has_text'
  - 'text: 51'
---

# Paired-end amplicon read QC (MGnify v5)

## When to use this sketch
- You have raw paired-end Illumina amplicon sequencing reads (16S, 18S, or ITS) and need a cleaned, merged, quality-controlled FASTA ready for MGnify-style downstream steps (SSU/LSU extraction, ASV/OTU calling, taxonomic assignment).
- You want the exact MGnify amplicon v5 QC recipe: fastp filtering, SeqPrep overlap merging, Trimmomatic sliding-window trimming, hard length filter, and PRINSEQ ambiguous-base filter, with a consolidated MultiQC report tracking read counts at each stage.
- You want per-sample QC statistics (`_initial_reads`, `_trimming`, `_length_filtering`, `_ambiguous_base_filtering`) aggregated into a single MultiQC HTML and tabular summary.
- You are working with a `list:paired` collection of samples in Galaxy (or equivalent paired inputs) and want reproducible, parameterized QC.

## Do not use when
- Reads are single-end — use a single-end amplicon QC sketch instead (the MGnify pipeline ships a sibling SE workflow).
- Reads are long-read (PacBio CCS, Nanopore) amplicons — merging via SeqPrep does not apply; use a long-read amplicon QC sketch.
- You want shotgun metagenomic QC (host-read removal, adapter-only trimming without merging) — pick a metagenomics QC sketch, not this amplicon one.
- You already have merged, filtered reads and only need ASV inference — skip QC and go directly to a DADA2/vsearch ASV sketch.
- You need variant calling, assembly, or RNA-seq QC — unrelated domains.

## Analysis outline
1. **fastp** — paired-end quality filtering (Phred cutoff, unqualified-base percent limit, min length) with optional overlap base correction; emits cleaned paired FASTQs plus HTML/JSON reports.
2. **Unzip collection** — split the paired collection into forward/reverse datasets for the merger (datatype set to `fastqsanger.gz`).
3. **SeqPrep (MGnify build)** — merge overlapping mates into a single longer read, trimming Illumina TruSeq adapters; outputs merged FASTQ.
4. **FastQC (post-merge)** — capture per-sample stats on merged reads, tagged `_initial_reads` via a find-and-replace rename step.
5. **Trimmomatic** (single-end mode on merged reads) — `SLIDINGWINDOW`, `LEADING`, `TRAILING`, `MINLEN` operations, Phred33 encoding.
6. **FastQC (post-trim)** — stats after Trimmomatic, tagged `_trimming`.
7. **Filter FASTQ** — hard length filter (`min_size`) discarding reads below the amplicon-appropriate threshold.
8. **FastQC (post-length-filter)** — stats tagged `_length_filtering`.
9. **PRINSEQ** — ambiguity filter, dropping reads whose N percentage exceeds the threshold.
10. **FASTQ→FASTA** and **FASTA Width** (60 cols) — produce the final `Paired-end post quality control FASTA files` collection.
11. **FastQC (post-ambiguity)** — stats tagged `_ambiguous_base_filtering`.
12. **MultiQC** — aggregate the four renamed FastQC text reports per sample into `Paired-end MultiQC report` (HTML) and `Paired-end MultiQC statistics` (tabular).

## Key parameters
- **fastp**
  - `qualified_quality_phred`: 20 (Phred cutoff for a base to count as qualified)
  - `unqualified_percent_limit`: 20 (max % unqualified bases per read)
  - `length_required`: 70 (drop reads shorter than this after trimming)
  - `base_correction`: off by default; turn on only for high-overlap libraries
- **SeqPrep** (hardcoded MGnify defaults): `quality_cutoff=13`, `min_length=30`, `min_base_pair_overlap=15`, `max_mismatch_fraction=0.02`, `min_match_fraction=0.9`, adapters `AGATCGGAAGAGCGGTTCAG` / `AGATCGGAAGAGCGTCGTGT`.
- **Trimmomatic** (run in single-end mode on the merged reads, Phred33)
  - `SLIDINGWINDOW`: window=4, required_quality=15
  - `LEADING`: 3
  - `TRAILING`: 3
  - `MINLEN`: 100
- **Filter FASTQ** `min_size`: 100 (matches Trimmomatic MINLEN; this is the amplicon length floor).
- **PRINSEQ** `N_percentage_content_filter`: 10 (drop reads with >10% Ns); all other PRINSEQ filters disabled.
- **FASTA Width**: 60 columns for the final FASTA formatting.
- Input collection type must be `list:paired`; final outputs are a FASTA collection plus a MultiQC HTML report and tabular stats.

## Test data
The source workflow ships a single-sample test: a `list:paired` collection containing one paired sample `ERR2715528` with `ERR2715528_forward.fastqsanger.gz` and `ERR2715528_reverse.fastqsanger.gz` hosted on Zenodo (record 13710235). Running the workflow with default parameters is expected to produce a `Paired-end post quality control FASTA files` collection whose `ERR2715528` element matches the reference `ERR2715528_PE.fasta`, a `Paired-end MultiQC statistics` tabular output matching `general_stats_PE.tabular`, and a `Paired-end MultiQC report` HTML that contains the per-stage sample labels `ERR2715528_initial_reads`, `ERR2715528_trimming`, `ERR2715528_length_filtering`, and `ERR2715528_ambiguous_base_filtering`, along with the expected retention percentages (e.g. `92.2`) and read counts (e.g. `51`).

## Reference workflow
MGnify's amplicon pipeline v5.0 - Quality control PE, release 0.3 (IWC, `workflows/amplicon/amplicon-mgnify/mgnify-amplicon-pipeline-v5-quality-control-paired-end`). Authored by EMBL-EBI MGnify (Rand Zoabi, Paul Zierep); Apache-2.0.
