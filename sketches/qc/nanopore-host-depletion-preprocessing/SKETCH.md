---
name: nanopore-host-depletion-preprocessing
description: Use when you have raw Oxford Nanopore long-read FASTQ samples (e.g. from
  microbiome or pathogen surveillance studies) and need to QC, adapter/quality-trim,
  and remove host-derived reads before downstream taxonomic profiling, assembly, or
  pathogen identification. Produces cleaned non-host FASTQ collections plus before/after
  QC reports and a host-removal summary table.
domain: qc
organism_class:
- microbial
- eukaryote
input_data:
- long-reads-ont
- host-reference-genome
source:
  ecosystem: iwc
  workflow: Nanopore Preprocessing
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/microbiome/pathogen-identification/nanopore-pre-processing
  version: '0.1'
  license: MIT
  slug: microbiome--pathogen-identification--nanopore-pre-processing
tools:
- name: nanoplot
  version: 1.42.0+galaxy1
- name: fastqc
  version: 0.74+galaxy0
- name: porechop
  version: 0.2.4+galaxy0
- name: fastp
  version: 0.23.4+galaxy0
- name: minimap2
  version: 2.28+galaxy0
- name: samtools
  version: 1.15.1+galaxy2
- name: bamtools
  version: 2.5.2+galaxy2
- name: kraken2
  version: 2.1.1+galaxy1
- name: krakentools
  version: 1.2+galaxy1
- name: multiqc
  version: 1.11+galaxy1
tags:
- nanopore
- long-read
- host-removal
- preprocessing
- microbiome
- pathogen
- qc
- decontamination
test_data:
- role: collection_of_all_samples__collection_of_all_samples_spike3bbarcode10
  url: https://zenodo.org/record/12190648/files/collection_of_all_samples_Spike3bBarcode10.fastq.gz
  sha1: 8596672e0eeb5b32bc29c16977cffa69916938f9
  filetype: fastqsanger.gz
- role: collection_of_all_samples__collection_of_all_samples_spike3bbarcode12
  url: https://zenodo.org/record/12190648/files/collection_of_all_samples_Spike3bBarcode12.fastq.gz
  sha1: e9e4213145438bf23b1a43dd78742da2bbd52771
  filetype: fastqsanger.gz
expected_output:
- role: nanoplot_qc_on_reads_after_preprocessing_nanostats
  description: Content assertions for `nanoplot_qc_on_reads_after_preprocessing_nanostats`.
  assertions:
  - 'collection_of_all_samples_Spike3bBarcode12: has_n_lines: {''n'': 24}'
---

# Nanopore host-depletion preprocessing

## When to use this sketch
- You have a collection of single-end Oxford Nanopore FASTQ files (fastqsanger/fastqsanger.gz) from a microbiome or pathogen-detection experiment.
- You need to generate QC reports (NanoPlot, FastQC, MultiQC) for the raw reads and confirm read-quality characteristics typical of ONT data.
- You need to trim adapters/chimeras with Porechop and quality/length-filter with fastp before downstream analysis.
- You need to remove host-derived reads (e.g. human, chicken, cow, bee) against a known host reference genome prior to taxonomic classification, assembly, or pathogen identification.
- You want a per-sample summary of total reads before vs after host removal and the percentage of host sequences found.
- This is the standard upstream step feeding PathoGFAIR / foodborne-pathogen-detection Nanopore workflows.

## Do not use when
- Reads are Illumina short reads — use a short-read preprocessing sketch instead (replace Porechop+fastp with cutadapt/trimmomatic and Minimap2 with Bowtie2; NanoPlot is not applicable).
- Reads are PacBio HiFi and you need HiFi-specific QC/trimming — the Porechop/NanoPlot chain is ONT-oriented.
- You already have host-depleted reads and only want taxonomic profiling — go straight to a Kraken2/Bracken or metagenomic-assembly sketch.
- You need variant calling against the host — this workflow discards host reads.
- You need paired-end handling — this sketch assumes single-end long reads; toggle tool options if you must adapt it.

