---
name: chip-seq-peak-calling-single-end
description: Use when you need to process single-end Illumina ChIP-seq FASTQ reads
  into narrow peak calls and coverage tracks against a standard reference genome (human,
  mouse, fly, worm). Covers adapter trimming, Bowtie2 alignment, MAPQ30 filtering,
  and MACS2 narrow peak calling with a fixed 200 bp fragment extension suitable for
  transcription factor or sharp histone marks like H3K4me3.
domain: epigenomics
organism_class:
- eukaryote
input_data:
- short-reads-single
- reference-genome-index
source:
  ecosystem: iwc
  workflow: 'ChIP-seq Analysis: Single-End Read Processing'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/epigenetics/chipseq-sr
  version: '1.1'
  license: MIT
tools:
- fastp
- bowtie2
- samtools
- macs2
- wig_to_bigwig
- multiqc
tags:
- chip-seq
- peak-calling
- narrow-peaks
- histone
- transcription-factor
- bowtie2
- macs2
- single-end
test_data:
- role: sr_fastq_input__wt_h3k4me3
  url: https://zenodo.org/record/1324070/files/wt_H3K4me3_read1.fastq.gz
  sha1: 60cef994485a6bddf9e2b7efca464efc34559c12
  filetype: fastqsanger.gz
expected_output:
- role: multiqc_webpage
  description: Content assertions for `MultiQC webpage`.
  assertions:
  - 'that: has_text'
  - 'text: wt_H3K4me3'
  - 'that: has_text'
  - 'text: <a href="#fastp" class="nav-l1">fastp</a>'
  - 'that: has_text'
  - 'text: <a href="#bowtie2" class="nav-l1">Bowtie 2 / HiSAT2</a>'
- role: multiqc_on_input_dataset_s_stats
  description: 'Content assertions for `MultiQC on input dataset(s): Stats`.'
  assertions:
  - "has_line: Sample\tmacs2-d\tmacs2-treatment_redundant_rate\tmacs2-peak_count\t\
    bowtie_2_hisat2-overall_alignment_rate\tfastp-after_filtering_q30_rate\tfastp-after_filtering_q30_bases\t\
    fastp-filtering_result_passed_filter_reads\tfastp-after_filtering_gc_content\t\
    fastp-pct_surviving\tfastp-pct_adapter\tfastp-before_filtering_read1_mean_length"
  - 'has_text_matching: {''expression'': ''wt_H3K4me3\t200.0\t0.0\t9\t98.[0-9]*\t93.[0-9]*\t2.3[0-9]*\t0.049[0-9]*\t57.[0-9]*\t99.[0-9]*\t0.12[0-9]*\t51.0''}'
- role: filtered_bam
  description: Content assertions for `filtered BAM`.
  assertions:
  - 'wt_H3K4me3: has_size: {''value'': 2587182, ''delta'': 200000}'
- role: macs2_summits
  description: Content assertions for `MACS2 summits`.
  assertions:
  - 'wt_H3K4me3: has_n_lines: {''n'': 9}'
- role: macs2_peaks
  description: Content assertions for `MACS2 peaks`.
  assertions:
  - 'wt_H3K4me3: that: has_text'
  - 'wt_H3K4me3: text: # effective genome size = 1.87e+09'
  - 'wt_H3K4me3: that: has_text'
  - 'wt_H3K4me3: text: # d = 200'
  - 'wt_H3K4me3: that: has_text'
  - 'wt_H3K4me3: text: # tags after filtering in treatment: 44528'
- role: macs2_narrowpeak
  description: Content assertions for `MACS2 narrowPeak`.
  assertions:
  - 'wt_H3K4me3: has_n_lines: {''n'': 9}'
- role: macs2_report
  description: Content assertions for `MACS2 report`.
  assertions:
  - 'wt_H3K4me3: that: has_text'
  - 'wt_H3K4me3: text: # effective genome size = 1.87e+09'
  - 'wt_H3K4me3: that: has_text'
  - 'wt_H3K4me3: text: # d = 200'
  - 'wt_H3K4me3: that: has_text'
  - 'wt_H3K4me3: text: # tags after filtering in treatment: 44528'
- role: coverage_from_macs2
  description: Content assertions for `coverage from MACS2`.
  assertions:
  - 'wt_H3K4me3: has_size: {''value'': 563563, ''delta'': 10000}'
- role: mapping_stats
  description: Content assertions for `mapping stats`.
  assertions:
  - 'wt_H3K4me3: that: has_text'
  - 'wt_H3K4me3: text: 49813 reads; of these:'
  - 'wt_H3K4me3: that: has_text'
  - 'wt_H3K4me3: text: 44357 (89.05%) aligned exactly 1 time'
  - 'wt_H3K4me3: that: has_text'
  - 'wt_H3K4me3: text: 98.27% overall alignment rate'
