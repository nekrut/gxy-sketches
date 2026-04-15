---
name: amplicon-dada2-denoising-paired-qiime2
description: Use when you need to denoise paired-end demultiplexed 16S/18S/ITS amplicon
  reads with DADA2 inside QIIME2 to build an ASV feature table, representative sequences,
  and per-sample denoising statistics. Assumes reads are already imported as a QIIME2
  .qza artifact and demultiplexed.
domain: amplicon
organism_class:
- microbial
- mixed-community
input_data:
- demultiplexed-paired-qza
- sample-metadata-tsv
source:
  ecosystem: iwc
  workflow: 'QIIME2 IIb: Denoising (sequence quality control) and feature table creation
    (paired-end)'
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
- amplicon
- 16S
- 18S
- ITS
- dada2
- asv
- qiime2
- paired-end
- denoising
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

# QIIME2 DADA2 paired-end denoising and feature table creation

## When to use this sketch
- You have paired-end Illumina amplicon reads (16S, 18S, ITS, or similar marker genes) that have already been imported and demultiplexed as a QIIME2 `.qza` artifact (`SampleData[PairedEndSequencesWithQuality]`).
- You want ASV-level resolution (DADA2) rather than OTU clustering, and need the canonical QIIME2 trio of outputs: feature table, representative sequences, denoising stats.
- You are preparing inputs for downstream QIIME2 steps: taxonomy classification, phylogeny, alpha/beta diversity.
- You have a sample metadata TSV in QIIME2 format and want the feature-table summary keyed to it.
- You have already inspected a `demux summarize` quality plot and chosen forward/reverse truncation lengths.

## Do not use when
- Reads are single-end — use the sibling `amplicon-dada2-denoising-single-qiime2` sketch instead.
- Reads are still multiplexed or in raw FASTQ form — run a QIIME2 import + demux workflow first to produce the `.qza`.
- You want OTU clustering (vsearch/closed-reference) rather than DADA2 ASVs.
- You need shotgun metagenomic profiling — use a metagenomics sketch, not an amplicon one.
- You want Deblur instead of DADA2 for denoising.
- You need primer removal / adapter trimming — do that upstream with `cutadapt trim-paired` before this step.

## Analysis outline
1. Provide the demultiplexed paired-end sequences as a QIIME2 `.qza` artifact and a tab-separated sample metadata file.
2. Run `qiime2 dada2 denoise-paired` with forward/reverse truncation lengths (required) and optional 5' trim lengths, producing `table.qza`, `representative_sequences.qza`, and `denoising_stats.qza`.
3. Visualize the representative sequences with `qiime2 feature-table tabulate-seqs` → `.qzv`.
4. Visualize the per-sample denoising statistics with `qiime2 metadata tabulate` on the stats artifact → `.qzv`.
5. Summarize the feature table against the sample metadata with `qiime2 feature-table summarize` → `.qzv` (shows per-sample and per-feature read counts).

## Key parameters
- `trunc_len_f` / `trunc_len_r` (required, integer): length to truncate forward and reverse reads from the 3' end. Pick from the demux quality profile where the median quality drops (typical 16S V4: ~150/150 or 240/160 depending on chemistry).
- `trim_left_f` / `trim_left_r` (optional, integer, default 0): bases to remove from the 5' end — use to strip residual primer if not already removed with cutadapt.
- `max_ee_f` / `max_ee_r`: expected error thresholds, default `2.0` each. Lower (e.g. 1.0) for stricter filtering on high-quality runs.
- `trunc_q`: quality score at which to truncate reads, default `2`. The workflow annotation notes: if retention after denoising is poor, drop `trunc_q` from 2 to 1.
- `min_overlap`: minimum merge overlap, default `12`.
- `pooling_method`: `independent` (default), or `pseudo` for rare-variant sensitivity across samples.
- `chimera_method`: `consensus` (default), `pooled`, or `none`.
- `n_reads_learn`: reads used to train the error model, default `1000000`.
- `hashed_feature_ids: true` and `retain_all_samples: true` are set by the workflow.

## Test data
The workflow is exercised with the QIIME2 2021.11 "Moving Pictures" tutorial data: a sample metadata TSV (`sample-metadata.tsv`) and a demultiplexed paired-end sequences artifact (`demux.qza`) fetched from `docs.qiime2.org`. The test parameters truncate forward reads to length 120 with no left trimming. A successful run produces (a) a feature table `.qza` containing a BIOM-format `feature-table.biom` of non-trivial size, (b) a representative sequences `.qza` whose `dna-sequences.fasta` contains ~770 FASTA records, and (c) a denoising stats `.qza` whose `stats.tsv` has 7 columns and ~36 lines (header plus one row per sample in the tutorial cohort).

## Reference workflow
IWC Galaxy workflow: `galaxyproject/iwc` — `workflows/amplicon/qiime2/qiime2-II-denoising/QIIME2-IIb-denoising-and-feature-table-creation-paired-end.ga`, release 0.3 (2024-11-04), using QIIME2 q2galaxy tools at version `2024.10.0`.
