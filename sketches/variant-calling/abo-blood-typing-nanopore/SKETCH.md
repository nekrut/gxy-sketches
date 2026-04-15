---
name: abo-blood-typing-nanopore
description: Use when you need to determine human ABO blood group phenotype from Oxford
  Nanopore (MinION) amplicon sequencing of ABO exons 6 and 7. Analyses barcoded long-read
  FASTQs, calls ABO-specific SNVs and predicts A/B/AB/O phenotype.
domain: variant-calling
organism_class:
- vertebrate
- human
- diploid
input_data:
- long-reads-ont
- amplicon-fastq
source:
  ecosystem: nf-core
  workflow: nf-core/abotyper
  url: https://github.com/nf-core/abotyper
  version: dev
  license: MIT
  slug: abotyper
tools:
- name: fastqc
  version: 0.12.1
- name: minimap2
- name: samtools
- name: multiqc
- name: pandas
tags:
- abo
- blood-group
- nanopore
- minion
- amplicon
- genotyping
- hla-rbc
- phenotyping
test_data: []
expected_output: []
---

# ABO blood typing from Oxford Nanopore amplicons

## When to use this sketch
- User wants to determine human ABO blood group (A/B/AB/O) from sequencing data.
- Inputs are Oxford Nanopore (MinION) long reads from a barcoded amplicon assay targeting the human ABO gene, specifically exon 6 and exon 7 (the clinically informative regions).
- FASTQs follow a per-barcode naming convention such as `SAMPLE_barcode01.fastq` and you want per-sample phenotype calls plus alignment QC.
- You need an auditable Excel/CSV report of the SNVs used to deduce each phenotype, not just a VCF.

## Do not use when
- You want general germline variant calling on a human genome — use a diploid short-read variant-calling sketch instead.
- You are HLA typing or typing other red cell antigen systems (Rh, Kell, Duffy, etc.) — this pipeline is ABO-specific and only genotypes curated ABO SNVs in exons 6/7.
- Your data is whole-genome or whole-exome, not an ABO-targeted amplicon.
- You only have Illumina short reads and have not validated coverage across the ABO exon 6/7 amplicons (pipeline supports it experimentally but was designed for ONT).
- You need structural variant / CNV detection in ABO.

## Analysis outline
1. **Reference indexing** — convert ABO exon 6 and exon 7 FASTA `.fai` indices into BED regions (`MAKEINDEX`).
2. **Read QC** — run FastQC on each per-barcode FASTQ.
3. **Alignment** — map reads to the ABO exon 6 and exon 7 reference sequences with `minimap2` (long-read preset), producing one BAM per sample per exon.
4. **Alignment metrics** — `samtools coverage`, `samtools flagstat`, and `samtools stats` on each BAM.
5. **Pileup** — `samtools mpileup` over the exon regions to get base-level counts.
6. **Nucleotide frequency** — custom `MPILEUP_NUCL_FREQ` step computes per-position base frequencies at ABO-relevant polymorphic loci.
7. **ABO SNP extraction** — `GETABOSNPS` pulls the curated ABO-diagnostic SNVs out of the frequency tables for each exon.
8. **Phenotype prediction** — `ABOSNPS2PHENO` combines exon 6 + exon 7 SNV patterns against curated rules to call the ABO phenotype per sample.
9. **Reporting** — MultiQC aggregates QC; pipeline writes `ABO_result.xlsx`, `ABO_result.txt`, and `final_export.csv` summarising calls.

## Key parameters
- `--input` (required): samplesheet CSV with `sample,fastq_1,fastq_2` columns; for ONT leave `fastq_2` blank. Sample IDs should match regex `^(IMM|INGS|NGS|[A-Z0-9]+)(-[0-9]+-[0-9]+)?_barcode\d+$` so the barcode can be parsed.
- `--outdir` (required): absolute output path.
- `--exon6fasta` / `--exon7fasta`: ABO exon 6 and exon 7 reference FASTAs. Defaults ship with the pipeline (`assets/refs/ABO_Database.fasta`); only override if you have curated replacements. Exon 7 CDS is truncated to 817 bp to cover the targeted SNVs.
- `--exon6fai` / `--exon7fai`: matching FASTA indices.
- `--skip_renaming` (default `true`): set to `false` and pass `--renaming_file` (tab-delimited `sequencingID<TAB>sampleName`) if you need sequencing IDs rewritten to clinical sample names in the report.
- `--genome`: leave unset / `null`; the pipeline uses its bundled ABO references, not iGenomes.
- `-profile`: use `docker`, `singularity`, or `conda` for reproducibility; add `test` for the bundled minimal dataset.

## Test data
The `test` profile points at the nf-core test-datasets samplesheet `abotyper/abotyper/samplesheet_test_abotyper.csv`, which provides a small set of Oxford Nanopore ABO amplicon FASTQs named with the `*_barcode\d+` convention. Running `nextflow run nf-core/abotyper -profile test,docker --outdir results` is expected to complete end-to-end on a laptop (≤4 CPUs, 15 GB RAM, 1 h) and produce, for each sample, per-exon BAM + coverage/flagstat/stats files, `mpileup.gz` archives, `ABOReadPolymorphisms.txt`, and `*.ABOPhenotype.txt` under `results/per_sample_processing/<sample>/exon{6,7}/`, plus top-level `ABO_result.xlsx`, `ABO_result.txt`, `final_export.csv`, and a MultiQC report under `qc-reports/multiqc/`.

## Reference workflow
nf-core/abotyper (dev, template v3.5.2; bundled tools: FastQC 0.12.1, minimap2 2.29-r1283, samtools 1.21, MultiQC 1.30). Method described in Mobegi et al., *Int. J. Mol. Sci.* 2025, 26(12):5443, doi:10.3390/ijms26125443.
