---
name: host-contamination-removal-short-reads
description: Use when you need to remove host or contaminant reads (e.g. human hg38)
  from paired-end short-read Illumina microbiome FASTQ data before downstream metagenomic
  analysis. Retains only reads that do not map to the provided reference genome.
domain: metagenomics
organism_class:
- microbiome
- host-vertebrate
input_data:
- short-reads-paired
- reference-genome-index
source:
  ecosystem: iwc
  workflow: Host or Contamination Removal on Short-Reads
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/microbiome/host-contamination-removal/host-contamination-removal-short-reads
  version: '0.3'
  license: MIT
  slug: microbiome--host-contamination-removal--host-contamination-removal-short-reads
tools:
- name: bowtie2
  version: 2.5.4+galaxy0
- name: multiqc
  version: 1.33+galaxy0
tags:
- microbiome
- decontamination
- host-removal
- short-reads
- illumina
- bowtie2
- multiqc
- preprocessing
test_data:
- role: short_reads__pair__forward
  url: https://zenodo.org/records/15089018/files/MAG_reads_forward.fastqsanger.gz
  filetype: fastqsanger.gz
- role: short_reads__pair__reverse
  url: https://zenodo.org/records/15089018/files/MAG_reads_reverse.fastqsanger.gz
  filetype: fastqsanger.gz
expected_output:
- role: multiqc_html_report
  description: Content assertions for `MultiQC HTML Report`.
  assertions:
  - 'has_text: Bowtie'
- role: bowtie2_mapping_statistics
  description: Content assertions for `Bowtie2 Mapping Statistics`.
  assertions:
  - 'pair: has_text: 9462 reads'
  - 'pair: has_n_lines: {''n'': 15}'
---

# Host or contamination removal on short-reads

## When to use this sketch
- You have paired-end Illumina short reads (`fastqsanger`/`fastqsanger.gz`) from a microbiome (DNA or RNA) sample.
- You need to strip reads originating from the host (commonly human/hg38) or another contaminant genome before assembly, taxonomic profiling, or MAG recovery.
- You have (or can select) a prebuilt Bowtie2 index for the host/contaminant reference.
- You want the decontaminated paired reads plus an aggregated MultiQC mapping report for QC.

## Do not use when
- Your reads are long reads from Oxford Nanopore or PacBio — use the sibling `host-contamination-removal-long-reads` sketch (Minimap2-based) instead.
- You need taxonomic classification or MAG assembly itself — this sketch is a preprocessing step; chain it into a metagenomics assembly or profiling sketch afterwards.
- You want to *keep* host reads (e.g. dual RNA-seq of host + pathogen) — this workflow discards aligned reads.
- You only have single-end reads; the workflow is wired for a `list:paired` collection.

## Analysis outline
1. Bowtie2 — map each paired-end sample against the host/contaminant reference index, enabling `unaligned_file` output and `save_mapping_stats`; keep only the unaligned read pairs.
2. MultiQC — aggregate the per-sample Bowtie2 mapping statistics into a single HTML report.

## Key parameters
- Bowtie2 `library.type`: `paired_collection` (input is a `list:paired` collection of fastqsanger(.gz)).
- Bowtie2 `reference_genome.source`: `indexed` — select a Galaxy built-in Bowtie2 index (e.g. `hg38` for human host removal). The reference is exposed as a runtime parameter (`Host/Contaminant Reference Genome`).
- Bowtie2 `analysis_type.presets`: `no_presets` (default end-to-end sensitivity; no custom preset).
- Bowtie2 `library.unaligned_file`: `true` — emit unaligned pairs as `output_unaligned_read_pairs` (renamed to *Reads without host or contaminant reads*). Aligned BAM output is hidden.
- Bowtie2 `save_mapping_stats`: `true` — emit per-sample mapping stats (renamed *Bowtie2 mapping statistics*), consumed by MultiQC.
- MultiQC `results.software`: `bowtie2`, `title`: `Host Removal`.
- Tool versions pinned by the workflow: Bowtie2 `2.5.4+galaxy0`, MultiQC `1.33+galaxy0`.

## Test data
The test profile uses a single `list:paired` collection with one pair named `pair`, whose forward/reverse reads are downloaded from Zenodo record 15089018 (`MAG_reads_forward.fastqsanger.gz` and `MAG_reads_reverse.fastqsanger.gz`) — a small MAG-style paired-end FASTQ pair in `fastqsanger.gz` format. The host reference is selected via the `Host/Contaminant Reference Genome` parameter set to the built-in Bowtie2 index `hg38`. Expected outputs are the decontaminated read pairs, a Bowtie2 mapping statistics file for `pair` that contains the string `9462 reads` and has exactly 15 lines, and a MultiQC HTML report that mentions `Bowtie` (and `pair`).

## Reference workflow
Galaxy IWC — `workflows/microbiome/host-contamination-removal/host-contamination-removal-short-reads`, workflow *Host or Contamination Removal on Short-Reads*, release 0.3 (MIT). Upstream tools: `devteam/bowtie2` 2.5.4+galaxy0 and `iuc/multiqc` 1.33+galaxy0.
