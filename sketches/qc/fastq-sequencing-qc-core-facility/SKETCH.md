---
name: fastq-sequencing-qc-core-facility
description: "Use when you need comprehensive quality control of raw Illumina FASTQ\
  \ sequencing data (single- or paired-end) for a sequencing core facility or project\
  \ kickoff \u2014 covering per-read QC, adapter/contaminant screening, alignment-based\
  \ metrics, and an aggregated MultiQC report. Not for downstream analysis."
domain: qc
organism_class:
- any
input_data:
- short-reads-paired
- short-reads-single
- reference-fasta
- illumina-run-directory
source:
  ecosystem: nf-core
  workflow: nf-core/seqinspector
  url: https://github.com/nf-core/seqinspector
  version: 1.0.1
  license: MIT
tools:
- fastqc
- fastq-screen
- seqfu
- seqtk
- bwa-mem2
- samtools
- picard
- multiqc
tags:
- qc
- fastq
- multiqc
- contamination
- core-facility
- illumina
- raw-reads
test_data: []
expected_output: []
---

# FASTQ sequencing QC for core facilities

## When to use this sketch
- You have raw Illumina FASTQ files (single-end or paired-end, gzipped) fresh off a sequencer and want a single aggregated QC report.
- You run a sequencing core facility or project kickoff and need per-sample, per-lane, per-project, and per-group QC summaries driven by sample tags.
- You want a combined view of read-level QC (FastQC, SeqFu stats), contamination screening (FastQ Screen against multiple reference genomes), and alignment-based metrics (Picard CollectMultipleMetrics, optionally CollectHsMetrics) aggregated via MultiQC.
- You optionally want to parse an Illumina run-folder (RTA / InterOp) to fold instrument-level statistics into the same report.
- You want to optionally downsample large FASTQs before QC to keep runtime bounded.

## Do not use when
- You need variant calls, expression quantification, assemblies, or any actual biological result — this pipeline is QC-only and its outputs are not meant to feed downstream analysis. Use a domain-specific sketch (e.g. `haploid-variant-calling-bacterial`, `bulk-rnaseq-star-salmon`, `bacterial-assembly-short-read`) instead.
- You have long reads (ONT / PacBio) — use a long-read QC sketch.
- You have 10x / single-cell FASTQs — use a single-cell QC sketch.
- You only want adapter/quality trimming with no reporting — use a trimming-focused sketch.
- You need hybrid-selection target QC as the primary deliverable with strict panel metrics — this pipeline can emit CollectHsMetrics but is not a panel-QC specialist.

## Analysis outline
1. Parse the samplesheet (`sample,fastq_1,fastq_2,rundir,tags`) and optionally parse the Illumina `rundir` for run-level stats (RUNDIRPARSER).
2. (Optional) Subsample reads per sample with `seqtk sample` when `--sample_size` is set (fraction or absolute count).
3. Run `FastQC` on each FASTQ for per-base quality, adapter content, and overrepresented sequences.
4. Run `seqfu stats` to produce length / count / N50 style sequence statistics.
5. Run `FastQ Screen` against a user-supplied panel of reference genomes (configured via `fastq_screen_references` CSV) for contamination screening.
6. If a reference is provided, build / reuse a `bwa-mem2` index and align reads with `bwa-mem2 mem`, then `samtools sort` + `samtools index` and `samtools faidx` the reference.
7. Run `picard CollectMultipleMetrics` on the sorted BAM for alignment / insert-size / base-quality cycle metrics.
8. Optionally run `picard CollectHsMetrics` when `--run_picard_collecthsmetrics` plus `--bait_intervals` and `--target_intervals` are supplied.
9. Aggregate everything with `MultiQC` into one global report plus one report per unique tag (e.g. per lane, per project, per group).

## Key parameters
- `--input`: CSV samplesheet with columns `sample,fastq_1,fastq_2,rundir,tags` (tags are colon-separated, case-sensitive, used to build per-group MultiQC reports).
- `--outdir`: absolute path to results directory.
- `--genome` or `--fasta`: reference for alignment-based QC. Without either, BWA-MEM2 / Picard steps are automatically skipped.
- `--sample_size`: integer (absolute read count) or float (fraction, e.g. `0.25`) to downsample before QC; default `0` = no subsampling.
- `--fastq_screen_references`: CSV listing reference name, aligner, basename, and directory for each FastQ Screen reference.
- `--run_picard_collecthsmetrics`: boolean, off by default; requires `--fasta`, `--bait_intervals`, `--target_intervals`, and `--dict`.
- `--bait_intervals` / `--target_intervals`: BED or interval_list files for hybrid-selection QC.
- `--skip_tools`: comma-separated subset of `{bwamem2_index,bwamem2_mem,fastqc,fastqscreen,picard_collectmultiplemetrics,rundirparser,samtools_faidx,samtools_index,seqfu_stats,seqtk_sample}` to disable specific steps.
- `--sort_bam`: default `true`; coordinate-sort BAMs after alignment.
- `--multiqc_title`: custom title for the global MultiQC report.
- `-profile`: `test` for the bundled minimal dataset, or `docker`/`singularity`/`conda` plus an institutional profile for real runs.

## Test data
The bundled `test` profile points `--input` at `seqinspector/testdata/NovaSeq6000/samplesheet.csv` from the nf-core test-datasets repository — a small NovaSeq6000 samplesheet of paired-end FASTQs with associated run-folder metadata and tag strings — and uses iGenomes `R64-1-1` (*Saccharomyces cerevisiae*) as the reference for BWA-MEM2 alignment and Picard metrics. FastQ Screen uses the example references CSV shipped in `assets/example_fastq_screen_references.csv`. A successful run produces per-sample FastQC HTML/zip, SeqFu stats TSVs, FastQ Screen text/HTML/PNG reports, sorted indexed BAMs, Picard `CollectMultipleMetrics` output files, and one global `multiqc/global_report/multiqc_report.html` plus one `multiqc/group_reports/<tag>/multiqc_report.html` per unique tag. Resource limits in the test profile are capped at 4 CPUs / 8 GB / 1 h so it runs on a laptop.

## Reference workflow
nf-core/seqinspector v1.0.1 (MIT) — https://github.com/nf-core/seqinspector. Key tool versions: bwa-mem2 2.3, FastQC 0.12.1, FastQ Screen 0.16.0, MultiQC 1.33, Picard 3.4.0, samtools 1.22.1, SeqFu 1.22.3, seqtk 1.4.
