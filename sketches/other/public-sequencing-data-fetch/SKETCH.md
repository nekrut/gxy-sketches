---
name: public-sequencing-data-fetch
description: Use when you need to download raw FastQ files and metadata for public
  sequencing accessions from SRA, ENA, DDBJ, or GEO (e.g. SRR/ERR/DRR run ids, SRX/ERX/DRX
  experiment ids, GSE/GSM, PRJNA/PRJEB study ids) and produce a ready-to-use samplesheet
  for a downstream nf-core pipeline.
domain: other
organism_class:
- any
input_data:
- accession-id-list
source:
  ecosystem: nf-core
  workflow: nf-core/fetchngs
  url: https://github.com/nf-core/fetchngs
  version: 1.12.0
  license: MIT
  slug: fetchngs
tools:
- name: nf-core/fetchngs
- name: sra-tools
  version: 3.0.8
- name: aspera-cli
- name: wget
- name: ENA API
tags:
- sra
- ena
- ddbj
- geo
- fastq-download
- metadata
- samplesheet
- public-data
- data-retrieval
test_data: []
expected_output: []
---

# Fetch public sequencing reads and metadata from SRA/ENA/DDBJ/GEO

## When to use this sketch
- You have a list of public database identifiers (SRA/ENA/DDBJ/GEO) and need the raw FastQ files plus curated metadata locally.
- Accepted id types include run (SRR/ERR/DRR), experiment (SRX/ERX/DRX), sample (SRS/ERS/DRS, SAMN/SAMEA/SAMD), study (SRP/ERP/DRP, PRJNA/PRJEB/PRJDB), submission (SRA/ERA/DRA), and GEO (GSE/GSM) ids.
- You want the download step to automatically resolve run ids up to experiment level so technical replicate runs of the same library can be merged downstream.
- You want an auto-generated samplesheet pre-formatted for a supported nf-core pipeline (rnaseq, atacseq, viralrecon Illumina mode, taxprofiler).
- You need to pull protected dbGaP data on AWS/GCP using a JWT cart file.

## Do not use when
- You already have local FASTQs — skip data fetching and route directly to the analysis sketch (e.g. bulk-rnaseq, variant-calling-*).
- You need reference genomes, annotation, or non-sequencing assets — fetchngs only retrieves sequencing reads and their metadata.
- Your data lives in a private S3/GCS bucket, local lab NAS, or Basespace — use the appropriate transfer tool instead, not fetchngs.
- You want to perform any QC, trimming, alignment, or quantification — fetchngs stops at downloaded FastQs and a samplesheet.

## Analysis outline
1. Prepare a plain-text `ids.csv` with one database identifier per line.
2. Resolve each id to its experiment-level run accessions via the ENA API (`sra_ids_to_runinfo.py`).
3. Fetch extensive per-run metadata from the ENA portal API.
4. Download FastQ files: `wget` from ENA FTP with md5 check (default), `aspera-cli` from ENA (`--download_method aspera`), or `sra-tools` prefetch + `fasterq-dump` when direct links are absent or `--download_method sratools` is forced.
5. Collate all metadata and FastQ paths into `samplesheet.csv`, plus `id_mappings.csv` and a MultiQC rename-config for informative sample labels.
6. Optionally shape the samplesheet columns for a downstream nf-core pipeline via `--nf_core_pipeline`.

## Key parameters
- `input`: path to the one-id-per-line CSV/TSV/TXT of accessions (required).
- `outdir`: absolute output directory (required).
- `download_method`: `ftp` (default, parallel wget + md5), `aspera` (aspera-cli + md5), or `sratools` (prefetch/fasterq-dump). Use `sratools` when samples may have >2 FastQ files per run (e.g. 10x/UMI libraries) — ENA FTP hides technical reads.
- `nf_core_pipeline`: one of `rnaseq`, `atacseq`, `viralrecon`, `taxprofiler` to emit a ready-to-consume samplesheet for that pipeline.
- `nf_core_rnaseq_strandedness`: default `auto` (works with nf-core/rnaseq ≥ v3.10).
- `ena_metadata_fields`: comma-separated override of ENA metadata columns; must at minimum include `run_accession,experiment_accession,library_layout,fastq_ftp,fastq_md5`.
- `sample_mapping_fields`: ENA fields used to build `id_mappings.csv` / MultiQC rename config.
- `skip_fastq_download`: metadata-only mode, no FastQs written.
- `dbgap_key`: path to a JWT cart file for protected dbGaP studies (cloud environments only; the cart must cover every run in each resolved experiment).

## Test data
The `test` profile downloads a small public accession list, `sra_ids_test.csv` from `nf-core/test-datasets` (branch ref `2732b911…`, path `testdata/v1.12.0/sra_ids_test.csv`), constrained to `max_cpus=2`, `max_memory=6.GB`, `max_time=6.h` so it runs on GitHub Actions. Running `-profile test,docker --outdir results` is expected to produce: downloaded FastQs under `results/fastq/` with matching `.md5` files under `results/fastq/md5/`; ENA metadata TSVs `*.runinfo_ftp.tsv` and `*.runinfo.tsv` under `results/metadata/`; and a collated `results/samplesheet/samplesheet.csv` plus `id_mappings.csv` and `multiqc_config.yml`. The `test_full` profile uses the larger `sra_ids_rnaseq_test_full.csv` accession list mirroring the nf-core/rnaseq full test inputs.

## Reference workflow
nf-core/fetchngs v1.12.0 — https://github.com/nf-core/fetchngs (MIT, DOI 10.5281/zenodo.5070524).
