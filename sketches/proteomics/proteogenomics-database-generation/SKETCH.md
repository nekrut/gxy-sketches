---
name: proteogenomics-database-generation
description: Use when you need to build a custom proteogenomics FASTA protein database
  by combining an ENSEMBL reference proteome with non-canonical products (ncRNA, pseudogenes,
  altORFs) and/or variant-derived proteins from COSMIC, cBioPortal, gnomAD, or a user
  VCF, optionally appending decoys for downstream MS/MS peptide identification.
domain: proteomics
organism_class:
- vertebrate
- eukaryote
input_data:
- ensembl-species-name
- optional-vcf
- optional-cosmic-credentials
source:
  ecosystem: nf-core
  workflow: nf-core/proteogenomicsdb
  url: https://github.com/nf-core/proteogenomicsdb
  version: 1.0.0
  license: MIT
tools:
- pypgatk
- nextflow
- decoypyrat
- ensembl-ftp
tags:
- proteogenomics
- protein-database
- fasta
- decoy
- cosmic
- cbioportal
- gnomad
- ensembl
- variant-proteins
- mass-spectrometry
test_data: []
expected_output: []
---

# Proteogenomics protein database generation

## When to use this sketch
- You are preparing a custom protein FASTA for MS/MS peptide/protein search (e.g. MaxQuant, Comet, MSGF+, SearchGUI) and need more than a plain UniProt/ENSEMBL reference.
- You want to augment an ENSEMBL reference proteome with non-canonical products (ncRNA translations, pseudogene translations, alternative ORFs).
- You want variant-containing protein sequences derived from COSMIC, cBioPortal studies, gnomAD exomes, or your own VCF, so you can identify sample- or cancer-specific peptides.
- You need target+decoy databases (reverse, shuffle, or DecoyPyRat) appended in a single, reproducible FASTA for FDR estimation.
- Your species is available in ENSEMBL (human, mouse, and other vertebrates are the primary use case).

## Do not use when
- You only need a stock canonical reference proteome — download directly from UniProt/ENSEMBL instead of running a pipeline.
- You want to call variants from proteomics or genomics data — this pipeline consumes existing variant resources, it does not call variants (see variant-calling sketches).
- You need to run the actual MS/MS search and quantification — this pipeline only builds the search database; use a proteomics search/quant pipeline (e.g. nf-core/quantms) downstream.
- Your organism is not in ENSEMBL (bacteria, most fungi via ENSEMBL Genomes may require alternate config).
- You want spectral identification of novel peptides end-to-end — combine this sketch for DB building with a separate search sketch.

## Analysis outline
1. Download the canonical reference proteome FASTA from ENSEMBL for `ensembl_name` via pypgatk's ENSEMBL downloader.
2. Optionally generate non-canonical protein sequences from ENSEMBL transcript annotations: ncRNA translations (`--ncrna`), pseudogene translations (`--pseudogenes`), and alternative ORFs (`--altorfs`), via pypgatk.
3. Optionally translate variants into mutated protein sequences: COSMIC mutants and cell lines (`--cosmic`, `--cosmic_celllines`, requires COSMIC credentials), cBioPortal studies (`--cbioportal`), gnomAD exomes VCF (`--gnomad`), and/or a user-supplied VCF (`--vcf --vcf_file`).
4. Concatenate the reference, non-canonical, and variant FASTAs into a combined target database.
5. Clean the database with pypgatk (`--clean_database`): drop sequences shorter than `minimum_aa`, handle internal stop codons (optionally splitting into two proteins via `--add_stop_codons`).
6. Generate decoys with the chosen `decoy_method` (`decoypyrat`, `protein-reverse`, or `protein-shuffle`) using `decoy_enzyme`, prefix them with `decoy_prefix`, and append to the final FASTA.
7. Emit a single output FASTA at `${outdir}/${final_database_protein}` plus a `pipeline_info/` directory with Nextflow reports.

## Key parameters
- `ensembl_name`: ENSEMBL species slug, e.g. `homo_sapiens`, `mus_musculus`.
- `add_reference` (default `true`): include the canonical ENSEMBL proteome.
- `ncrna`, `pseudogenes`, `altorfs`, `ensembl`: toggle each class of non-canonical sequences (all default off).
- `cosmic`, `cosmic_celllines`, `cosmic_user_name`, `cosmic_password`, `cosmic_cancer_type` (default `all`), `cosmic_cellline_name` (default `all`): COSMIC variant proteome settings; account credentials are mandatory.
- `cbioportal`, `cbioportal_study_id`, `cbioportal_accepted_values` (default `all`), `cbioportal_filter_column` (default `CANCER_TYPE`).
- `gnomad`, `gnomad_file_url` (default gnomAD exomes r2.1.1 sites VCF).
- `vcf`, `vcf_file`, `af_field`: generic VCF-based variant translation.
- `decoy` (bool), `decoy_method` (`decoypyrat`|`protein-reverse`|`protein-shuffle`, default `decoypyrat`), `decoy_enzyme` (default `Trypsin`), `decoy_prefix` (default `Decoy_`).
- `clean_database`, `minimum_aa` (default `6`), `add_stop_codons`.
- `final_database_protein` (default `final_proteinDB.fa`), `outdir` (default `./results`).

## Test data
The bundled `test` profile runs without any user-supplied files: it points `ensembl_name` at `meleagris_gallopavo` (turkey) and lets the pipeline pull the small canonical ENSEMBL proteome over the network. All variant sources (`ensembl`, `gnomad`, `cosmic`, `cosmic_celllines`, `cbioportal`) are disabled while `decoy` and `clean_database` are enabled, so the run exercises download, cleanup, and DecoyPyRat-based decoy generation on a minimal proteome. The expected output is a single cleaned target+decoy FASTA at `results/final_proteinDB.fa` containing turkey reference proteins plus matching `Decoy_`-prefixed entries, together with a `pipeline_info/` directory of Nextflow execution reports. A larger `test_full` profile repeats the run on `homo_sapiens` with `cbioportal=true` and `decoy=true` to cover a realistic cBioPortal variant proteome build.

## Reference workflow
nf-core/pgdb v1.0.0 (https://github.com/nf-core/pgdb), built on top of pypgatk (https://github.com/bigbio/py-pgatk). See pipeline docs at https://nf-co.re/pgdb and the pypgatk handbook at https://pgatk.readthedocs.io/ for per-source parameter details.
