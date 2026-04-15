---
name: host-read-decontamination
description: Use when you need to screen (meta)genomic FASTQ reads for a specific
  host or contaminant taxon (default Homo sapiens) and optionally filter those reads
  out before downstream metagenomic profiling or assembly. Supports short and long
  reads, with kraken2 and/or bbduk classification and optional blastn validation.
domain: qc
organism_class:
- vertebrate
- metagenome
- any
input_data:
- short-reads-paired
- short-reads-single
- long-reads
- reference-fasta
- kraken2-database
source:
  ecosystem: nf-core
  workflow: nf-core/detaxizer
  url: https://github.com/nf-core/detaxizer
  version: 1.3.0
  license: MIT
  slug: detaxizer
tools:
- name: fastqc
  version: 0.12.1
- name: fastp
- name: kraken2
- name: bbduk
- name: blastn
- name: seqkit
- name: bbmap
- name: multiqc
tags:
- decontamination
- host-removal
- human-read-removal
- metagenomics
- kraken2
- bbduk
- contamination-screen
test_data: []
expected_output: []
---

# Host/contaminant read decontamination

## When to use this sketch
- You have raw Illumina short-read and/or long-read FASTQ files and need to identify and remove reads from a specific taxon (default *Homo sapiens*) before metagenomic profiling, assembly, or public data release.
- You want a benchmarked decontamination step feeding into nf-core/mag or nf-core/taxprofiler.
- You need to screen for an arbitrary taxon or taxonomic subtree (e.g. Mammalia, a specific viral family) present in a kraken2 database.
- You want a choice between fast k-mer classification (bbduk), taxonomic classification (kraken2), or both combined, with optional blastn validation of candidate host reads.
- You only need read assessment (counts/IDs) without actually removing reads (`--skip_filter`).

## Do not use when
- You want to *call variants* or *assemble* the contaminant/host genome — this sketch is for removal, not analysis of the host.
- You are doing generic adapter/quality trimming only with no taxonomic filtering — use a plain fastp/fastqc sketch instead.
- You need full taxonomic profiling of a microbiome — use an nf-core/taxprofiler sketch; detaxizer only isolates one taxon.
- You need reference-based host removal via alignment to a single genome with bwa/bowtie2/minimap2 and no k-mer/taxonomic step — a mapping-based host-removal sketch is a better fit.
- Your inputs are 10x single-cell, bulk RNA-seq counts, BAM/CRAM, or assembled contigs — detaxizer expects raw FASTQ.

## Analysis outline
1. Raw read QC with FastQC.
2. Optional adapter/quality trimming with fastp (`--preprocessing`).
3. Classify reads against the target taxon with kraken2 (`--classification_kraken2`), bbduk (`--classification_bbduk`), or both (recommended for best recall).
4. Isolate reads assigned to `tax2filter` (or its subtree) from the kraken2 report; merge with bbduk hit IDs when both are used.
5. Optional blastn validation (`--validation_blastn`) of candidate host reads against a FASTA-derived database, filtered by identity/coverage/e-value.
6. Filter raw (or trimmed, via `--filter_trimmed`) FASTQs by read ID using seqkit (default) or bbmap `filterbyname.sh`; emit decontaminated FASTQs and, optionally, the removed reads (`--output_removed_reads`).
7. Optional post-filtering kraken2 re-classification of filtered and removed reads as a sanity check (`--classification_kraken2_post_filtering`).
8. Per-sample summary TSVs and a MultiQC report; optionally emit nf-core/mag and nf-core/taxprofiler samplesheets.

## Key parameters
- `input`: CSV samplesheet with columns `sample,short_reads_fastq_1,short_reads_fastq_2,long_reads_fastq_1`.
- `tax2filter`: taxon or subtree to remove; default `Homo sapiens`. Must exist in the kraken2 database.
- `kraken2db`: path/URL to a kraken2 database. Default Standard (~60 GB download, ~80 GB RAM); use `k2_standard_08gb_*` for modest hardware at the cost of recall.
- `fasta_bbduk`: contaminant reference FASTA for bbduk (default: GRCh38 via iGenomes `genome`).
- `fasta_blastn`: FASTA used to build the blastn validation database (only if `validation_blastn` is set).
- `classification_kraken2`, `classification_bbduk`: enable each classifier; combine both for the best-recall benchmark setting.
- `kraken2confidence` (default 0.0), `cutoff_tax2filter`, `cutoff_tax2keep`, `cutoff_unclassified`: fine-tune kraken2 isolation; tighten to reduce false positives.
- `bbduk_kmers` (default 27): bbduk k-mer length.
- `blast_identity` (40.0), `blast_coverage` (40.0), `blast_evalue` (0.01): blastn validation thresholds.
- `preprocessing`, `filter_trimmed`: enable fastp and choose whether the filter operates on raw or trimmed reads.
- `filtering_tool`: `seqkit` (default, normalizes headers) or `bbmap` (exact match; warning: BBTools forces base quality to 0 for N).
- `filter_with_classification`, `skip_filter`, `output_removed_reads`, `classification_kraken2_post_filtering`: control filtering behavior and auditing.
- `generate_downstream_samplesheets` with `generate_pipeline_samplesheets="taxprofiler,mag"`: emit input sheets for downstream nf-core pipelines.

## Test data
The `test` profile uses a tiny samplesheet from nf-core/test-datasets (`detaxizer/samplesheets/samplesheet.csv`) covering short single-end, paired-end, and long-read combinations, a truncated GRCh38 chr21 10 kb region FASTA (`genome.hg38.chr21_10000bp_region.fa`) for bbduk, and the `minigut_kraken.tgz` mini kraken2 database. It runs with `tax2filter='unclassified'` and `kraken2confidence=0.0` so that both classifiers produce hits on the tiny inputs. Expected outputs include per-sample classification ID lists and summary TSVs under `classification/`, filtered FASTQs under `filter/filtered/`, kraken2 and bbduk reports, a MultiQC HTML, and generated `downstream_samplesheets/taxprofiler.csv` plus `mag-{pe,se}.csv`. The `test_full` profile swaps in the full GRCh38 FASTA, the 8 GB kraken2 Standard database, `tax2filter='Homo sapiens'`, and enables post-filtering kraken2 and removed-reads output.

## Reference workflow
nf-core/detaxizer v1.3.0 (https://github.com/nf-core/detaxizer). Benchmarking and recommended settings: Seidel et al., *NAR Genomics and Bioinformatics* 2025, doi:10.1093/nargab/lqaf125.
