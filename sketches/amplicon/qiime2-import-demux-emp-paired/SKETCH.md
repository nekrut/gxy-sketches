---
name: qiime2-import-demux-emp-paired
description: Use when you need to import multiplexed paired-end amplicon (16S/ITS/18S)
  sequencing data generated with the Earth Microbiome Project (EMP) protocol into
  QIIME 2 and demultiplex it using a barcodes FASTQ plus sample metadata. Produces
  a QIIME 2 per-sample sequences artifact (.qza) and a summary visualization (.qzv)
  ready for downstream DADA2/Deblur denoising.
domain: amplicon
organism_class:
- microbial
- metagenomic
input_data:
- multiplexed-paired-end-fastq
- barcodes-fastq
- sample-metadata-tsv
source:
  ecosystem: iwc
  workflow: 'QIIME2 Ib: multiplexed data (paired-end)'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/amplicon/qiime2/qiime2-I-import
  version: '0.3'
  license: MIT
tools:
- qiime2
- q2-demux
- qiime2-tools-import
tags:
- qiime2
- amplicon
- 16S
- emp-protocol
- demultiplexing
- paired-end
- import
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

# QIIME 2 import and demultiplexing (EMP paired-end)

## When to use this sketch
- You have raw paired-end amplicon sequencing reads that are still multiplexed — i.e. all samples are pooled in one forward FASTQ and one reverse FASTQ, with per-read barcodes in a separate barcodes FASTQ.
- The library was prepared following the Earth Microbiome Project (EMP) protocol, so barcodes live in a dedicated index read rather than inline in the amplicon reads.
- You need a QIIME 2 `SampleData[PairedEndSequencesWithQuality]` artifact (`.qza`) as the starting point for a downstream amplicon workflow (DADA2, Deblur, taxonomy, diversity).
- You have a tab-separated sample metadata file whose barcode column name you know (it becomes the `Metadata parameter` input).
- You want a `demux summarize` QZV visualization to inspect per-sample read counts and quality score distributions before denoising.

## Do not use when
- Your data is **already demultiplexed** (one FASTQ pair per sample, CASAVA-style filenames) — use the sibling `qiime2-import-demux-casava-paired` / demultiplexed-import sketch instead.
- Your data is **single-end** multiplexed EMP data — use the sibling `qiime2-import-demux-emp-single` sketch.
- Barcodes are **inline** in the reads (not in a separate index FASTQ) or follow a non-EMP multiplexing scheme — strip them with `cutadapt` first and then use a demultiplexed-import sketch.
- You want denoising, OTU picking, taxonomy assignment, or diversity analysis — this sketch stops at the demultiplexed QZA/QZV; chain it to a DADA2/Deblur sketch.
- Your reads are long-read (PacBio/Nanopore) amplicons — different import types and denoisers apply.

## Analysis outline
1. Collect forward FASTQ, reverse FASTQ, and barcodes FASTQ (all `fastqsanger.gz`) into an `EMPPairedEndDirFmt` bundle and import with `qiime2 tools import` → `EMPPairedEndSequences` artifact.
2. Import the sample metadata TSV with `qiime2 tools import` as `ImmutableMetadata` / `ImmutableMetadataFormat` → metadata artifact.
3. Run `qiime2 demux emp-paired` with the sequences artifact, the metadata artifact, and the barcode column name; toggle `rev_comp_mapping_barcodes` if the metadata barcodes are the reverse complement of what is in the barcode reads.
4. Run `qiime2 demux summarize` on the per-sample sequences to generate the QZV for quality inspection and to pick DADA2 trim/trunc positions downstream.

## Key parameters
- Import type: `EMPPairedEndSequences`; import format: `EMPPairedEndDirFmt` with files named `forward.fastq.gz`, `reverse.fastq.gz`, `barcodes.fastq.gz`.
- Metadata import type: `ImmutableMetadata` (`ImmutableMetadataFormat`).
- `qiime2 demux emp-paired`:
  - `barcodes.column`: name of the metadata column holding per-sample barcode sequences (exposed as the `Metadata parameter` workflow input).
  - `rev_comp_mapping_barcodes`: boolean; set `true` when the metadata barcodes need reverse-complementing to match the barcode reads.
  - `rev_comp_barcodes`: `false` (default).
  - `golay_error_correction`: `true` (default; assumes 12 nt Golay barcodes as in EMP).
  - `ignore_description_mismatch`: `false`.
- `qiime2 demux summarize`: subsample size `n = 10000` reads for the per-sample quality plots.
- QIIME 2 tool versions: `2024.10.0` (q2galaxy `2024.10.0`).

## Test data
The workflow is exercised with the QIIME 2 "Moving Pictures" tutorial dataset hosted at `data.qiime2.org/2024.2/tutorials/moving-pictures/`: a multiplexed `sequences.fastq.gz`, the matching `barcodes.fastq.gz`, and `sample_metadata.tsv`. The `Metadata parameter` is set to `barcode-sequence` and `Reverse complement barcodes` is `false`. (Note: the IWC test manifest shipped with this workflow reuses the single-end tutorial files; for a real paired-end run you would supply both forward and reverse EMP FASTQs.) A successful run yields a demultiplexed sequences QZA of roughly 20 MB containing ~34 per-sample `L?S???_*_L001_R1_001.fastq.gz` archive members, with the internal `metadata.yml` reporting `phred-offset: 33` and the QIIME 2 provenance `metadata.yaml` declaring `type: SampleData[SequencesWithQuality]` and `format: SingleLanePerSampleSingleEndFastqDirFmt`, plus a companion `demux summarize` QZV visualization.

## Reference workflow
IWC `workflows/amplicon/qiime2/qiime2-I-import/QIIME2-Ib-multiplexed-data-paired-end.ga`, release 0.3 (2024-11-04), based on QIIME 2 2024.10. Part of the `QIIME2 I: import` workflow family in the Galaxy IWC repository.
