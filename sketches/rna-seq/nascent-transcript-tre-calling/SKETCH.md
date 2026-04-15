---
name: nascent-transcript-tre-calling
description: Use when you need to process nascent-transcript or transcriptional start
  site (TSS) sequencing data (GRO-seq, PRO-seq, GRO-cap, PRO-cap, CoPRO, CAGE, NETCAGE,
  RAMPAGE, csRNA-seq, STRIPE-seq) from short-read FASTQ to aligned BAMs, strand-specific
  coverage tracks, de novo transcript / TRE calls, and gene + nascent-transcript read
  counts against a reference genome with a GTF.
domain: rna-seq
organism_class:
- vertebrate
- eukaryote
input_data:
- short-reads-paired
- short-reads-single
- reference-fasta
- gtf-annotation
source:
  ecosystem: nf-core
  workflow: nf-core/nascent
  url: https://github.com/nf-core/nascent
  version: 2.3.0
  license: MIT
  slug: nascent
tools:
- name: fastqc
  version: 0.12.1
- name: fastp
  version: 0.23.4
- name: bwa
- name: bwa-mem2
- name: dragmap
- name: bowtie2
- name: hisat2
- name: samtools
- name: umi-tools
- name: picard
- name: rseqc
- name: preseq
- name: bbmap
- name: bedtools
- name: deeptools
- name: homer
- name: grohmm
- name: pints
- name: featurecounts
  version: 2.0.1
- name: multiqc
  version: '1.27'
tags:
- nascent
- gro-seq
- pro-seq
- gro-cap
- pro-cap
- tss
- tre
- enhancer-rna
- run-on
- transcript-identification
test_data: []
expected_output: []
---

# Nascent transcript and TRE calling from run-on / TSS assays

## When to use this sketch
- Input is short-read FASTQ from a nascent-transcription or TSS assay: GRO-seq, PRO-seq, GRO-cap, PRO-cap, CoPRO, CAGE, NETCAGE, RAMPAGE, csRNA-seq, or STRIPE-seq.
- You want the full path from raw reads to strand-specific bedGraph/bigWig coverage, de novo transcript / transcriptional regulatory element (TRE) calls, and per-gene + per-nascent-transcript counts.
- You have (or can point at via iGenomes) a reference FASTA plus a GTF/GFF for a eukaryotic genome (human, mouse, fly, etc.).
- You care about identifying unannotated transcription units, divergent/bidirectional eRNAs, or promoter-proximal TSS peaks — not just measuring steady-state mRNA abundance.
- You optionally want UMI-based deduplication (`--with_umi`) for PRO-seq style libraries.

## Do not use when
- The library is standard poly-A / total RNA-seq measuring mature mRNA abundance — use a conventional `rna-seq` sketch (nf-core/rnaseq) instead; nascent-transcript tooling (groHMM, PINTS, HOMER GRO-seq) will misinterpret those reads.
- You are doing single-cell RNA-seq, small RNA / miRNA profiling, or ribosome profiling — different sketches apply.
- You only need variant calling or structural variants from the aligned BAM — use a variant-calling sketch.
- Your reads are long-read (ONT/PacBio) — nf-core/nascent targets short-read Illumina.
- You are calling ChIP-seq / ATAC-seq peaks on DNA-binding or accessibility data — use the appropriate epigenomics sketch; HOMER/PINTS here are configured for nascent RNA, not ChIP peaks.

## Analysis outline
1. Read QC on raw FASTQ with **FastQC**.
2. Adapter and quality trimming with **fastp** (skippable via `--skip_trimming`).
3. Align trimmed reads to the reference FASTA with the chosen aligner: **bwa** (default), **bwa-mem2**, **DRAGMAP**, **Bowtie 2**, **HISAT2**, or **STAR** (selected by `--aligner`).
4. Coordinate-sort and index BAMs with **samtools**; emit flagstat/idxstats/stats.
5. If `--with_umi` is set, deduplicate by UMI with **UMI-tools dedup**; otherwise mark PCR duplicates with **picard MarkDuplicates**.
6. Post-alignment QC: **RSeQC** modules (bam_stat, infer_experiment, read_distribution, etc.), **Preseq** library-complexity curves, and **BBMap pileup** for per-chromosome coverage.
7. Build strand-specific coverage: **bedtools genomecov** bedGraphs (plus/minus/dreg) and **deepTools bamCoverage** bigWigs.
8. De novo transcript / TRE identification driven by `--assay_type`:
   - **PINTS** for all supported assays (default); scatter-gathered per chromosome, emits unidirectional, divergent, and bidirectional peak BEDs.
   - **HOMER findPeaks -style groseq** when `assay_type = GROseq`, with optional uniqmap for repetitive regions.
   - **groHMM** (GRO-seq / PRO-seq) with a tuning sweep over `UTS` x `LtProbB` to pick hold-out parameters, then transcript calling and repair.