## Analysis outline
1. Ingest a Galaxy dataset collection of per-sample Nanopore FASTQ files.
2. Raw-read QC with NanoPlot and FastQC, aggregated by MultiQC (before-preprocessing report).
3. Adapter and chimera trimming with Porechop (end and middle adapter settings tuned for ONT).
4. Quality/length filtering with fastp in single-end mode.
5. Post-trim QC with NanoPlot + FastQC (feeds the after-preprocessing MultiQC report).
6. Map trimmed reads against the host reference genome with Minimap2, using a preset chosen via the `samples_profile` parameter (e.g. `map-ont`, `map-pb`).
7. Split the alignment BAM into mapped (host) vs unmapped (non-host) reads with bamtools split-mapped.
8. Convert both BAMs back to FASTQ with samtools fastx (excluding secondary/supplementary alignments).
9. As a second host-depletion pass, run Kraken2 (kalamari DB) on the non-host FASTQ and use KrakenTools extract_kraken_reads to exclude common host taxids (9031 chicken, 9606 human, 9913 cow), emitting the final `collection_of_preprocessed_samples`.
10. Run FastQC on the host-sequence FASTA, grep `Total Sequences` lines before and after host removal, collapse/join them, and compute `(host/total)*100` to build `removed_hosts_percentage_tabular`.
11. Emit the final MultiQC after-preprocessing HTML report that includes the host-removal summary table.

## Key parameters
- `samples_profile` (Minimap2 preset): `map-ont` for standard Nanopore; `map-pb` for PacBio-style reads. Drives alignment sensitivity against the host.
- `host_reference_genome`: cached Galaxy genome build for the expected host (e.g. `hg38`, `galGal4`, `apiMel3`). Required.
- Porechop: `adapter_threshold=90.0`, `check_reads=10000`, `end_threshold=75.0`, `middle_threshold=85.0`, `min_split_read_size=1000`, output format `fastq.gz`.
- fastp: single-end mode, default quality filtering and length filtering enabled; polyG/polyX trimming off; HTML report on.
- Minimap2: BAM output, `no_end_flt=true`, `q_occ_frac=0.01`, reference from cached Galaxy build.
- samtools fastx: exclusive filter flags `256,2048` (drop secondary/supplementary), output `fastqsanger.gz`.
- Kraken2: database `kalamari`, `confidence=0.0`, `minimum_hit_groups=2`, `use_names=true`, report with minimizer data and zero counts.
- KrakenTools extract_kraken_reads: `exclude=true`, `include_children=true`, `include_parents=true`, `taxid="9031 9606 9913"`, `max=100000000`, FASTQ output.
- Host-percentage compute: expression `(c3/c2)*100`, new column `removed_hosts_percentage`.

## Test data
A Galaxy dataset collection of two single-end Nanopore FASTQ files — `collection_of_all_samples_Spike3bBarcode10.fastq.gz` and `collection_of_all_samples_Spike3bBarcode12.fastq.gz` — hosted on Zenodo record 12190648 and downsampled from a foodborne-pathogen spike-in experiment. The job sets `samples_profile=map-pb` and `host_reference_genome=apiMel3` (honeybee) as the host reference. The test asserts that the post-preprocessing NanoPlot `nanostats` tabular for `Spike3bBarcode12` has exactly 24 lines, confirming that trimming, host depletion, and post-trim QC completed end-to-end. Running the workflow additionally produces before/after MultiQC HTML reports, the `collection_of_preprocessed_samples` cleaned FASTQ collection, and the `removed_hosts_percentage_tabular` summary.

## Reference workflow
Galaxy IWC — `workflows/microbiome/pathogen-identification/nanopore-pre-processing` (Nanopore Preprocessing), release 0.1, MIT-licensed. Part of the PathoGFAIR / microGalaxy pathogen-detection suite; see the GTN tutorial `topics/microbiome/tutorials/pathogen-detection-from-nanopore-foodborne-data`.
