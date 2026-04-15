---
name: pacbio-hifi-tumor-normal-somatic
description: 'Use when you have matched tumor/normal PacBio HiFi long-read sequencing
  data from a human cancer sample and want an end-to-end somatic characterisation
  pipeline scaffold (QC plus intended somatic SNV/indel/SV/CNV, tumor purity/clonality,
  HRD, and methylation/DMR analyses). Note: the upstream pipeline is in early development
  (1.0.0dev) and only read QC is wired up so far.'
domain: variant-calling
organism_class:
- vertebrate
- diploid
- human
input_data:
- long-reads-pacbio-hifi
- tumor-normal-paired
- reference-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/pacsomatic
  url: https://github.com/nf-core/pacsomatic
  version: dev
  license: MIT
  slug: pacsomatic
tools:
- name: fastqc
  version: 0.12.1
- name: multiqc
  version: 1.25.1
tags:
- somatic
- cancer
- tumor-normal
- pacbio
- hifi
- long-read
- snv
- indel
- sv
- cnv
- hrd
- methylation
- dmr
test_data: []
expected_output: []
---

# PacBio HiFi tumor/normal somatic genomics

## When to use this sketch
- Matched tumor and normal samples from a human cancer patient, sequenced on PacBio HiFi.
- You want a single nf-core pipeline scaffold that is intended to cover somatic SNV/indel, SV, and CNV calling, plus downstream tumor purity/clonality, HRD (CHORD), and methylation/DMR analyses.
- You are comfortable running a pre-release pipeline whose present implementation only performs raw-read QC (FastQC + MultiQC) and treating downstream modules as TODO.
- You want an nf-core-style samplesheet-driven entry point with iGenomes/FASTA reference support, Docker/Singularity/Conda profiles, and standard Nextflow reporting.

## Do not use when
- You have Illumina short reads — use an Illumina somatic pipeline such as `nf-core/sarek` instead of this sketch.
- You have only a single (tumor-only or normal-only) sample with no matched control — somatic variant calling requires a matched pair; consider a germline long-read sketch.
- Your organism is not human/vertebrate cancer (e.g. bacterial, viral, plant) — pick a domain-specific sibling sketch.
- You need a production-grade, validated somatic caller today — the downstream somatic modules in `nf-core/pacsomatic` are not yet implemented and the CITATIONS currently list only FastQC, MultiQC, and framework tools.
- You are doing germline long-read variant calling or de novo assembly — use a dedicated long-read germline or assembly sketch.

## Analysis outline
1. Parse samplesheet CSV (`sample,fastq_1,fastq_2`) and concatenate per-sample FASTQs when a sample has multiple rows.
2. Run `FastQC` on each set of raw reads for per-sample quality metrics.
3. Aggregate QC and software versions into a `MultiQC` HTML report.
4. (Planned, not yet implemented in source) Align tumor and normal HiFi reads to the reference and pair them for downstream somatic analysis.
5. (Planned) Somatic SNV/indel, SV, and CNV calling with annotation.
6. (Planned) Tumor purity and clonality estimation.
7. (Planned) Homologous recombination deficiency assessment via CHORD.
8. (Planned) Methylation calling and differential methylation region (DMR) detection and annotation.

## Key parameters
- `--input`: path to samplesheet CSV with columns `sample,fastq_1,fastq_2` (required).
- `--outdir`: absolute output directory (required).
- `--genome`: iGenomes key (e.g. `GRCh38`, `GRCh37`) for a human cancer run; mutually exclusive with `--fasta`.
- `--fasta`: path to a custom reference FASTA when not using iGenomes.
- `--igenomes_ignore`: set to `true` to fully disable the iGenomes config when passing a custom `--fasta`.
- `--multiqc_title` / `--multiqc_config`: customise the aggregated QC report.
- `-profile`: one of `docker`, `singularity`, `podman`, `apptainer`, `conda`, plus the built-in `test` / `test_full` profiles for CI-style runs.
- `-params-file`: YAML/JSON file carrying the above; use this instead of `-c` for parameters.

## Test data
The bundled `test` and `test_full` profiles do not yet ship real PacBio HiFi tumor/normal fixtures — they are template placeholders inherited from the nf-core template. They point `--input` at the `viralrecon` Illumina amplicon samplesheets hosted under `nf-core/test-datasets` and set `--genome R64-1-1` (S. cerevisiae) purely to exercise the FastQC + MultiQC path on tiny data. A successful `-profile test` run is expected to produce a `fastqc/` directory with per-sample `*_fastqc.html` / `*_fastqc.zip`, a top-level `multiqc/multiqc_report.html` with its `multiqc_data/` and `multiqc_plots/` companions, and the standard `pipeline_info/` directory (execution report, timeline, trace, DAG, `software_versions.yml`, reformatted `samplesheet.valid.csv`, `params.json`). No somatic variant, SV, CNV, HRD, or methylation outputs are produced yet.

## Reference workflow
`nf-core/pacsomatic` (version `1.0.0dev`, Nextflow DSL2 ≥ 24.04.2, MIT-licensed), authored by Wenchao Zhang and Haidong Yi. Repository: https://github.com/nf-core/pacsomatic. Consult the pipeline's `nextflow_schema.json`, `docs/usage.md`, and `docs/output.md` for authoritative parameter and output definitions, and watch upstream releases for when the planned somatic, HRD, and methylation modules land.
