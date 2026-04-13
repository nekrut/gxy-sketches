---
name: bisulfite-methylation-bismark
description: Use when you need to quantify DNA cytosine methylation (5mC) from whole-genome
  or reduced-representation bisulfite sequencing (WGBS/RRBS/EM-seq/PBAT) Illumina
  short reads against a reference genome, producing per-cytosine methylation calls
  and coverage. Default workflow uses Bismark + Bowtie2 with Trim Galore preprocessing.
domain: epigenomics
organism_class:
- eukaryote
- vertebrate
- bacterial
input_data:
- short-reads-paired
- short-reads-single
- reference-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/methylseq
  url: https://github.com/nf-core/methylseq
  version: 4.2.0
  license: MIT
tools:
- fastqc
- trim-galore
- bismark
- bowtie2
- samtools
- qualimap
- preseq
- multiqc
tags:
- methylation
- bisulfite
- wgbs
- rrbs
- em-seq
- pbat
- 5mc
- cpg
- epigenetics
test_data: []
expected_output: []
---

# Bisulfite methylation calling (Bismark)

## When to use this sketch
- You have Illumina bisulfite-converted short reads (WGBS, RRBS, EM-seq, PBAT, single-cell BS, NOMe-seq) and want per-cytosine methylation calls.
- You need CpG (and optionally CHG/CHH) methylation coverage files, bedGraphs, and M-bias QC against a reference genome.
- You want a turnkey pipeline that handles adapter trimming, three-letter alignment, deduplication, methylation extraction, and QC aggregation.
- You are working with a library prep kit that needs preset hard-clipping (Accel, Zymo, EM-seq, single-cell, PBAT) — the pipeline has ready-made flags.
- Optional targeted (hybrid-capture) methylation panels where you want bedGraphs filtered to a BED of target regions and Picard CollectHsMetrics.

## Do not use when
- Your data is TAPS (TET-assisted pyridine borane) or otherwise preserves the original base — use a `taps-methylation-bwamem` sibling sketch that runs BWA-MEM + rastair instead (`--aligner bwamem` or `--taps`).
- You want GPU-accelerated bwa-meth via Parabricks fq2bammeth — use a `bisulfite-methylation-bwameth` sibling sketch (`--aligner bwameth`, optionally `-profile gpu` / `--use_mem2`).
- You need differential methylation region (DMR) calling or downstream statistical modeling — this pipeline stops at per-cytosine calls; hand off to methylKit, DSS, or bsseq.
- You have Oxford Nanopore / PacBio long-read methylation (5mC/5hmC) from basecaller mod tags — use a long-read modification sketch.
- You want variant calling from BS-seq data — out of scope.

## Analysis outline
1. Parse samplesheet CSV (`sample,fastq_1,fastq_2,genome`) and concatenate re-sequenced lanes per sample (`cat`).
2. Raw read QC with FastQC.
3. Adapter and quality trimming with Trim Galore, applying any library-type preset (`--pbat`, `--em_seq`, `--rrbs`, `--single_cell`, `--accel`, `--zymo`).
4. Build or reuse a Bismark three-letter genome index from `--fasta` (cached if `--bismark_index` supplied).
5. Align trimmed reads with Bismark (Bowtie2 by default, or HISAT2 with `--aligner bismark_hisat` for splice-aware / SLAM-seq).
6. Deduplicate alignments with `bismark deduplicate` (auto-skipped for RRBS).
7. Extract per-cytosine methylation calls with `bismark_methylation_extractor`, producing context-split call files, bedGraph, and `.bismark.cov.gz` coverage.
8. Optionally run `coverage2cytosine` for stranded CpG reports (`--cytosine_report`) or NOMe-seq (`--nomeseq`).
9. Generate per-sample Bismark HTML report and run-wide Bismark summary.
10. Optional alignment QC: Qualimap BamQC (`--run_qualimap`) and library-complexity estimation with Preseq (`--run_preseq`).
11. Optional targeted analysis: filter bedGraphs to `--target_regions_file` and run Picard CollectHsMetrics (`--run_targeted_sequencing --collecthsmetrics`).
12. Aggregate all QC and reports with MultiQC.

## Key parameters
- `--input samplesheet.csv` — CSV with columns `sample,fastq_1,fastq_2,genome`; rows with identical `sample` are concatenated.
- `--outdir <dir>` — required results directory.
- `--aligner bismark` (default) or `bismark_hisat` — keep Bismark for this sketch; avoid `bwameth`/`bwamem`.
- `--genome GRCh38` (iGenomes) OR `--fasta genome.fa[.gz]` (+ optional `--bismark_index`).
- Library presets (pick at most one): `--pbat`, `--em_seq`, `--rrbs`, `--single_cell`, `--accel`, `--zymo`, `--slamseq` (needs `bismark_hisat`).
- Directionality: `--non_directional` for non-directional libraries (auto-set by `--single_cell`/`--zymo`).
- Trim overrides: `--clip_r1`, `--clip_r2`, `--three_prime_clip_r1`, `--three_prime_clip_r2`, `--nextseq_trim`, or `--skip_trimming_presets` to decouple presets from the aligner mode.
- Methylation extraction: `--comprehensive` (merge strands per context), `--cytosine_report` (stranded CX report), `--meth_cutoff N` (min coverage for a call), `--ignore_r2 2` (default, mitigate Read2 end-repair bias), `--no_overlap true` (default, avoid double-counting PE overlaps), `--all_contexts` to emit CHG/CHH in addition to CpG.
- Alignment tuning: `--relax_mismatches` with `--num_mismatches 0.6`, `--local_alignment`, `--minins`/`--maxins` for PE insert bounds, `--unmapped` to dump unaligned reads.
- Targeted mode: `--run_targeted_sequencing --target_regions_file targets.bed [--collecthsmetrics]`.
- QC toggles: `--run_qualimap`, `--run_preseq`, `--skip_fastqc`, `--skip_multiqc`, `--skip_deduplication` (forced true for `--rrbs`).
- Runtime: `-profile docker|singularity|podman|conda|test`, `-params-file params.yaml`, `-resume`.

## Test data
The bundled `test` profile (`conf/test.config`) points at the nf-core test-datasets methylseq branch and uses a tiny reference FASTA (`reference/genome.fa.gz` + `.fai`) together with the pipeline's `assets/samplesheet.csv`. That samplesheet mixes single-end *SRR389222* sub-sampled human bisulfite reads (`SRR389222_sub1/sub2/sub3.fastq.gz`, all sharing one `sample` ID so they are concatenated) with a paired-end `Ecoli_10K_methylated` sample. A successful run produces a Bismark index, trimmed FASTQs, deduplicated BAMs, per-sample `*.bismark.cov.gz`, bedGraph and context-split methylation call files under `bismark/methylation_calls/`, per-sample + summary Bismark HTML reports, and an aggregated `multiqc/bismark/multiqc_report.html`. The full-size AWS test (`test_full`) swaps in `samplesheet_full.csv` against `--genome GRCh38` and is the reference for real-world resource scaling.

## Reference workflow
nf-core/methylseq v4.2.0 — https://github.com/nf-core/methylseq (MIT). Default pipeline: FastQC → Trim Galore → Bismark (Bowtie2) → Bismark deduplicate → `bismark_methylation_extractor` → Bismark report/summary → MultiQC, with optional Qualimap, Preseq, and targeted-sequencing subworkflows.
