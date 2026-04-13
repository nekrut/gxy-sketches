---
name: chipseq-peak-calling-tf-histone
description: Use when you need to call and quantify ChIP-seq peaks for transcription
  factors or histone marks from short-read Illumina data against a reference genome,
  with matched input controls, peak annotation, consensus peak generation across replicates,
  and DESeq2-based differential binding. Supports both narrow (TF) and broad (histone)
  peak modes.
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
  workflow: nf-core/chipseq
  url: https://github.com/nf-core/chipseq
  version: 2.1.0
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
- bedtools
- bamtools
- macs3
- homer
- deeptools
- phantompeakqualtools
- preseq
- featurecounts
- deseq2
- multiqc
tags:
- chip-seq
- peak-calling
- tf-binding
- histone-mark
- differential-binding
- consensus-peaks
- encode
- macs3
test_data: []
expected_output: []
---

# ChIP-seq peak calling and differential binding (TF / histone)

## When to use this sketch
- You have Illumina short-read ChIP-seq FASTQs for one or more antibodies, each with matched input/IgG controls and ideally biological replicates.
- Target organism has a standard reference genome + GTF (human, mouse, fly, worm, etc.) — iGenomes keys like `GRCh38`, `hg19`, `mm10` are directly supported and blacklists are bundled for the common assemblies.
- Goal is the full ENCODE-style recipe: QC, align, filter, call peaks (narrow for TFs, broad for histone marks), annotate, build a consensus peakset per antibody, quantify with featureCounts, and run DESeq2 PCA / differential binding.
- Either single-end or paired-end libraries; the pipeline auto-detects from the samplesheet.

## Do not use when
- Your assay is ATAC-seq or CUT&RUN / CUT&Tag — prefer the `atacseq` or `cutandrun` siblings (nf-core/atacseq, nf-core/cutandrun). ATAC lacks an IP/input contrast and wants Tn5 shifting.
- You are doing bulk RNA-seq, small RNA, or variant calling — wrong domain entirely.
- You have no control (input/IgG) library at all — MACS3 IP-vs-control calling is central here; use a control-free peak caller instead.
- You need allele-specific or single-cell ChIP — out of scope.
- You want IDR-based reproducible peak sets as the primary output — this pipeline uses a simpler `min_reps_consensus` merge, not IDR.

## Analysis outline
1. Raw read QC with FastQC.
2. Adapter and quality trimming with Trim Galore! (Cutadapt).
3. Align trimmed reads to the reference with the chosen aligner: `bwa` (default), `bowtie2`, `chromap`, or `star`. Index is built from FASTA if not supplied.
4. Merge library-level BAMs per sample (Picard MergeSamFiles), mark duplicates (Picard MarkDuplicates).
5. Filter alignments with SAMtools / BAMTools / pysam / BEDTools: drop duplicates, multi-mappers, unmapped, blacklisted regions, >4 mismatches, insert size >2 kb, discordant/orphan pairs (PE).
6. Alignment QC: Picard CollectMultipleMetrics, Preseq library complexity, SAMtools stats.
7. Generate per-sample bigWig tracks normalised to 1 M mapped reads (BEDTools genomecov + UCSC bedGraphToBigWig).
8. ChIP-specific QC: deepTools plotFingerprint (IP vs control enrichment), plotProfile over gene bodies, phantompeakqualtools NSC/RSC cross-correlation.
9. Call peaks per IP vs its control with MACS3 — `--broad` by default, `--narrow_peak` for TFs.
10. Annotate peaks to nearest gene/TSS with HOMER `annotatePeaks.pl` (using the supplied GTF).
11. Build a consensus peakset per antibody across replicates (BEDTools merge), quantify reads in consensus intervals with featureCounts (SAF input).
12. DESeq2 PCA, sample-distance heatmap, and differential binding on the consensus count matrix.
13. Aggregate everything into a MultiQC report and emit an IGV session XML linking bigWigs + peak tracks.

## Key parameters
- `--input`: CSV samplesheet with columns `sample,fastq_1,fastq_2,replicate,antibody,control,control_replicate`. `antibody` + `control` are mandatory for IP rows and blank for input rows.
- `--genome` (e.g. `GRCh38`, `hg19`, `mm10`) OR explicit `--fasta` + `--gtf` (`--gff` also accepted).
- `--aligner`: one of `bwa` (default), `bowtie2`, `chromap`, `star`.
- `--read_length`: one of 50/75/100/150/200; used to look up MACS3 effective genome size when `--macs_gsize` is not given.
- `--macs_gsize`: effective genome size for MACS3; auto-filled for iGenomes references.
- `--narrow_peak`: set for transcription factors / sharp marks; omit for broad histone marks (default is `--broad`, with `--broad_cutoff 0.1`).
- `--macs_fdr` / `--macs_pvalue`: mutually exclusive peak significance cutoffs.
- `--min_reps_consensus` (default 1): raise to 2+ to require a peak in ≥N replicates for the consensus set.
- `--blacklist`: ENCODE-style blacklist BED; bundled automatically for GRCh37, GRCh38, hg19, hg38, GRCm38, mm10.
- `--fragment_size` (default 200): used to extend single-end reads for coverage/peak calling.
- `--keep_dups`, `--keep_multi_map`: disable duplicate / multi-mapper filtering if you really want to.
- `--skip_preseq`, `--skip_spp`, `--skip_plot_fingerprint`, `--skip_deseq2_qc`, etc. to trim steps for small/test data.
- `-profile`: `docker` / `singularity` / `conda` / `test` / `test_full`.

## Test data
The bundled `test` profile pulls a tiny ChIP-seq samplesheet from nf-core/test-datasets (`chipseq/samplesheet/v2.1/samplesheet_test.csv`) together with a small reference FASTA and GTF borrowed from the atacseq test set, with `read_length = 50`, `fingerprint_bins = 100`, and `skip_preseq = true` so it runs under the 2-CPU / 6 GB / 6 h GitHub Actions cap. Running it is expected to produce a MultiQC report, per-sample filtered BAMs and bigWigs under `<aligner>/merged_library/`, MACS3 broadPeak calls with HOMER annotations, a per-antibody consensus peak BED + featureCounts matrix, and DESeq2 PCA/clustering outputs. The `test_full` profile runs the FoxA1 (TF / narrow) and EZH2 (histone / broad) datasets from GSE59530 and GSE57632 against `hg19` for full-scale benchmarking.

## Reference workflow
nf-core/chipseq v2.1.0 — https://github.com/nf-core/chipseq (DOI 10.5281/zenodo.3240506). MIT-licensed Nextflow DSL2 pipeline; see `nextflow_schema.json` and `docs/usage.md` for the complete parameter and samplesheet reference.
