---
name: mapseq-otu-to-ampvis2-reformat
description: Use when you have per-sample MAPseq OTU tables (tab-separated sequence
  counts with MGnify-style sk__/k__/p__/c__/o__/f__/g__/s__ taxonomy strings) plus
  a sample metadata sheet and you need to reshape them into a combined OTU table,
  taxonomy table, and an ampvis2 R object for downstream amplicon/microbiome visualization
  and diversity analysis.
domain: amplicon
organism_class:
- bacterial
- eukaryote
input_data:
- mapseq-otu-tables
- sample-metadata-tabular
source:
  ecosystem: iwc
  workflow: MAPseq to ampvis2
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/amplicon/amplicon-mgnify/mapseq-to-ampvis2
  version: '0.2'
  license: MIT
tools:
- query_tabular
- awk
- collapse_collections
- collection_column_join
- ampvis2_load
tags:
- amplicon
- 16s
- mgnify
- mapseq
- ampvis2
- otu-table
- taxonomy
- reformatting
- microbiome
test_data:
- role: mapseq_otu_tables__srr11032273
  url: https://zenodo.org/records/13347829/files/SRR11032273.tsv
  sha1: d2fd3d89b234bbab32970eaf9f0726c58ed29d88
- role: mapseq_otu_tables__srr11032274
  url: https://zenodo.org/records/13347829/files/SRR11032274.tsv
  sha1: 05f4509710e8616a83dd39c2731e032ac3ad1949
- role: mapseq_otu_tables__srr11032275
  url: https://zenodo.org/records/13347829/files/SRR11032275.tsv
  sha1: e80d81e221443905b8219cbeddfbcbea1da4bb59
- role: mapseq_otu_tables__srr11032276
  url: https://zenodo.org/records/13347829/files/SRR11032276.tsv
  sha1: 767b4e0db91d7146d09f1155e2d12d3e0dbf4735
- role: mapseq_otu_tables__srr11032277
  url: https://zenodo.org/records/13347829/files/SRR11032277.tsv
  sha1: 9ddfccd5031022ff22a291ff60c5b310769344ca
- role: mapseq_otu_tables__srr11038211
  url: https://zenodo.org/records/13347829/files/SRR11038211.tsv
  sha1: cdfa0e890e8b643616b6ffbc03ab90e40cbcd0cb
- role: mapseq_otu_tables__srr11038212
  url: https://zenodo.org/records/13347829/files/SRR11038212.tsv
  sha1: c928219b888de07d2e0fab00e28d7f37544fe974
- role: mapseq_otu_tables__srr11038213
  url: https://zenodo.org/records/13347829/files/SRR11038213.tsv
  sha1: 90592603e92455196e4521093ef408cd4515562b
- role: mapseq_otu_tables__srr11038214
  url: https://zenodo.org/records/13347829/files/SRR11038214.tsv
  sha1: 1f115a5823d08bf00976ebd09768f333580b4cbf
- role: mapseq_otu_tables__srr11038215
  url: https://zenodo.org/records/13347829/files/SRR11038215.tsv
  sha1: 63e64aba69f7dfae646f6b06cf939986bdbb39f0
- role: otu_table_metadata
  url: https://zenodo.org/records/13347829/files/test_metadata_formatted.tabular
  sha1: 01b1f71016d2fbb1add6e5f36a32f61db40f8bb2
expected_output:
- role: ampvis2_object
  description: Content assertions for `Ampvis2 object`.
  assertions:
  - 'that: has_size'
  - 'value: 15000'
  - 'delta: 1000'
---

# MAPseq OTU tables to ampvis2 object

## When to use this sketch
- You have already run MAPseq (typically via the MGnify amplicon pipeline) and hold one tab-separated OTU table per sample, each with sequence counts and a semicolon-delimited lineage using the `sk__`/`k__`/`p__`/`c__`/`o__`/`f__`/`g__`/`s__` prefix convention.
- You want to join those per-sample tables into a single wide OTU abundance table, derive a consolidated taxonomy table, and load both together with a sample metadata file into an ampvis2 R object for alpha/beta diversity, ordination, heatmaps, or rank-abundance plots.
- You are working in Galaxy (or an IWC-compatible runner) and prefer a pre-built reformatting pipeline over writing custom awk/SQL glue.
- Your samples are 16S/18S/ITS amplicon data whose taxonomy was assigned by MAPseq against an MGnify-style reference (SILVA, UNITE, PR2, etc.).

