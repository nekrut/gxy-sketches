---
name: qiime2-import-demultiplexed-paired-end
description: Use when you already have per-sample demultiplexed paired-end amplicon
  FASTQ files (e.g. 16S/18S/ITS Illumina MiSeq reads following the Casava 1.8 naming
  scheme) and need to load them into a QIIME 2 artifact (.qza) as SampleData[PairedEndSequencesWithQuality]
  before running DADA2/Deblur or other QIIME 2 downstream analyses.
domain: amplicon
organism_class:
- microbial-community
input_data:
- short-reads-paired
- demultiplexed-fastq-collection
source:
  ecosystem: iwc
  workflow: 'QIIME2 Id: Demultiplexed data (paired-end)'
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
- name: collection_element_identifiers
  version: 0.0.2
- name: regex_find_replace
- name: relabel_from_file
tags:
- qiime2
- amplicon
- 16S
- 18S
- ITS
- import
- demultiplexed
- paired-end
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

# QIIME 2 import: demultiplexed paired-end amplicon data

## When to use this sketch
- You have paired-end amplicon FASTQs that are **already demultiplexed** (one R1/R2 pair per sample) and need a QIIME 2 `.qza` artifact to feed into DADA2, Deblur, taxonomy, or diversity analyses.
- Filenames follow (or can be coerced into) the Casava 1.8 laneless scheme `<sampleid>_<something>_R[12]_001.fastq.gz`; lane tags like `_L001_` are tolerated and stripped automatically.
- All FASTQs are provided as a single flat Galaxy collection of `fastqsanger.gz` / `fastqillumina.gz` files.
- You want a `demux summarize` QZV visualization alongside the artifact to eyeball per-sample read counts and quality profiles before denoising.

## Do not use when
- Reads are **single-end** — use the `qiime2-import-demultiplexed-single-end` sibling sketch instead.
- Data is still **multiplexed** (one or two big FASTQs plus a barcodes file and sample metadata) — use `qiime2-import-multiplexed-emp-paired` or the single-end EMP variant, which runs `qiime2 demux emp-paired` after import.
- Multiplexing uses a non-EMP barcoding scheme — pre-process with Galaxy `cutadapt` to demultiplex first, then use this sketch.
- You need a full amplicon analysis (denoising, taxonomy, diversity) — this sketch only covers the **import** stage; chain it into a downstream QIIME 2 workflow.

## Analysis outline
1. Collect the paired FASTQs into a single flat Galaxy list collection (`fastqsanger.gz` or `fastqillumina.gz`).
2. `Extract element identifiers` — dump the collection element names to a text file.
3. `Regex Find And Replace` — strip `_L[0-9]{3}_` lane tokens from each identifier so they match the Casava laneless format.
4. `Relabel identifiers` — rename the collection elements in-place using the cleaned name list.
5. `qiime2 tools import` — import the relabeled collection as `SampleData[PairedEndSequencesWithQuality]` using `CasavaOneEightLanelessPerSampleDirFmt`, emitting `input-data-demultiplexed.qza`.
6. `qiime2 demux summarize` — build a `demux-visualization.qzv` of per-sample counts and quality distributions for QC.

## Key parameters
- `qiime2 tools import`
  - semantic type: `SampleData[PairedEndSequencesWithQuality]`
  - source format: `CasavaOneEightLanelessPerSampleDirFmt`
  - input picker: `collection` (single flat list of paired R1/R2 files)
  - add file extension: `no` (inputs are already `.fastq.gz`)
- `Regex Find And Replace`
  - pattern: `_L[0-9][0-9][0-9]_`
  - replacement: `_`
- `Relabel identifiers`: `strict: false` (tolerates already-clean names).
- `qiime2 demux summarize`
  - `n` (subsample for quality plot): `10000`
- Required filename regex for inputs after relabeling: `.+_.+_R[12]_001\.fastq\.gz`.

## Test data
The IWC test profile for this workflow family uses the QIIME 2 *Moving Pictures* tutorial data hosted at `data.qiime2.org/2024.2/tutorials/moving-pictures/` (`sequences.fastq.gz`, `barcodes.fastq.gz`, and `sample_metadata.tsv`). Note that the shipped test manifest actually exercises the sibling single-end EMP-multiplexed import, not this paired-end demultiplexed path, so for the demultiplexed paired-end variant supply a small flat collection of per-sample `*_R1_001.fastq.gz` / `*_R2_001.fastq.gz` files. A successful run yields `input-data-demultiplexed.qza` (a `SampleData[PairedEndSequencesWithQuality]` artifact whose internal `metadata.yaml` declares `format: CasavaOneEightLanelessPerSampleDirFmt` and `type: SampleData[PairedEndSequencesWithQuality]`, with `phred-offset: 33` in the inner `data/metadata.yml`) plus a `demux-visualization.qzv` showing per-sample R1/R2 counts and quality plots.

## Reference workflow
Galaxy IWC `workflows/amplicon/qiime2/qiime2-I-import/QIIME2-Id-demultiplexed-data-paired-end.ga`, release 0.3 (2024-11-04), using `qiime2 tools import` and `qiime2 demux summarize` at QIIME 2 `2024.10.0`.
