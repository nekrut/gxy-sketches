---
name: short-read-fastqc-multiqc
description: Use when you need a minimal read-level quality-control summary for Illumina
  short-read FASTQ samples (single- or paired-end) and want an aggregated MultiQC
  report, with no trimming, alignment, or variant calling. This sketch covers the
  nf-core/troughgraph dev template, which currently only runs FastQC and MultiQC.
domain: qc
organism_class:
- any
input_data:
- short-reads-single
- short-reads-paired
source:
  ecosystem: nf-core
  workflow: nf-core/troughgraph
  url: https://github.com/nf-core/troughgraph
  version: dev
  license: MIT
  slug: troughgraph
tools:
- name: fastqc
  version: 0.12.1
- name: multiqc
  version: '1.27'
- name: nextflow
tags:
- qc
- fastqc
- multiqc
- illumina
- short-reads
- template
- nf-core
test_data: []
expected_output: []
---

# Short-read FastQC + MultiQC pipeline

## When to use this sketch
- You have Illumina short-read FASTQ files (single-end or paired-end, gzipped) and want per-file quality metrics.
- You want one aggregated HTML report summarising base-quality distributions, adapter contamination, GC content, and overrepresented sequences across many samples.
- You need a quick first-pass QC before deciding on a downstream analysis (alignment, assembly, variant calling, etc.).
- You are running nf-core/troughgraph at its current `dev` stage, which is an nf-core template and only implements FastQC + MultiQC (the repository's stated permafrost-landscape scope is not yet implemented).

## Do not use when
- You need adapter or quality trimming — use a trimming-enabled QC sketch (e.g. fastp/Trim Galore based).
- You need alignment, variant calling, assembly, or expression quantification — pick the domain-specific sketch for that analysis.
- You have long reads (ONT/PacBio) — use a long-read QC sketch (NanoPlot/pycoQC).
- You want contamination screening against reference databases — use a Kraken2/FastQ Screen sketch.
- You need the actual permafrost / trough-graph quantitative analysis advertised in the repository description; it is not implemented in the current `dev` template.

## Analysis outline
1. Prepare a 3-column CSV samplesheet (`sample,fastq_1,fastq_2`); leave `fastq_2` blank for single-end. Rows sharing a `sample` value are concatenated before QC.
2. Run `nextflow run nf-core/troughgraph -profile <docker|singularity|conda> --input samplesheet.csv --outdir results` to launch the pipeline.
3. FastQC runs on each FASTQ, producing per-sample HTML + ZIP reports under `results/fastqc/`.
4. MultiQC aggregates all FastQC outputs and software-version metadata into `results/multiqc/multiqc_report.html`.
5. Nextflow emits execution reports, timeline, trace, DAG, and a `params.json` under `results/pipeline_info/` for provenance.

## Key parameters
- `--input` (required): path to the samplesheet CSV; must match `assets/schema_input.json` (columns `sample`, `fastq_1`, `fastq_2`).
- `--outdir` (required): absolute path to the results directory.
- `-profile`: one of `docker`, `singularity`, `podman`, `apptainer`, `conda`, plus optional `test` for bundled demo data. Multiple profiles may be chained (`-profile test,docker`).
- `--genome` / `--fasta`: optional reference selection via iGenomes (`--genome R64-1-1` in the test profile) or a custom FASTA; not consumed by the current FastQC/MultiQC-only steps but accepted by the schema.
- `--multiqc_title`, `--multiqc_config`, `--multiqc_logo`, `--multiqc_methods_description`: MultiQC report customisation.
- `--email` / `--email_on_fail`: optional run-completion notifications.
- Resource caps for the `test` profile: 4 CPUs, 15 GB RAM, 1 h wall time (set via `process.resourceLimits`).

## Test data
The `test` profile points `--input` at the nf-core test-datasets samplesheet `viralrecon/samplesheet/samplesheet_test_illumina_amplicon.csv` (paired-end Illumina amplicon FASTQs) and sets `--genome R64-1-1`. A `test_full` profile uses the matching `samplesheet_full_illumina_amplicon.csv` from the same location. A successful run is expected to produce per-sample `*_fastqc.html` / `*_fastqc.zip` under `results/fastqc/`, a consolidated `results/multiqc/multiqc_report.html` with a FastQC section for every input FASTQ, a populated `multiqc_data/` directory, and the standard `pipeline_info/` Nextflow execution reports.

## Reference workflow
nf-core/troughgraph (version `1.0dev`, template generated with nf-core tools 3.2.0). The pipeline is an nf-core template stub: its schema advertises input/output, reference-genome, institutional, and generic options, but only FastQC and MultiQC steps are wired up in the current code. Upstream homepage: https://nf-co.re/troughgraph.
