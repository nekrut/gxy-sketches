---
name: sars-cov-2-variant-calling-illumina-se-wgs
description: Use when you need to call SARS-CoV-2 variants (including low-frequency/intra-host
  minor variants) from single-end Illumina whole-genome shotgun sequencing reads against
  the Wuhan-Hu-1 (NC_045512.2) reference, with SnpEff annotation of effects on viral
  ORFs.
domain: variant-calling
organism_class:
- viral
- haploid
input_data:
- short-reads-single
- reference-fasta
source:
  ecosystem: iwc
  workflow: 'COVID-19: variation analysis on WGS SE data'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/sars-cov-2-variant-calling/sars-cov-2-se-illumina-wgs-variant-calling
  version: 0.1.6
  license: MIT
  slug: sars-cov-2-variant-calling--sars-cov-2-se-illumina-wgs-variant-calling
tools:
- name: fastp
  version: 0.24.0+galaxy4
- name: bowtie2
  version: 2.5.3+galaxy1
- name: picard-markduplicates
  version: 3.1.1.0
- name: lofreq
  version: 2.1.5+galaxy0
- name: snpeff
  version: 4.5covid19
- name: multiqc
  version: 1.27+galaxy3
tags:
- sars-cov-2
- covid-19
- viral
- wgs
- illumina
- single-end
- lofreq
- low-frequency-variants
- snpeff
test_data:
- role: nc_045512_2_fasta_sequence_of_sars_cov_2
  url: https://zenodo.org/record/4555735/files/NC_045512.2_reference.fasta?download=1
- role: single_end_collection__srr11605118
  url: https://www.be-md.ncbi.nlm.nih.gov/Traces/sra-reads-be/fastq?acc=SRR11605118
expected_output:
- role: annotated_variants
  description: Content assertions for `annotated_variants`.
  assertions:
  - "SRR11605118: has_line: #CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"
  - 'SRR11605118: has_text_matching: {''expression'': ''NC_045512.2\t16111\t.\tC\tT\t[0-9.]*\tPASS\tDP=[0-9]*;AF=0.[89][0-9]*;SB=0;DP4=[0-9]*,[0-9]*,[0-9]*,[0-9]*;EFF=SYNONYMOUS_CODING\\(LOW|SILENT|Cta/Tta|L5283|7096|ORF1ab|protein_coding|CODING|GU280_gp01|2|T\\),SYNONYMOUS_CODING\\(LOW|SILENT|Cta/Tta|L891|931|ORF1ab|protein_coding|CODING|YP_009725307.1|2|T|WARNING_TRANSCRIPT_NO_START_CODON\\)''}'
---

# SARS-CoV-2 variant calling from single-end Illumina WGS reads

## When to use this sketch
- Input is single-end Illumina FASTQ reads from a SARS-CoV-2 whole-genome shotgun (non-amplicon) experiment.
- Reference is the Wuhan-Hu-1 genome (NC_045512.2) and you want SnpEff annotation against the covid19-specific database.
- You need sensitive detection of both consensus and low-allele-frequency (intra-host) SNVs and indels using LoFreq.
- One sample or a collection of samples processed independently through the same pipeline.

## Do not use when
- Reads are paired-end Illumina WGS — use the sibling `sars-cov-2-variant-calling-illumina-pe-wgs` sketch instead.
- Reads come from an ARTIC or other tiled-amplicon protocol requiring primer trimming with ivar — use the ampliconic SARS-CoV-2 variant-calling sketch.
- Reads are Oxford Nanopore long reads — use the ONT SARS-CoV-2 variant-calling sketch.
- You need consensus sequence assembly / Pangolin lineage assignment as a primary output (this workflow stops at annotated VCFs).
- Organism is not SARS-CoV-2; SnpEff is hard-wired to the `NC_045512.2` covid19 database.

## Analysis outline
1. **Quality/adapter trimming** of single-end reads with `fastp` (default quality and length filters, adapter auto-detection).
2. **Read mapping** to the NC_045512.2 reference with `Bowtie2` using the `--very-sensitive` preset and auto-assigned read groups.
3. **Duplicate removal** with Picard `MarkDuplicates` (`remove_duplicates=true`, `assume_sorted=true`, `LENIENT` validation).
4. **QC aggregation** of fastp, Bowtie2 mapping stats, and MarkDuplicates metrics with `MultiQC`.
5. **Viterbi realignment** of the deduplicated BAM with `lofreq viterbi` to correct mapping artifacts around indels.
6. **Indel quality insertion** with `lofreq indelqual` using the Dindel model, needed for LoFreq indel calling.
7. **Variant calling** with `lofreq call` across the full genome, calling both SNVs and indels at a very permissive significance threshold to expose minor variants.
8. **Strand-bias soft filtering** with `lofreq filter` (FDR-controlled compound strand-bias filter, `--print-all`).
9. **Functional annotation** of the filtered VCF with `SnpEff` using the `NC_045512.2` covid19 database (classic/EFF format, UTR/intergenic/up-/downstream effects suppressed).

## Key parameters
- Bowtie2 preset: `--very-sensitive`; single-end library mode.
- Picard MarkDuplicates: `REMOVE_DUPLICATES=true`, `VALIDATION_STRINGENCY=LENIENT`, `OPTICAL_DUPLICATE_PIXEL_DISTANCE=100`.
- lofreq viterbi: keep BQ2 bases (`replace_bq2=keep`, `defqual=2`).
- lofreq indelqual strategy: `dindel` with the same reference FASTA.
- lofreq call: `min_cov=5`, `max_depth=1,000,000`, `min_bq=30`, `min_alt_bq=30`, `min_mq=20`, extended BAQ on, significance `sig=0.0005`, Bonferroni off, `--call-indels`, whole-genome (no region restriction).
- lofreq filter: strand-bias `mtc=fdr`, `sb_alpha=0.001`, `sb_compound=true`, no AF or coverage cutoffs, `--print-all` (soft-flagging only).
- SnpEff: `genome_version=NC_045512.2` (covid19 DB, tool version `4.5covid19`), annotations `-formatEff -classic`, filterOut `-no-downstream -no-intergenic -no-upstream -no-utr`, `udLength=0`.

## Test data
The source test profile provides one single-end Illumina run, SRR11605118, streamed directly from NCBI SRA as a one-element Galaxy collection, together with the NC_045512.2 Wuhan-Hu-1 reference FASTA hosted on Zenodo (record 4555735). A successful run produces a SnpEff-annotated VCF per input sample; the test asserts the file is valid VCFv4.0 with the standard `#CHROM\tPOS\t...` header, contains the canonical lineage-defining variant at `NC_045512.2:241 C>T`, and carries a synonymous ORF1ab variant at position 16111 (`C>T`) passing filters with allele frequency in the 0.8–0.9 range and SnpEff EFF annotation indicating a synonymous coding change in ORF1ab (`L5283` / `L891` on transcripts `GU280_gp01` / `YP_009725307.1`).

## Reference workflow
Galaxy IWC `sars-cov-2-variant-calling/sars-cov-2-se-illumina-wgs-variant-calling`, workflow name "COVID-19: variation analysis on WGS SE data", release 0.1.6 (2025-03-10), MIT-licensed, authored by Wolfgang Maier. Upstream: https://github.com/galaxyproject/iwc/tree/main/workflows/sars-cov-2-variant-calling/sars-cov-2-se-illumina-wgs-variant-calling
