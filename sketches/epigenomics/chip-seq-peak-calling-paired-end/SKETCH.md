---
name: chip-seq-peak-calling-paired-end
description: Use when you need to process paired-end Illumina ChIP-seq FASTQ data
  through adapter trimming, genome alignment, stringent BAM filtering, and narrow
  peak calling to identify transcription factor or histone mark (e.g. H3K4me3) binding
  sites against an indexed reference genome. Produces filtered BAM, MACS2 narrowPeak/summits,
  bigWig coverage, and a MultiQC report.
domain: epigenomics
organism_class:
- eukaryote
input_data:
- short-reads-paired
- reference-genome-index
source:
  ecosystem: iwc
  workflow: 'ChIP-seq Analysis: Paired-End Read Processing'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/epigenetics/chipseq-pe
  version: '1.1'
  license: MIT
tools:
- fastp
- bowtie2
- samtools
- macs2
- ucsc-wigToBigWig
- multiqc
tags:
- chip-seq
- epigenomics
- peak-calling
- histone-mark
- transcription-factor
- narrow-peaks
- paired-end
test_data:
- role: pe_fastq_input__wt_h3k4me3__forward
  url: https://zenodo.org/record/1324070/files/wt_H3K4me3_read1.fastq.gz
  sha1: 60cef994485a6bddf9e2b7efca464efc34559c12
  filetype: fastqsanger.gz
- role: pe_fastq_input__wt_h3k4me3__reverse
  url: https://zenodo.org/record/1324070/files/wt_H3K4me3_read2.fastq.gz
  sha1: beaa36e4cfd92910672d1c2948d6a94204dc9788
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
    fastp-pct_surviving\tfastp-pct_adapter\tfastp-before_filtering_read1_mean_length\t\
    fastp-before_filtering_read2_mean_length"
  - 'has_text_matching: {''expression'': ''wt_H3K4me3\t20[12].0\t0.0\t13\t98.[0-9]*\t93.[0-9]*\t4.5[0-9]*\t0.095[0-9]*\t57.[0-9]*\t95.[0-9]*\t0.19[0-9]*\t51.0\t51.0''}'
- role: filtered_bam
  description: Content assertions for `filtered BAM`.
  assertions:
  - 'wt_H3K4me3: has_size: {''value'': 5311841, ''delta'': 500000}'
- role: macs2_summits
  description: Content assertions for `MACS2 summits`.
  assertions:
  - 'wt_H3K4me3: has_n_lines: {''n'': 13}'
- role: macs2_peaks
  description: Content assertions for `MACS2 peaks`.
  assertions:
  - 'wt_H3K4me3: that: has_text'
  - 'wt_H3K4me3: text: # effective genome size = 1.87e+09'
  - 'wt_H3K4me3: that: has_text_matching'
  - 'wt_H3K4me3: expression: # fragment size is determined as 20[12] bps'
  - 'wt_H3K4me3: that: has_text'
  - 'wt_H3K4me3: text: # fragments after filtering in treatment: 42745'
- role: macs2_narrowpeak
  description: Content assertions for `MACS2 narrowPeak`.
  assertions:
  - 'wt_H3K4me3: has_n_lines: {''n'': 13}'
- role: macs2_report
  description: Content assertions for `MACS2 report`.
  assertions:
  - 'wt_H3K4me3: that: has_text'
  - 'wt_H3K4me3: text: # effective genome size = 1.87e+09'
  - 'wt_H3K4me3: that: has_text_matching'
  - 'wt_H3K4me3: expression: # fragment size is determined as 20[12] bps'
  - 'wt_H3K4me3: that: has_text'
  - 'wt_H3K4me3: text: # fragments after filtering in treatment: 42745'
- role: coverage_from_macs2
  description: Content assertions for `coverage from MACS2`.
  assertions:
  - 'wt_H3K4me3: has_size: {''value'': 568174, ''delta'': 50000}'
- role: mapping_stats
  description: Content assertions for `mapping stats`.
  assertions:
  - 'wt_H3K4me3: that: has_text'
  - 'wt_H3K4me3: text: 1344 (2.82%) aligned concordantly 0 times'
  - 'wt_H3K4me3: that: has_text'
  - 'wt_H3K4me3: text: 42961 (90.29%) aligned concordantly exactly 1 time'
  - 'wt_H3K4me3: that: has_text'
  - 'wt_H3K4me3: text: 3276 (6.89%) aligned concordantly >1 times'
---

# ChIP-seq peak calling (paired-end)

