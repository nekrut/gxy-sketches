---
name: metagenomic-amr-profiling-short-reads
description: Use when you need to taxonomically profile a metagenomic short-read sample
  and detect antibiotic resistance genes (ARGs) directly from the reads (no assembly),
  with ARG hits normalized to the CARD ARO ontology. Assumes QC'd, host-decontaminated
  paired Illumina FASTQs.
domain: metagenomics
organism_class:
- microbial-community
- bacterial
input_data:
- short-reads-paired
- sylph-database
- sylph-taxonomy-database
- groot-arg-database
- deeparg-database
source:
  ecosystem: iwc
  workflow: Metagenomics Taxonomic and Antibiotic Resistance Gene (ARG) Profiling
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/microbiome/metagenomic-raw-reads-amr-analysis
  version: '1.1'
  license: GPL-3.0-or-later
  slug: microbiome--metagenomic-raw-reads-amr-analysis
tools:
- name: sylph
  version: 0.8.1+galaxy0
- name: sylph-tax
- name: groot
  version: 1.1.2+galaxy2
- name: deeparg
  version: 1.0.4+galaxy1
- name: argnorm
  version: 1.0.0+galaxy0
- name: tooldistillator
  version: 1.0.4+galaxy0
- name: multiqc
  version: 1.33+galaxy0
tags:
- metagenomics
- amr
- arg
- taxonomic-profiling
- short-reads
- abromics
- aro
- card
test_data:
- role: metagenomics_reads_after_quality_control_and_host_contamination_removal__raw_reads_metag_test__forward
  url: https://zenodo.org/records/17895994/files/PSM6XBT3_500k_R1.fastq.gz
- role: metagenomics_reads_after_quality_control_and_host_contamination_removal__raw_reads_metag_test__reverse
  url: https://zenodo.org/records/17895994/files/PSM6XBT3_500k_R2.fastq.gz
expected_output:
- role: groot_report
  description: Content assertions for `Groot Report`.
  assertions:
  - 'raw_reads_metag_test: has_text: argannot~~~(Bla)cfxA2~~~AF504910:1-966'
  - 'raw_reads_metag_test: has_n_columns: {''n'': 4}'
- role: argnorm_groot_report
  description: Content assertions for `argNorm Groot Report`.
  assertions:
  - 'raw_reads_metag_test: has_text: ARO:3003002'
  - 'raw_reads_metag_test: has_n_columns: {''n'': 1}'
- role: tooldistillator_summarize
  description: Content assertions for `Tooldistillator Summarize`.
  assertions:
  - 'raw_reads_metag_test: that: has_text'
  - 'raw_reads_metag_test: text: groot_report'
  - 'raw_reads_metag_test: that: has_text'
  - 'raw_reads_metag_test: text: sylph_report'
  - 'raw_reads_metag_test: that: has_text'
  - 'raw_reads_metag_test: text: sylphtax_report'
  - 'raw_reads_metag_test: that: has_text'
  - 'raw_reads_metag_test: text: argnorm_report'
  - 'raw_reads_metag_test: that: has_text'
  - 'raw_reads_metag_test: text: deeparg_report'
  - 'raw_reads_metag_test: that: has_text'
  - 'raw_reads_metag_test: text: sylph-tax.sylphmpa_file'
- role: multiqc_report
  description: Content assertions for `MultiQC report`.
  assertions:
  - 'that: has_text'
  - 'text: multiqc'
  - 'that: has_text'
  - 'text: sylphtax'
  - 'that: has_text'
  - 'text: DeepARG'
  - 'that: has_text'
  - 'text: Groot'
---

# Metagenomic taxonomic and ARG profiling from short reads

## When to use this sketch
- You have paired-end Illumina metagenomic reads from a microbial community (gut, environmental, clinical swab, etc.) and want both *who is there* and *which resistance genes are present*.
- Reads have already been through quality trimming and host/contaminant removal; you are starting from clean `fastqsanger(.gz)` files organized as a `list:paired` collection.
- You want ARG calls from two orthogonal methods (alignment-based Groot against a variation-graph ARG DB, and deep-learning based deepARG) with their outputs harmonized to the CARD Antibiotic Resistance Ontology (ARO) via argNorm.
- You want a combined taxonomic + AMR report (MultiQC) and a machine-readable JSON summary (ToolDistillator) suitable for downstream aggregation across many samples (ABRomics-style cohorts).

