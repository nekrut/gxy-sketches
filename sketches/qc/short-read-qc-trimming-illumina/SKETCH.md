---
name: short-read-qc-trimming-illumina
description: Use when you need to quality-check and trim paired-end Illumina short-read
  FASTQ files before any downstream analysis (variant calling, assembly, RNA-seq,
  metagenomics, etc.), producing cleaned paired reads plus an aggregated MultiQC report.
domain: qc
organism_class:
- bacterial
- eukaryote
- archaea
- viral
input_data:
- short-reads-paired
source:
  ecosystem: iwc
  workflow: Short-read quality control and trimming
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/read-preprocessing/short-read-qc-trimming
  version: '0.3'
  license: MIT
  slug: read-preprocessing--short-read-qc-trimming
tools:
- name: fastp
  version: 1.1.0+galaxy0
- name: multiqc
  version: 1.33+galaxy0
tags:
- qc
- trimming
- adapter-removal
- illumina
- preprocessing
- multiqc
- fastp
- paired-end
test_data:
- role: raw_reads__pair__forward
  url: https://zenodo.org/records/11484215/files/paired_r1.fastq.gz
  filetype: fastqsanger.gz
- role: raw_reads__pair__reverse
  url: https://zenodo.org/records/11484215/files/paired_r2.fastq.gz
  filetype: fastqsanger.gz
expected_output:
- role: multiqc_html_report
  description: Content assertions for `MultiQC HTML report`.
  assertions:
  - 'has_text: pair'
- role: fastp_json_report
  description: Content assertions for `fastp JSON report`.
  assertions:
  - 'pair: has_text: 59230948'
---

# Short-read quality control and trimming (Illumina paired-end)

## When to use this sketch
- You have paired-end Illumina FASTQ(.gz) files and need a generic preprocessing step before any downstream workflow.
- You want adapter removal, per-base quality filtering, and minimum-length filtering in a single fastp pass.
- You want an aggregated MultiQC HTML report summarising QC metrics across many samples.
- Organism-agnostic: works for bacteria, archaea, eukaryotes, viruses — the step is purely read-level preprocessing.

## Do not use when
- Input is long-read (ONT / PacBio) — use a long-read QC/trimming sketch (NanoPlot / filtlong / chopper) instead.
- Input is single-end only — this sketch expects a `list:paired` collection. Adapt or use a single-end variant.
- You need k-mer-based contaminant decontamination, host read removal, or duplicate removal as part of QC — those require additional tools (bbduk, kraken2, bowtie2 vs host) not covered here.
- You want per-read UMI extraction, polyG tail correction for NovaSeq/NextSeq-specific artefacts, or merging of overlapping pairs — these fastp features are disabled in this workflow.
- You are doing amplicon / 16S preprocessing where primer trimming and DADA2-style filtering are required — use an amplicon-specific sketch.

## Analysis outline
1. Ingest raw reads as a `list:paired` collection of fastqsanger(.gz) files.
2. Run **fastp** on each pair: adapter trimming (optional explicit adapter sequences for R1/R2), quality filtering at a configurable Phred threshold, and length filtering at a configurable minimum length. Produces trimmed paired reads, an HTML report, and a JSON report per sample.
3. Run **MultiQC** over the collection of fastp JSON reports to produce a single aggregated HTML QC report across all samples.

## Key parameters
- `single_paired_selector: paired_collection` — input must be a `list:paired` collection.
- `qualified_quality_phred: 15` (default) — bases with Phred ≥ this value are considered qualified; raise to 20 for stricter filtering.
- `length_required: 15` (default) — reads shorter than this after trimming are discarded; typically raise to ~30–50 for most downstream uses.
- `adapter_sequence1` / `adapter_sequence2` — optional explicit forward/reverse adapter sequences; leave null to rely on fastp auto-detection for paired-end.
- `disable_adapter_trimming: false`, `disable_quality_filtering: false`, `disable_length_filtering: false` — all core filters enabled.
- Disabled by design in this workflow: duplicate evaluation, low-complexity filter, polyG/polyX tail trimming, sliding-window cutting (cut_front/cut_tail/cut_right), base correction, UMI processing, read merging, overrepresentation analysis.
- MultiQC configured with a single `fastp` software section consuming the fastp JSON reports.

## Test data
A single paired-end sample wrapped in a `list:paired` collection with one pair identifier `pair`, whose forward and reverse reads are downloaded from Zenodo record 11484215 (`paired_r1.fastq.gz`, `paired_r2.fastq.gz`) as `fastqsanger.gz`. Parameters in the test use the defaults: qualified quality score 15, minimal read length 15, no explicit adapters. The run is expected to emit a per-sample fastp JSON report whose content matches a 2×301-cycle paired-end library (~300,000 input reads, ~295,680 surviving reads, ~59,230,948 bases) and a MultiQC HTML report that contains the `pair` sample name and the usual "Filtered Reads" section.

## Reference workflow
Galaxy IWC `workflows/read-preprocessing/short-read-qc-trimming` — "Short-read quality control and trimming", release 0.3 (fastp 1.1.0+galaxy0, MultiQC 1.33+galaxy0).
