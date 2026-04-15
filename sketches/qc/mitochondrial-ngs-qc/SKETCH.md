---
name: mitochondrial-ngs-qc
description: Use when you need to run quality control on Illumina short-read sequencing
  data intended for downstream mitochondrial DNA analysis, producing per-sample FastQC
  reports and an aggregated MultiQC summary against a nuclear+mtDNA reference. This
  is an early-stage scaffold pipeline that currently only implements read QC.
domain: qc
organism_class:
- vertebrate
- eukaryote
input_data:
- short-reads-paired
- short-reads-single
- reference-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/mitodetect
  url: https://github.com/nf-core/mitodetect
  version: dev
  license: MIT
  slug: mitodetect
tools:
- name: fastqc
  version: 0.12.1
- name: multiqc
  version: '1.27'
tags:
- mitochondria
- mtdna
- qc
- fastqc
- multiqc
- illumina
test_data: []
expected_output: []
---

# Mitochondrial NGS read QC

## When to use this sketch
- You have Illumina short-read FASTQ data (single- or paired-end) that will feed into a mitochondrial DNA analysis project and you need baseline read quality metrics.
- You want a standardized nf-core entry point that takes a samplesheet + reference genome and emits per-sample FastQC and a MultiQC summary.
- You are scaffolding a mitochondrial variant / heteroplasmy workflow and need the QC stage wired up before the mtDNA-specific steps exist.
- Samples may have been re-sequenced across multiple lanes; the pipeline concatenates per-sample reads before QC.

## Do not use when
- You need actual mitochondrial variant calling, heteroplasmy quantification, haplogroup assignment, or mtDNA copy-number estimation — this pipeline is a template and only runs read QC today; use a dedicated mtDNA variant caller sketch instead.
- Your input is long-read (ONT/PacBio) data — use a long-read QC sketch.
- You are calling nuclear variants — use a germline or somatic short-variant sketch.
- You need assembly of the mitochondrial genome — use an organelle assembly sketch.

## Analysis outline
1. Parse and validate the input samplesheet (`sample,fastq_1,fastq_2`), merging lanes per sample.
2. Run `FastQC` on each sample's raw reads to collect per-base quality, adapter, and overrepresented-sequence metrics.
3. Aggregate all QC outputs with `MultiQC` into a single HTML report plus parsed data tables.
4. Emit Nextflow execution reports and `software_versions.yml` under `pipeline_info/`.

## Key parameters
- `--input`: CSV samplesheet with header `sample,fastq_1,fastq_2`; `fastq_2` may be blank for single-end. Repeated `sample` rows are concatenated.
- `--outdir`: absolute output directory (required).
- `--genome` / `--fasta`: iGenomes key (e.g. `GRCh37`, `R64-1-1`) or explicit FASTA path; used as the reference context for QC.
- `--igenomes_ignore`: set when supplying your own `--fasta` and not using iGenomes.
- `-profile`: pick `docker`, `singularity`, `conda`, etc.; combine with `test` for the bundled minimal test.
- `--multiqc_title` / `--multiqc_config`: customize the MultiQC report header and modules.

## Test data
The `test` profile reuses the `viralrecon` Illumina amplicon samplesheet from `nf-core/test-datasets` as a stand-in input and sets `genome = 'R64-1-1'` (S. cerevisiae) as the reference. The `test_full` profile points at the full viralrecon Illumina amplicon samplesheet with the same reference. Running `-profile test,docker --outdir results` is expected to complete and produce `results/fastqc/*_fastqc.html` + `*_fastqc.zip` per sample, `results/multiqc/multiqc_report.html` with a populated `multiqc_data/` directory, and a `results/pipeline_info/` folder with Nextflow execution reports and `software_versions.yml`.

## Reference workflow
nf-core/mitodetect (dev, template version 1.0.0dev; nf-core template 3.2.0) — https://github.com/nf-core/mitodetect. Note: at this revision the pipeline is an nf-core template scaffold; only FastQC + MultiQC are implemented, and downstream mtDNA-specific steps are TODO.
