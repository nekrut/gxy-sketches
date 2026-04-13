---
name: ena-submission-mags-bins-assemblies
description: Use when you need to submit metagenome-assembled genomes (MAGs), bins,
  or metagenomic assemblies to the ENA public archive via Webin-CLI, including automated
  study registration, coverage/completeness/taxonomy metadata filling, and manifest
  generation.
domain: other
organism_class:
- microbial
- metagenome
input_data:
- assembly-fasta
- mag-fasta
- short-reads-paired
- ena-metadata
source:
  ecosystem: nf-core
  workflow: nf-core/seqsubmit
  url: https://github.com/nf-core/seqsubmit
  version: dev
  license: MIT
tools:
- ena-webin-cli
- genome_uploader
- assembly_uploader
- coverm
- checkm2
- cat_pack
- barrnap
- trnascan-se
- multiqc
tags:
- ena
- submission
- mag
- bin
- metagenomic-assembly
- insdc
- webin
- upload
- archive
- mgnify
test_data: []
expected_output: []
---

# ENA submission for MAGs, bins, and metagenomic assemblies

## When to use this sketch
- You have finished assembling or binning metagenomic data and need to deposit the resulting sequences into ENA/INSDC for publication or archiving.
- Raw reads underlying the assemblies are already submitted to ENA and you have their run accessions (e.g. ERR/SRR IDs).
- You hold a valid ENA Webin account and can provide credentials as Nextflow secrets (`ENA_WEBIN`, `ENA_WEBIN_PASSWORD`).
- You want automated metadata completion: computing coverage from reads with CoverM, completeness/contamination with CheckM2, taxonomic lineage with CAT/BAT, and rRNA/tRNA presence with barrnap + tRNAscan-SE for MISAG/MIMAG classification.
- You need to either reuse an existing ENA study accession (`PRJ`/`ERP`) or register a fresh study from a metadata file before uploading.

## Do not use when
- You need to submit raw sequencing reads (FASTQ) rather than assemblies — this pipeline assumes reads are already in ENA.
- You are submitting isolate/bacterial single-organism genome assemblies — ENA has a different assembly submission route and this workflow targets metagenomic data.
- You need assembly or binning itself — run an assembly pipeline (e.g. nf-core/mag) first and feed its outputs here.
- You want to compute MAG quality for analysis only (no upload) — run CheckM2/CAT_pack directly; submission steps are the point of this pipeline.
- You need to submit to NCBI/GenBank or DDBJ directly; this workflow only targets ENA Webin-CLI.

## Analysis outline
1. Parse the `--mode`-specific samplesheet (`mags`/`bins` → genome schema, `metagenomic_assemblies` → assembly schema) and validate columns.
2. Optionally register a new ENA study via `REGISTERSTUDY` from `--study_metadata` (JSON/CSV/TSV), otherwise reuse `--submission_study` accession.
3. For rows missing `coverage`/`genome_coverage`, map reads back with **CoverM** (`coverm contig` for assemblies, `coverm genome` for MAGs/bins) to compute average depth.
4. For MAGs/bins missing `completeness`/`contamination`, run **CheckM2** (database from `--checkm2_db` or downloaded from Zenodo id `14897628`).
5. For MAGs/bins missing `NCBI_lineage`, run **CAT_pack** BAT with the `nr` database (or `--cat_db`) to assign NCBI taxonomy.
6. For MAGs/bins missing `RNA_presence`, run **barrnap** (rRNA) and **tRNAscan-SE 2.0** (tRNA); flag `Yes` when all of 16S/23S/5S exceed `rrna_limit` (80% length) and tRNA count ≥ `trna_limit` (18).
7. Assemble per-sample metadata CSVs and generate ENA manifests with `genome_uploader` (MAGs/bins) or `assembly_uploader` (assemblies).
8. Submit or dry-run validate with **ENA Webin-CLI** against the TEST or LIVE endpoint depending on `--test_upload`.
9. Aggregate run stats in **MultiQC** and publish metadata, manifests, and Webin-CLI accession TSVs under `--outdir`.

## Key parameters
- `--mode`: one of `mags`, `bins`, `metagenomic_assemblies` — selects GENOMESUBMIT vs ASSEMBLYSUBMIT subworkflow.
- `--input`: samplesheet CSV; columns differ per mode and must match the exact order shown in `docs/usage.md`.
- `--centre_name`: submitter organisation (required, passed as Webin-CLI `-centerName`).
- `--submission_study` **XOR** `--study_metadata`: existing ENA `PRJ`/`ERP` accession, or a metadata file to auto-register a new study.
- `--test_upload`: default `true`; submits to the ENA TEST endpoint (data purged after 24 h). Set `false` only for real LIVE submissions.
- `--webincli_submit`: default `true`; set `false` to validate manifests without uploading.
- `--upload_tpa`: default `false`; set `true` for Third Party Assembly studies.
- `--upload_force`: default `true`; forces regeneration of sample XMLs in `genome_uploader`.
- `--webin_cli_version`: default `9.0.3`.
- `--checkm2_db` / `--checkm2_db_zenodo_id` (default `14897628`): CheckM2 database source.
- `--cat_db` / `--cat_db_download_id` (default `nr`): CAT_pack database (use `nr`, not `gtdb`, because ENA requires NCBI taxonomy).
- `--rrna_limit` (default `80`) and `--trna_limit` (default `18`): thresholds for the RNA presence decision.
- Secrets: `nextflow secrets set ENA_WEBIN` and `ENA_WEBIN_PASSWORD` must be set before launch.

## Test data
The bundled `test` profile runs `--mode mags` against a small multi-bin samplesheet (`seqsubmit/samplesheets/mag_multiple_bins_missing_metadata.csv`) hosted on `nf-core/test-datasets`, with `--submission_study PRJEB98843`, `--centre_name TEST_CENTER`, `--test_upload true`, and a tiny pre-built CAT_pack database (`small_cat_db/tax-db.tar.gz`); CheckM2 runs with a downloaded database. Because the sheet intentionally omits several metadata fields, the run exercises CoverM coverage estimation, CheckM2 completeness/contamination, CAT/BAT lineage assignment, and barrnap + tRNAscan-SE RNA inference, then builds manifests and performs a TEST-server Webin-CLI validation submission. Expected outputs under `--outdir` include `mags/genomes_metadata.csv`, `mags/upload/manifests/`, per-sample `coverage/`, `checkm2/`, `taxonomy/`, `rna/barrnap/`, `rna/trnascanse/`, `upload/webin_cli/` accession TSVs, plus a `multiqc/multiqc_report.html` and the standard `pipeline_info/` reports.

## Reference workflow
[nf-core/seqsubmit](https://github.com/nf-core/seqsubmit) (dev, template 3.5.1), MIT license. Wraps `genome_uploader`, `assembly_uploader`, and ENA Webin-CLI 9.0.3 alongside CoverM, CheckM2, CAT_pack, barrnap, and tRNAscan-SE 2.0. Maintained by the EBI Metagenomics / MGnify team.
