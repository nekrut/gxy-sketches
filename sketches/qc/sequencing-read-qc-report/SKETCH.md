---
name: sequencing-read-qc-report
description: Use when you need a minimal quality-control report for raw sequencing
  FASTQ files (per-base quality, adapter content, duplication, overrepresented sequences)
  aggregated into a single HTML summary across many samples. Covers both single-end
  and paired-end short reads; no alignment, trimming, or variant calling.
domain: qc
organism_class:
- any
input_data:
- short-reads-paired
- short-reads-single
source:
  ecosystem: nf-core
  workflow: nf-core/evexplorer
  url: https://github.com/nf-core/evexplorer
  version: dev
  license: MIT
tools:
- fastqc
- multiqc
tags:
- qc
- fastqc
- multiqc
- raw-reads
- report
- nf-core-template
test_data: []
expected_output: []
---

# Raw sequencing read QC report

## When to use this sketch
- You have one or more FASTQ files (single-end or paired-end Illumina / ONT-in-FASTQ) and need per-sample quality metrics before deciding on downstream analysis.
- You want a single aggregated HTML report (MultiQC) covering many samples, suitable for sharing with wet-lab collaborators.
- You are triaging a new dataset: checking adapter contamination, GC skew, per-base quality decay, duplication and overrepresented sequences.
- You want a reproducible nf-core samplesheet-driven QC step that fits upstream of any downstream pipeline.

## Do not use when
- You need to trim or filter reads before downstream analysis — use a dedicated trimming sketch (e.g. `fastp-read-trimming` or the QC step inside nf-core/rnaseq, nf-core/sarek, nf-core/viralrecon).
- You need alignment-based QC (insert size, duplication from BAM, coverage) — use a sketch built on `samtools stats` / `picard CollectMultipleMetrics` / `qualimap`.
- You need contamination screening against reference databases — use a `kraken2` / `fastq_screen` sketch.
- You need long-read-specific QC metrics (read length N50, yield curves) — use a sketch built on `NanoPlot` / `pycoQC`.
- The user is asking for a full analysis (variant calling, RNA-seq quantification, assembly) — pick the domain-specific sketch; those pipelines already run FastQC internally.

## Analysis outline
1. Parse the nf-core samplesheet (`sample,fastq_1,fastq_2`) and auto-detect single vs. paired-end per row.
2. Concatenate FASTQ files that share the same `sample` identifier (multi-lane merge) before QC.
3. Run `FastQC` on each (merged) FASTQ to produce per-file HTML reports and zipped metric tables.
4. Run `MultiQC` over the `fastqc/` outputs plus pipeline software-versions to produce a single `multiqc_report.html` with aggregated plots.
5. Emit Nextflow execution reports (timeline, trace, DAG) and a validated samplesheet in `pipeline_info/`.

## Key parameters
- `--input` (required): path to CSV samplesheet with header `sample,fastq_1,fastq_2`; `fastq_2` left blank for single-end rows.
- `--outdir` (required): absolute path to results directory (must be absolute for cloud).
- `--multiqc_title`: sets the MultiQC report page header and output filename.
- `--multiqc_config` / `--multiqc_logo` / `--multiqc_methods_description`: override MultiQC presentation and embed a methods blurb.
- `-profile`: pick `docker`, `singularity`, `podman`, `apptainer`, or `conda` for software provisioning; stack with `test` for the bundled minimal profile.
- `--max_cpus`, `--max_memory`, `--max_time`: cap per-job resource requests on small systems (defaults 16 CPU / 128 GB / 240 h).
- Reference parameters (`--genome`, `--fasta`, `--igenomes_ignore`) are accepted by the schema but not consumed by the QC-only steps; leave unset unless a downstream module requires them.

## Test data
The bundled `test` profile points at a small nf-core-style samplesheet hosted on the `ammarsabir15/test-datasets` `evexplorer` branch (`sample_sheet/samplesheet.csv`) listing a handful of FASTQ entries, and a local `custom_genome.fa` FASTA under `/references/DERFINDER_ref/`. The `platform` parameter is set to `ont` in the test profile. A successful `-profile test` run should produce a `fastqc/` directory with `*_fastqc.html` and `*_fastqc.zip` per input FASTQ, a `multiqc/multiqc_report.html` aggregating them, and a `pipeline_info/` directory containing the Nextflow execution reports and validated samplesheet. A `test_full` profile is also declared, pointing at the `viralrecon` full-size Illumina amplicon samplesheet with `genome = 'R64-1-1'`.

## Reference workflow
nf-core/evexplorer (dev), https://github.com/nf-core/evexplorer — an nf-core template-stage pipeline whose currently implemented steps are FastQC for per-sample raw-read QC and MultiQC for aggregation, driven by the standard nf-core samplesheet schema (`assets/schema_input.json`).