---

# ChIP-seq peak calling (single-end reads)

## When to use this sketch
- User has single-end Illumina ChIP-seq FASTQ files (one file per sample) and wants peaks, coverage tracks, and QC.
- Target is a standard reference genome with a prebuilt Bowtie2 index (e.g. hg38, mm10, dm6, ce11).
- The signal is narrow/punctate: transcription factor binding or sharp histone marks such as H3K4me3, H3K27ac, H3K9ac.
- No matched input/IgG control is available, or the user is fine running MACS2 without a control track.
- A fixed fragment extension of ~200 bp is appropriate (typical sonicated ChIP library).

## Do not use when
- Reads are paired-end — use a paired-end ChIP-seq sketch instead.
- Signal is broad (H3K27me3, H3K9me3, H3K36me3) and MACS2 `--broad` mode is required.
- The experiment is ATAC-seq, CUT&RUN, or CUT&Tag — those need different trimming, shift, and peak-calling parameters.
- The user needs differential binding across conditions as the primary output (this sketch stops at per-sample peaks/bigwigs).
- PCR duplicate removal must happen before peak calling on the BAM itself; here duplicates are only filtered internally by MACS2 (`--keep-dup 1`).

## Analysis outline
1. Adapter and quality trimming of single-end FASTQ with **fastp** (phred30, drop reads <15 bp, drop reads with too many low-quality bases).
2. Align trimmed reads to the selected reference with **Bowtie2** using default/sensitive preset, saving mapping stats.
3. Filter the BAM to MAPQ ≥ 30 with **samtools filter** to retain confidently mapped reads.
4. Call narrow peaks with **MACS2 callpeak** on the filtered BAM using `--nomodel --extsize 200`, producing narrowPeak, summits, and a treatment pileup bedGraph.
5. Convert the MACS2 treatment pileup bedGraph to **bigWig** with `wigToBigWig` for genome-browser visualization.
6. Extract a compact MACS2 summary (header lines of the peaks xls) with a grep step.
7. Aggregate fastp, Bowtie2, and MACS2 logs into a **MultiQC** HTML + stats report.

## Key parameters
- fastp: `qualified_quality_phred: 30`, `unqualified_percent_limit: <user>` (default 70; ~85 for 100 bp reads, ~70 for 50 bp), `length_required: 15`, adapter sequence optional (auto-detect or explicit TruSeq/Nextera).
- Bowtie2: single-end, indexed reference, default sensitive preset, mapping stats saved.
- samtools filter: `mapq: 30`, output BAM, header kept.
- MACS2 callpeak: `--format BAM`, `--nomodel`, `--extsize 200`, `--shift 0`, `--qvalue 0.05`, `--keep-dup 1`, `--call-summits`, `--gsize <effective genome size>` (hs 2.7e9, mm 1.87e9, dm 1.2e8, ce 9e7), `--spmr` toggled by the `Normalize profile` boolean to emit Signal-per-Million-Reads bedGraph.
- No control (input) track is supplied; lambda is estimated from the treatment itself.
- bedGraph→bigWig conversion uses preset settings.

## Test data
The source test profile runs a single mouse H3K4me3 sample (`wt_H3K4me3_read1.fastq.gz` from Zenodo record 1324070) against the `mm10` Bowtie2 index with `Effective genome size: 1870000000`, TruSeq adapter `GATCGGAAGAGCACACGTCTGAACTCCAGTCAC`, `Percentage of bad quality bases per read: 70`, and `Normalize profile: true`. The expected results assert: Bowtie2 reports 49,813 input reads with 44,357 (89.05%) uniquely mapped and a 98.27% overall alignment rate; the MAPQ30-filtered BAM is ~2.59 MB; MACS2 produces exactly 9 narrowPeak entries and 9 summits with header lines `# effective genome size = 1.87e+09`, `# d = 200`, and `# tags after filtering in treatment: 44528`; the MACS2 bigWig coverage track is ~564 KB; and the MultiQC stats table contains per-sample fastp, Bowtie2, and MACS2 columns for `wt_H3K4me3`.

## Reference workflow
Galaxy IWC `workflows/epigenetics/chipseq-sr` — *ChIP-seq Analysis: Single-End Read Processing*, release 1.1 (2026-04-06), MIT, authored by Lucille Delisle. Tool versions: fastp 1.3.1, Bowtie2 2.5.5, samtool_filter2 1.8, MACS2 2.2.9.1, MultiQC 1.33.
