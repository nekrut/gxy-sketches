---
name: mgnify-otu-rank-abundance-summary
description: Use when you need to collapse a collection of per-sample MAPseq/MGnify
  amplicon OTU tables into a single cross-sample abundance matrix at one chosen taxonomic
  rank (superkingdom through species). Input is the OTU tabular collection from the
  MGnify amplicon pipeline; output is one tidy tab-delimited summary table with taxonomy
  columns and one count column per sample.
domain: amplicon
organism_class:
- bacterial
- eukaryote
input_data:
- mapseq-otu-tables-tabular
source:
  ecosystem: iwc
  workflow: Taxonomic abundance summary tables for a specified taxonomic rank
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/amplicon/amplicon-mgnify/taxonomic-rank-abundance-summary-table
  version: '0.2'
  license: MIT
tools:
- map_param_value
- gawk
- galaxy-grouping
- filter_tabular
- collection_column_join
tags:
- amplicon
- 16s
- 18s
- ssu
- lsu
- mgnify
- mapseq
- otu
- taxonomy
- summary-table
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
expected_output:
- role: taxonomic_rank_summary_table
  description: Content assertions for `Taxonomic rank summary table`.
  assertions:
  - 'that: has_size'
  - 'size: 11263'
  - 'that: has_text'
  - "text: superkingdom\tkingdom\tphylum\tclass\torder\tfamily\tERR3046414\tERR3046440\t\
    ERR4319664\tERR4319712"
  - 'that: has_text'
  - "text: Bacteria\tunassigned\tActinobacteria\tAcidimicrobiia\tunassigned\tunassigned\t\
    0\t0\t1\t3"
  - 'that: has_text'
  - "text: Bacteria\tunassigned\tActinobacteria\tActinobacteria\tActinomycetales\t\
    Actinomycetaceae\t4\t1\t0\t0"
  - 'that: has_n_lines'
  - 'n: 129'
  - 'that: has_n_columns'
  - 'n: 10'
---

# MGnify amplicon OTU rank-abundance summary table

## When to use this sketch
- You already have a Galaxy dataset collection of MAPseq-style OTU tabular files (typically `*_MERGED_FASTQ_SSU_OTU.tabular` or LSU equivalents) from the MGnify amplicon pipeline, one per sample.
- You want a single wide summary table where rows are taxa collapsed to one chosen rank (superkingdom, kingdom, phylum, class, order, family, genus, or species) and columns are per-sample read counts.
- You are preparing input for downstream diversity, barplot, or heatmap analyses and need the taxonomy flattened to a specific level with unassigned ranks explicitly labelled `unassigned`.
- You are running this as a sub-step of a larger MGnify amplicon analysis in Galaxy/IWC.

## Do not use when
- You still need to go from raw FASTQ reads to OTU tables — run the upstream MGnify amplicon / MAPseq classification workflow first.
- You want multiple ranks at once — invoke this workflow once per rank, or use a multi-rank sibling workflow if available.
- Your OTU tables are not in the MAPseq/MGnify format (semicolon-separated `superkingdom__;kingdom__;phylum__;...` taxonomy in column 3, counts in column 2); the embedded awk scripts assume that exact schema.
- You need relative abundances, rarefaction, or statistical testing — this workflow only sums raw counts.
- Your data is shotgun metagenomic taxonomic profiling (Kraken2/MetaPhlAn) rather than amplicon OTU tables.

## Analysis outline
1. **Select rank-specific awk scripts** — `Map parameter value` (iuc/map_param_value 0.2.0) twice, mapping the user's rank choice to (a) a per-sample flattening awk program and (b) a final header/column-splitting awk program.
2. **Flatten taxonomy per sample** — `Text reformatting` (bgruening/tp_awk_tool 9.5+galaxy0) runs the first mapped awk over each OTU table in the collection, keeping only the taxonomy path truncated to the chosen rank (levels 1–8) and the count column, substituting `unassigned` for empty `xx__` fields.
3. **Sum counts per taxon** — `Group` (Grouping1 2.1.4) groups on column 1 (flattened taxonomy) and sums column 2 to collapse duplicate rows within a sample.
4. **Prepend sample identifier** — `Filter Tabular` (iuc/filter_tabular 3.3.1) with `prepend_dataset_name` adds the Galaxy element identifier as a new leading column so samples can be tracked after merging.
5. **Reshape to (taxa, sample_count)** — `Text reformatting` again emits a 2-column table with header `taxa\t<sample_id>` and rows `taxon\tcount`.
6. **Join samples into a matrix** — `Column join` (iuc/collection_column_join 0.0.3) joins every per-sample 2-column file on column 1 (`identifier_column: 1`, `has_header: 1`, `fill_char: 0`) producing a wide taxa × samples table.
7. **Expand taxonomy columns and rewrite header** — final `Text reformatting` runs the second mapped awk, splitting the joined `;`-separated taxonomy back into one column per rank up to the chosen level and rewriting the header to `superkingdom\tkingdom\t…\t<rank>\t<sample_ids>`. Output is renamed `Taxonomic rank summary table`.

## Key parameters
- `Taxonomic rank` (workflow input): text, default `phylum`, restricted to `superkingdom | kingdom | phylum | class | order | family | genus | species`. This single value drives both `Map parameter value` steps and therefore how many taxonomy columns appear in the output.
- `Map parameter value` → `on_unmapped: fail` — invalid rank strings hard-fail the run rather than silently defaulting.
- `Group` tool: `groupcol: 1`, operation `sum` on `opcol: 2`, `ignorecase: false` — do not change; the flattening step guarantees taxonomy is in column 1 and counts in column 2.
- `Filter Tabular`: single line filter `prepend_dataset_name` — required so the per-sample 2-column output carries the Galaxy element identifier into the merged header.
- `Column join`: `identifier_column: 1`, `has_header: 1`, `fill_char: 0`, `old_col_in_header: false` — zero-fills taxa missing from a given sample, which is the correct behaviour for count matrices.
- Downstream awk header format hard-codes the column order `superkingdom kingdom phylum class order family genus species`; any custom rank vocabulary would require editing both map_param_value tables.

## Test data
The workflow's planemo test supplies a list collection of four MAPseq SSU OTU tabular files downloaded from Zenodo record 13710235: `ERR3046414`, `ERR3046440`, `ERR4319664`, and `ERR4319712` (`*_MERGED_FASTQ_SSU_OTU.tabular`, SHA-1 hashes pinned in the test spec). The `Taxonomic rank` parameter is set to `family`. The single expected output is a `Taxonomic rank summary table` of exactly 129 lines and 10 columns (6 taxonomy columns `superkingdom kingdom phylum class order family` plus one count column per sample) and file size 11263 bytes. The test asserts specific rows such as `Bacteria\tunassigned\tActinobacteria\tAcidimicrobiia\tunassigned\tunassigned\t0\t0\t1\t3` and `Bacteria\tunassigned\tActinobacteria\tActinobacteria\tActinomycetales\tActinomycetaceae\t4\t1\t0\t0`, confirming both the zero-fill behaviour and the `unassigned` substitution for empty lineage entries.

## Reference workflow
Galaxy IWC workflow `amplicon/amplicon-mgnify/taxonomic-rank-abundance-summary-table`, release 0.2 (2025-03-10), MIT, author Rand Zoabi. Source: https://github.com/galaxyproject/iwc/tree/main/workflows/amplicon/amplicon-mgnify/taxonomic-rank-abundance-summary-table
