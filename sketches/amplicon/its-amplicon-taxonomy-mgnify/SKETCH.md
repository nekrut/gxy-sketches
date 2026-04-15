---
name: its-amplicon-taxonomy-mgnify
description: "Use when you have pre-processed eukaryotic amplicon sequences (fungal/protist\
  \ ITS) and matching LSU/SSU rRNA BED coordinates, and you need to mask rRNA regions,\
  \ classify the remaining ITS sequences against both ITSoneDB and UNITE, and produce\
  \ OTU tables plus Krona pie charts \u2014 i.e. the ITS branch of the MGnify v5 amplicon\
  \ pipeline."
domain: amplicon
organism_class:
- eukaryote
- fungi
input_data:
- amplicon-fasta-processed
- rrna-bed-coordinates
source:
  ecosystem: iwc
  workflow: MGnify's amplicon pipeline v5.0 - ITS
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/amplicon/amplicon-mgnify/mgnify-amplicon-pipeline-v5-its
  version: '0.2'
  license: Apache-2.0
  slug: amplicon--amplicon-mgnify--mgnify-amplicon-pipeline-v5-its
tools:
- name: bedtools
  version: 2.31.1
- name: mapseq
  version: 2.1.1+galaxy0
- name: biom-convert
  version: 2.1.15+galaxy1
- name: krona
tags:
- its
- fungi
- mgnify
- itsonedb
- unite
- otu
- krona
- metabarcoding
test_data:
- role: lsu_and_ssu_bed__drr010481_fastq_fasta
  url: https://zenodo.org/records/13710235/files/DRR010481.bed
- role: lsu_and_ssu_bed__err2715528_merged_fastq_fasta
  url: https://zenodo.org/records/13710235/files/ERR2715528.bed
- role: processed_sequences__drr010481_fastq_fasta
  url: https://zenodo.org/records/13710235/files/DRR010481_SE.fasta
- role: processed_sequences__err2715528_merged_fastq_fasta
  url: https://zenodo.org/records/13710235/files/ERR2715528_PE.fasta
expected_output:
- role: its_otu_tables_itsonedb
  description: Content assertions for `ITS OTU tables (ITSoneDB)`.
  assertions:
  - 'DRR010481_FASTQ.fasta: that: has_text'
  - 'DRR010481_FASTQ.fasta: text: # Constructed from biom file'
  - 'DRR010481_FASTQ.fasta: that: has_text'
  - 'DRR010481_FASTQ.fasta: text: # OTU ID'
  - 'DRR010481_FASTQ.fasta: that: has_text'
  - 'DRR010481_FASTQ.fasta: text: Unspecified'
  - 'DRR010481_FASTQ.fasta: that: has_text'
  - 'DRR010481_FASTQ.fasta: text: taxonomy'
  - 'DRR010481_FASTQ.fasta: that: has_text'
  - 'DRR010481_FASTQ.fasta: text: taxid'
  - 'DRR010481_FASTQ.fasta: that: has_n_columns'
  - 'DRR010481_FASTQ.fasta: comment: #'
  - 'DRR010481_FASTQ.fasta: n: 4'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_text'
  - 'ERR2715528_MERGED_FASTQ.fasta: text: # Constructed from biom file'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_text'
  - 'ERR2715528_MERGED_FASTQ.fasta: text: # OTU ID'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_text'
  - 'ERR2715528_MERGED_FASTQ.fasta: text: Unspecified'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_text'
  - 'ERR2715528_MERGED_FASTQ.fasta: text: taxonomy'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_text'
  - 'ERR2715528_MERGED_FASTQ.fasta: text: taxid'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_n_columns'
  - 'ERR2715528_MERGED_FASTQ.fasta: comment: #'
  - 'ERR2715528_MERGED_FASTQ.fasta: n: 4'
- role: its_taxonomic_classifications_using_itsonedb
  description: Content assertions for `ITS taxonomic classifications using ITSoneDB`.
  assertions:
  - 'DRR010481_FASTQ.fasta: that: has_text'
  - 'DRR010481_FASTQ.fasta: text: # mapseq v1.2.6 (Jan 20 2023)'
  - 'DRR010481_FASTQ.fasta: that: has_text'
  - 'DRR010481_FASTQ.fasta: text: ITSone'
  - 'DRR010481_FASTQ.fasta: that: has_n_columns'
  - 'DRR010481_FASTQ.fasta: comment: #'
  - 'DRR010481_FASTQ.fasta: n: 15'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_text'
  - 'ERR2715528_MERGED_FASTQ.fasta: text: # mapseq v1.2.6 (Jan 20 2023)'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_text'
  - 'ERR2715528_MERGED_FASTQ.fasta: text: ITSone'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_n_columns'
  - 'ERR2715528_MERGED_FASTQ.fasta: comment: #'
  - 'ERR2715528_MERGED_FASTQ.fasta: n: 15'
