---
name: consensus-peak-calling-chipseq-paired-end
description: Use when you need high-confidence consensus peaks from multiple ChIP-seq
  paired-end replicates (duplicate-removed BAMs) by intersecting per-replicate MACS2
  peaks and cross-checking against peaks called on depth-normalized pooled data. Produces
  a narrowPeak BED shared by at least N replicates plus an averaged normalized bigWig.
domain: epigenomics
organism_class:
- eukaryote
input_data:
- chipseq-bam-paired-end
- replicate-collection
source:
  ecosystem: iwc
  workflow: Consensus Peak Calling for ChIP-seq Paired-End Replicates
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/epigenetics/consensus-peaks
  version: '1.5'
  license: MIT
tools:
- macs2
- samtools
- bedtools
- deeptools
- multiqc
tags:
- chip-seq
- peak-calling
- consensus-peaks
- replicates
- macs2
- narrowpeak
- paired-end
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

# Consensus Peak Calling for ChIP-seq Paired-End Replicates

## When to use this sketch
- You have 2+ paired-end ChIP-seq replicates (same condition) as duplicate-removed BAM files and want a single confident peak set.
- You want consensus peaks defined as MACS2 summits supported by at least a user-specified minimum number of replicates.
- You want to control for library-size differences between replicates by downsampling all BAMs to the smallest library size before pooled peak calling.
- You also need an averaged, normalized coverage track (bigWig) across replicates for visualization.
- Works for flat replicate collections or nested collections (multiple conditions, each with replicates).

## Do not use when
- Your reads are single-end ChIP-seq — use the paired `consensus-peak-calling-chipseq-single-end` sibling sketch (MACS2 format differs: BAM vs BAMPE).
- Your data is ATAC-seq or CUT&RUN — use the `consensus-peak-calling-atac-cutandrun` sibling sketch (uses BED/Tn5-style shifted inputs rather than BAMPE with MACS2 model building).
- You have a single replicate — consensus logic is not meaningful; run plain MACS2 peak calling.
- Duplicates have not yet been removed from your BAMs — run a dedup step first (e.g. Picard MarkDuplicates / samtools markdup) before feeding this workflow.
- You want broad domain peaks (e.g. H3K27me3, H3K9me3) — this workflow is configured for narrow peaks with summit calling; broad-mode MACS2 is not used.
- You need input/IgG control subtraction in MACS2 — this workflow runs MACS2 without a control track.

## Analysis outline
1. Count reads per replicate BAM with `samtools view -c` and collapse counts to find the minimum library size (Table Compute `min`).
2. Call per-replicate narrow peaks with `MACS2 callpeak` (format `BAMPE`, `--call-summits`, q ≤ 0.05, no control).
3. Convert each per-replicate MACS2 treat pileup (bedGraph) to bigWig and average all replicate bigWigs with deepTools `bigwigAverage` at the user `bin_size`.
4. Compute the multi-way intersection of per-replicate narrowPeak BEDs with `bedtools multiintersect` and filter to intervals supported by `≥ min_overlap` replicates.
5. Subsample every replicate BAM to the smallest library size with `samtools view --subsample-target` (seed fixed for reproducibility).
6. Call peaks jointly on the pooled subsampled BAMs with a second `MACS2 callpeak` (multi-treatment, `BAMPE`, `--call-summits`).
7. Intersect the pooled-call narrowPeaks with the filtered multi-intersection BED (`bedtools intersect -wa -wb`) and keep only pooled peaks whose **summit** coordinate falls inside a ≥x-replicate interval (Filter on summit position vs interval bounds), then `cut` back to 10-column narrowPeak and deduplicate.
8. Run `MultiQC` on the per-replicate and pooled MACS2 tabular reports for QC.

## Key parameters
- `Minimum number of overlap` (int): minimum number of replicates whose peak intervals must contain a pooled-call summit to retain it. Typical: 2 for 2–3 replicates; scale with replicate count.
- `effective_genome_size` (int, MACS2 `--gsize`): manual value. Guidance from the workflow: *H. sapiens* 2.7e9, *M. musculus* 1.87e9, *D. melanogaster* 1.2e8, *C. elegans* 9e7.
- `bin_size` (int): bigWig bin size for `bigwigAverage`. Smaller = higher resolution, larger files; larger = coarser, smaller files.
- MACS2 fixed: `format=BAMPE`, `qvalue=0.05`, `--call-summits`, `keep-dup=1`, `--spmr` (normalized pileup), no control track, model-building on (`mfold 5 50`, `bw 300`, `d_min 20`).
- `samtools view` subsample: `--subsample-target <min_reads>`, `seed=1`.
- Final filter expression over bedtools intersect output keeps rows where the pooled peak's summit (computed from narrowPeak start + peak-offset column) lies strictly inside the ≥x-replicate interval.

## Test data
The repository ships a sibling ATAC/CUT&RUN test (no standalone ChIP-PE test job), which exercises the identical consensus logic: a collection of three paired-end mm10 BAMs (`rep1.bam`, `rep2.bam`, `rep3.bam`) with `Minimum number of overlap = 2`, `effective_genome_size = 1870000000` (mouse), and `bin_size = 50`. Expected outputs assert that per-replicate MACS2 narrowPeak files contain 4, 6, and 4 peaks respectively; the averaged bigWig is ~1388 bytes (±100); the pooled (merged) MACS2 narrowPeak has 8 peaks; the MultiQC HTML contains the text `MACS2: Fragment Length`; and the final `shared_narrowPeak` consensus BED contains 4 peaks supported by at least 2 of the 3 replicates. For ChIP-seq paired-end use, supply analogous duplicate-removed BAMPE replicates with a ChIP-appropriate `effective_genome_size`.

## Reference workflow
Galaxy IWC — `workflows/epigenetics/consensus-peaks/consensus-peaks-chip-pe.ga`, release 1.5 (MIT). Author: Lucille Delisle. Uses MACS2 2.2.9.1, samtools 1.22, bedtools 2.31.1, deepTools bigwigAverage 3.5.4, MultiQC 1.33.
