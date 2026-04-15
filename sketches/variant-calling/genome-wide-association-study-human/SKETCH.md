---
name: genome-wide-association-study-human
description: Use when you need to run a genome-wide association study (GWAS) on human
  cohort data to identify SNPs statistically associated with a phenotype or disease
  trait. Assumes population-scale diploid human samples with genotype and phenotype
  information.
domain: variant-calling
organism_class:
- human
- vertebrate
- diploid
input_data:
- short-reads-paired
- samplesheet-csv
source:
  ecosystem: nf-core
  workflow: nf-core/gwas
  url: https://github.com/nf-core/gwas
  version: dev
  license: MIT
  slug: gwas
tools:
- name: multiqc
- name: nextflow
tags:
- gwas
- association
- human
- population-genetics
- snp
- cohort
test_data: []
expected_output: []
---

# Genome-wide association study (human cohort)

## When to use this sketch
- You have a cohort of human samples with sequencing data (Illumina short reads) and a phenotype/trait of interest, and want to test SNPs for statistical association with that trait.
- You need a reproducible nf-core style pipeline for population-scale association testing rather than a per-sample variant call.
- The cohort is diploid human data where standard GWAS assumptions (Hardy-Weinberg, linkage disequilibrium, population structure correction) apply.
- You want the pipeline to handle sample QC aggregation and produce a MultiQC summary alongside association results.

## Do not use when
- You only need per-sample germline variant calls without association testing — use a human germline variant calling sketch instead.
- Your organism is bacterial or haploid — use `haploid-variant-calling-bacterial` or a comparable prokaryote sketch.
- You are doing rare-variant burden testing on exome/WES data where GWAS single-marker tests are underpowered — use a rare-variant / burden-testing workflow.
- You need somatic variant calling from tumor/normal pairs — use a somatic calling sketch.
- Your input is already a called VCF with phenotypes and you only need the association step — a lighter PLINK/REGENIE-only workflow is more appropriate.

## Analysis outline
1. Ingest a samplesheet CSV listing `sample,fastq_1,fastq_2` rows (paired or single end); concatenate lanes per sample where identifiers repeat.
2. Perform per-sample read QC and aggregate metrics for downstream reporting.
3. Align reads and generate genotype calls across the cohort (pipeline-provided alignment and calling steps).
4. Apply cohort-level variant and sample QC filters appropriate for association testing.
5. Run genome-wide single-marker association tests against the phenotype of interest.
6. Aggregate per-step QC and run summaries with MultiQC into a single HTML report.

## Key parameters
- `--input`: path to the samplesheet CSV with `sample,fastq_1,fastq_2` columns; required.
- `--outdir`: absolute path to the results directory; required.
- `-profile`: one of `docker`, `singularity`, `conda`, or an institutional profile — controls the software environment.
- `-profile test`: runs the bundled minimal test samplesheet for smoke-testing without providing any other data paths.
- `-params-file`: YAML/JSON file to pin parameters for reproducible reruns instead of passing flags on the CLI.
- `--email` / `--multiqc_title`: optional run-summary email and MultiQC report title.

## Test data
The `test` profile points `--input` at `gwas/samplesheets/samplesheet_gwas_test.csv` from the nf-core test-datasets repository (a minimal cohort samplesheet of paired-end FASTQs) and runs under a resource cap of 4 CPUs / 8 GB / 1 h. The `test_full` profile uses a larger samplesheet plus a reference FASTA for end-to-end validation. A successful test run produces a MultiQC HTML report under `multiqc/multiqc_report.html`, a `pipeline_info/` directory with Nextflow execution reports, and a validated samplesheet copy, confirming that inputs were parsed and the pipeline executed to completion.

## Reference workflow
nf-core/gwas (https://github.com/nf-core/gwas), version `1.0.0dev` (nf-core template 3.5.2). Requires Nextflow ≥ 25.04.0 and is distributed under the MIT license.