9. Optional **BEDTools intersect** filtering of called transcripts/TREs against `--filter_bed` (regions to exclude, e.g. promoters) and `--intersect_bed` (regions to require, e.g. H3K27ac/H3K4me1).
10. Quantify reads over both annotated genes and predicted nascent transcripts with **featureCounts**.
11. Aggregate all QC, alignment, dedup, coverage, and transcript-identification metrics into a single **MultiQC** report.

## Key parameters
- `input`: CSV samplesheet with columns `sample,fastq_1,fastq_2`; rows sharing a `sample` name are concatenated across lanes.
- `outdir`: absolute output directory.
- `assay_type` (required): one of `CoPRO`, `GROcap`, `PROcap`, `CAGE`, `NETCAGE`, `RAMPAGE`, `csRNAseq`, `STRIPEseq`, `PROseq`, `GROseq`, or the `R_5` / `R_3` / `R1_5` / `R1_3` / `R2_5` / `R2_3` read-end variants — drives PINTS and enables HOMER GRO-seq when set to `GROseq`.
- `aligner`: `bwa` (default), `bwamem2`, `dragmap`, `bowtie2`, `hisat2`, or `star`.
- Reference: either `--genome <iGenomes ID>` (e.g. `GRCh38`, `hg38`, `mm10`) or an explicit `--fasta` plus `--gtf`/`--gff`; optional prebuilt `--bwa_index` / `--bwamem2_index` / `--dragmap` / `--bowtie2_index` / `--hisat2_index` / `--star_index`, and `--save_reference` to persist generated indices.
- UMI handling: `--with_umi` to enable UMI-tools dedup; `--umitools_dedup_stats` for extra stats.
- Trimming / alignment skips: `--skip_trimming`, `--skip_alignment`.
- groHMM tuning grid: `--grohmm_min_uts` (default 5), `--grohmm_max_uts` (default 45), `--grohmm_min_ltprobb` (default -100), `--grohmm_max_ltprobb` (default -400); set min=max on both to pin a single `(UTS, LtProbB)` pair. `--skip_grohmm` turns the whole groHMM branch off (often needed when memory is constrained).
- HOMER: `--use_homer_uniqmap` to enable uniqmap-aware calling; `--homer_uniqmap` for a custom uniqmap file/URL. HOMER peak-caller knobs (`-tssFold`, `-bodyFold`, `-minBodySize`, `-maxBodySize`) are tunable via `withName: HOMER_FINDPEAKS { ext.args = ... }`.
- TRE post-filtering: `--filter_bed` (regions transcripts must NOT overlap, e.g. promoters) and `--intersect_bed` (regions transcripts MUST overlap, e.g. enhancer histone marks or known TREs).

## Test data
The bundled `test` profile runs a minimal human GRO-seq-style dataset: a samplesheet from `assets/samplesheet.csv` pointing at downsampled FASTQs, aligned against a chromosome-21-only GRCh38 reference (`GRCh38_chr21.fa` + `genes_chr21.gtf`) with a prebuilt HISAT2 index tarball, all hosted under the `nf-core/test-datasets` `nascent` branch. `assay_type` is set to `GROseq`, groHMM is skipped for memory reasons, the groHMM tuning grid is shrunk to `UTS 5–10` x `LtProbB -100…-150`, and `filter_bed` / `intersect_bed` are pulled from `tests/config/unwanted_region.bed` and `tests/config/wanted_region.bed`. A successful run should produce trimmed FASTQs, sorted+indexed BAMs, strand-split bedGraph and bigWig coverage, PINTS `*_divergent_peaks.bed` / `*_bidirectional_peaks.bed` / `*_unidirectional_peaks.bed`, HOMER `*.peaks.txt` and `*.bed`, featureCounts tables under `quantification/featurecounts/gene/` and `quantification/featurecounts/nascent/`, and a consolidated `multiqc/multiqc_report.html`. The `test_full` profile swaps in the full `hg38` iGenomes reference and a larger GRO-seq samplesheet (`assets/samplesheet_full.csv`) for AWS CI.

## Reference workflow
nf-core/nascent v2.3.0 — https://github.com/nf-core/nascent (DOI 10.5281/zenodo.7245273, MIT). Based on the pipeline schema (`nextflow_schema.json`), `docs/usage.md`, `docs/output.md`, and `conf/test.config` / `conf/test_full.config` at that release.
