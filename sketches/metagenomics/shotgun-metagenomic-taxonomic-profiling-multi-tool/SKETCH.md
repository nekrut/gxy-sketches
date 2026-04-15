---
name: shotgun-metagenomic-taxonomic-profiling-multi-tool
description: Use when you need to taxonomically classify and profile shotgun metagenomic
  sequencing reads (short-read Illumina and/or long-read Nanopore) against one or
  more reference databases in parallel using multiple classifiers (Kraken2, MetaPhlAn,
  Centrifuge, Kaiju, DIAMOND, KrakenUniq, mOTUs, MALT, KMCP, ganon) with standardised
  cross-tool output tables. For community composition of microbial DNA, not 16S amplicons
  or assembly-based analyses.
domain: metagenomics
organism_class:
- microbial
- bacterial
- viral
- eukaryote
input_data:
- short-reads-paired
- short-reads-single
- long-reads-ont
- long-reads-fasta
- classifier-database
source:
  ecosystem: nf-core
  workflow: nf-core/taxprofiler
  url: https://github.com/nf-core/taxprofiler
  version: 1.2.6
  license: MIT
  slug: taxprofiler
tools:
- name: fastp
- name: adapterremoval
  version: 2.3.2
- name: porechop
- name: filtlong
  version: 0.2.1
- name: nanoq
  version: 0.10.0
- name: bowtie2
- name: minimap2
- name: kraken2
- name: bracken
- name: krakenuniq
- name: centrifuge
  version: 1.0.4.2
- name: kaiju
  version: 1.10.0
- name: diamond
- name: malt
- name: metaphlan
  version: 4.1.1
- name: motus
- name: kmcp
- name: ganon
- name: taxpasta
- name: krona
- name: multiqc
- name: nonpareil
  version: 3.5.5
tags:
- metagenomics
- taxonomic-profiling
- taxonomic-classification
- shotgun
- microbiome
- kraken2
- metaphlan
- multi-classifier
- taxpasta
test_data: []
expected_output: []
---

# Shotgun metagenomic taxonomic profiling (multi-tool)

## When to use this sketch
- User has shotgun metagenomic sequencing reads (Illumina short reads and/or Oxford Nanopore long reads) and wants to know *what is in the sample* (community composition / relative abundance).
- User wants to run multiple classifiers/profilers in parallel (e.g. Kraken2 + MetaPhlAn + Centrifuge) against one or more reference databases and compare results via a standardised merged taxon table.
- User needs a production-grade pipeline that handles raw-read QC, adapter trimming, complexity filtering, host-read removal, and run merging before classification.
- User wants per-tool per-database profiles plus a unified cross-tool TSV/BIOM output suitable for downstream diversity or differential-abundance analysis.
- Typical contexts: human gut/skin microbiome, environmental metagenomics, ancient DNA screening, clinical pathogen detection, wastewater surveillance.

## Do not use when
- The input is 16S/18S/ITS amplicon data — use an amplicon sketch (DADA2/QIIME2) instead.
- The goal is *de novo* metagenome assembly, binning, or MAG recovery — use an assembly-oriented sketch (e.g. nf-core/mag).
- The goal is calling variants against a single known reference — use a variant-calling sketch.
- The goal is functional profiling (KEGG/pathways) rather than taxonomy — taxprofiler does not run HUMAnN-style functional profilers.
- You only want to validate specific taxonomic hits post-classification — use a validation pipeline (e.g. genomic-medicine-sweden/metaval) downstream of this sketch.

## Analysis outline
1. Read QC on raw reads with FastQC (or falco for long reads).
2. Short-read preprocessing: adapter/quality trimming with fastp or AdapterRemoval2; optional pair merging; optional length filter.
3. Long-read preprocessing: adapter trimming with Porechop_ABI (or Porechop); length/quality filtering with nanoq (or Filtlong).
4. Optional low-complexity filtering with bbduk, PRINSEQ++, or fastp (short reads only).
5. Optional metagenome coverage/redundancy estimation with Nonpareil (short reads, shallow libraries).
6. Optional host-read removal: Bowtie2 (short reads) or minimap2 (long reads) against a host FASTA; keep unmapped reads via samtools.
7. Optional run/library merging per sample (`perform_runmerging`).
8. Parallel taxonomic classification/profiling, each gated on a `--run_<tool>` flag plus a matching row in the database sheet: Kraken2, Bracken (requires Kraken2), KrakenUniq, Centrifuge, Kaiju, DIAMOND, MALT, MetaPhlAn, mOTUs, KMCP, ganon.
9. Per-tool multi-sample merged reports (e.g. `combine_kreports.py`, `kaiju2table`, `motus merge`) and standardised cross-tool tables with Taxpasta (`taxpasta merge`/`standardise`).
10. Visualisation with Krona interactive pie charts (Kraken2/Centrifuge/Kaiju/MALT) and aggregate MultiQC report.

