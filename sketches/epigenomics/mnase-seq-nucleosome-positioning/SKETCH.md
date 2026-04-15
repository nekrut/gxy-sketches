---
name: mnase-seq-nucleosome-positioning
description: Use when you have MNase-seq (micrococcal nuclease digestion) short-read
  data and need to map mono-nucleosome fragments, call nucleosome positions, and generate
  normalized coverage/occupancy profiles across features such as TSSs or gene bodies.
  Assumes paired-end Illumina reads and a reference genome.
domain: epigenomics
organism_class:
- eukaryote
input_data:
- short-reads-paired
- reference-fasta
- gtf-annotation
source:
  ecosystem: nf-core
  workflow: nf-core/mnaseseq
  url: https://github.com/nf-core/mnaseseq
  version: 1.0.0
  license: MIT
  slug: mnaseseq
tools:
- name: fastqc
- name: trim-galore
- name: bwa
- name: picard
- name: samtools
- name: bamtools
- name: bedtools
- name: preseq
- name: deeptools
- name: danpos2
- name: ucsc-bedgraphtobigwig
- name: multiqc
- name: igv
tags:
- mnase-seq
- nucleosome
- chromatin
- positioning
- occupancy
- bigwig
- danpos
test_data: []
expected_output: []
---

# MNase-seq nucleosome positioning

## When to use this sketch
- You have MNase-digested DNA sequencing data and want to profile nucleosome positions, occupancy, and fuzziness genome-wide.
- Input is paired-end (or single-end) Illumina FASTQ, organized by experimental group and replicate, plus a reference genome FASTA and GTF.
- You need normalized bigWig tracks (1M-read scaled), DANPOS2 nucleosome calls, and gene-body/TSS meta-profiles.
- You want per-library QC plus optional merging across libraries/replicates to boost depth for footprinting-style analyses.

## Do not use when
- The assay is ATAC-seq, ChIP-seq, or CUT&RUN — use the matching `atac-seq-*`, `chip-seq-*`, or `cutandrun-*` sketches instead; filtering, peak calling, and fragment-size handling differ.
- You are doing bulk RNA-seq, variant calling, or de novo assembly.
- You only need raw alignment/QC with no nucleosome positioning — a generic alignment-QC sketch is lighter weight.
- The organism is prokaryotic (no nucleosomes) — this pipeline assumes eukaryotic chromatin.

## Analysis outline
1. Raw read QC with FastQC.
2. Adapter and quality trimming with Trim Galore!.
3. Align trimmed reads to the reference with BWA; sort/index with SAMtools.
4. Mark duplicates per library with Picard MarkDuplicates.
5. Merge libraries belonging to the same sample (Picard MergeSamFiles), re-mark duplicates.
6. Filter alignments: drop blacklisted regions (BEDTools/SAMtools), duplicates, secondary/unmapped/multi-mapped reads, reads with >`max_mismatch` mismatches or soft-clipping (BAMTools), and for paired-end reads enforce FR orientation, same-chromosome, and insert-size window (Pysam/BAMTools) to retain mono-nucleosome fragments.
7. Library-complexity estimation (Preseq) and alignment QC (Picard CollectMultipleMetrics, SAMtools stats).
8. Build 1M-read-normalized bigWig tracks via BEDTools genomecov + bedGraphToBigWig.
9. Genome-wide coverage QC with deepTools plotFingerprint.
10. Call nucleosome positions and generate smoothed normalized bigWigs with DANPOS2 `dpos`.
11. Compute gene-body / TSS meta-profiles with deepTools computeMatrix + plotProfile from the DANPOS2 bigWigs.
12. Optionally merge replicates within an experimental group and repeat steps 5–11 at the merged-replicate level.
13. Emit an IGV session (`igv_session.xml`) bundling bigWig tracks and DANPOS nucleosome BED files, plus an aggregate MultiQC report.

## Key parameters
- `--input`: CSV with columns `group,replicate,fastq_1,fastq_2`; same `group`+`replicate` across rows means multi-lane libraries that get merged.
- `--genome` (iGenomes key, e.g. `GRCh37`, `GRCm38`, `BDGP6`, `R64-1-1`) or explicit `--fasta` + `--gtf` (+ optional `--bwa_index`, `--gene_bed`, `--tss_bed`, `--blacklist`).
- `--single_end`: switch to SE mode; SE coverage extension controlled by `--fragment_size` (default `150`).
- Mono-nucleosome insert-size window: `--min_insert 100`, `--max_insert 200` (paired-end filter).
- `--max_mismatch 4`: drop reads with more than 4 mismatches (XM tag).
- `--keep_dups` / `--keep_multi_map`: retain duplicates / multi-mappers (off by default; leave off for standard nucleosome calling).
- `--skip_merge_replicates`: disable the replicate-merged branch if you only want per-sample analysis.
- `--fingerprint_bins 500000`: deepTools plotFingerprint resolution.
- Skip flags: `--skip_fastqc`, `--skip_picard_metrics`, `--skip_preseq`, `--skip_plot_fingerprint`, `--skip_plot_profile`, `--skip_danpos`, `--skip_igv`, `--skip_multiqc`.
- Blacklists for GRCh37/GRCh38/GRCm38/hg19/hg38/mm10 are bundled and applied automatically when those `--genome` keys are used.

## Test data
The `test` profile pulls a minimal MNase-seq design CSV from the `nf-core/test-datasets` `mnaseseq` branch together with a small reference FASTA and GTF reused from the `chipseq` test dataset. Resources are clamped (`max_cpus=2`, `max_memory=6.GB`) and `fingerprint_bins=100` so the run completes inside CI. Expected outputs include per-library and merged-library filtered BAMs under `bwa/mergedLibrary/`, 1M-read-normalized bigWigs, DANPOS2 nucleosome BED/xls calls under `bwa/mergedLibrary/danpos/`, deepTools plotFingerprint/plotProfile PDFs, an `igv/igv_session.xml`, and an aggregate `multiqc/multiqc_report.html`.

## Reference workflow
nf-core/mnaseseq v1.0.0 (https://github.com/nf-core/mnaseseq), MIT licensed; DOI 10.5281/zenodo.6581372. See `docs/usage.md` and `docs/output.md` in that repository for exhaustive parameter and output-layout details.
