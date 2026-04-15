---
name: amplicon-rrna-taxonomic-classification-silva
description: Use when you need to detect ribosomal RNA (SSU/LSU) regions in already
  quality-controlled amplicon or metagenomic sequences and assign taxonomy against
  the SILVA reference using the MGnify v5 approach. Produces per-sample OTU tables
  (TSV/BIOM/HDF5/JSON) and Krona pie charts for both 16S/18S (SSU) and 23S/28S (LSU)
  fractions.
domain: amplicon
organism_class:
- bacterial
- archaeal
- eukaryote
input_data:
- amplicon-fasta
- rfam-covariance-models
- clan-info
source:
  ecosystem: iwc
  workflow: MGnify's amplicon pipeline v5.0 - rRNA prediction
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/amplicon/amplicon-mgnify/mgnify-amplicon-pipeline-v5-rrna-prediction
  version: '0.2'
  license: Apache-2.0
  slug: amplicon--amplicon-mgnify--mgnify-amplicon-pipeline-v5-rrna-prediction
tools:
- name: infernal-cmsearch
  version: 1.1.5+galaxy0
- name: cmsearch-deoverlap
  version: 0.08+galaxy2
- name: bedtools
  version: 2.31.1+galaxy0
- name: mapseq
  version: 2.1.1+galaxy0
- name: biom-convert
  version: 2.1.15+galaxy1
- name: krona
tags:
- amplicon
- 16S
- 18S
- 23S
- 28S
- rRNA
- SSU
- LSU
- SILVA
- taxonomy
- mgnify
- metabarcoding
test_data:
- role: processed_sequences__drr010481_fastq_fasta
  url: https://zenodo.org/records/13710235/files/DRR010481_SE.fasta
  sha1: 99230f36fe6b5536b7c060a252d3b053a15b9d74
- role: processed_sequences__err2715528_merged_fastq_fasta
  url: https://zenodo.org/records/13710235/files/ERR2715528_PE.fasta
  sha1: 9d5e24ff500dd71fc95592018942963a4cc2e6e2
- role: clan_information_file
  url: ftp://ftp.ebi.ac.uk/pub/databases/metagenomics/pipeline-5.0/ref-dbs/rfam_models/ribosomal_models/ribo.claninfo
  sha1: ac1d31c511c0726873c0fd7cad5ab207fed3228c
expected_output:
- role: ssu_taxonomic_classifications_using_silva_db
  description: Content assertions for `SSU taxonomic classifications using SILVA DB`.
  assertions:
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_text'
  - 'ERR2715528_MERGED_FASTQ.fasta: text: # mapseq v1.2.6 (Jan 20 2023)'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_text'
  - 'ERR2715528_MERGED_FASTQ.fasta: text: SILVA'
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_n_columns'
  - 'ERR2715528_MERGED_FASTQ.fasta: comment: #'
  - 'ERR2715528_MERGED_FASTQ.fasta: n: 15'
- role: ssu_otu_tables_silva_db
  description: Content assertions for `SSU OTU tables (SILVA DB)`.
  assertions:
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
- role: lsu_otu_tables_silva_db
  description: Content assertions for `LSU OTU tables (SILVA DB)`.
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
- role: lsu_taxonomic_classifications_using_silva_db
  description: Content assertions for `LSU taxonomic classifications using SILVA DB`.
  assertions:
  - 'DRR010481_FASTQ.fasta: that: has_text'
  - 'DRR010481_FASTQ.fasta: text: # mapseq v1.2.6 (Jan 20 2023)'
  - 'DRR010481_FASTQ.fasta: that: has_text'
  - 'DRR010481_FASTQ.fasta: text: SILVA'
  - 'DRR010481_FASTQ.fasta: that: has_n_columns'
  - 'DRR010481_FASTQ.fasta: comment: #'
  - 'DRR010481_FASTQ.fasta: n: 15'
- role: ssu_otu_tables_in_hdf5_format_silva_db
  description: Content assertions for `SSU OTU tables in HDF5 format (SILVA DB)`.
  assertions:
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_size'
  - 'ERR2715528_MERGED_FASTQ.fasta: value: 37000'
  - 'ERR2715528_MERGED_FASTQ.fasta: delta: 10000'
- role: ssu_otu_tables_in_json_format_silva_db
  description: Content assertions for `SSU OTU tables in JSON format (SILVA DB)`.
  assertions:
  - 'ERR2715528_MERGED_FASTQ.fasta: that: has_text'
  - 'ERR2715528_MERGED_FASTQ.fasta: text: "type": "OTU table"'
- role: ssu_taxonomic_abundance_pie_charts_silva_db
  description: Content assertions for `SSU taxonomic abundance pie charts (SILVA DB)`.
  assertions:
  - 'that: has_text'
  - 'text: ERR2715528_MERGED_FASTQ_fasta'
- role: lsu_otu_tables_in_hdf5_format_silva_db
  description: Content assertions for `LSU OTU tables in HDF5 format (SILVA DB)`.
  assertions:
  - 'DRR010481_FASTQ.fasta: that: has_size'
  - 'DRR010481_FASTQ.fasta: value: 37000'
  - 'DRR010481_FASTQ.fasta: delta: 10000'
- role: lsu_otu_tables_in_json_format_silva_db
  description: Content assertions for `LSU OTU tables in JSON format (SILVA DB)`.
  assertions:
  - 'DRR010481_FASTQ.fasta: that: has_text'
  - 'DRR010481_FASTQ.fasta: text: "type": "OTU table"'
- role: lsu_taxonomic_abundance_pie_charts_silva_db
  description: Content assertions for `LSU taxonomic abundance pie charts (SILVA DB)`.
  assertions:
  - 'that: has_text'
  - 'text: DRR010481_FASTQ_fasta'
