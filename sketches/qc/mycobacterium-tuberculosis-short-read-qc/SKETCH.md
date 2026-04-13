---
name: mycobacterium-tuberculosis-short-read-qc
description: Use when you have Illumina short-read sequencing of Mycobacterium tuberculosis
  (Mtb) isolates and need baseline read-level quality control as a first pass before
  downstream strain typing or variant analysis. Current implementation covers raw
  read QC and aggregated reporting only; no alignment or variant calling is produced.
domain: qc
organism_class:
- bacterial
- haploid
input_data:
- short-reads-paired
- short-reads-single
source:
  ecosystem: nf-core
  workflow: nf-core/tbanalyzer
  url: https://github.com/nf-core/tbanalyzer
  version: dev
  license: MIT
tools:
- fastqc
- multiqc
tags:
- tuberculosis
- mtb
- mycobacterium
- read-qc
- illumina
- nf-core
- bacterial
test_data: []
expected_output: []
---

# Mycobacterium tuberculosis short-read QC

## When to use this sketch
- You have Illumina single- or paired-end FASTQ data from cultured Mtb isolates (or other Mycobacterium spp.) and need a first-pass read quality assessment.
- You want a single aggregated MultiQC report over many Mtb libraries to triage which samples are good enough to pass downstream.
- You are building a TB-GVAS-style Mtb characterization pipeline and need the upstream QC stage that nf-core/tbanalyzer (dev template) currently provides.
- Samples may be multi-lane: the same `sample` ID across rows is automatically concatenated before QC.

## Do not use when
- You need SNV/indel calls, lineage/spoligotype assignment, or drug-resistance prediction for Mtb — this sketch does not call variants (see a dedicated `haploid-variant-calling-bacterial` or Mtb-specific typing sketch).
- You have Nanopore/PacBio long reads — use a long-read bacterial QC sketch instead.
- You have mixed metagenomic sputum reads and need taxonomic decontamination before QC — use a metagenomic QC sketch.
- You need assembly or annotation of the Mtb genome — use a bacterial assembly sketch (e.g. nf-core/bacass).

## Analysis outline
1. Parse the input samplesheet (`sample,fastq_1,fastq_2`) and concatenate FASTQs that share a sample ID across lanes.
2. Run FastQC on each (merged) library to compute per-base quality, adapter content, GC and overrepresented-sequence metrics.
3. Aggregate FastQC outputs plus pipeline version info into a single MultiQC HTML report.
4. Emit Nextflow execution reports (`execution_report.html`, `execution_timeline.html`, `execution_trace.txt`, `pipeline_dag.svg`) and the validated samplesheet for provenance.

## Key parameters
- `--input` (required): CSV samplesheet with header `sample,fastq_1,fastq_2`; `fastq_2` empty for single-end.
- `--outdir` (required): absolute path for published results.
- `--genome` / `--fasta`: reference selector — accepted by the schema (iGenomes or FASTA) but the current dev template does not use it for alignment; leave unset unless you are extending the pipeline.
- `--multiqc_title`, `--multiqc_config`, `--multiqc_logo`: customize the aggregated report.
- `-profile`: pick one of `docker`, `singularity`, `podman`, `apptainer`, `conda`, etc.; combine with `test` for the bundled minimal dataset.
- `-params-file params.yaml`: preferred way to pin parameters across runs (do not pass parameters via `-c`).

## Test data
The bundled `test` profile points `--input` at the nf-core test-datasets samplesheet `viralrecon/samplesheet/samplesheet_test_illumina_amplicon.csv` (a small set of paired-end Illumina FASTQs) and sets `genome = 'R64-1-1'` as a placeholder reference. Resource limits are capped at 4 CPUs / 15 GB / 1 h so it runs on a laptop. A successful `-profile test` run produces per-sample FastQC HTML/ZIP under `fastqc/`, a consolidated `multiqc/multiqc_report.html` plus `multiqc_data/` and `multiqc_plots/`, and the standard `pipeline_info/` execution reports. A `test_full` profile exists and points at the corresponding full-size viralrecon samplesheet for CI.

## Reference workflow
nf-core/tbanalyzer (dev, template v1.0dev; https://github.com/nf-core/tbanalyzer), originally authored by @abhi18av. The stated long-term goal is TB-GVAS — comprehensive Mtb species- and strain-level genomic characterization — but the current dev release only implements FastQC + MultiQC on top of the nf-core template. Revisit this sketch once alignment, variant calling, and lineage typing modules land in the pipeline.
