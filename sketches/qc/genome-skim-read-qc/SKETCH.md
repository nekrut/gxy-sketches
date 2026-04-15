---
name: genome-skim-read-qc
description: Use when you need baseline quality control of low-coverage whole-genome
  shotgun (genome skim) short-read Illumina data prior to organelle assembly or off-target
  genome analysis. Produces per-sample FastQC reports and an aggregated MultiQC summary;
  does not yet perform filtering, assembly, or annotation.
domain: qc
organism_class:
- eukaryote
input_data:
- short-reads-paired
- short-reads-single
source:
  ecosystem: nf-core
  workflow: nf-core/genomeskim
  url: https://github.com/nf-core/genomeskim
  version: dev
  license: MIT
  slug: genomeskim
tools:
- name: fastqc
  version: 0.11.9
- name: multiqc
  version: '1.12'
tags:
- genome-skim
- qc
- fastqc
- multiqc
- short-reads
- organelle-prep
test_data: []
expected_output: []
---

# Genome skim short-read QC

## When to use this sketch
- You have low-coverage (~0.1-5x) Illumina short-read shotgun data generated as a genome skim, typically intended for downstream organelle (plastid / mitochondrion) assembly or nuclear marker mining.
- You need a first-pass quality assessment: base-quality distributions, adapter content, duplication, overrepresented sequences, and a single aggregated report across many samples.
- Inputs are gzipped FASTQ files described by an nf-core-style samplesheet with `sample,fastq_1,fastq_2` columns; single-end rows leave `fastq_2` empty.
- Multiple sequencing runs/lanes per sample are expected — the pipeline concatenates reads sharing a `sample` identifier before QC.

## Do not use when
- You need actual trimming, filtering, deduplication, or contamination removal — this pipeline (in its current `dev` state) only runs FastQC + MultiQC and does not modify reads. Use `nf-core/fastquorum`, `nf-core/readsimulator` preprocessing, or a dedicated fastp/trim-galore workflow instead.
- You want organelle assembly (plastome / mitogenome). Despite the pipeline's stated intent, organelle assembly steps are not yet implemented here; use `GetOrganelle`, `NOVOPlasty`, or a dedicated organelle assembly workflow.
- You are calling variants, assembling nuclear genomes, or doing RNA-seq — pick the domain-specific nf-core pipeline (`nf-core/sarek`, `nf-core/bacass`, `nf-core/rnaseq`, etc.).
- You are working with long reads (ONT/PacBio) — FastQC is not the right QC tool; use `nf-core/nanoseq`-style QC.

## Analysis outline
1. Parse and validate the input samplesheet (`sample,fastq_1,fastq_2`), auto-detecting single- vs paired-end rows.
2. Concatenate FASTQ files that share a `sample` identifier across lanes/runs.
3. Run `FastQC` on each (merged) sample to produce per-sample HTML + zipped metrics.
4. Run `MultiQC` to aggregate FastQC outputs (and pipeline software versions) into a single HTML report.
5. Emit Nextflow execution reports (`execution_report.html`, `execution_timeline.html`, `execution_trace.txt`, `pipeline_dag.svg`) into `pipeline_info/`.

## Key parameters
- `--input` (required): path to the samplesheet CSV with header `sample,fastq_1,fastq_2`.
- `--outdir` (required): absolute output directory; produces `fastqc/`, `multiqc/`, and `pipeline_info/` subdirectories.
- `--genome` / `--fasta`: reference selector from iGenomes (e.g. `GRCh38`, `R64-1-1`) or a direct FASTA path. Currently only wired through for future reference-dependent steps; not consumed by FastQC/MultiQC themselves.
- `--igenomes_ignore`: set `true` to bypass iGenomes config when supplying a custom `--fasta`.
- `--multiqc_title`, `--multiqc_config`: customize the aggregated report title and MultiQC config.
- `-profile`: must include a container engine (`docker`, `singularity`, `podman`, `conda`, ...) plus optionally `test` for the bundled minimal dataset.
- Resource caps (`--max_cpus`, `--max_memory`, `--max_time`) default to 16 / 128.GB / 240.h and should be lowered on laptops or CI (the `test` profile sets 2 / 6.GB / 6.h).

## Test data
The bundled `test` profile reuses the nf-core viralrecon Illumina amplicon samplesheet (`samplesheet_test_illumina_amplicon.csv` from `nf-core/test-datasets`) as a stand-in minimal input, with `genome = 'R64-1-1'` (*Saccharomyces cerevisiae*) selected from iGenomes. It is sized to run within 2 CPUs / 6 GB / 6 h on GitHub Actions. Running `nextflow run nf-core/genomeskim -profile test,docker --outdir results` is expected to produce per-sample `fastqc/*_fastqc.html` and `*_fastqc.zip` files, a `multiqc/multiqc_report.html` with parsed `multiqc_data/` and `multiqc_plots/` subdirectories, and a `pipeline_info/` folder containing Nextflow execution reports and a reformatted `samplesheet.valid.csv`. The `test_full` profile points at the larger viralrecon full-size amplicon samplesheet for AWS CI benchmarking.

## Reference workflow
nf-core/genomeskim (version `dev`, MIT license) — https://github.com/nf-core/genomeskim. Note that as of the `dev` branch the implemented steps are limited to FastQC and MultiQC; the README advertises future genome-skim filtering and organelle assembly modules that are not yet present, so treat this sketch strictly as a QC entry point.
