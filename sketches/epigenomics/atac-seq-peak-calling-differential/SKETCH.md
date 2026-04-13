---
name: atac-seq-peak-calling-differential
description: 'Use when you have bulk ATAC-seq Illumina short-read FASTQ data (single-
  or paired-end) from a supported model organism and need an end-to-end analysis:
  QC, alignment, mitochondrial/blacklist/duplicate filtering, MACS2 peak calling,
  consensus peak counting and DESeq2 differential accessibility across conditions
  and replicates.'
domain: epigenomics
organism_class:
- eukaryote
- vertebrate
input_data:
- short-reads-paired
- short-reads-single
- reference-fasta
- gtf-annotation
source:
  ecosystem: nf-core
  workflow: nf-core/atacseq
  url: https://github.com/nf-core/atacseq
  version: 2.1.2
  license: MIT
tools:
- fastqc
- trim-galore
- bwa
- bowtie2
- chromap
- star
- picard
- samtools
- bamtools
- bedtools
- macs2
- homer
- featurecounts
- deseq2
- deeptools
- ataqv
- preseq
- multiqc
tags:
- atac-seq
- chromatin-accessibility
- peak-calling
- differential-accessibility
- macs2
- deseq2
- nf-core
test_data: []
expected_output: []
---

# Bulk ATAC-seq peak calling and differential accessibility

## When to use this sketch
- Bulk ATAC-seq (Tn5 transposition) Illumina short-read FASTQs, single- or paired-end, with one or more biological replicates per condition.
- You want open-chromatin peaks per sample plus a consensus peakset and DESeq2 PCA/clustering across conditions.
- Reference organism has a FASTA + GTF (iGenomes GRCh37/GRCh38/GRCm38/hg19/hg38/mm10 etc. give pre-computed MACS2 gsize and blacklists).
- You need standard ATAC-seq QC: FastQC, Picard metrics, Preseq complexity, deepTools fingerprint/profile, ataqv, and a consolidated MultiQC report.
- Optional IgG/input control tracks per sample are available (`--with_control`).

## Do not use when
- Single-cell ATAC-seq (10x scATAC, sci-ATAC) — use a dedicated scATAC sketch, not this bulk pipeline.
- ChIP-seq / CUT&RUN / CUT&Tag with antibody enrichment — use the nf-core/chipseq sibling sketch; peak-calling defaults and fragment handling differ.
- You only want alignment/QC without peaks — use a generic short-read alignment sketch.
- Long-read (ONT/PacBio) accessibility assays (e.g. Fiber-seq, nanoNOMe).
- Differential motif footprinting as the primary goal — this pipeline stops at peaks + DESeq2; use a footprinting-specific workflow downstream.

## Analysis outline
1. Raw read QC with FastQC.
2. Adapter trimming with Trim Galore! (auto-detects Nextera `CTGTCTCTTATA`).
3. Align to reference with the chosen aligner (default BWA-MEM; alternatives: Bowtie2, Chromap, STAR).
4. Merge technical replicates (same sample+replicate across lanes) with Picard MergeSamFiles.
5. Mark duplicates with Picard MarkDuplicates.
6. Filter alignments with SAMtools + BAMTools + pysam: drop mitochondrial, blacklisted, duplicate, multi-mapped, unmapped, >4-mismatch, soft-clipped reads; for PE also drop insert >2 kb, inter-chromosomal, non-FR, and orphan mates.
7. Library QC: Picard CollectMultipleMetrics, Preseq complexity, deepTools plotFingerprint and plotProfile over TSS/gene body, normalised 1M-scaled bigWigs.
8. Call peaks per merged library with MACS2 (broad by default; narrow with `--narrow_peak`). Optionally supply control samples.
9. Annotate peaks with HOMER `annotatePeaks.pl` against the GTF.
10. Build a consensus peakset across samples with BEDTools, quantify with featureCounts, run DESeq2 for PCA, sample distance heatmap and differential accessibility.
11. Merge filtered BAMs across biological replicates and repeat peak calling + consensus + DESeq2 at the merged-replicate level (skip with `--skip_merge_replicates`).
12. Run ataqv for ATAC-specific QC and aggregate everything into a MultiQC report; emit an IGV session XML with bigWig/peak tracks.

## Key parameters
- `--input`: CSV samplesheet with columns `sample,fastq_1,fastq_2,replicate` (add `control,control_replicate` with `--with_control`).
- `--outdir`: absolute output directory.
- `--genome` (iGenomes key, e.g. `GRCh38`, `hg19`, `mm10`) OR explicit `--fasta` + `--gtf`.
- `--read_length`: one of `50|75|100|150|200`; used to look up MACS2 effective genome size when `--macs_gsize` is not given.
- `--aligner`: `bwa` (default) | `bowtie2` | `chromap` | `star`. Chromap currently disabled for PE downstream.
- `--narrow_peak`: switch MACS2 from default `--broad` to narrowPeak mode; `--broad_cutoff` default `0.1`.
- `--macs_fdr` / `--macs_pvalue`: mutually exclusive peak significance thresholds.
- `--mito_name` (e.g. `chrM`, `MT`) and `--keep_mito` to toggle mitochondrial filtering; `--blacklist` BED (auto-supplied for common genomes).
- `--with_control`: enables paired control columns in samplesheet for MACS2 control tracks.
- `--min_reps_consensus`: replicates required for a peak to enter consensus (default `1`; raise for reproducibility filtering).
- `--skip_merge_replicates`, `--keep_dups`, `--keep_multi_map`, `--deseq2_vst` (default `true`): common toggles.
- `--fragment_size`: SE read extension (default `200`).
- `-profile`: `docker`/`singularity`/`conda`/etc.; combine with `test` for the bundled smoke test.

## Test data
The `test` profile pulls a minimal samplesheet (`samplesheet_test.csv`) and a tiny reference FASTA + GTF from the `nf-core/test-datasets` atacseq branch, with `mito_name: MT`, `read_length: 50`, and `fingerprint_bins: 100` to fit GitHub Actions (2 CPU, 6 GB, 6 h). Running `nextflow run nf-core/atacseq -profile test,docker --outdir results` should complete with FastQC/Trim Galore logs, BWA BAMs, filtered merged-library BAMs, normalised bigWigs, MACS2 broadPeak calls, a HOMER-annotated consensus peakset with featureCounts matrix, DESeq2 PCA and sample-distance outputs, ataqv JSON+HTML, an IGV session XML, and a consolidated MultiQC report under `multiqc/broad_peak/`. The `test_full` profile runs the same workflow on a full `hg19` samplesheet for release-time validation.

## Reference workflow
nf-core/atacseq v2.1.2 (https://github.com/nf-core/atacseq), DOI 10.5281/zenodo.2634132. See `docs/usage.md` and `nextflow_schema.json` for the authoritative parameter reference.