## Key parameters
- `--input samplesheet.csv` — 6-column sheet: `sample,run_accession,instrument_platform,fastq_1,fastq_2,fasta`. Platform from ENA controlled vocab (`ILLUMINA`, `OXFORD_NANOPORE`, ...). FASTA rows bypass preprocessing.
- `--databases databases.csv` — 4- or 5-column sheet: `tool,db_name,db_params[,db_type],db_path`. `db_path` may be a directory or `.tar.gz`. `db_type` ∈ `short`, `long`, `short;long` (default both).
- `--run_<tool>` flags (opt-in): `--run_kraken2`, `--run_bracken`, `--run_krakenuniq`, `--run_centrifuge`, `--run_kaiju`, `--run_diamond`, `--run_malt`, `--run_metaphlan`, `--run_motus`, `--run_kmcp`, `--run_ganon`. A tool runs only when BOTH its flag and a matching DB row are provided.
- Preprocessing toggles: `--perform_shortread_qc`, `--perform_longread_qc`, `--shortread_qc_mergepairs`, `--perform_shortread_complexityfilter` (`--shortread_complexityfilter_tool bbduk|prinseqplusplus|fastp`), `--perform_shortread_hostremoval`, `--perform_longread_hostremoval` (requires `--hostremoval_reference <host.fa>`), `--perform_runmerging`.
- Bracken special case: `db_params` must use `;` to separate Kraken2 args from Bracken args (e.g. `;-r 150` or `;-l S`). Bracken is auto-skipped on `OXFORD_NANOPORE` rows; KMCP and ganon are also short-read only.
- DIAMOND: paired-end only uses R1 unless `--shortread_qc_mergepairs`; `--diamond_output_format tsv|sam|daa|...`; `--diamond_save_reads` forces SAM and disables taxon tables.
- Standardisation: `--run_profile_standardisation` enables Taxpasta; `--standardisation_taxpasta_format tsv|csv|biom|arrow|parquet`; `--taxpasta_taxonomy_dir <taxdump>` plus `--taxpasta_add_name/_rank/_lineage` to enrich the merged table.
- Visualisation: `--run_krona` (+ `--krona_taxonomy_directory` required for MALT Krona plots).
- Outputs: `--save_analysis_ready_fastqs` to keep the final cleaned reads that actually went into classification; per-tool `--*_save_reads` / `--*_save_readclassifications` flags to retain aligned-read outputs.

## Test data
The bundled `-profile test` configuration pulls a samplesheet and `database_v1.2.csv` from the nf-core test-datasets taxprofiler branch, plus the shared `homo_sapiens/genome/genome.fasta` as a host-removal reference and a sarscov2 `krona_taxonomy.tab`. The samplesheet exercises a mix of paired/single-end Illumina FASTQs and at least one Oxford Nanopore run so that both short- and long-read branches fire. The database sheet provides small demo indices for Kraken2, Bracken, KrakenUniq, Centrifuge, Kaiju, DIAMOND, MetaPhlAn, KMCP, and ganon (MALT and mOTUs are disabled in the default test). A successful run produces FastQC HTMLs, fastp/AdapterRemoval + Porechop/nanoq logs, Bowtie2/minimap2 host-removal stats, per-tool classification reports under `kraken2/`, `bracken/`, `centrifuge/`, `kaiju/`, `metaphlan/`, `diamond/`, `krakenuniq/`, `kmcp/`, `ganon/`, standardised per-database tables under `taxpasta/`, Krona HTML plots under `krona/`, and a top-level `multiqc/multiqc_report.html` summarising every stage. The full-size test (`-profile test_full`) uses the Meslier 2022 benchmarking dataset with a viral host reference and enables MALT and mOTUs additionally.

## Reference workflow
nf-core/taxprofiler v1.2.6 (https://github.com/nf-core/taxprofiler). Cite Stamouli et al., bioRxiv 2023, doi:10.1101/2023.10.20.563221 and the Zenodo DOI 10.5281/zenodo.7728364. Individual classifiers/profilers and Taxpasta have their own citations listed in `CITATIONS.md`.
