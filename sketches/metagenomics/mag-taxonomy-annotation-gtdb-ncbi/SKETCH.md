---
name: mag-taxonomy-annotation-gtdb-ncbi
description: Use when you have a collection of metagenome-assembled genomes (MAGs)
  or bins (from MetaBAT2, SemiBin2, dRep, Binette, etc.) and need to assign taxonomy
  with GTDB-Tk and reconcile the GTDB lineages against NCBI taxonomy names and taxIDs
  in a single merged per-bin table.
domain: metagenomics
organism_class:
- bacterial
- archaeal
- prokaryote
input_data:
- mag-fasta-collection
- gtdbtk-database
source:
  ecosystem: iwc
  workflow: MAGs taxonomy annotation
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/microbiome/mags-taxonomy-annotation
  version: '0.1'
  license: MIT
  slug: microbiome--mags-taxonomy-annotation
tools:
- name: gtdbtk
  version: 2.5.2+galaxy1
- name: gtdb_to_taxdump
  version: 0.1.9+galaxy0
- name: name2taxid
  version: 0.20.0+galaxy0
- name: multiqc
  version: 1.33+galaxy0
tags:
- mag
- bin
- taxonomy
- gtdb
- ncbi
- taxid
- metagenomics
- classification
test_data:
- role: sequence_collection__50contig_reads_binette_bin1_fasta
  url: https://zenodo.org/records/18635101/files/50contig_reads_binette_bin1.fasta
- role: sequence_collection__50contig_reads_binette_bin2_fasta
  url: https://zenodo.org/records/18635101/files/50contig_reads_binette_bin2.fasta
- role: sequence_collection__50contig_reads_binette_bin3_fasta
  url: https://zenodo.org/records/18635101/files/50contig_reads_binette_bin3.fasta
- role: sequence_collection__50contig_reads_binette_bin4_fasta
  url: https://zenodo.org/records/18635101/files/50contig_reads_binette_bin4.fasta
expected_output:
- role: multiqc_html_report
  description: Content assertions for `MultiQC HTML report`.
  assertions:
  - 'that: has_text'
  - 'text: GTDB-Tk'
  - 'that: has_text'
  - 'text: Unclassified'
- role: gtdb_tk_summary_files
  description: Content assertions for `GTDB-Tk summary files`.
  assertions:
  - 'gtdbtk.bac120.summary: that: has_text'
  - 'gtdbtk.bac120.summary: text: 50contig_reads_binette_bin1.fasta'
  - 'gtdbtk.bac120.summary: that: has_text'
  - 'gtdbtk.bac120.summary: text: Unclassified'
  - 'gtdbtk.bac120.summary: that: has_text'
  - 'gtdbtk.bac120.summary: text: 95.0'
- role: gtdb_ncbi_mapping
  description: Content assertions for `GTDB-NCBI mapping`.
  assertions:
  - 'gtdbtk.bac120.summary: that: has_text'
  - 'gtdbtk.bac120.summary: text: gtdb_taxonomy'
  - 'gtdbtk.bac120.summary: that: has_text'
  - 'gtdbtk.bac120.summary: text: NA'
  - 'gtdbtk.bac120.summary: that: has_text'
  - 'gtdbtk.bac120.summary: text: species'
- role: ncbi_names_to_taxids_mapping
  description: Content assertions for `NCBI names to taxIDs mapping`.
  assertions:
  - 'gtdbtk.bac120.summary: that: has_text'
  - 'gtdbtk.bac120.summary: text: ncbi_taxonomy'
  - 'gtdbtk.bac120.summary: that: has_text'
  - 'gtdbtk.bac120.summary: text: unclassified'
  - 'gtdbtk.bac120.summary: that: has_text'
  - 'gtdbtk.bac120.summary: text: 12908'
- role: full_gtdb_to_ncbi_mapping
  description: Content assertions for `full GTDB to NCBI mapping`.
  assertions:
  - 'gtdbtk.bac120.summary: that: has_text'
  - 'gtdbtk.bac120.summary: text: GTDB_name'
  - 'gtdbtk.bac120.summary: that: has_text'
  - 'gtdbtk.bac120.summary: text: 1648'
  - 'gtdbtk.bac120.summary: that: has_text'
  - 'gtdbtk.bac120.summary: text: species'
---

# MAG taxonomy annotation with GTDB-Tk and NCBI reconciliation

