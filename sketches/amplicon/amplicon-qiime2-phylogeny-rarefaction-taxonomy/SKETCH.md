---
name: amplicon-qiime2-phylogeny-rarefaction-taxonomy
description: Use when you have QIIME2 DADA2 outputs (ASV representative sequences
  and feature table) from a 16S/18S/ITS amplicon study and need downstream phylogenetic
  tree construction, alpha rarefaction curves, and taxonomic classification with barplots.
  Assumes demultiplexing and DADA2 denoising are already complete.
domain: amplicon
organism_class:
- bacterial
- eukaryote
input_data:
- qiime2-rep-seqs-qza
- qiime2-feature-table-qza
- sample-metadata-tsv
- sepp-reference-qza
- taxonomic-classifier-qza
source:
  ecosystem: iwc
  workflow: QIIME2-III-V-Phylogeny-Rarefaction-Taxonomic-Analysis
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/amplicon/qiime2/qiime2-III-VI-downsteam
  version: '0.2'
  license: MIT
  slug: amplicon--qiime2--qiime2-III-VI-downsteam--QIIME2-VI-diversity-metrics-and-estimations
tools:
- name: qiime2
  version: 2024.10.0+dist.h3d8a7e27
- name: sepp
- name: fragment-insertion
- name: classify-sklearn
- name: alpha-rarefaction
- name: taxa-barplot
tags:
- 16s
- amplicon
- qiime2
- asv
- phylogeny
- rarefaction
- taxonomy
- microbiome
test_data:
- role: metadata
  url: https://data.qiime2.org/2024.2/tutorials/pd-mice/sample_metadata.tsv
  sha1: bfad679a672dbe8284586f19c9ce86ee53bd5f9c
  filetype: tabular
- role: representative_sequences
  url: https://docs.qiime2.org/2024.2/data/tutorials/pd-mice/dada2_rep_set.qza
  sha1: 3bfd12aba18bc6008c64ab8aa992fc8af678ebbf
  filetype: qza
- role: feature_table
  url: https://docs.qiime2.org/2024.2/data/tutorials/pd-mice/dada2_table.qza
  sha1: 9a205d939eee56bb766e6d8efbcdd772d230bcd3
  filetype: qza
- role: taxonomic_classifier
  url: https://docs.qiime2.org/2024.10/data/tutorials/pd-mice/gg-13-8-99-515-806-nb-classifier.qza
  sha1: f13acbfb6ed4cc65843a8223e5ed7c8733ebd1e4
  filetype: qza
- role: sepp_fragment_insertion_reference
  url: https://data.qiime2.org/2024.2/common/sepp-refs-gg-13-8.qza
  sha1: 3e57b667260647aec575de59adca76f2f54ffe16
  filetype: qza
expected_output:
- role: rooted_tree
  description: Content assertions for `Rooted tree`.
  assertions:
  - 'has_size: {''min'': ''2M'', ''max'': ''3M''}'
  - 'has_archive_member: {''path'': ''^[^/]*/data/tree.nwk'', ''n'': 1, ''asserts'':
    [{''has_text_matching'': {''expression'': ''k__Bacteria''}}]}'
  - 'has_archive_member: {''path'': ''^[^/]*/metadata.yaml'', ''n'': 1, ''asserts'':
    [{''has_line'': {''line'': ''type: Phylogeny[Rooted]''}}, {''has_line'': {''line'':
    ''format: NewickDirectoryFormat''}}]}'
- role: rarefaction_curve
  description: Content assertions for `Rarefaction curve`.
  assertions:
  - 'has_size: {''min'': ''400k'', ''max'': ''500k''}'
  - 'has_archive_member: {''path'': ''^[^/]*/data/index.html'', ''n'': 1}'
  - 'has_archive_member: {''path'': ''^[^/]*/data/.*\\.csv'', ''n'': 3}'
  - 'has_archive_member: {''path'': ''^[^/]*/data/.*\\.jsonp'', ''n'': 21}'
- role: taxonomy_classification
  description: Content assertions for `Taxonomy classification`.
  assertions:
  - 'has_size: {''min'': ''40k'', ''max'': ''80k''}'
  - 'has_archive_member: {''path'': ''^[^/]*/metadata.yaml'', ''n'': 1, ''asserts'':
    [{''has_line'': {''line'': ''type: FeatureData[Taxonomy]''}}, {''has_line'': {''line'':
    ''format: TSVTaxonomyDirectoryFormat''}}]}'
  - 'has_archive_member: {''path'': ''^[^/]*/data/taxonomy.tsv'', ''n'': 1, ''asserts'':
    [{''has_n_lines'': {''n'': 288}}]}'
- role: taxa_barplot
  description: Content assertions for `Taxa barplot`.
  assertions:
  - 'has_size: {''min'': ''400k'', ''max'': ''500k''}'
  - 'has_archive_member: {''path'': ''^[^/]*/data/.*\\.csv'', ''n'': 7}'
  - 'has_archive_member: {''path'': ''^[^/]*/data/.*\\.jsonp'', ''n'': 7}'
