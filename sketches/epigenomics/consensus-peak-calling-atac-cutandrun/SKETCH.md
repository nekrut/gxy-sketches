---
name: consensus-peak-calling-atac-cutandrun
description: Use when you need high-confidence consensus peaks from multiple replicate
  ATAC-seq or CUT&RUN BAM files (duplicates already removed). Calls MACS2 peaks per
  replicate, intersects across replicates, subsamples all BAMs to the smallest library
  size, re-calls peaks on the pooled downsampled reads, and keeps merged peaks whose
  summits overlap an intersection supported by at least N replicates.
domain: epigenomics
organism_class:
- eukaryote
input_data:
- aligned-bam-deduplicated
source:
  ecosystem: iwc
  workflow: Consensus Peak Calling for ATAC-seq and CUT and RUN Replicates
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/epigenetics/consensus-peaks
  version: '1.5'
  license: MIT
tools:
- macs2
- bedtools
- samtools
- deeptools
- multiqc
tags:
- atac-seq
- cut-and-run
- peak-calling
- consensus-peaks
- replicates
- macs2
- chromatin-accessibility
test_data: []
expected_output:
- role: individual_macs2_narrowpeaks
  description: Content assertions for `individual_macs2_narrowPeaks`.
  assertions:
  - 'rep1: has_n_lines: {''n'': 4}'
  - 'rep2: has_n_lines: {''n'': 6}'
  - 'rep3: has_n_lines: {''n'': 4}'
- role: average_bigwig
  description: Content assertions for `average_bigwig`.
  assertions:
  - 'has_size: {''value'': 1388, ''delta'': 100}'
- role: merged_macs2_narrowpeaks
  description: Content assertions for `merged_macs2_narrowPeaks`.
  assertions:
  - 'has_n_lines: {''n'': 8}'
- role: multiqc_output
  description: Content assertions for `multiqc_output`.
  assertions:
  - 'has_text: MACS2: Fragment Length'
- role: shared_narrowpeak
  description: Content assertions for `shared_narrowPeak`.
  assertions:
  - 'has_n_lines: {''n'': 4}'
---

# Consensus peak calling for ATAC-seq and CUT&RUN replicates

## When to use this sketch
- You have N (≥2) replicate BAM files from ATAC-seq or CUT&RUN on the same condition, already aligned and with PCR duplicates removed.
- You want a single high-confidence narrowPeak BED representing peaks reproducibly supported by at least a user-defined minimum number of replicates.
- You need library-size normalization: the workflow subsamples every replicate to the smallest library size before pooled peak calling, so differences in sequencing depth do not bias the consensus.
- You also want a per-replicate normalized bigWig and a replicate-averaged bigWig track for visualization.
- You are working with a genome where an effective genome size is known (e.g. human 2.7e9, mouse 1.87e9, fly 1.2e8, worm 9e7).

## Do not use when
- You are calling peaks from ChIP-seq with a matched input/IgG control — this workflow runs MACS2 without a control track; use a dedicated ChIP-seq consensus workflow instead.
- You only have a single replicate — the whole point is replicate intersection; run plain MACS2 narrow peak calling on one sample.
- You need broad-domain peaks (e.g. H3K27me3, H3K9me3) — MACS2 is configured in narrow mode with `call_summits` on; use a broad-mark consensus workflow.
- Your BAMs still contain PCR duplicates — deduplicate upstream (e.g. Picard MarkDuplicates / samtools markdup) first.
- You are starting from raw FASTQ — pair this with an upstream ATAC-seq / CUT&RUN alignment + dedup workflow; this sketch starts at rmDup BAM.
- You need differential accessibility between conditions — this produces a consensus peak set, not a statistical comparison; feed the output into DiffBind / DESeq2 downstream.

## Analysis outline
1. Convert each replicate rmDup BAM to BED with `bedtools bamtobed`.
2. Call narrow peaks on each replicate individually with `MACS2 callpeak` (no control, `--nomodel`, `--call-summits`, SPMR-normalized pileup).
3. Convert each per-replicate normalized bedGraph pileup to bigWig and average across replicates with deepTools `bigwigAverage` at the user-specified `bin_size`.
4. Compute a multi-intersection across all per-replicate narrowPeak BEDs with `bedtools multiintersect` and filter rows where the replicate-count column is ≥ the user's `Minimum number of overlap`.
5. In parallel, count reads in every replicate BAM with `samtools view -c`, take the minimum across replicates, and subsample each BAM down to that target with `samtools view` subsampling (fixed seed).
6. Convert each downsampled BAM to BED and call peaks once more with `MACS2 callpeak` on the pooled set of downsampled BEDs (multi-treatment mode).
7. Intersect the pooled narrowPeak set with the filtered multi-intersect regions (`bedtools intersect -wa -wb`), then keep only rows where the MACS2 summit position falls inside the intersection interval, cut to 10 narrowPeak columns, and deduplicate to produce `shared_narrowPeak`.
8. Aggregate MACS2 stats from both individual and pooled peak calls into a `MultiQC` HTML report.

## Key parameters
- `Minimum number of overlap` (integer, required): minimum number of replicates whose peaks must overlap at a summit for it to be kept. Typical value is 2 for 2–3 replicates; scale with N.
- `effective_genome_size` (integer, required): passed to MACS2 `--gsize`. Canonical values: H. sapiens 2700000000, M. musculus 1870000000, D. melanogaster 120000000, C. elegans 90000000.
- `bin_size` (integer, required): bin size for deepTools `bigwigAverage`; smaller = higher resolution but larger files.
- MACS2 fixed settings (do not change without reason): `--format BED`, `--qvalue 0.05`, `--nomodel --extsize 200 --shift -100` (ATAC-style centering), `--call-summits`, `--SPMR`, `--keep-dup all` (duplicates are already removed upstream), no control track.
- Subsampling: `samtools view` subsample with `seed=1` targeting the minimum read count across replicates; downstream pooled MACS2 call uses multi-treatment mode over all downsampled replicates.

## Test data
The test profile provides a Galaxy collection of three mouse (mm10) rmDup BAM replicates (`rep1.bam`, `rep2.bam`, `rep3.bam`) with `Minimum number of overlap = 2`, `effective_genome_size = 1870000000`, and `bin_size = 50`. Running the workflow is expected to yield per-replicate narrowPeak BEDs with 4, 6, and 4 peaks respectively, a pooled `merged_macs2_narrowPeaks` BED of 8 peaks, a final `shared_narrowPeak` consensus BED of 4 peaks supported by ≥2 replicates, an `average_bigwig` track of roughly 1388 bytes (±100), and a MultiQC HTML report containing the MACS2 fragment-length section.

## Reference workflow
Galaxy IWC — `workflows/epigenetics/consensus-peaks/consensus-peaks-atac-cutandrun.ga`, release 1.5 (MIT), by Lucille Delisle. See the workflow README and `strategy.png` in that directory for the overlap-plus-downsample rationale.