- role: its_otu_tables_unite_db
  description: Content assertions for `ITS OTU tables (UNITE DB)`.
  assertions:
  - 'DRR010481_FASTQ.fasta: that: has_text'
  - 'DRR010481_FASTQ.fasta: text: # Constructed from biom file'
  - 'DRR010481_FASTQ.fasta: that: has_text'
  - 'DRR010481_FASTQ.fasta: text: # OTU ID'
  - 'DRR010481_FASTQ.fasta: that: has_text'
  - 'DRR010481_FASTQ.fasta: text: Unspecified'
  - 'DRR010481_FASTQ.fasta: that: has_text'
  - 'DRR010481_FASTQ.fasta: text: taxonomy'
  - 'DRR010481_FASTQ.fasta: that: has_text'
  - 'DRR010481_FASTQ.fasta: text: taxid'
  - 'DRR010481_FASTQ.fasta: that: has_n_columns'
  - 'DRR010481_FASTQ.fasta: comment: #'
  - 'DRR010481_FASTQ.fasta: n: 4'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_text'
  - 'ERR2715528_MERGED_FASTQ.fasta: text: # Constructed from biom file'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_text'
  - 'ERR2715528_MERGED_FASTQ.fasta: text: # OTU ID'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_text'
  - 'ERR2715528_MERGED_FASTQ.fasta: text: Unspecified'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_text'
  - 'ERR2715528_MERGED_FASTQ.fasta: text: taxonomy'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_text'
  - 'ERR2715528_MERGED_FASTQ.fasta: text: taxid'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_n_columns'
  - 'ERR2715528_MERGED_FASTQ.fasta: comment: #'
  - 'ERR2715528_MERGED_FASTQ.fasta: n: 4'
- role: its_taxonomic_classifications_using_unite_db
  description: Content assertions for `ITS taxonomic classifications using UNITE DB`.
  assertions:
  - 'DRR010481_FASTQ.fasta: that: has_text'
  - 'DRR010481_FASTQ.fasta: text: # mapseq v1.2.6 (Jan 20 2023)'
  - 'DRR010481_FASTQ.fasta: that: has_text'
  - 'DRR010481_FASTQ.fasta: text: UNITE'
  - 'DRR010481_FASTQ.fasta: that: has_n_columns'
  - 'DRR010481_FASTQ.fasta: comment: #'
  - 'DRR010481_FASTQ.fasta: n: 15'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_text'
  - 'ERR2715528_MERGED_FASTQ.fasta: text: # mapseq v1.2.6 (Jan 20 2023)'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_text'
  - 'ERR2715528_MERGED_FASTQ.fasta: text: UNITE'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_n_columns'
  - 'ERR2715528_MERGED_FASTQ.fasta: comment: #'
  - 'ERR2715528_MERGED_FASTQ.fasta: n: 15'
- role: its_otu_tables_in_hdf5_format_itsonedb
  description: Content assertions for `ITS OTU tables in HDF5 format (ITSoneDB)`.
  assertions:
  - 'DRR010481_FASTQ.fasta: that: has_size'
  - 'DRR010481_FASTQ.fasta: value: 37000'
  - 'DRR010481_FASTQ.fasta: delta: 10000'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_size'
  - 'ERR2715528_MERGED_FASTQ.fasta: value: 72000'
  - 'ERR2715528_MERGED_FASTQ.fasta: delta: 10000'
- role: its_otu_tables_in_json_format_unite_db
  description: Content assertions for `ITS OTU tables in JSON format (UNITE DB)`.
  assertions:
  - 'DRR010481_FASTQ.fasta: that: has_text'
  - 'DRR010481_FASTQ.fasta: text: "type": "OTU table"'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_text'
  - 'ERR2715528_MERGED_FASTQ.fasta: text: "type": "OTU table"'
- role: its_taxonomic_abundance_pie_charts_itsonedb
  description: Content assertions for `ITS taxonomic abundance pie charts (ITSoneDB)`.
  assertions:
  - 'that: has_text'
  - 'text: DRR010481_FASTQ_fasta'
  - 'that: has_text'
  - 'text: ERR2715528_MERGED_FASTQ_fasta'
- role: its_otu_tables_in_hdf5_format_unite_db
  description: Content assertions for `ITS OTU tables in HDF5 format (UNITE DB)`.
  assertions:
  - 'DRR010481_FASTQ.fasta: that: has_size'
  - 'DRR010481_FASTQ.fasta: value: 37000'
  - 'DRR010481_FASTQ.fasta: delta: 10000'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_size'
  - 'ERR2715528_MERGED_FASTQ.fasta: value: 72000'
  - 'ERR2715528_MERGED_FASTQ.fasta: delta: 10000'
