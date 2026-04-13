---
name: amplicon-read-qc-single-end
description: 'Use when you need to quality-control single-end amplicon (16S/18S/ITS)
  sequencing reads prior to ASV/OTU calling or taxonomic profiling, producing cleaned
  FASTA files and a MultiQC report. Implements the MGnify v5.0 amplicon QC recipe:
  Trimmomatic trimming, length filtering, and ambiguous-base (N%) filtering.'
domain: qc
organism_class:
- metagenome
- microbial-community
input_data:
- short-reads-single
- amplicon-fastq
source:
  ecosystem: iwc
  workflow: MGnify's amplicon pipeline v5.0 - Quality control SE
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/amplicon/amplicon-mgnify/mgnify-amplicon-pipeline-v5-quality-control-single-end
  version: '0.3'
  license: Apache-2.0
tools:
- fastqc
- trimmomatic
- fastq_filter
- prinseq
- multiqc
- fasta_formatter
tags:
- amplicon
- 16S
- 18S
- ITS
- mgnify
- quality-control
- single-end
- metagenomics
- microgalaxy
test_data:
- role: single_end_reads__drr010481
  url: https://zenodo.org/records/13710235/files/DRR010481.fastqsanger.gz
  sha1: bc6268d53b1836d6e5db43d41de2d5f66d9c8b94
expected_output:
- role: single_end_multiqc_report
  description: Content assertions for `Single-end MultiQC report`.
  assertions:
  - 'that: has_text'
  - 'text: DRR010481_ambiguous_base_filtering'
  - 'that: has_text'
  - 'text: 84.0'
  - 'that: has_text'
  - 'text: DRR010481_initial_reads'
  - 'that: has_text'
  - 'text: 47'
  - 'that: has_text'
  - 'text: DRR010481_length_filtering'
  - 'that: has_text'
  - 'text: DRR010481_trimming'
  - 'that: has_text'
  - 'text: DRR010481_ambiguous_base_filtering'
  - 'that: has_text'
  - 'text: 48'
  - 'that: has_text'
  - 'text: 553'
  - 'that: has_text'
  - 'text: 242'
  - 'that: has_text'
  - 'text: DRR010481_initial_reads'
  - 'that: has_text'
  - 'text: DRR010481_length_filtering'
  - 'that: has_text'
  - 'text: DRR010481_trimming'
---

# Amplicon read QC (single-end, MGnify v5.0)

## When to use this sketch
- User has single-end amplicon sequencing reads (16S/18S rRNA, ITS, or similar marker genes) and needs to clean them before downstream ASV/OTU inference or taxonomic assignment.
- User wants to reproduce the MGnify amplicon pipeline v5.0 QC stage on Galaxy, producing cleaned per-sample FASTA files plus a MultiQC summary across raw, trimmed, length-filtered, and ambiguity-filtered stages.
- The starting data is a collection of `.fastq.gz` files (one per sample), not paired-end reads.
- You want deterministic, report-friendly output suitable for feeding into the MGnify amplicon ASV / taxonomy subworkflows.

## Do not use when
- Reads are paired-end — use the sibling sketch for the MGnify amplicon v5.0 paired-end QC subworkflow instead.
- Reads are long-read (PacBio CCS, Nanopore) — amplicon long-read QC needs a different trimmer (e.g. NanoFilt/chopper) and different length cutoffs.
- You are doing shotgun metagenomics or metatranscriptomics QC — use a shotgun-metagenomics QC sketch (fastp + host removal) rather than this amplicon-specific recipe.
- You need primer removal by sequence (e.g. cutadapt with primer pairs) — this subworkflow only trims by quality and length; primer clipping must be done upstream or added separately.
- You need full amplicon analysis end-to-end (ASV inference, taxonomy) — this sketch only covers the QC stage.

## Analysis outline
1. **Initial FastQC** on raw single-end reads to characterise input quality.
2. **Trimmomatic** (`SE` mode, Phred33) applying `SLIDINGWINDOW`, `LEADING`, `TRAILING`, and `MINLEN` operations to quality-trim reads.
3. **FastQC** on post-trimming reads.
4. **Filter FASTQ** (`fastq_filter`) to drop reads below a minimum length after trimming.
5. **FastQC** on post-length-filtering reads.
6. **PRINSEQ** ambiguity filter to drop reads whose percentage of `N` bases exceeds a threshold.
7. **FastQC** on post-ambiguity-filtering reads.
8. **Rename + MultiQC** aggregation of all four FastQC stages (initial / trimming / length_filtering / ambiguous_base_filtering) per sample via `tp_find_and_replace` tag rewrites.
9. **FASTQ → FASTA** conversion of cleaned reads, then **FASTA formatter** (60-column width) to emit the final per-sample FASTA collection.

## Key parameters
- `Trimmomatic SLIDINGWINDOW required_quality`: **15** (default)
- `Trimmomatic SLIDINGWINDOW window_size`: **4** (default)
- `Trimmomatic LEADING`: **3** (default)
- `Trimmomatic TRAILING`: **3** (default)
- `Trimmomatic MINLEN`: **100** (default)
- `Trimmomatic quality_score`: `-phred33` (hard-coded; switch only if reads are genuinely Phred64)
- `Trimmomatic illuminaclip`: disabled (no adapter file supplied — pre-clip adapters/primers upstream if needed)
- `Filter FASTQ min_size`: **100** (default; must match or exceed Trimmomatic MINLEN)
- `PRINSEQ N_percentage threshold`: **10** (max % of N bases tolerated per read)
- `FastQC kmers`: 7; all other FastQC knobs at defaults
- `FASTA formatter width`: **60** columns
- Input collection type: `list` of single-end FASTQ (fastqsanger.gz)

## Test data
A one-element single-end collection containing `DRR010481.fastqsanger.gz` (a public amplicon run hosted on Zenodo at record 13710235) is passed in as the `Single-end reads` collection; all Trimmomatic / length / ambiguity parameters use the defaults above. Running the workflow is expected to produce (a) a `Single-end MultiQC statistics` tabular file matching the reference `general_stats_SE.tabular` on Zenodo record 14746033, (b) a `Single-end MultiQC report` HTML whose text contains per-stage sample tags `DRR010481_initial_reads`, `DRR010481_trimming`, `DRR010481_length_filtering`, and `DRR010481_ambiguous_base_filtering` along with expected read-count values (e.g. `84.0`, `553`, `242`, `48`, `47`), and (c) a `Single-end post quality control FASTA files` collection whose `DRR010481` element matches the reference `DRR010481_SE.fasta`. The test asserts on these MultiQC text markers and on exact equality of the FASTA output.

## Reference workflow
Galaxy IWC — `workflows/amplicon/amplicon-mgnify/mgnify-amplicon-pipeline-v5-quality-control-single-end`, release **0.3** (MGnify amplicon pipeline v5.0 — Quality control SE subworkflow, Apache-2.0, authored by MGnify/EMBL: Rand Zoabi, Paul Zierep). Tool versions pinned: Trimmomatic 0.39+galaxy2, FastQC 0.74+galaxy1, fastq_filter 1.1.5+galaxy2, PRINSEQ 0.20.4+galaxy2, fastqtofasta 1.1.5+galaxy2, fasta_formatter 1.0.1+galaxy2, MultiQC 1.27+galaxy3.
