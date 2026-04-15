---
name: amplicon-otu-taxonomic-summary-tables
description: Use when you already have per-sample OTU tables from an MGnify-style
  amplicon (16S/18S SSU) pipeline and need to merge them into cross-sample taxonomic
  abundance summary tables, including a full-lineage table and a collapsed phylum-level
  table. Purely a post-processing / table aggregation step; does not perform read
  QC, OTU picking, or taxonomic assignment.
domain: amplicon
organism_class:
- microbial-community
input_data:
- otu-tables-tabular
source:
  ecosystem: iwc
  workflow: MGnify amplicon summary tables
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/amplicon/amplicon-mgnify/mgnify-amplicon-taxonomic-summary-tables
  version: '0.2'
  license: MIT
  slug: amplicon--amplicon-mgnify--mgnify-amplicon-taxonomic-summary-tables
tools:
- name: query_tabular
  version: 3.3.2
- name: gnu-awk
- name: galaxy-grouping
- name: filter_tabular
  version: 3.3.1
- name: collection_column_join
  version: 0.0.3
tags:
- amplicon
- 16S
- 18S
- SSU
- MGnify
- OTU
- taxonomy
- summary-table
- phylum
- microgalaxy
test_data:
- role: otu_tables__err3046414_merged_fastq_ssu_otu_tabular
  url: https://zenodo.org/records/13710235/files/ERR3046414_MERGED_FASTQ_SSU_OTU.tabular
  sha1: b7d84db93bff8ac05ba6cc6abe8c357d80d5ddc6
- role: otu_tables__err3046440_merged_fastq_ssu_otu_tabular
  url: https://zenodo.org/records/13710235/files/ERR3046440_MERGED_FASTQ_SSU_OTU.tabular
  sha1: 6416384de86346b5a861e15660ceca9b922cc1a9
- role: otu_tables__err4319664_merged_fastq_ssu_otu_tabular
  url: https://zenodo.org/records/13710235/files/ERR4319664_MERGED_FASTQ_SSU_OTU.tabular
  sha1: 5a6f57bf76bd8b55ef67ee6a924edf7bd562e791
- role: otu_tables__err4319712_merged_fastq_ssu_otu_tabular
  url: https://zenodo.org/records/13710235/files/ERR4319712_MERGED_FASTQ_SSU_OTU.tabular
  sha1: 2842edc7d83ecfede21ff6565c9cd56ef520298d
expected_output: []
---

# MGnify amplicon OTU taxonomic summary tables

## When to use this sketch
- You have a collection of per-sample OTU tables produced by the MGnify v5 amplicon pipeline (SSU rRNA) or an equivalent tool that emits `count`, `taxonomy`, `OTU-id`-style tabular OTU files with semicolon-delimited `sk__;k__;p__;...` lineages.
- You need two cross-sample wide tables: (1) a full taxonomic-lineage abundance matrix and (2) a phylum-level (superkingdom/kingdom/phylum) collapsed abundance matrix, both with samples as columns.
- You want a lightweight, Galaxy-native post-processing step with no additional biological inference — only reshaping, grouping, and joining.

## Do not use when
- You are starting from raw FASTQ amplicon reads and still need primer trimming, denoising/clustering, and taxonomic classification — run a full amplicon pipeline (e.g. DADA2, QIIME2, or the upstream MGnify amplicon workflow) first, then feed its OTU tables into this sketch.
- You want genus- or species-level abundance tables or alpha/beta diversity — this sketch only emits the full lineage and a phylum-collapsed view.
- Your inputs are BIOM files or shotgun metagenomic profiles (e.g. MetaPhlAn, Kraken) — the awk rules here assume MGnify's `sk__;k__;p__;c__;o__;f__;g__;s__` semicolon format in a specific column layout.
- You need differential-abundance testing, ordination, or visualization — use a dedicated downstream stats/plotting workflow.

## Analysis outline
1. Ingest a Galaxy list collection of per-sample OTU tables (one tabular per sample, MGnify SSU OTU format).
2. For the full-lineage table: Query Tabular selects columns `c1,c4,c3` (OTU id, taxonomy, count) per sample, stripping comment lines and prepending the dataset identifier.
3. Text reformatting (awk) rewrites the header to `#SampleID` + taxonomy and emits one `(taxa, count)` row per OTU.
4. Collection Column Join merges all per-sample two-column tables on the taxonomy key using `fill_char=0` and a shared header, producing a wide matrix.
5. A final awk pass trims sample-name suffixes after the first underscore in the column headers and writes the user-named taxonomic abundance summary table.
6. For the phylum-level table: an awk pass over each raw OTU table keeps only the first three lineage ranks (`sk__`, `k__`, `p__`), substituting `unassigned` for missing ranks, and emits `superkingdom;kingdom;phylum \t count`.
7. Galaxy Group sums counts per collapsed lineage within each sample.
8. Filter Tabular prepends the dataset name, Collection Column Join merges the per-sample phylum tables, and a final awk splits the lineage back into three columns (`superkingdom`, `kingdom`, `phylum`) and cleans sample headers, producing the user-named phylum-level summary table.

## Key parameters
- OTU table collection: Galaxy `list` collection; each element must be an MGnify-style SSU OTU tabular with at least columns OTU id, count, taxonomy (semicolon-delimited with `rank__value` tokens) and `#`-prefixed comment lines.
- Query Tabular SQL: `SELECT c1, c4, c3 FROM t1;` with line filters `comment_char=35` and `prepend_dataset_name` — assumes the MGnify column order.
- Phylum awk: `levels = 3` (superkingdom, kingdom, phylum); empty ranks become `unassigned`.
- Grouping tool: `groupcol=1`, operation `sum` on column 2 — aggregates counts per collapsed lineage per sample.
- Collection Column Join: `identifier_column=1`, `has_header=1`, `fill_char=0` — taxa absent from a sample are filled with 0.
- Output naming: two required text parameters — `Taxonomic abundance summary table name` and `Phylum level taxonomic abundance summary table name` — are applied as RenameDatasetAction on the final two awk steps.

## Test data
The test job supplies a list collection of four MGnify SSU OTU tabular files from Zenodo record 13710235: `ERR3046414`, `ERR3046440`, `ERR4319664`, and `ERR4319712` (all `_MERGED_FASTQ_SSU_OTU.tabular`). The two text parameters are set to `taxonomic_summary_table` and `phylum_taxonomic_summary_table`. Running the workflow is expected to produce two tabular outputs matching the Zenodo-hosted references `taxonomic_summary_table.tabular` (full-lineage wide matrix, taxa × 4 samples) and `phylum_taxonomic_summary_table.tabular` (superkingdom/kingdom/phylum × 4 samples, with `0` fill for absent phyla and `unassigned` for missing ranks).

## Reference workflow
Galaxy IWC — `workflows/amplicon/amplicon-mgnify/mgnify-amplicon-taxonomic-summary-tables` (`MGnify amplicon summary tables`, release 0.2, MIT). Subworkflow of the MGnify v5 amplicon pipeline port; author: Rand Zoabi.
