---
name: iclip-rbp-crosslink-peak-calling
description: Use when you need to analyze CLIP/iCLIP sequencing data to map single-nucleotide
  RNA-protein crosslink sites and call binding peaks for an RNA-binding protein from
  single-end UMI-barcoded short reads against a reference genome (human, mouse, fly,
  yeast, etc.).
domain: rna-seq
organism_class:
- eukaryote
input_data:
- short-reads-single
- reference-fasta
- gtf-annotation
source:
  ecosystem: nf-core
  workflow: nf-core/clipseq
  url: https://github.com/nf-core/clipseq
  version: 1.0.0
  license: MIT
  slug: clipseq
tools:
- name: cutadapt
- name: umi_tools
- name: bowtie2
- name: star
- name: samtools
- name: bedtools
- name: icount
- name: paraclu
- name: pureclip
- name: piranha
- name: dreme
- name: rseqc
- name: preseq
- name: multiqc
tags:
- clip
- iclip
- rbp
- rna-protein
- crosslink
- peak-calling
- umi
test_data: []
expected_output: []
---

# iCLIP / CLIP-seq crosslink and peak calling

## When to use this sketch
- You have single-end FASTQ files from a CLIP-family protocol (iCLIP, iCLIP2, eCLIP-like) where reads carry UMIs and the 5' end of the read marks the RNA-protein crosslink position.
- Goal is to identify single-nucleotide crosslink sites for an RNA-binding protein (RBP) and call binding peaks on a reference genome with annotation.
- Organism has an available genome FASTA (+ optional GTF) and optionally a small-RNA (rRNA/tRNA) premapping reference; supported out-of-the-box for human, mouse, rat, zebrafish, fruitfly, yeast.
- You want CLIP-aware QC (library complexity, crosslink distribution over gene features, peak-caller comparison) and optional de novo motif discovery around crosslink sites.

## Do not use when
- Data is standard mRNA-seq for expression / differential expression (use a bulk RNA-seq sketch instead).
- Data is paired-end eCLIP with size-matched input controls requiring IP-vs-input peak calling — this pipeline does not model paired input controls and only supports single-end input.
- You are doing m6A / MeRIP-seq, RIP-seq without UMIs, Ribo-seq, or CLASH — the crosslink-at-read-start model does not apply.
- You need differential binding between conditions (this sketch stops at per-sample peaks and QC).
- You only have a transcriptome FASTA and need transcript-level quantification.

## Analysis outline
1. Raw-read QC with FastQC.
2. Optional UMI extraction from the 5' of the read into the read name (UMI-tools extract), if not already done at demultiplexing.
3. Adapter and quality trimming with Cutadapt (default Illumina adapter `AGATCGGAAGAGC`, min length 12 nt).
4. Premap to rRNA/tRNA small-RNA reference with Bowtie 2; keep unmapped reads for genome alignment.
5. Splice-aware genome alignment with STAR, disabling 5' soft-clipping to preserve crosslink position.
6. UMI-aware PCR deduplication with UMI-tools `dedup` (directional method).
7. Extract single-nucleotide crosslink positions (read 5' end − 1) with BEDTools, emit stranded BED and BEDGRAPH tracks.
8. Peak calling with one or more of iCount, Paraclu, PureCLIP, Piranha (selected via `--peakcaller`).
9. Optional de novo motif discovery around crosslink sites with DREME (default ±20 nt window, sample 1000 peaks).
10. CLIP-specific QC: Preseq library complexity, RSeQC read distribution over gene features, custom `clipqc` metrics, aggregated into a MultiQC report.

## Key parameters
- `--input`: CSV design with columns `sample,fastq` (single-end only, `.fastq.gz` / `.fq.gz`).
- `--fasta` (+ optional `--gtf`, `--star_index`, `--fai`) or `--genome` for iGenomes (e.g. `GRCh38`, `GRCm38`, `BDGP6`, `R64-1-1`).
- `--smrna_org {human|mouse|rat|zebrafish|fruitfly|yeast}` or `--smrna_fasta` to drive rRNA/tRNA premapping.
- `--adapter` (default `AGATCGGAAGAGC`).
- `--move_umi` e.g. `NNNNNNNNN` to extract a 9 nt UMI from the read start; `--umi_separator` (default `:`, use `_` when UMI is appended with underscore); `--deduplicate true`.
- `--peakcaller` any comma-separated subset of `icount,paraclu,pureclip,piranha` or `all` (peak calling is OFF unless set).
- iCount: `--half_window 3`, `--merge_window 3`, optional `--segment` file.
- Paraclu: `--min_value 10`, `--min_density_increase 2`, `--max_cluster_length 200`.
- PureCLIP: `--pureclip_bc 0` (protein binding characteristic), `--pureclip_dm 8` (merge distance), `--pureclip_iv all` (or e.g. `chr1;chr2` to restrict HMM training).
- Piranha: `--bin_size_both 3`, `--cluster_dist 3`.
- Motif: `--motif true`, `--motif_sample 1000`.

## Test data
The bundled `test` profile runs from a minimal nf-core/test-datasets CLIP-seq metadata CSV of single-end FASTQ samples, a gzipped human chromosome 20 reference FASTA (`chr20.fa.gz`), and `smrna_org = human` to drive rRNA/tRNA premapping; resources are capped to 2 CPUs / 6 GB so it runs on CI. Running the pipeline end-to-end is expected to produce per-sample trimmed FASTQs, premap and STAR BAMs, UMI-deduplicated BAMs, single-nucleotide crosslink BED/BEDGRAPH tracks under `xlinks/`, a `clipqc/` TSV summary, Preseq and RSeQC outputs, and a consolidated `multiqc/multiqc_report.html`; peak-calling and motif outputs only appear when `--peakcaller` (and `--motif`) are set, as in the `test_full` profile which additionally enables `peakcaller = icount,paraclu,pureclip,piranha` and `motif = true` against GRCh38.

## Reference workflow
nf-core/clipseq v1.0.0 (https://github.com/nf-core/clipseq), DOI 10.5281/zenodo.4723016.