## When to use this sketch
- You already have recovered MAGs / bins (one FASTA per bin) from a metagenomics assembly+binning pipeline and need taxonomic labels.
- You want GTDB-Tk lineages as the primary classification but also need NCBI-compatible names and numeric taxIDs (e.g. for downstream tools that expect NCBI taxonomy such as Krona, Kraken reports, ENA submissions).
- You want a single per-bin table combining BinID, GTDB lineage, rank, NCBI name and NCBI TaxID, plus a MultiQC summary.
- Inputs are bacterial/archaeal prokaryotic genomes (GTDB-Tk scope); eukaryotic bins are out of scope.

## Do not use when
- You still need to recover bins from raw reads/contigs — run an assembly + binning sketch first (e.g. metaSPAdes/MEGAHIT + MetaBAT2/SemiBin2) and feed its output here.
- You only need GTDB-Tk classification without NCBI reconciliation — run `gtdbtk classify_wf` directly instead.
- Your organisms are eukaryotic MAGs — GTDB-Tk does not classify them; use EukCC/BUSCO-based taxonomy sketches.
- You want read-based taxonomic profiling (Kraken2, MetaPhlAn, mOTUs) rather than per-MAG classification.
- You need functional annotation of MAGs (Prokka, Bakta, eggNOG) — different sketch.

## Analysis outline
1. Input: a Galaxy collection of MAG FASTAs plus a cached GTDB-Tk reference database (release 220 in the reference test).
2. Run `GTDB-Tk classify_wf` on the bin collection to produce bac120/ar53 summary files with GTDB lineages.
3. Concatenate per-domain summaries, extract the classification column (`Cut c2`) and deduplicate lineage strings with awk.
4. Strip all-but-species prefix (`^.*;`) to get leaf taxon names, then pass the unique name list through `gtdb_to_taxdump` (NCBI-GTDB map mode) using the matching GTDB metadata release to produce a GTDB→NCBI name mapping.
5. Extract NCBI names, remove rank prefixes (`[a-z]__`), and resolve them to NCBI numeric taxIDs with `name2taxid` against a cached NCBI taxdump.
6. Paste the GTDB-NCBI map and the NCBI name→taxID table side by side and rename the `gtdb_taxonomy` column to `classification`.
7. Derive a per-lineage rank label (domain/phylum/class/order/family/genus/species/unclassified) from the GTDB prefix using awk.
8. Join the per-bin GTDB-Tk summary (BinID keyed on column 1/2) with the rank+NCBI mapping table to produce the final 5-column table: `BinID\tRank\tGTDB_name\tNCBI_name\tNCBI_TaxID`.
9. Feed the GTDB-Tk summary and the merged mapping table into MultiQC (gtdbtk module + custom_content table) for an HTML report.

## Key parameters
- `gtdbtk classify_wf`: `min_perc_aa: 10`, `min_af: 0.65`, `full_tree: false` (uses split tree for lower memory).
- `gtdb_to_taxdump`: `mode: gtdb`, `completeness: 50.0`, `contamination: 5.0`, `fraction: 0.9`, `max_tips: 100`; the cached GTDB metadata release MUST match the GTDB-Tk reference DB release (release 220 in the test).
- `name2taxid`: uses a cached NCBI taxdump (2024-06-05 in the test); `name_field: 1`, `sci_name: false`.
- Column conventions in the final table: BinID, Rank, GTDB_name, NCBI_name, NCBI_TaxID — downstream consumers depend on this header.
- Unmatched NCBI names are filled with `0` (empty_string_filler in the easyjoin step) and rank-less rows are labelled `unclassified`.

## Test data
The reference test uses a list collection of four small bacterial MAG FASTAs produced by Binette from a 50-contig toy metagenome (`50contig_reads_binette_bin1.fasta` … `bin4.fasta`, hosted on Zenodo record 18635101) plus a cached GTDB-Tk release 220 database (`full_database_release_220_downloaded_2024-10-19`). The workflow is expected to emit a GTDB-Tk bac120 summary containing the bin filenames and `Unclassified` entries (with 95.0 percent-AA values), a GTDB→NCBI mapping containing `gtdb_taxonomy`/`NA`/`species`, an NCBI name→taxID table containing `ncbi_taxonomy`, the literal string `unclassified`, and taxID `12908` (NCBI's "unclassified sequences"), a merged full mapping table with header `GTDB_name` and at least one resolved taxID (e.g. `1648`), plus a MultiQC HTML report mentioning `GTDB-Tk` and `Unclassified`.

## Reference workflow
Galaxy IWC `workflows/microbiome/mags-taxonomy-annotation` (MAGs taxonomy annotation, release 0.1, MIT). Built on GTDB-Tk classify_wf 2.5.2, gtdb_to_taxdump 0.1.9, name2taxid 0.20.0 and MultiQC 1.33 as packaged in the Galaxy ToolShed.
