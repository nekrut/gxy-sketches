---
name: phage-identification-metagenomic
description: Use when you need to identify, annotate, and quantify bacteriophage (viral)
  sequences from metagenomic or genomic assemblies, including de novo virus calling,
  quality filtering, dereplication, abundance estimation, host prediction, and lifestyle
  classification. Assumes you already have assembled contigs (e.g. from nf-core/mag)
  plus the short reads used to build them.
domain: metagenomics
organism_class:
- viral
- phage
- bacteriophage
input_data:
- metagenomic-assembly-fasta
- short-reads-paired
source:
  ecosystem: nf-core
  workflow: nf-core/phageannotator
  url: https://github.com/nf-core/phageannotator
  version: dev
  license: MIT
tools:
- geNomad
- CheckV
- BLAST
- vRhyme
- bowtie2
- CoverM
- mash
- iPHoP
- BACPHLIP
- prodigal-gv
- inStrain
- propagAtE
- FastQC
- MultiQC
tags:
- phage
- virus
- metagenomics
- viral-discovery
- host-prediction
- lifestyle
- abundance
- dereplication
- checkv
- genomad
test_data: []
expected_output: []
---

# Phage identification and annotation from metagenomic assemblies

## When to use this sketch
- User has (meta)genomic assemblies and wants to find bacteriophage / viral contigs in them.
- User wants the full phage discovery chain: virus calling → QC → dereplication → abundance → annotation.
- User asks for host prediction (iPHoP), lifestyle (temperate vs lytic via BACPHLIP), or phage taxonomy.
- Study is based on short-read Illumina data paired with existing contigs (e.g. downstream of nf-core/mag).
- User wants per-sample abundance tables for viral OTUs, suitable as input to nf-core/differentialabundance.

## Do not use when
- User only has raw reads and needs to assemble first → run nf-core/mag (or similar) to produce contigs, then feed here.
- User is doing bacterial/archaeal MAG recovery without phage focus → nf-core/mag.
- User is doing human/eukaryotic variant calling → see `haploid-variant-calling-bacterial` or germline/somatic variant sketches.
- User wants amplicon-based virome profiling from marker primers → amplicon / 16S-style sketch.
- User wants functional annotation of bacterial ORFs → nf-core/funcscan (this sketch only predicts phage ORFs with prodigal-gv and hands them off).
- User is classifying eukaryotic viruses from clinical RNA-seq → use a dedicated viral-metagenomics/RNA-virus sketch instead.

## Analysis outline
1. Filter input assemblies by minimum contig length (`assembly_min_length`, default 1000 bp).
2. (Optional) Estimate viral enrichment of libraries with ViromeQC (`run_viromeqc`).
3. (Optional) Screen reads for reference viruses with `mash screen` (`run_reference_containment` + `reference_virus_fasta`).
4. De novo viral sequence identification with **geNomad** (`genomad_min_score`, `genomad_max_fdr`, `genomad_splits`).
5. (Optional) Extend viral contigs with COBRA (`run_cobra`) using the original assembler's kmer range.
6. Quality assessment and filtering of candidate viruses with **CheckV** (length, completeness, provirus/warning flags).
7. ANI-based dereplication/clustering of viral genomes using all-vs-all **BLAST** + CheckV's ANI clustering scripts.
8. (Optional) Viral binning of fragmented genomes with **vRhyme**.
9. Align reads to the viral genome database with **bowtie2** and compute per-sample abundance with **CoverM**.
10. Viral taxonomy via **geNomad** marker classification and/or `mash` genome-proximity (`run_genomad_taxonomy`).
11. (Optional) Host prediction with **iPHoP** (`run_iphop`, `iphop_min_score`).
12. (Optional) Lifestyle (virulent/temperate) prediction with **BACPHLIP** (`run_bacphlip`).
13. Protein-coding gene prediction with **prodigal-gv**; optional functional annotation with Pharokka (`run_pharokka`).
14. (Optional) Strain-level microdiversity with **inStrain** and active prophage detection with **propagAtE**.
15. Aggregate read QC (FastQC) and pipeline summary with **MultiQC**.

## Key parameters
- `input`: CSV samplesheet with `sample,fastq_1,fastq_2`; multiple rows per sample are concatenated.
- `assembly_min_length`: 1000 (drop short contigs before virus calling).
- `genomad_min_score`: 0.7 (minimum geNomad virus score).
- `genomad_max_fdr`: 0.1 (enables `--enable-score-calibration`).
- `genomad_splits`: 5 (memory/speed tradeoff for geNomad database shards).
- `genomad_db`, `checkv_db`, `iphop_db`, `pharokka_db`: paths to prebuilt databases; the pipeline can download if absent.
- `checkv_min_length`: 3000, `checkv_min_completeness`: 50, plus `checkv_remove_proviruses` / `checkv_remove_warnings` for strict filtering.
- `blast_min_percent_identity`: 90, `anicluster_min_ani`: 95, `anicluster_min_tcov`: 85 — 95% ANI / 85% AF species-level vOTU clustering.
- `coverm_metrics`: `mean` (per-genome abundance metric; change to `tpm`, `rpkm`, etc. as needed).
- `mash_screen_min_score`: 0.95 (containment threshold for reference-virus screening).
- Enablement flags: `run_reference_containment`, `run_cobra`, `run_genomad_taxonomy`, `run_iphop`, `run_bacphlip`, `run_pharokka`; skip flags: `skip_genomad`, `skip_checkv`, `skip_virus_clustering`, `skip_read_alignment`, `skip_instrain`.

## Test data
The pipeline's `test` profile uses a minimal public samplesheet hosted on the nf-core/test-datasets `phageannotator` branch, containing a small number of paired Illumina FASTQ samples along with a tiny reference virus FASTA derived from a *Bacteroides fragilis* test assembly. It runs with `mash_screen_min_score = 0` and `genomad_splits = 5` so that geNomad and mash screen produce results on toy inputs under 2 CPUs / 6 GB RAM. A successful run should emit geNomad virus calls, CheckV quality tables, a dereplicated vOTU FASTA, per-sample CoverM abundance tables, and a MultiQC report under `<outdir>`. A `test_full` profile is also provided for larger AWS-scale validation.

## Reference workflow
nf-core/phageannotator (dev branch, MIT). See https://github.com/nf-core/phageannotator and the tool citations in `CITATIONS.md` for geNomad, CheckV, vRhyme, bowtie2, CoverM, iPHoP, BACPHLIP, prodigal-gv, inStrain, and propagAtE.
