---
name: chipseq-consensus-peaks-single-end
description: Use when you have multiple single-end ChIP-seq replicate BAM files (PCR
  duplicates already removed) and need a high-confidence consensus narrowPeak set
  whose summits are supported by at least N replicates. Controls for library-size
  differences via subsampling before joint peak calling with MACS2.
domain: epigenomics
organism_class:
- eukaryote
input_data:
- chipseq-bam-single-end
- replicate-collection
source:
  ecosystem: iwc
  workflow: Consensus Peak Calling for ChIP-seq Single-End Replicates
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/epigenetics/consensus-peaks
  version: '1.5'
  license: MIT
  slug: epigenetics--consensus-peaks--consensus-peaks-chip-sr
tools:
- name: macs2
  version: 2.2.9.1+galaxy0
- name: samtools
  version: 1.22+galaxy2
- name: bedtools
  version: 2.31.1
- name: deeptools
  version: 3.5.4+galaxy0
- name: multiqc
  version: 1.33+galaxy2
tags:
- chip-seq
- peak-calling
- consensus-peaks
- macs2
- single-end
- replicates
- narrowpeak
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

# ChIP-seq consensus peak calling (single-end replicates)

## When to use this sketch
- You have N single-end ChIP-seq replicate BAM files (PCR duplicates already removed) for one condition, and want a single narrowPeak BED whose summits are reproducibly supported by at least X of N replicates.
- You want to control for differences in library depth between replicates before joint peak calling, by downsampling all replicates to the smallest library size.
- You also want per-replicate MACS2 peaks, an averaged normalized coverage bigWig across replicates, and a MultiQC summary of the MACS2 runs.
- Works for transcription-factor or sharp histone-mark ChIP-seq where MACS2 narrow peak calling with summit detection is appropriate.
- Supports nested collections for multiple conditions, each with multiple replicates.

## Do not use when
- Reads are paired-end ChIP-seq — use the paired-end sibling sketch (`consensus-peaks-chip-pe`).
- Data is ATAC-seq or CUT&RUN — use the dedicated `consensus-peaks-atac-cutandrun` workflow variant; it takes BAM but uses ATAC/CUT&RUN-tuned MACS2 settings.
- You need broad histone-mark peaks (e.g. H3K27me3, H3K9me3) — this sketch runs MACS2 in narrow mode with `--call-summits`; a broad-peak variant is required instead.
- You have only a single replicate — consensus logic requires N≥2.
- Duplicates have not been removed from the input BAMs — deduplicate first (e.g. with MarkDuplicates / Picard) before running this workflow.
- You need differential binding analysis (DiffBind/csaw) rather than a reproducible peak set.

## Analysis outline
1. Input: a Galaxy dataset collection of N single-end, duplicate-removed BAM files (one per replicate).
2. Per replicate, call narrow peaks with MACS2 `callpeak` (`--nomodel`, `extsize 200`, `--call-summits`, q-value 0.05, SPMR normalized pileup).
3. Convert each per-replicate normalized bedGraph pileup to bigWig and compute an averaged coverage bigWig across replicates with deepTools `bigwigAverage` at the user-defined `bin_size`.
4. Compute a multi-way intersection of per-replicate narrowPeak BEDs with `bedtools multiinter`, then filter the intersection to intervals supported by at least `Minimum number of overlap` replicates.
5. Count reads per replicate with `samtools view -c`, take the minimum across replicates, and subsample every replicate BAM down to that minimum with `samtools view --subsample-target` (seed=1).
6. Call peaks jointly on all subsampled BAMs combined via MACS2 `callpeak` (same settings as step 2, treatment=multi).
7. Intersect merged narrowPeaks with the replicate-supported intersection BED (`bedtools intersect -wa -wb`), then filter rows so the peak summit coordinate (chrom start + peak-offset column 10) falls inside an intersection interval.
8. Cut back to the 10 narrowPeak columns, deduplicate, and emit the final `shared_narrowPeak` BED. Aggregate MACS2 reports with MultiQC.

## Key parameters
- `Minimum number of overlap` (integer, required): X in "summit must be present in ≥X replicates" — typically 2 for triplicates.
- `effective_genome_size` (integer, required, passed to MACS2 `--gsize`): H. sapiens 2700000000, M. musculus 1870000000, D. melanogaster 120000000, C. elegans 90000000.
- `bin_size` (integer, required): bin size for the averaged normalized-coverage bigWig; smaller = higher resolution but larger file.
- MACS2 callpeak (both individual and merged runs): format=BAM, `--nomodel`, `--extsize 200`, `--shift 0`, `--qvalue 0.05`, `--call-summits`, `--keep-dup 1`, `--SPMR`, no control, narrow peaks only.
- Subsampling: `samtools view` target = minimum read count across replicates, fixed seed=1 for reproducibility.
- Final filter expression: `(c2+c10) >= c12 and (c2+c10) < c13` — enforces that the MACS2 summit coordinate lies inside the replicate-intersection interval.

## Test data
The source workflow ships a test that uses a Galaxy collection of three mm10 single-end ChIP-seq replicate BAMs (`rep1.bam`, `rep2.bam`, `rep3.bam`) with PCR duplicates removed, `Minimum number of overlap=2`, `effective_genome_size=1870000000` (mouse), and `bin_size=50`. Expected outcomes: per-replicate MACS2 narrowPeak files with 4, 6, and 4 peaks respectively; an `average_bigwig` of roughly 1388 bytes (±100); a merged-BAM MACS2 narrowPeak set with 8 peaks; a MultiQC HTML report containing the string "MACS2: Fragment Length"; and a final `shared_narrowPeak` BED containing 4 consensus peaks whose summits are supported by at least 2 replicates. Note the test uses the ATAC/CUT&RUN sibling workflow's test harness, but the assertions apply equivalently to the single-end ChIP-seq variant.

## Reference workflow
Galaxy IWC `workflows/epigenetics/consensus-peaks/consensus-peaks-chip-sr.ga` ("Consensus Peak Calling for ChIP-seq Single-End Replicates"), release 1.5, MIT license, by Lucille Delisle. Key tool versions: MACS2 2.2.9.1, samtools 1.22, bedtools 2.31.1, deepTools bigwigAverage 3.5.4, MultiQC 1.33.