- role: its_taxonomic_abundance_pie_charts_unite_db
  description: Content assertions for `ITS taxonomic abundance pie charts (UNITE DB)`.
  assertions:
  - 'that: has_text'
  - 'text: DRR010481_FASTQ_fasta'
  - 'that: has_text'
  - 'text: ERR2715528_MERGED_FASTQ_fasta'
---

# MGnify v5 ITS amplicon taxonomy

## When to use this sketch
- You are analyzing fungal or other eukaryotic ITS amplicon data (ITS1/ITS2) and want MGnify-compatible outputs.
- You already have QC'd, dereplicated amplicon sequences in FASTA (e.g. from the MGnify v5 quality-control subworkflow) plus per-sample BED files marking LSU and SSU rRNA hits (typically from cmsearch against Rfam ribosomal covariance models).
- You need dual-database taxonomic assignment against both ITSoneDB and UNITE, with OTU tables in TSV and BIOM (HDF5 + JSON) and Krona HTML charts.
- You want the MGnify pipeline v5 behavior specifically, where LSU/SSU regions are hard-masked before ITS classification.

## Do not use when
- Your amplicon targets the 16S/18S rRNA gene rather than ITS — use the sibling MGnify v5 SSU/LSU amplicon sketch instead.
- You start from raw FASTQ and still need primer trimming, merging, quality filtering, or rRNA detection — run the MGnify v5 amplicon quality-control / rRNA-prediction subworkflow first, then feed its outputs here.
- You want ASV-level resolution with DADA2 or denoising — this workflow is OTU-style via MAPseq closed-reference assignment, not denoising.
- You need shotgun metagenomic taxonomic profiling — use a metagenomics sketch (Kraken2, MetaPhlAn, mOTUs) instead.

## Analysis outline
1. Filter empty BED datasets and align BED/FASTA collections by element identifier so every sample has both an LSU/SSU BED and a processed sequence FASTA (Galaxy Filter empty datasets + Filter collection).
2. Mask LSU and SSU rRNA regions in each sample's FASTA with `bedtools maskfasta` using N as the mask character, yielding ITS-only sequences.
3. Classify the masked ITS sequences against the MGnify ITSoneDB reference with MAPseq, producing per-sample classifications, OTU TSV (with and without taxid), and a Krona-formatted table.
4. Independently classify the same masked sequences against the MGnify UNITE reference with MAPseq.
5. Reformat MAPseq outputs with awk to drop samples that produced no hits, then filter empty datasets downstream so only populated results propagate.
6. Convert populated OTU TSVs to BIOM HDF5 and BIOM JSON via `biom convert` (OTU table type, `process_obs_metadata=taxonomy`) for both databases.
7. Render Krona HTML pie charts for ITSoneDB and UNITE results, gated by a subworkflow that maps non-empty collections to a boolean so Krona is skipped when no sample classified.

## Key parameters
- `bedtools maskfasta`: `mc: N`, `soft: false`, `fullheader: false` — hard-mask rRNA regions with N.
- MAPseq (ITSoneDB): cached reference `mgnify_its_itsonedb_from_2023-09-26`, `minid1: 1`, `minid2: 1`, `minscore: 30`, `tophits: 80`, `topotus: 40`, `otulim: 50`, `outfmt: simple`, `mapseq2biom: yes`, `krona_input: true`.
- MAPseq (UNITE): identical scoring parameters, cached reference `mgnify_its_unite_from_2023-09-26`.
- `biom convert`: input `tsv` with `process_obs_metadata: taxonomy`, output `biom` `OTU table`, emitted in both `hdf5` and `json` flavors.
- Krona pie chart: `type_of_data: text`, `root_name: Root`, conditionally executed via `when` boolean derived from collection emptiness.

## Test data
Two public MGnify amplicon samples are supplied as aligned collections: DRR010481 (single-end) and ERR2715528 (paired, merged), each as a processed FASTA plus a matching BED of LSU/SSU coordinates hosted on Zenodo record 13710235. Running the workflow is expected to produce per-sample ITS FASTA files (rRNA-masked), MAPseq tabular classifications containing the `# mapseq v1.2.6` header and the `ITSone` or `UNITE` database tag across 15 columns, OTU TSVs with the `# Constructed from biom file` header and 4 columns including a `taxonomy`/`taxid` observation, BIOM HDF5 files in the ~37 kB (DRR010481) and ~72 kB (ERR2715528) size range, BIOM JSON files containing `"type": "OTU table"`, and Krona HTML charts that embed both sample identifiers.

## Reference workflow
IWC `workflows/amplicon/amplicon-mgnify/mgnify-amplicon-pipeline-v5-its`, release 0.2 (MGnify amplicon pipeline v5.0 — ITS subworkflow), Apache-2.0, maintained by EMBL-EBI MGnify.
