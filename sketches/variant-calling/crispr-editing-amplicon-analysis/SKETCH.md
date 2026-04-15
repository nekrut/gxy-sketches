---
name: crispr-editing-amplicon-analysis
description: Use when you need to quantify CRISPR/Cas9 genome-editing outcomes (indels,
  HDR knock-ins, substitutions) from targeted amplicon sequencing of edited cell pools
  or clones. Runs CRISPResso on paired or single-end Illumina reads around a known
  sgRNA cut site to report editing efficiency and allele frequencies.
domain: variant-calling
organism_class:
- eukaryote
- vertebrate
input_data:
- short-reads-paired
- amplicon-fastq
- reference-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/crisprvar
  url: https://github.com/nf-core/crisprvar
  version: dev
  license: MIT
  slug: crisprvar
tools:
- name: crispresso
- name: fastqc
- name: multiqc
- name: nextflow
tags:
- crispr
- cas9
- genome-editing
- amplicon
- indel
- hdr
- editing-efficiency
test_data: []
expected_output: []
---

# CRISPR amplicon editing analysis

## When to use this sketch
- You have targeted amplicon sequencing (Illumina short reads, paired or single-end) spanning an sgRNA cut site in an edited cell population or clone.
- You need per-sample editing efficiency: fraction of reads with indels, substitutions, or HDR-mediated knock-in at the protospacer.
- You know the amplicon reference sequence and the sgRNA/protospacer sequence.
- You want a reproducible Nextflow pipeline that wraps CRISPResso with FastQC + MultiQC reporting.

## Do not use when
- You are calling germline or somatic variants genome-wide from WGS/WES — use a generic short-read variant-calling sketch instead.
- You are doing a pooled CRISPR screen with a guide library and need guide counts / enrichment — use a CRISPR-screen / MAGeCK-style sketch.
- You are looking for unbiased off-target discovery across the genome (GUIDE-seq, CIRCLE-seq, DISCOVER-seq) — this amplicon workflow only interrogates loci you pre-selected.
- Your reads are long-read (ONT/PacBio) amplicons — CRISPResso2 has a long-read mode, but this nf-core pipeline targets Illumina.

## Analysis outline
1. Stage paired-end (or `--singleEnd`) FASTQ files via the `--reads` glob pattern.
2. Run FastQC on raw reads for per-sample QC.
3. Run CRISPResso on each sample against the supplied amplicon reference (`--fasta` or an iGenomes `--genome` key) and sgRNA to quantify indels, substitutions, and HDR events around the predicted cut site.
4. Aggregate FastQC and pipeline metrics with MultiQC into a single HTML report.
5. Emit per-sample CRISPResso output folders plus the MultiQC summary under `results/`.

## Key parameters
- `--reads`: quoted glob for input FASTQs, e.g. `'data/*_R{1,2}.fastq.gz'`; must contain a `*` wildcard and `{1,2}` for paired-end.
- `--singleEnd`: set when inputs are single-end; cannot be mixed with paired-end in one run.
- `--genome` / `--fasta`: amplicon or host reference; `--genome` uses iGenomes keys (e.g. `GRCh37`, `GRCm38`), `--fasta` points at a local FASTA.
- `-profile`: choose compute/container stack — `docker`, `singularity`, `conda`, `awsbatch`, or `test` (self-contained test profile).
- `--outdir`: results directory (default `results`).
- `--max_memory`, `--max_cpus`, `--max_time`: caps for auto-resubmitted jobs (exit 143 triggers 2×/3× retry).
- AWS Batch only: `--awsqueue`, `--awsregion`, plus S3 `-w` and `--outdir`.

## Test data
The pipeline ships a `-profile test` configuration that pulls a small bundled FASTQ set and reference over the network, so no local inputs are required to smoke-test it. A representative invocation is `nextflow run nf-core/crisprvar -profile test,docker`, which stages a handful of amplicon FASTQs through FastQC, CRISPResso, and MultiQC. Expected outputs are a `results/fastqc/` directory with per-sample HTML+zip reports, CRISPResso per-sample result folders containing editing-efficiency tables and allele-frequency plots, and a `results/multiqc/Project_multiqc_report.html` aggregate report plus its `Project_multiqc_data/` directory.

## Reference workflow
nf-core/crisprvar (dev branch, https://github.com/nf-core/crisprvar), MIT-licensed Nextflow pipeline wrapping CRISPResso, FastQC, and MultiQC for CRISPR amplicon editing analysis.
