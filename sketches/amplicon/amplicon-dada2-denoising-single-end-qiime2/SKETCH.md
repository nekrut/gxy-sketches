---
name: amplicon-dada2-denoising-single-end-qiime2
description: Use when you need to denoise demultiplexed single-end Illumina amplicon
  (16S/18S/ITS marker gene) reads into an ASV feature table with QIIME2's DADA2 plugin,
  producing a feature table, representative sequences, and per-sample denoising statistics.
  Assumes reads are already demultiplexed and delivered as a QIIME2 .qza artifact.
domain: amplicon
organism_class:
- microbial-community
- mixed
input_data:
- demultiplexed-single-end-qza
- qiime2-metadata-tsv
source:
  ecosystem: iwc
  workflow: 'QIIME2 IIa: Denoising (sequence quality control) and feature table creation
    (single-end)'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/amplicon/qiime2/qiime2-II-denoising
  version: '0.3'
  license: MIT
  slug: amplicon--qiime2--qiime2-II-denoising--QIIME2-IIb-denoising-and-feature-table-creation-paired-end
tools:
- name: qiime2
  version: 2024.10.0+q2galaxy.2024.10.0
- name: dada2
- name: q2-feature-table
- name: q2-metadata
tags:
- qiime2
- dada2
- amplicon
- 16s
- asv
- denoising
- single-end
- feature-table
test_data:
- role: metadata
  url: https://docs.qiime2.org/2021.11/data/tutorials/moving-pictures-usage/sample-metadata.tsv
  sha1: 9dbc3213da14db9468fec0e33205d10164f12256
  filetype: tabular
- role: demultiplexed_sequences
  url: https://docs.qiime2.org/2021.11/data/tutorials/moving-pictures-usage/demux.qza
  sha1: 740c8177b1bc9fd22a66d38ffc65c8a06dd58e55
  filetype: qza
expected_output:
- role: denoising_output_table
  description: Content assertions for `Denoising output table`.
  assertions:
  - 'has_size: {''min'': ''20k''}'
  - 'has_archive_member: {''path'': ''^[^/]*/data/feature-table.biom'', ''n'': 1}'
- role: representative_denoised_sequences
  description: Content assertions for `Representative denoised sequences`.
  assertions:
  - 'has_size: {''min'': ''20k''}'
  - 'has_archive_member: {''path'': ''^[^/]*/metadata.yaml'', ''n'': 1}'
  - 'has_archive_member: {''path'': ''^[^/]*/data/dna-sequences.fasta'', ''n'': 1,
    ''asserts'': [{''has_text_matching'': {''expression'': ''>.*'', ''n'': 770}}]}'
- role: denoising_statistics
  description: Content assertions for `Denoising statistics`.
  assertions:
  - 'has_size: {''min'': 0}'
  - 'has_size: {''min'': ''10k''}'
  - 'has_archive_member: {''path'': ''^[^/]*/data/stats.tsv'', ''n'': 1, ''asserts'':
    [{''has_n_columns'': {''n'': 7}}, {''has_n_lines'': {''n'': 36}}]}'
---

# QIIME2 DADA2 denoising and feature table (single-end)

## When to use this sketch
- You have single-end Illumina amplicon reads (e.g. 16S rRNA V4, ITS, 18S) that are already demultiplexed per-sample.
- Inputs are packaged as a QIIME2 `SampleData[SequencesWithQuality]` artifact (`demux.qza`) plus a tab-separated QIIME2 sample metadata file.
- You want amplicon sequence variants (ASVs) rather than OTUs, with chimera filtering, PhiX filtering, and per-sample denoising statistics.
- Downstream goal is a QIIME2 feature table + representative sequences ready for taxonomy classification and diversity analysis.

## Do not use when
- Reads are paired-end — use the sibling `amplicon-dada2-denoising-paired-end-qiime2` sketch, which exposes reverse-read truncation/trimming parameters.
- Reads are still multiplexed or in raw FASTQ form — run a QIIME2 import + demux workflow first (sibling `amplicon-qiime2-import-demultiplex`).
- You want closed/open-reference OTU clustering with VSEARCH instead of DADA2 denoising.
- You are working with shotgun metagenomics, metatranscriptomics, or non-amplicon data — use a metagenomics sketch.
- You need Deblur instead of DADA2 (different error model, different parameter set).

## Analysis outline
1. Ingest demultiplexed single-end sequences (`qza`) and a QIIME2 sample metadata TSV.
2. Denoise with `qiime2 dada2 denoise-single`, producing a feature table, representative sequences, and denoising stats.
3. Tabulate representative sequences with `qiime2 feature-table tabulate-seqs` → `qzv` for interactive inspection and BLAST links.
4. Tabulate denoising statistics with `qiime2 metadata tabulate` → `qzv` to see reads retained at each DADA2 step.
5. Summarize the feature table with `qiime2 feature-table summarize` against the sample metadata → `qzv` showing per-sample and per-feature frequencies.

## Key parameters
- `trunc_len` (required, integer): 3' truncation length for the single-end reads. Choose from the demux quality plot where median Q drops; common values are 120–250 depending on amplicon length and run quality. Reads shorter than `trunc_len` after trimming are discarded.
- `trim_left` (optional, integer, default 0): 5' bases to remove, typically to strip primer/adapter remnants if not already removed.
- `max_ee`: `2.0` (maximum expected errors per read).
- `trunc_q`: `2` (truncate reads at the first base with quality ≤ this value). Drop to `1` if denoising retention is poor.
- `pooling_method`: `independent` (per-sample denoising; use `pseudo` only if you need cross-sample rare-variant detection).
- `chimera_method`: `consensus`; `min_fold_parent_over_abundance`: `1.0`.
- `n_reads_learn`: `1000000` reads used to train the DADA2 error model.
- `hashed_feature_ids`: `true` (stable MD5 feature IDs across runs).
- `retain_all_samples`: `true` (keep empty samples in the output table).
- Tool versions pinned to QIIME2 `2024.10` / q2galaxy `2024.10.0`.

## Test data
The workflow test uses the QIIME2 "Moving Pictures" tutorial data: the single-end demultiplexed artifact `demux.qza` and the sample metadata TSV hosted at `docs.qiime2.org/2021.11/data/tutorials/moving-pictures-usage/`, run with `Truncation length = 120` and `Trimming length = 0`. Expected outputs are three QIIME2 artifacts: a feature table (`feature-table.biom` inside the `qza`, ≥20 kB), representative sequences (`dna-sequences.fasta` containing 770 `>`-prefixed records, `qza` ≥20 kB), and denoising statistics (`stats.tsv` with 7 columns and 36 lines = 2 header rows + 34 samples, `qza` ≥10 kB). The tests assert archive structure and size rather than byte-identical goldens, so minor DADA2 version drift is tolerated.

## Reference workflow
Galaxy IWC: `workflows/amplicon/qiime2/qiime2-II-denoising/QIIME2-IIa-denoising-and-feature-table-creation-single-end.ga`, release 0.3 (2024-11-04), authored by Debjyoti Ghosh / Helmholtz-Zentrum für Umweltforschung (UFZ), MIT licensed. Tool versions pinned to q2galaxy 2024.10.0 (QIIME2 2024.10).
