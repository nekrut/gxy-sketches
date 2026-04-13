---
name: deep-mutational-scanning-shotgun
description: Use when analyzing shotgun (random fragmentation) short-read paired-end
  sequencing data from a deep mutational scanning (DMS) experiment on a long open
  reading frame, to align reads, count amino acid/nucleotide variants, run DMS library
  QC, and estimate per-variant fitness scores from matched input/output samples.
domain: other
organism_class:
- eukaryote
- other
input_data:
- short-reads-paired
- reference-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/deepmutscan
  url: https://github.com/nf-core/deepmutscan
  version: dev
  license: MIT
tools:
- bwa-mem
- samtools
- vsearch
- gatk-AnalyzeSaturationMutagenesis
- fastqc
- multiqc
- dimsum
- mutscan
tags:
- deep-mutational-scanning
- dms
- shotgun-sequencing
- saturation-mutagenesis
- fitness
- variant-counting
- orf
- protein-engineering
test_data: []
expected_output: []
---

# Shotgun Deep Mutational Scanning (DMS) on long ORFs

## When to use this sketch
- The experiment is a deep mutational scanning / site-saturation mutagenesis screen on a single long open reading frame (ORF), where a mutant library has been subjected to selection and sequenced.
- Sequencing was done by random fragmentation / tagmentation ("shotgun") with paired-end short reads (typically 150 bp PE Illumina), NOT variant-specific barcodes.
- The user has matched `input` (pre-selection) and `output` (post-selection) FASTQ pairs, usually in replicates, and wants per-variant counts and/or fitness scores.
- The mutagenesis design uses a known degenerate codon scheme (NNK, NNS, NNH, NNN, combinations, or a user-defined custom codon library).
- The user needs DMS-specific QC: per-position mutation recovery, coverage evenness along the ORF, amino-acid-level count heatmaps, and library saturation curves.
- Exact codon coordinates of the ORF within the supplied reference FASTA are known (`start-stop`, 1-based, inclusive of stop codon).

## Do not use when
- The DMS library was sequenced via variant-specific barcodes or amplicon sequencing of the full variant region — use a barcode-based DMS or amplicon-counting workflow instead (e.g. Enrich2/mutscan standalone on amplicons).
- You are calling clinical or population variants against a genomic reference — use a conventional germline or somatic variant-calling sketch.
- The input is single-cell, bulk RNA-seq for expression, metagenomic, long-read, or ChIP-seq data — pick the matching domain sketch.
- You only have a single condition with no paired input/output selection — you can still run alignment, counting and library QC, but fitness estimation is not meaningful; skip `--fitness`/`--dimsum`/`--mutscan`.
- The target is a short region amenable to a single amplicon — simpler DMS tools (DiMSum, mutscan) can be run directly without shotgun preprocessing.

## Analysis outline
1. Raw read QC with FastQC and MultiQC aggregation across all samples.
2. Align paired-end reads to the reference ORF FASTA with `bwa mem` (index built on the fly).
3. Filter out exact-wildtype and indel-containing alignments with `samtools view` (shotgun reads outside the mutated region are indistinguishable from true WT and must be dropped).
4. Merge overlapping read pairs into high-quality consensus molecules with `vsearch --fastq_mergepairs`, then re-align the merged reads with `bwa mem` to reduce per-base error.
5. Count single, double, and higher-order nucleotide variants against the reference ORF with GATK `AnalyzeSaturationMutagenesis`, using the `--reading_frame start-stop` codon coordinates.
6. DMS library QC: compute per-position mutation efficiency, amino-acid recovery, rolling coverage, count-vs-coverage heatmaps, and (optionally) a rarefaction/sequencing-depth saturation curve via `--run_seqdepth`.
7. Merge per-sample count tables across replicates and input/output groups into `counts_merged.tsv` and build an experimental design file for fitness estimation.
8. Estimate variant fitness as log(output/input) normalised to synonymous-wildtype codons (default module), and/or hand off to DiMSum or mutscan when `--dimsum` / `--mutscan` are enabled.

## Key parameters
- `--input` samplesheet CSV with columns `sample,type,replicate,file1,file2`; `type` must be `input` or `output`, and replicates must be integers. One row per paired FASTQ pair.
- `--fasta` reference FASTA containing (at minimum) the ORF of interest.
- `--reading_frame` exact 1-based codon coordinates of the ORF inside the FASTA, in the form `start-stop` (e.g. `352-1383`). Must include the stop codon and be divisible into whole codons.
- `--mutagenesis_type` degenerate codon scheme used in library construction: one of `nnk` (default), `nns`, `nnh`, `nnn`, `nnk_nns`, `nnk_nns_nnh`, or `custom`. With `custom`, also pass `--custom_codon_library` pointing to a CSV of allowed codons (global or per-position).
- `--min_counts` minimum per-variant count threshold; variants below are zeroed out (default `10`, lower it for small test/toy datasets).
- `--aimed_cov` target coverage used as a reference line in QC plots (default `100`).
- `--sliding_window_size` window size for rolling-coverage and rolling-count QC plots (default `10`).
- `--fitness` enable the built-in fitness estimation and the preparatory count-merging / design-file generation step. Required for any downstream fitness output.
- `--dimsum` enable the DiMSum fitness module (AMD/x86_64 only) in addition to the default fitness estimator.
- `--mutscan` enable the mutscan-based fitness estimator.
- `--run_seqdepth` enable the rarefaction-based sequencing saturation module (computationally expensive; off by default).
- Runtime: always pass `-profile` with a container engine (`docker`, `singularity`, `apptainer`, `podman`, or `conda`) plus any institutional profile; `-profile test` runs a minimal built-in dataset end to end.

## Test data
The bundled `test` profile points at a small GID1A deep mutational scanning dataset hosted under `nf-core/test-datasets/deepmutscan/`: a samplesheet `samplesheet/GID1A_test.csv` that lists paired-end input and output FASTQs for the human GID1A ORF, together with the reference `testdata/GID1A.fasta`. The ORF coordinates are provided as `--reading_frame 352-1383` and the test profile relaxes `min_counts` to `2`, uses the combined `nnk_nns` mutagenesis scheme, and turns on `run_seqdepth` and `fitness`. A successful run produces per-sample BAM files under `intermediate_files/bam_files/`, GATK `AnalyzeSaturationMutagenesis` variant count tables in `intermediate_files/gatk/`, DMS QC PDFs (`counts_heatmap.pdf`, `rolling_coverage.pdf`, `SeqDepth.pdf`, etc.) under `library_QC/`, a merged `fitness/counts_merged.tsv`, `fitness/default_results/fitness_estimation.tsv` with fitness and error estimates, replicate/fitness correlation plots, the standard `fastqc/` and `multiqc/` reports, and the Nextflow `timeline.html` / `report.html` execution traces.

## Reference workflow
nf-core/deepmutscan (dev), https://github.com/nf-core/deepmutscan — shotgun-sequencing DMS processing pipeline by Wehnert & Stammnitz (CRG Barcelona); Nextflow DSL2, MIT licensed. Core tools: bwa-mem, samtools, vsearch, GATK AnalyzeSaturationMutagenesis, FastQC, MultiQC, with optional DiMSum / mutscan fitness modules.