## Do not use when
- You still have raw amplicon FASTQs and have not yet produced OTU tables — run an upstream amplicon pipeline (DADA2, QIIME2, or the MGnify MAPseq workflow) first.
- Your OTU/ASV tables come from DADA2, QIIME2, mothur, or a biom file — use an ampvis2 loader sketch tailored to that format instead; the awk rules here assume MAPseq's specific three-column layout and `sk__`-prefixed lineage.
- You need shotgun metagenomic taxonomic profiles (Kraken2, MetaPhlAn, mOTUs) — those require a different reformatting path.
- You want to perform the downstream ampvis2 analyses themselves (heatmap, ordinate, rarefy) rather than just build the ampvis2 object.

## Analysis outline
1. Ingest a Galaxy dataset collection of per-sample MAPseq OTU TSVs and a single metadata tabular file.
2. Per sample, run Query Tabular to compute a `relative_abundance` column as `count * 100 / SUM(count) OVER()`, stripping `#` comment lines and prepending the dataset name.
3. Per sample, run awk to emit a two-column `OTU\t<sample>` table where rows are `OTU_<id>` and relative abundance, with the sample name derived from the filename prefix.
4. Column-join (Collection Column Join) all per-sample tables on OTU id with `fill_char=0` to build a wide OTU-by-sample matrix.
5. Run awk once more to trim trailing `.` suffixes from sample column headers, yielding the final `OTU table`.
6. In parallel, run awk on the raw MAPseq tables to split the lineage string into nine columns (`OTU`, Superkingdom, Kingdom, Phylum, Class, Order, Family, Genus, Species).
7. Collapse the per-sample taxonomy collection into one file, prepend a header row, and use Query Tabular with `GROUP BY OTU` + `GROUP_CONCAT(DISTINCT …)` to deduplicate per-OTU lineages into the final `Taxonomy table`.
8. Feed the OTU table, Taxonomy table, and user metadata into `ampvis2 load` to emit the `Ampvis2 object` plus normalized `metadata_list` and `taxonomy_list` tabulars.

## Key parameters
- Query Tabular (abundance): `sqlquery = SELECT c1, c2, c3, c3 * 100 / SUM(c3) OVER() AS relative_abundance FROM t1;` with line filters `comment_char=#` and `prepend_dataset_name`.
- Awk (taxonomy split): matches lineage tokens by the prefixes `sk__`, `k__`, `p__`, `c__`, `o__`, `f__`, `g__`, `s__`; OTU ids are rewritten as `OTU_<id>`.
- Collection Column Join: `identifier_column=1`, `fill_char=0`, `has_header=0`, `old_col_in_header=true` — required so missing OTUs across samples become zero counts.
- Query Tabular (taxonomy dedup): `GROUP BY c1` with `GROUP_CONCAT(DISTINCT c2..c9)` to merge duplicate OTU rows coming from multiple samples.
- ampvis2 load: `write_lists = [tax, metadata]`, `guess_column_types=true`, `pruneSingletons=false`; `fasta` and `tree` left as runtime/optional.
- No taxonomy rank filtering, rarefaction, or normalization is applied — the ampvis2 object preserves raw (count-derived) tables.

## Test data
The test job supplies a Galaxy list collection of ten per-sample MAPseq OTU TSVs (SRR11032273–SRR11032277 and SRR11038211–SRR11038215) hosted on Zenodo record 13347829, together with a single `test_metadata_formatted.tabular` sample sheet. Running the workflow is expected to reproduce the exact `OTU_table.tabular` and `tax_table.tabular`/`taxonomy_list.tabular` golden files on Zenodo (records 13347829 and 14745803), plus a byte-identical `metadata_list.tabular`. The binary `Ampvis2 object` is verified with a size assertion (`has_size ≈ 15000 ± 1000` bytes) because its serialized R representation is not bit-stable across runs.

## Reference workflow
IWC `workflows/amplicon/amplicon-mgnify/mapseq-to-ampvis2`, MAPseq to ampvis2 v0.2 (Galaxy `.ga`, MIT-licensed, authors Rand Zoabi and Mara Besemer). Key tool versions: `query_tabular 3.3.2`, `tp_awk_tool 9.5+galaxy0`, `collapse_collections 5.1.0`, `collection_column_join 0.0.3`, `ampvis2_load 2.8.9+galaxy0`.