## Do not use when
- You only need taxonomic profiling without AMR — use a dedicated metagenomic-taxonomic-profiling sketch instead.
- You have long reads (ONT/PacBio) — this pipeline is tuned for short-read k-mer/MinHash sketch sizes and Groot windowing.
- You want ARGs from *assembled contigs* or MAGs rather than raw reads — use an assembly-based AMR sketch (e.g. abricate/AMRFinderPlus on contigs).
- Reads are not yet QC'd or host-filtered — run a metagenomic QC/host-removal sketch first; this workflow assumes clean input.
- You need strain-level resolution beyond Sylph's containment profiling, or functional profiling beyond AMR (KEGG/CAZy/etc.).

## Analysis outline
1. Unzip the `list:paired` collection into separate forward/reverse datasets and concatenate R1+R2 into a single FASTQ for Groot (cat).
2. Taxonomic profiling: run `sylph profile` against a prebuilt Sylph genome sketch DB, then attach taxonomy via `sylph-tax` metadata to produce per-sample taxonomic profiles and sylphmpa files.
3. ARG detection (alignment): run `Groot` on the concatenated reads against an ARG variation-graph index (e.g. arg-annot) with a read-length-matched window and a coverage cutoff.
4. ARG detection (ML): run `DeepARG short reads` in paired-collection mode against a deepARG database, emitting per-read ARG mappings plus type/subtype summaries.
5. Normalize ARG calls to CARD ARO identifiers with `argNorm` (once with `tool=groot` + Groot DB, once with `tool=deeparg`).
6. Post-process for reporting: strip header lines, rename columns (`ARG`, `Read_Count`, `Gene_Length`, `Coverage`), relabel collection identifiers, and guard Groot failures with a fallback empty `no_results` file via `Filter failed datasets`.
7. Aggregate all tool outputs into a single JSON via `ToolDistillator` (groot, sylph, sylphtax, argnorm×2, deeparg, tabular sylphmpa) and condense with `ToolDistillator Summarize`.
8. Build a combined `MultiQC` report with custom-content tables for Groot+argNorm ARGs, DeepARG ARGs, and the sylph-tax taxonomic profile.

## Key parameters
- Sylph profile: `min_num_kmers: 50`, abundance column `relative_abundance`, `estimate_unknown: false`, cached DB mode, paired-group input.
- Groot index: `windowSize` = average read length (default `100`, must match reads), `kmerSize: 31`, `sketchSize: 21`, `maxK: 4`, `maxSketchSpan: 30`, `numPart: 8`.
- Groot align/report: `contThresh: 0.97`, `minKmerCov: 1`, `noAlign: true`, coverage mode `cutoff` with `covCutoff` user-supplied (default `0.95`; test profile uses `0.6`).
- DeepARG: `deeparg_identity: 80`, `deeparg_evalue: 1e-10`, `gene_coverage: 95`, `bowtie_16s_identity: 0.8`, `deeparg_probability` user-supplied (default `0.8`; reads below this become *potential* ARGs).
- argNorm: run twice with `choose_tool.tool` set to `groot` (passing the same Groot ARG DB identifier, e.g. `groot-argannot`) and `deeparg` — output columns include the ARO accession (e.g. `ARO:3003002`).
- Databases are runtime parameters: a Sylph genome sketch DB (`.syldb`), a Sylph-tax taxonomy metadata bundle, a Groot ARG DB, a matching argNorm DB label, and a DeepARG DB.

## Test data
The workflow ships one test sample, `raw_reads_metag_test`, a downsampled (~500k read pairs) gut metagenome (`PSM6XBT3_500k_R1/R2.fastq.gz` from Zenodo 17895994), supplied as a nested `list:paired` collection. Databases used for the test run are Sylph `OceanDNA-c200-v0.3`, a Sylph-tax metadata snapshot, Groot `arg-annot.90`, argNorm `groot-argannot`, and DeepARG 1.0.4; parameters are `windowSize=100`, `covCutoff=0.6`, `deeparg_probability=0.8`. Expected assertions: the Groot report is a 4-column tabular containing `argannot~~~(Bla)cfxA2~~~AF504910:1-966`; the argNorm-on-Groot report contains an ARO identifier `ARO:3003002`; Sylph taxonomy outputs contain `Taxonomic_abundance` / `clade_name`; DeepARG reports contain `#ARG`; the ToolDistillator summary JSON mentions each of `groot_report`, `sylph_report`, `sylphtax_report`, `argnorm_report`, `deeparg_report`, and `sylph-tax.sylphmpa_file`; the MultiQC HTML references `sylphtax`, `DeepARG`, and `Groot`.

## Reference workflow
Galaxy IWC — `workflows/microbiome/metagenomic-raw-reads-amr-analysis`, release 1.1 (ABRomics consortium, GPL-3.0-or-later). Tools: sylph 0.8.1, Groot 1.1.2, DeepARG 1.0.4, argNorm 1.0.0, ToolDistillator 1.0.4, MultiQC 1.33.
