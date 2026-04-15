---
name: qiime2-import-demultiplexed-single-end
description: Use when you need to import a collection of already-demultiplexed single-end
  amplicon FASTQ files (one file per sample, Casava-style naming) into a QIIME 2 artifact
  for downstream 16S/18S/ITS analysis, and produce a per-sample read-count/quality
  summary visualization.
domain: amplicon
organism_class:
- bacterial
- eukaryote
input_data:
- short-reads-single
- demultiplexed-fastq-collection
source:
  ecosystem: iwc
  workflow: 'QIIME2 Ic: Demultiplexed data (single-end)'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/amplicon/qiime2/qiime2-I-import
  version: '0.3'
  license: MIT
  slug: amplicon--qiime2--qiime2-I-import--QIIME2-Id-demultiplexed-data-paired-end
tools:
- name: qiime2
  version: 2024.10.0+dist.h3d8a7e27
- name: qiime2-tools-import
- name: qiime2-demux-summarize
  version: 2024.10.0+q2galaxy.2024.10.0
- name: regex_find_replace
- name: collection_element_identifiers
  version: 0.0.2
tags:
- qiime2
- amplicon
- 16s
- 18s
- its
- import
- demultiplexed
- single-end
- casava
test_data:
- role: sequences
  url: https://data.qiime2.org/2024.2/tutorials/moving-pictures/emp-single-end-sequences/sequences.fastq.gz
  sha1: deb63e94140495c3a51f32e3e95cbcc8f862baa4
  filetype: fastqsanger.gz
- role: barcodes
  url: https://data.qiime2.org/2024.2/tutorials/moving-pictures/emp-single-end-sequences/barcodes.fastq.gz
  sha1: 450c3c4af2d48cd60c492a485167e807fadb51a8
  filetype: fastqsanger.gz
- role: metadata
  url: https://data.qiime2.org/2024.2/tutorials/moving-pictures/sample_metadata.tsv
  sha1: c2def67243e8074d95c98b6a8ffe81dc4e2cdd65
  filetype: tabular
expected_output:
- role: demultiplexed_single_end_data
  description: Content assertions for `Demultiplexed single-end data`.
  assertions:
  - 'has_size: {''value'': ''20M'', ''delta'': ''1M''}'
  - 'has_archive_member: {''path'': ''.*data/L[0-9]S[0-9]{1,3}_[0-9]{1,2}_L001_R1_001\\.fastq\\.gz'',
    ''n'': 34}'
  - 'has_archive_member: {''path'': ''.*/data/metadata.yml'', ''asserts'': [{''has_text'':
    {''text'': ''phred-offset: 33''}}]}'
  - 'has_archive_member: {''path'': ''^[^/]*/metadata.yaml'', ''n'': 1, ''asserts'':
    [{''has_text'': {''text'': ''uuid:''}}, {''has_text'': {''text'': ''type: SampleData[SequencesWithQuality]''}},
    {''has_text'': {''text'': ''format: SingleLanePerSampleSingleEndFastqDirFmt''}}]}'
---

# QIIME 2 import: demultiplexed single-end reads

## When to use this sketch
- You have per-sample, already-demultiplexed single-end amplicon FASTQ files (one `.fastq.gz` per sample) and want to wrap them into a QIIME 2 `SampleData[SequencesWithQuality]` artifact (`.qza`).
- File names roughly follow the Casava 1.8 pattern `SampleID_S#_L00#_R1_001.fastq.gz`; lane tokens (`_L001_`, `_L002_`, ...) are present or absent and need to be normalized to the laneless layout.
- You also want a `qiime2 demux summarize` visualization (`.qzv`) showing per-sample read counts and per-position quality, as the first step before DADA2/Deblur denoising.
- The input files are `fastqsanger.gz` or `fastqillumina.gz` in a single flat Galaxy collection.

## Do not use when
- Reads are paired-end — use the sibling `qiime2-import-demultiplexed-paired-end` sketch.
- Data is still multiplexed with EMP-style barcodes in one or two big FASTQs — use `qiime2-import-multiplexed-emp-single-end` or `...-paired-end`, which run `qiime2 demux emp-single`/`emp-paired` after import.
- Data is multiplexed with a non-EMP protocol (inline primers/barcodes) — demultiplex first with `cutadapt` and then feed the result into this sketch.
- You want to proceed past import to ASV inference, taxonomy, or diversity — those are downstream QIIME 2 sketches and are not part of this import-only workflow.

## Analysis outline
1. Accept a flat Galaxy collection of single-end demultiplexed FASTQs (`fastqsanger.gz` / `fastqillumina.gz`) as input.
2. `Extract element identifiers` — dump the collection's sample identifiers to a text file.
3. `Regex Find And Replace` — strip any `_L[0-9][0-9][0-9]_` lane token from the identifiers (`_L001_` → `_`) so filenames match the Casava laneless format.
4. `Relabel identifiers` — rename collection elements in place from the cleaned name list.
5. `qiime2 tools import` — import as type `SampleData[SequencesWithQuality]` using `CasavaOneEightLanelessPerSampleDirFmt`, producing `input-data-demultiplexed.qza`.
6. `qiime2 demux summarize` — generate `demux-visualization.qzv` with per-sample counts and quality-score distributions.

## Key parameters
- Import semantic type: `SampleData[SequencesWithQuality]` (single-end).
- Import format: `CasavaOneEightLanelessPerSampleDirFmt` (not the lane-aware variant).
- Regex find/replace: pattern `_L[0-9][0-9][0-9]_` → `_` applied to element identifiers before relabeling.
- `qiime2 demux summarize` subsampling: `n = 10000` reads per sample for the quality plot.
- Input collection type: flat `list` (not `paired`), formats restricted to `fastqsanger.gz` or `fastqillumina.gz`.
- Output phred offset is expected to be 33 (Sanger); the workflow does not convert encodings.

## Test data
The source test job is adapted from the QIIME 2 "Moving Pictures" tutorial and points at `sequences.fastq.gz`, `barcodes.fastq.gz`, and `sample_metadata.tsv` from `data.qiime2.org/2024.2/tutorials/moving-pictures/`. For this single-end *demultiplexed* sketch, only a per-sample collection of `fastqsanger.gz` reads is actually consumed — the barcode/metadata files belong to the sibling multiplexed workflow and can be ignored here. A successful run produces a `SampleData[SequencesWithQuality]` QIIME 2 artifact around 20 MB (±1 MB) that internally contains 34 per-sample FASTQs matching `data/L[0-9]S[0-9]{1,3}_[0-9]{1,2}_L001_R1_001.fastq.gz`, a `data/metadata.yml` declaring `phred-offset: 33`, and a top-level `metadata.yaml` recording `type: SampleData[SequencesWithQuality]` and `format: SingleLanePerSampleSingleEndFastqDirFmt`, plus a `demux-visualization.qzv`.

## Reference workflow
Galaxy IWC workflow `QIIME2 Ic: Demultiplexed data (single-end)`, version 0.3 (`workflows/amplicon/qiime2/qiime2-I-import` in `galaxyproject/iwc`), using `qiime2 tools import` 2024.10.0 and `qiime2 demux summarize` 2024.10.0.
