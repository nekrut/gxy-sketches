---
name: metagenome-read-mapping-to-genome-collection
description: Use when you need to quantify gene-level abundance by mapping metagenomic
  or metatranscriptomic short reads against a (potentially large) collection of prokaryotic
  reference genomes or MAGs, producing per-feature count tables for downstream differential
  abundance analysis. Optionally pre-filters the genome set with sourmash k-mer sketches.
domain: metagenomics
organism_class:
- bacterial
- archaeal
- prokaryote
input_data:
- short-reads-paired
- short-reads-single
- genome-collection-fasta
- genome-annotations-gff
source:
  ecosystem: nf-core
  workflow: nf-core/magmap
  url: https://github.com/nf-core/magmap
  version: 1.0.0
  license: MIT
  slug: magmap
tools:
- name: fastqc
  version: 0.12.1
- name: trim-galore
- name: bbduk
- name: sourmash
- name: prokka
- name: bbmap
- name: featurecounts
  version: 2.0.6
- name: samtools
- name: multiqc
tags:
- metagenomics
- metatranscriptomics
- mags
- gene-quantification
- read-mapping
- prokaryotic
- featurecounts
- sourmash
test_data: []
expected_output: []
---

# Metagenome/metatranscriptome read mapping to a genome collection

## When to use this sketch
- You have Illumina short reads from metagenomes or metatranscriptomes and want per-gene (CDS/rRNA/tRNA/tmRNA) read counts across a panel of prokaryotic genomes or MAGs.
- The reference is a *collection* of many genomes (user-provided MAGs, isolates, single-cell genomes, or GTDB/NCBI genomes) rather than a single organism.
- You intend to feed the resulting count tables into a downstream differential abundance tool (e.g. nf-core/differentialabundance, DESeq2, edgeR).
- You optionally want sourmash to prefilter or remotely fetch the subset of reference genomes that are actually represented in your samples.
- You may also want to strip rRNA/contaminant reads with a user-provided fasta before mapping.

## Do not use when
- Your reference is a single eukaryotic organism with a canonical genome+GTF — use an `rna-seq` sketch (nf-core/rnaseq) instead.
- You need *de novo* assembly and binning of MAGs from the reads — use a metagenome assembly/binning sketch (nf-core/mag).
- You only want taxonomic profiling / community composition without gene-level quantification — use a taxonomic profiling sketch (nf-core/taxprofiler).
- You need SNV/indel variant calling against a haploid reference — use a `haploid-variant-calling-bacterial` sketch.
- You have long reads (ONT/PacBio) as primary input — this pipeline assumes Illumina short reads.

## Analysis outline
1. Raw read QC with FastQC.
2. Adapter and quality trimming with Trim Galore!.
3. Optional contaminant/rRNA filtering with BBduk using a user-supplied reference fasta (`--sequence_filter`).
4. Optional genome prefiltering and/or remote genome fetching with sourmash, matching read k-mer sketches against the user's genomes and/or NCBI sourmash indexes.
5. Gene calling and functional annotation with Prokka for any reference genome lacking a supplied GFF (results cached in `--prokka_store_dir`).
6. Concatenate selected genome contigs and build a BBmap index.
7. Map cleaned reads to the concatenated reference with BBmap (configurable ambiguous-mapping policy).
8. Count reads per feature (CDS, rRNA, tRNA, tmRNA by default) with subread featureCounts.
9. Collate per-sample, per-feature TSV count tables, overall mapping statistics, and genome metadata (GTDB / GTDB-Tk / CheckM) with an R collect_stats step.
10. Aggregate QC and logs into a MultiQC report.

## Key parameters
- `--input`: samplesheet CSV with columns `sample,fastq_1,fastq_2` (fastq_2 blank for single-end; repeated sample rows are concatenated across lanes).
- `--genomeinfo`: CSV with columns `accno,genome_fna,genome_gff` describing local reference genomes; `genome_gff` is optional and missing ones will be filled by Prokka.
- `--indexes`: one or more sourmash SBT/index files (e.g. GTDB `gtdb-rs214-reps.k21.sbt.zip`) for remote genome discovery.
- `--remote_genome_sources`: comma-separated NCBI `assembly_summary` files used to resolve sourmash hits to downloadable FTP paths (defaults to RefSeq + GenBank summaries).
- `--genome_store_dir` / `--prokka_store_dir`: persistent cache directories for downloaded genomes and Prokka annotations — reuse between runs to avoid recomputing.
- `--skip_sourmash`: `true` by default (no sourmash prefiltering of user genomes); set to `false` to enable filtering and/or remote index-driven fetching.
- `--sourmash_ksize`: k-mer size for sourmash sketches (default 21; must match the index).
- `--sequence_filter`: fasta of sequences (e.g. SILVA rRNA) to remove with BBduk before mapping.
- `--bbmap_minid`: minimum mapping identity (default 0.9).
- `--bbmap_ambiguous`: how BBmap handles multi-mapping reads — `best` (default), `all`, `random`, or `toss`. Pair `all` with `--featurecounts_fraction true` for fractional multi-mapped counting.
- `--features`: comma-separated feature types to count (default `CDS,rRNA,tRNA,tmRNA`).
- `--bbmap_save_bam` / `--bbmap_save_index` / `--save_concatenated_genomes` / `--sourmash_save_sourmash`: optional flags to persist intermediate artifacts.
- `--gtdb_metadata`, `--gtdbtk_metadata`, `--checkm_metadata`: optional TSVs merged into `magmap.genome_metadata.tsv.gz` for annotated downstream tables.
- `--skip_qc`, `--skip_fastqc`, `--skip_trimming`: toggles to bypass preprocessing steps.

## Test data
The bundled `test` profile (`conf/test.config`) runs a minimal sanity check using a small samplesheet from `nf-core/test-datasets` (magmap branch), a `genometest.csv` pointing at a tiny set of reference genome FASTAs under `magmap/testdata/`, and an rRNA filter fasta (`metatdenovo/test_data/rrna.fna.gz`) supplied via `--sequence_filter`. Running `nextflow run nf-core/magmap -profile test,docker --outdir results` is expected to complete end-to-end on ≤4 CPUs / 15 GB RAM within an hour and produce gzipped summary tables under `results/summary_tables/` (`magmap.overall_stats.tsv.gz`, `magmap.<feature>.counts.tsv.gz`, `magmap.genomes2orfs.tsv.gz`, `magmap.prokka-annotations.tsv.gz`), Prokka annotations under `magmap_prokka/<accno>/`, BBmap and BBduk logs, and a final `multiqc/multiqc_report.html`. The `test_full` profile swaps in a larger samplesheet and `genomes_full_test.csv`, reusing cached genomes and Prokka outputs from S3 (`s3://nf-core-awsmegatests/magmap/input/databases/...`).

## Reference workflow
nf-core/magmap v1.0.0 (https://github.com/nf-core/magmap), DOI 10.5281/zenodo.17752714. Authored by Danilo Di Leo, Emelie Nilsson, and Daniel Lundin. Downstream count tables are designed to feed nf-core/differentialabundance; see also the sibling pipelines nf-core/taxprofiler (community profiling), nf-core/mag (assembly + binning), and nf-core/rnaseq (eukaryotic single-reference RNA-seq).