---

# MGnify v5 rRNA prediction and SILVA taxonomic classification

## When to use this sketch
- You have post-QC amplicon or shotgun FASTA sequences and need to isolate rRNA reads (SSU and LSU) before taxonomic assignment.
- You want MGnify-compatible outputs: per-sample OTU tables, BIOM (HDF5 + JSON), and Krona visualizations against SILVA.
- You want a reference-based classifier (MAPseq) rather than de novo OTU clustering (DADA2/VSEARCH).
- You need both SSU (16S/18S) and LSU (23S/28S) classifications from the same input collection in one run.
- You are replicating or extending the MGnify amplicon pipeline v5.0 in Galaxy.

## Do not use when
- Your reads are raw FASTQ that still need adapter/primer trimming and merging — run an amplicon QC workflow first (MGnify v5 QC subworkflow) and feed its outputs here.
- You want ASV-level resolution with DADA2 — use a DADA2-based amplicon sketch instead.
- You want closed-reference OTU picking against Greengenes or clustering with VSEARCH/SWARM — use a different amplicon-clustering sketch.
- You are doing whole-genome taxonomic profiling of shotgun metagenomes — use a Kraken2/MetaPhlAn metagenomics sketch.
- You need functional annotation (KO/Pfam/InterProScan) of non-rRNA reads — use a separate MGnify functional-annotation subworkflow.

## Analysis outline
1. cmsearch (Infernal, `--hmmonly`) scans each input FASTA against the MGnify 5.0 Rfam ribosomal covariance model database.
2. CMsearch-deoverlap removes lower-scoring overlapping hits using the Rfam clan information file.
3. Query Tabular (SQLite) splits deoverlapped hits into four strand/unit buckets: SSU forward, SSU reverse, LSU forward, LSU reverse (matched on `c3 like 'SSU%'`/`'LSU%'` and coordinate orientation).
4. awk reformats each bucket into 6-column BED (name, start-1, end, forward/reverse, score=1, strand); forward and reverse are concatenated per unit to produce `SSU_BED` and `LSU_BED`, plus a combined `LSU and SSU BED regions` output.
5. Filter collection drops samples whose BED is empty so bedtools does not fail, then `bedtools getfasta` extracts SSU and LSU subsequences from each sample's processed FASTA.
6. `fasta_formatter` rewraps the extracted FASTA at width 60 to produce `SSU FASTA files` and `LSU FASTA files`.
7. MAPseq classifies each rRNA fraction against the cached MGnify SSU and LSU SILVA references (release 2023-09-26), emitting classifications, OTU TSV (with and without taxid), and Krona-format tables.
8. biom-convert turns the OTU TSVs into BIOM HDF5 and JSON tables (observation metadata = taxonomy, table type = OTU table).
9. Krona builds per-dataset taxonomic-abundance pie charts from the MAPseq Krona output; conditional execution uses a helper subworkflow that maps empty/non-empty collections to a boolean `when` gate so Krona and biom-convert skip empty samples.

## Key parameters
- cmsearch: `--hmmonly`, `-Z 1000.0`, `--mxsize 128`, `--smxsize 128`, `noali=true`, database = `mgnify_5_0_rfam` (Rfam ribosomal models).
- CMsearch-deoverlap: default (`maxkeep=false`, `dirty=false`); requires the `ribo.claninfo` clan file.
- Query Tabular bucketing: `c3 like 'SSU%'` vs `'LSU%'`, with `c8 <= c9` = forward strand and `c8 > c9` = reverse strand.
- BED reformat: `$2 - 1` to convert 1-based cmsearch coordinates to 0-based BED; strand labels `forward/+` and `reverse/-`.
- fasta_formatter width: 60.
- MAPseq: `minid1=1`, `minid2=1`, `minscore=30`, `tophits=80`, `topotus=40`, `otulim=50`, `outfmt=simple`; cached DBs `mgnify_ssu_from_2023-09-26` and `mgnify_lsu_from_2023-09-26`; `mapseq2biom` with `krona_input=true`.
- biom-convert: input TSV with `process_obs_metadata=taxonomy`, output BIOM OTU table in both HDF5 and JSON flavors.
- Krona: `root_name=Root`, `type_of_data=text`, gated by `when=$(inputs.when)` so it only fires when the upstream collection is non-empty.

## Test data
The test job supplies a collection of two post-QC FASTA samples — `DRR010481_FASTQ.fasta` (single-end run) and `ERR2715528_MERGED_FASTQ.fasta` (merged paired-end run) from Zenodo record 13710235 — together with the MGnify 5.0 `ribo.claninfo` clan file fetched from the EBI FTP. Running the workflow is expected to yield per-sample `LSU and SSU BED regions` matching the provided golden BEDs, non-empty `SSU FASTA files` for ERR2715528 and `LSU FASTA files` for DRR010481, MAPseq classifications containing the `# mapseq v1.2.6 (Jan 20 2023)` header and `SILVA` tag with 15 columns, OTU tables with the `# Constructed from biom file` / `# OTU ID` / `taxonomy` / `taxid` markers and 4 columns, HDF5 BIOM files of roughly 37 kB (±10 kB), JSON BIOM files containing `"type": "OTU table"`, and Krona HTML charts mentioning the corresponding sample identifiers.

## Reference workflow
IWC: `workflows/amplicon/amplicon-mgnify/mgnify-amplicon-pipeline-v5-rrna-prediction` (MGnify amplicon pipeline v5.0 — rRNA prediction), release 0.2, Apache-2.0. Upstream reference: EMBL-EBI MGnify pipeline v5.0 ribosomal models and SILVA DB from 2023-09-26.