- role: taxonomy_classification_table
  description: Content assertions for `Taxonomy classification table`.
  assertions:
  - 'has_size: {''min'': ''1M'', ''max'': ''2M''}'
  - 'has_archive_member: {''path'': ''^[^/]*/data/metadata.tsv'', ''n'': 1, ''asserts'':
    [{''has_n_lines'': {''n'': 289}}]}'
---

# QIIME2 downstream: phylogeny, rarefaction, and taxonomy

## When to use this sketch
- You already have DADA2 outputs from QIIME2 (representative sequences `.qza` and feature table `.qza`) and need to run the standard downstream triad: phylogenetic tree, alpha rarefaction, and taxonomy.
- Your amplicon targets a marker with an available SEPP reference (e.g. 16S against Greengenes `sepp-refs-gg-13-8`) and a pre-trained naive Bayes classifier (Greengenes or SILVA).
- You have a tab-separated sample metadata file and want QZV visualizations (rarefaction curves, taxa barplot, taxonomy table) to explore before diversity analyses.
- You want outputs (rooted tree, taxonomy) that feed directly into `core-metrics-phylogenetic` for alpha/beta diversity as a follow-on step.

## Do not use when
- You are starting from raw demultiplexed or multiplexed reads — run a QIIME2 import + DADA2 denoising sketch first to produce the `rep-seqs.qza` and `table.qza` this workflow expects.
- You need alpha/beta diversity metrics, PCoA, Emperor plots, or group significance tests — use the sibling `amplicon-qiime2-core-metrics-diversity` sketch (the QIIME2 VI workflow) which chains after this one.
- You want de novo or `align-to-tree-mafft-fasttree` phylogeny instead of SEPP fragment insertion against a reference — this workflow is SEPP-only.
- Your data are shotgun metagenomics or non-amplicon — use a metagenomics profiling sketch.
- You need a trained classifier built from scratch — this sketch consumes a pre-fitted sklearn classifier.

## Analysis outline
1. `qiime2 fragment-insertion sepp` — insert DADA2 representative sequences into a SEPP reference phylogeny to produce a rooted tree (and placements).
2. `qiime2 feature-classifier classify-sklearn` — assign taxonomy to the representative sequences using a pre-trained naive Bayes classifier.
3. `qiime2 taxa barplot` — build interactive taxonomy barplot from the feature table, taxonomy, and sample metadata.
4. `qiime2 metadata tabulate` — render the taxonomy classification as an interactive QZV table.
5. `qiime2 diversity alpha-rarefaction` — compute alpha rarefaction curves across a user-defined depth range using the rooted tree, feature table, and metadata.

## Key parameters
- `fragment-insertion sepp`: `alignment_subset_size: 1000`, `placement_subset_size: 5000` (defaults retained).
- `classify-sklearn`: `confidence: 0.7`, `read_orientation: auto`, `reads_per_batch: auto`.
- `alpha-rarefaction`: `min_depth` (user input, ≥1), `max_depth` (user input, chosen from feature table sampling depth), `steps: 10`, `iterations: 10`.
- `taxa barplot`: default `level_delimiter` (none); taxonomy levels are inferred from the classifier.
- Classifier and SEPP reference must match the amplicon region (e.g. Greengenes 13_8 515F/806R for V4 16S).

## Test data
The test profile uses the Parkinson's Mouse tutorial dataset from QIIME2 docs: `sample_metadata.tsv`, DADA2 outputs `dada2_rep_set.qza` and `dada2_table.qza`, the Greengenes 13_8 SEPP reference `sepp-refs-gg-13-8.qza`, and the Greengenes 13_8 99% 515F/806R pre-fitted naive Bayes classifier `gg-13-8-99-515-806-nb-classifier.qza`. Rarefaction is run with `Minimum depth = 1` and `Maximum depth = 2019`. Expected outputs are a rooted tree QZA (~2–3 MB, Newick containing `k__Bacteria`, type `Phylogeny[Rooted]`), an alpha rarefaction QZV (~400–500 KB with 3 CSVs and 21 JSONP data files), a taxonomy QZA (`FeatureData[Taxonomy]`, ~40–80 KB, `taxonomy.tsv` with 288 lines), a taxa barplot QZV (~400–500 KB, 7 CSV and 7 JSONP assets), and a taxonomy classification QZV table (~1–2 MB, `metadata.tsv` with 289 lines).

## Reference workflow
IWC `workflows/amplicon/qiime2/qiime2-III-VI-downsteam/QIIME2-III-V-Phylogeny-Rarefaction-Taxonomic-Analysis.ga`, release 0.2, QIIME2 tool suite `2024.10.0+q2galaxy.2024.10.0`. Mirrors the downstream steps of the QIIME2 Parkinson's Mouse tutorial (https://docs.qiime2.org/2024.5/tutorials/pd-mice/).
