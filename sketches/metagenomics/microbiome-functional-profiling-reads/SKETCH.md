---
name: microbiome-functional-profiling-reads
description: Use when you need read-based functional profiling of microbiome / metagenomic
  sequencing data to quantify gene families, metabolic pathways, KEGG orthologs, enzyme
  functions, or antimicrobial resistance genes from short-read Illumina or long-read
  Oxford Nanopore FASTQ files, against user-supplied functional databases (HUMAnN/ChocoPhlAn,
  EggNOG, CARD, etc.).
domain: metagenomics
organism_class:
- microbial-community
- metagenome
input_data:
- short-reads-paired
- short-reads-single
- long-reads-ont
- functional-database
source:
  ecosystem: nf-core
  workflow: nf-core/funcprofiler
  url: https://github.com/nf-core/funcprofiler
  version: dev
  license: MIT
tools:
- humann
- metaphlan
- fmh-funprofiler
- mifaser
- diamond
- eggnog-mapper
- rgi
- fastqc
- multiqc
tags:
- metagenomics
- microbiome
- functional-profiling
- humann
- metaphlan
- kegg
- amr
- card
- eggnog
- gene-families
- pathways
test_data: []
expected_output: []
---

# Microbiome read-based functional profiling

## When to use this sketch
- You have raw microbiome / metagenomic FASTQ files (Illumina paired- or single-end, or Oxford Nanopore long reads) and want per-sample functional profiles without assembly.
- You need gene-family or metabolic-pathway abundances (HUMAnN v3 or v4, with MetaPhlAn as the taxonomic prescreen producing `*_genefamilies.tsv`, `*_pathabundance.tsv`, `*_pathcoverage.tsv`).
- You want fast sketch-based KEGG Orthology (KO) profiles via FMH FunProfiler.
- You want enzyme-function (EC) profiles via mifaser, translated alignment via DIAMOND blastx against a `.dmnd` protein database, or orthology/GO/KEGG/COG annotations via EggNOG-mapper.
- You want antimicrobial-resistance gene profiles from reads against CARD via RGI BWT.
- You have multiple sequencing runs per biological sample that should be merged before profiling.

## Do not use when
- You need taxonomic profiling only (species/strain abundances) — use a metagenomic taxonomic profiling sketch (e.g. one built around nf-core/taxprofiler) instead.
- You need to assemble metagenomes into contigs/MAGs and then annotate genes — use a metagenome assembly + binning sketch (nf-core/mag).
- You need AMR detection from assembled genomes or contigs rather than raw reads — use an assembly-based AMR annotation sketch.
- You are doing amplicon / 16S rRNA profiling — use an amplicon (DADA2/QIIME2) sketch.
- You want variant calling or isolate genomics — use the relevant variant-calling sketch.

## Analysis outline
1. Parse samplesheet CSV (`sample`, `run_accession`, `instrument_platform`, `fastq_1`, `fastq_2`, `fasta`) and databases CSV (`tool`, `db_name`, `db_entity`, `db_params`, `db_type`, `db_path`).
2. Run FastQC (and short/long-read QC subworkflow) on raw reads for preprocessing QC.
3. Optionally merge multiple runs of the same sample into one FASTQ per sample (`perform_runmerging`).
4. For each enabled profiler, route merged reads to the matching database entries:
   - HUMAnN v3 / v4 — MetaPhlAn taxonomic prescreen, then HUMAnN against ChocoPhlAn nucleotide + UniRef90 protein + utility-mapping databases.
   - FMH FunProfiler — FracMinHash sketch lookup against a KEGG sketch database producing `*.ko.txt`.
   - mifaser — read-to-protein mapping against a GS-21/GS-580 style database producing `analysis.tsv` of EC-level counts.
   - DIAMOND blastx — translated alignment of reads against a `.dmnd` protein database, tabular BLAST output.
   - EggNOG-mapper — search (diamond/mmseqs/hmmer) against EggNOG proteins + data dir, producing `*.emapper.annotations`.
   - RGI BWT — Bowtie2/BWA alignment of reads against the CARD database producing AMR gene hit tables (TXT + JSON).
5. Aggregate QC and per-tool logs with MultiQC into `multiqc_report.html`.

## Key parameters
- `--input` (required): samplesheet CSV; columns `sample,run_accession,instrument_platform,fastq_1,fastq_2,fasta`; platform ∈ {ILLUMINA, OXFORD_NANOPORE, PACBIO_SMRT, ION_TORRENT, BGISEQ, DNBSEQ, LS454}.
- `--databases` (required): databases CSV with columns `tool,db_name,db_entity,db_params,db_type,db_path`; `db_type` restricts to `short`, `long`, or `short;long`.
- `--outdir` (required): absolute results path.
- Profiler toggles (at least one required; all default off except as noted): `--run_humann_v3`, `--run_humann_v4`, `--run_fmhfunprofiler`, `--run_mifaser`, `--run_diamond`, `--run_eggnogmapper`, `--run_rgi`.
- `--humann_renorm_to_cpm`: emit HUMAnN copies-per-million normalised tables.
- `--perform_runmerging` (default true): concatenate runs sharing a `sample` name before profiling; `--save_runmerged_reads` to keep the merged FASTQs.
- `--skip_preprocessing_qc`: skip preprocessing QC filtering.
- `--save_untarred_databases`: keep decompressed `.tar.gz` database archives under `results/untar`.
- Database-sheet conventions: HUMAnN requires four rows with the same `db_name` and `db_entity` ∈ {`humann_metaphlan`, `humann_nucleotide`, `humann_protein`, `humann_utility`}; EggNOG-mapper requires two rows with `db_entity` ∈ {`eggnogmapper_db` (with `db_params` set to `diamond`/`mmseqs`/`hmmer`), `eggnogmapper_data_dir`}; DIAMOND `db_path` points at the directory containing the `.dmnd` file; RGI `db_path` points at the loaded CARD directory containing `card.json`.
- Execution: `-profile docker|singularity|conda|...`; pass parameters via `-params-file params.yaml`, not `-c`.

## Test data
The pipeline's `test` profile pulls a small shortread-only metagenomic samplesheet from the nf-core/test-datasets `taxprofiler` branch (`samplesheet_shortreadsonly.csv`) and a `database.csv` from the `funcprofiler` test-datasets branch. It enables `run_fmhfunprofiler`, `run_humann_v3`, `run_humann_v4`, and `run_mifaser` (DIAMOND, RGI, EggNOG-mapper off), with run-merging on and both short- and long-read QC disabled, capped at 4 CPUs / 15 GB / 1 h. A successful run produces per-sample HUMAnN `*_genefamilies.tsv`, `*_pathabundance.tsv`, `*_pathcoverage.tsv` plus MetaPhlAn `*_profile.txt`, FMH FunProfiler `*.ko.txt`, mifaser `analysis.tsv`/`analysis.log`, and a consolidated `multiqc/multiqc_report.html`.

## Reference workflow
nf-core/funcprofiler (version `1.0.0dev`, template 3.3.2, Nextflow ≥ 24.10.5), MIT-licensed, https://github.com/nf-core/funcprofiler. Run with `nextflow run nf-core/funcprofiler -r <release> -profile <docker|singularity|conda> --input samplesheet.csv --databases databases.csv --outdir results --run_humann_v3` (add further `--run_*` flags as needed).
