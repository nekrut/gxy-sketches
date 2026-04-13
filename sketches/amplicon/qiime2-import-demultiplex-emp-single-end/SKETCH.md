---
name: qiime2-import-demultiplex-emp-single-end
description: "Use when you have single-end multiplexed 16S/amplicon sequencing data\
  \ generated with the Earth Microbiome Project (EMP) protocol that still needs to\
  \ be demultiplexed \u2014 i.e. one FASTQ of reads plus a separate barcodes FASTQ\
  \ and a sample metadata sheet \u2014 and you want to import it into a QIIME 2 artifact\
  \ (.qza) ready for downstream denoising."
domain: amplicon
organism_class:
- bacterial
- microbial-community
input_data:
- short-reads-single
- barcodes-fastq
- sample-metadata-tsv
source:
  ecosystem: iwc
  workflow: 'QIIME2 Ia: multiplexed data (single-end)'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/amplicon/qiime2/qiime2-I-import
  version: '0.3'
  license: MIT
tools:
- qiime2
- q2-demux
- qiime2-tools-import
tags:
- qiime2
- 16s
- amplicon
- emp
- demultiplex
- microbiome
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

# QIIME 2 import and EMP demultiplexing (single-end)

## When to use this sketch
- You have single-end amplicon (e.g. 16S rRNA) reads produced with the **Earth Microbiome Project (EMP)** protocol.
- Reads are still **multiplexed**: one `sequences.fastq.gz` plus a matching `barcodes.fastq.gz`.
- You also have a tab-separated sample metadata sheet with a column holding the per-sample barcode sequences.
- You want a QIIME 2 `SampleData[SequencesWithQuality]` artifact plus a `demux summarize` visualization, as the first stage of a QIIME 2 amplicon pipeline (feeding DADA2 / Deblur downstream).

## Do not use when
- Reads are **paired-end** EMP-multiplexed → use the paired-end sibling sketch (`qiime2-import-demultiplex-emp-paired-end`).
- Data is **already demultiplexed** (one FASTQ per sample, Casava-style naming) → use the `qiime2-import-casava-*` sibling sketches.
- Multiplexing uses **inline barcodes** or a non-EMP protocol → pre-process with `cutadapt demux` before importing, not `demux emp-single`.
- You need denoising, taxonomy, or diversity analysis — those are downstream QIIME 2 sketches; this sketch stops at demultiplexing.

## Analysis outline
1. **Import sequences + barcodes** with `qiime2 tools import` using type `EMPSingleEndSequences` / format `EMPSingleEndDirFmt` → yields a `.qza` named `input-data-single-end`.
2. **Import metadata** with `qiime2 tools import` as `ImmutableMetadata` so the barcode column is usable as a QIIME 2 metadata artifact.
3. **Demultiplex** with `qiime2 demux emp-single`, passing the imported sequences, the metadata artifact, and the name of the barcode column; optionally reverse-complement the mapping barcodes.
4. **Summarize** the demultiplexed artifact with `qiime2 demux summarize` to get a `.qzv` visualization of per-sample read counts and quality.

## Key parameters
- `import_root.type`: `EMPSingleEndSequences` (format `EMPSingleEndDirFmt`).
- `import_root.type` (metadata): `ImmutableMetadata`.
- `demux emp-single` inputs: `seqs` (imported EMP artifact), `barcodes.source` (imported metadata), `barcodes.column` (user-supplied column name, e.g. `barcode-sequence`).
- `golay_error_correction`: `true` (default; standard for EMP 12-nt Golay barcodes).
- `rev_comp_barcodes`: `false`.
- `rev_comp_mapping_barcodes`: user-supplied boolean — flip to `true` if the metadata barcodes are the reverse complement of what the sequencer emitted.
- `demux summarize.n`: `10000` subsampled reads for the quality plot.
- Input file types must be `fastqsanger.gz` or `fastqillumina.gz`; metadata must be `tabular` TSV.

## Test data
The workflow is tested with the QIIME 2 *Moving Pictures* tutorial dataset: a single `sequences.fastq.gz` of multiplexed EMP single-end reads, a matching `barcodes.fastq.gz`, and `sample_metadata.tsv` whose `barcode-sequence` column is fed in as the metadata parameter with `Reverse complement barcodes = false`. The expected primary output is the demultiplexed artifact `demux-single-end.qza` (~20 MB) containing 34 per-sample FASTQs named like `L*S*_*_L001_R1_001.fastq.gz`, an internal `data/metadata.yml` recording `phred-offset: 33`, and a top-level `metadata.yaml` declaring `type: SampleData[SequencesWithQuality]` with `format: SingleLanePerSampleSingleEndFastqDirFmt`. A companion `demux-single-end-visualization.qzv` is also produced.

## Reference workflow
Galaxy IWC `workflows/amplicon/qiime2/qiime2-I-import` — *QIIME2 Ia: multiplexed data (single-end)*, release 0.3 (2024-11-04), using QIIME 2 `2024.10.0` Galaxy tools (`qiime2_core__tools__import`, `qiime2__demux__emp_single`, `qiime2__demux__summarize`).
