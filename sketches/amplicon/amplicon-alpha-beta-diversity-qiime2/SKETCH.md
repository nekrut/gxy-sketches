---
name: amplicon-alpha-beta-diversity-qiime2
description: Use when you have a QIIME2 DADA2 feature table, sample metadata, and
  a rooted phylogenetic tree from a 16S/18S/ITS amplicon study and need to compute
  alpha and beta diversity metrics, run group-significance tests, and generate PCoA/Emperor
  visualizations at a chosen rarefaction sampling depth.
domain: amplicon
organism_class:
- bacterial
- eukaryote
input_data:
- qiime2-feature-table-qza
- qiime2-rooted-tree-qza
- sample-metadata-tsv
source:
  ecosystem: iwc
  workflow: 'QIIME2 VI: Diversity metrics and estimations'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/amplicon/qiime2/qiime2-III-VI-downsteam
  version: '0.2'
  license: MIT
  slug: amplicon--qiime2--qiime2-III-VI-downsteam--QIIME2-VI-diversity-metrics-and-estimations
tools:
- name: qiime2
  version: 2024.10.0+dist.h3d8a7e27
- name: q2-diversity
- name: core-metrics-phylogenetic
- name: alpha-group-significance
- name: beta-group-significance
- name: emperor
tags:
- qiime2
- 16s
- amplicon
- microbiome
- alpha-diversity
- beta-diversity
- unifrac
- bray-curtis
- jaccard
- pcoa
- permanova
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

# QIIME2 amplicon alpha- and beta-diversity analysis

## When to use this sketch
- You already have a QIIME2 `FeatureTable[Frequency]` (e.g. `dada2_table.qza`) and a rooted phylogeny (`Phylogeny[Rooted]`) produced by an upstream amplicon workflow (DADA2 + SEPP / de novo tree).
- You have a tab-separated sample metadata file compatible with QIIME2 and at least one categorical column suitable for group comparisons.
- The user wants standard community-ecology outputs: Shannon, observed features, Pielou evenness, Faith PD, Jaccard, Bray-Curtis, and weighted/unweighted UniFrac, plus PCoA/Emperor plots.
- The user wants to test whether a metadata variable (treatment, genotype, body site, timepoint, etc.) significantly structures community composition via PERMANOVA.
- A reasonable rarefaction sampling depth has already been chosen (typically from an alpha-rarefaction curve in a prior step).

## Do not use when
- You still need to go from raw FASTQs to a feature table — run a DADA2 / denoising amplicon workflow first.
- You do not yet have a rooted phylogenetic tree — run a QIIME2 phylogeny workflow (e.g. `fragment-insertion sepp` against a reference such as `sepp-refs-gg-13-8`) first; that is the sibling `qiime2-III-V` downstream workflow, not this one.
- You need taxonomic classification, taxa barplots, or alpha-rarefaction curve selection — those belong in the sibling `qiime2-III-V` taxonomy/rarefaction workflow.
- You are doing differential abundance, longitudinal, or machine-learning analyses (ANCOM, q2-longitudinal, q2-sample-classifier) — those are downstream of this sketch.
- Your data are shotgun metagenomics reads rather than marker-gene amplicons.

## Analysis outline
1. Import the sample metadata TSV as a QIIME2 `ImmutableMetadata` artifact via `qiime2 tools import` (used later by beta-group-significance which needs a `.qza` metadata source).
2. Run `qiime2 diversity core-metrics-phylogenetic` on the feature table, rooted tree, and metadata at the chosen sampling depth. This single step rarefies the table and emits: rarefied table; Faith PD, observed features, Shannon, and Pielou evenness alpha vectors; Jaccard, Bray-Curtis, unweighted UniFrac, and weighted UniFrac distance matrices; matching PCoA results; and Emperor visualizations for each beta metric.
3. Run `qiime2 diversity alpha-group-significance` against the metadata three times — once each on the Pielou evenness, observed features, and Shannon vectors — to produce Kruskal-Wallis group comparison visualizations.
4. Run `qiime2 diversity beta-group-significance` (PERMANOVA, 999 permutations, non-pairwise) against the Jaccard, Bray-Curtis, and weighted UniFrac distance matrices using the user-supplied target metadata column.
5. Bundle the core-metrics outputs into four Galaxy collections for downstream convenience: distance matrices, PCoA results, Emperor plots, and a richness/evenness collection containing the rarefied table plus the four alpha vectors.

## Key parameters
- `sampling_depth` (integer, required): even-sampling depth for rarefaction inside core-metrics-phylogenetic. Choose based on a prior alpha-rarefaction curve to trade off per-sample feature retention against sample inclusion.
- `metadata_column` (text, required): the metadata column name passed to beta-group-significance as the grouping variable.
- `beta-group-significance.method`: `permanova` (workflow default).
- `beta-group-significance.permutations`: `999`.
- `beta-group-significance.pairwise`: `false`.
- `core-metrics-phylogenetic.with_replacement`: `false`; `ignore_missing_samples`: `false`.
- Inputs must be QIIME2 artifacts: `FeatureTable[Frequency]` (`.qza`), `Phylogeny[Rooted]` (`.qza`), and a QIIME2-valid metadata TSV.

## Test data
The workflow is exercised with the QIIME2 Parkinson's Mouse tutorial dataset: `sample_metadata.tsv`, the DADA2 feature table `dada2_table.qza`, and the DADA2 representative sequences `dada2_rep_set.qza`, plus the SEPP reference `sepp-refs-gg-13-8.qza` and the Greengenes 13-8 515F/806R naive-Bayes classifier — these last three feed the sibling III-V phylogeny/taxonomy workflow that produces the rooted tree consumed here. Expected outputs are QIIME2 visualization artifacts (`.qzv`) for alpha-group-significance on Pielou evenness, observed features, and Shannon, plus PERMANOVA `.qzv` visualizations for Jaccard, Bray-Curtis, and weighted UniFrac, and four Galaxy collections (distance matrices, PCoA, Emperor, richness/evenness) wrapping the `core-metrics-phylogenetic` outputs. The IWC test manifest bundled with this workflow actually validates the upstream III-V stage (rooted tree size 2–3 MB containing `data/tree.nwk` with `k__Bacteria`, rarefaction curve `.qzv` ~400–500 kB with 21 jsonp panels, taxonomy TSV with 288 lines, and a 289-line taxa table), which establishes the artifacts that feed this diversity stage.

## Reference workflow
Galaxy IWC: `workflows/amplicon/qiime2/qiime2-III-VI-downsteam` — "QIIME2 VI: Diversity metrics and estimations", release 0.2 (2024-11-04), MIT. Built on QIIME2 2024.10 q2-diversity tools. Analogous to the Parkinson's Mouse tutorial (`https://docs.qiime2.org/2024.5/tutorials/pd-mice/`).