## When to use this sketch
- User has paired-end Illumina ChIP-seq FASTQ files (single treatment, typically no matched input control) and wants peak calls plus coverage tracks.
- Target is a sharp/narrow binding pattern: transcription factors or punctate histone marks like H3K4me3, H3K27ac, H3K9ac.
- A Bowtie2-indexed reference genome is available (human, mouse, fly, worm, zebrafish, etc.) and an effective genome size can be supplied.
- User wants standard outputs: filtered BAM, narrowPeak BED, summits BED, bigWig coverage, and a MultiQC summary.

## Do not use when
- Data is single-end — use a single-end ChIP-seq sketch instead.
- Target is a broad histone mark (H3K27me3, H3K9me3, H3K36me3); prefer a broad-peak ChIP-seq variant that runs MACS2 with `--broad`.
- Analysis is ATAC-seq, CUT&RUN, or CUT&Tag — those require different fragment handling and peak-calling defaults.
- Organism is bacterial/haploid variant calling, or the task is differential binding across conditions (use DiffBind/csaw-style sketches downstream of this one).
- Reads are long-read (Nanopore/PacBio) or from a non-Illumina protocol.

## Analysis outline
1. Adapter and quality trim paired reads with **fastp** (Illumina adapters via read overlap, q30 threshold, min length 15 bp).
2. Align trimmed pairs to an indexed reference genome with **Bowtie2** using default (end-to-end) parameters; capture mapping stats.
3. Filter the BAM with **samtools/samtool_filter2** to keep only MAPQ ≥ 30 and properly paired / concordant reads (SAM flag 0x0002).
4. Call narrow peaks with **MACS2 callpeak** in `BAMPE` mode using the user-supplied effective genome size, q-value 0.05, call-summits enabled, duplicate handling `--keep-dup 1`; emit treatment pileup bedGraph (SPMR-normalized if requested).
5. Convert the MACS2 treatment pileup bedGraph to **bigWig** via `wigToBigWig` for genome-browser display.
6. Extract a textual MACS2 summary (grep non-`#` header lines from peaks.xls) as a per-sample report.
7. Aggregate fastp, Bowtie2, and MACS2 logs with **MultiQC** into an HTML report and stats table.

## Key parameters
- `fastp qualified_quality_phred: 30`; `unqualified_percent_limit`: user-supplied (default 70; ~85 for 100 bp reads, ~70 for 50 bp reads).
- `fastp length_required: 15` (reads shorter than 15 bp after trimming are discarded).
- `bowtie2`: paired collection, `presets: no_presets` (defaults), `save_mapping_stats: true`.
- `samtool_filter2 mapq: 30`, `reqBits: 0x0002` (properly paired); header retained (`-h`).
- `macs2 callpeak format: BAMPE`, `qvalue: 0.05`, `keep_dup: 1`, `call_summits: true`, `nomodel_type: create_model` (mfold 5–50, band width 300), `gsize`: user (human 2.7e9, mouse 1.87e9, fly 1.2e8, worm 9e7), `--SPMR` toggled by the `Normalize profile` boolean.
- MACS2 control track is **not** supplied by this workflow — treatment-only calling. PCR duplicates remain in the filtered BAM and are removed inside MACS2 via `--keep-dup 1`.

## Test data
One paired-end sample, `wt_H3K4me3`, with forward/reverse FASTQ gz files hosted on Zenodo (record 1324070), exercised against the `mm10` Bowtie2 index with effective genome size 1.87e9 and SPMR normalization enabled. Running the workflow is expected to produce: a filtered BAM of roughly 5.3 MB; MACS2 narrowPeak and summits BED files with 13 peaks; a MACS2 peaks.xls whose header records the effective genome size `1.87e+09`, a fragment size around 201–202 bp, and 42,745 fragments after filtering in treatment; a bigWig coverage track of roughly 568 KB; Bowtie2 mapping stats showing ~90.3% concordant-exactly-once alignment; and a MultiQC HTML report plus tabular stats containing the `wt_H3K4me3` row with fastp, Bowtie2, and MACS2 columns.

## Reference workflow
Galaxy IWC `workflows/epigenetics/chipseq-pe` — "ChIP-seq Analysis: Paired-End Read Processing" v1.1 (MIT, L. Delisle et al.). Tool versions: fastp 1.3.1+galaxy0, Bowtie2 2.5.5+galaxy0, samtool_filter2 1.8+galaxy1, MACS2 2.2.9.1+galaxy0, MultiQC 1.33+galaxy3, wig_to_bigWig 1.1.1.
