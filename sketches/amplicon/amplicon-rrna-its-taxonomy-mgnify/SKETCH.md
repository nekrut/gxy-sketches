---
name: amplicon-rrna-its-taxonomy-mgnify
description: Use when you need to taxonomically profile microbial community amplicon
  sequencing data (16S/18S SSU, 23S/28S LSU rRNA, or fungal ITS) starting from SRA
  accessions or raw Illumina short reads, producing OTU tables and abundance summaries
  against SILVA, ITSoneDB, and UNITE. Handles both single-end and paired-end inputs
  and is marker-gene agnostic (does not assume a specific primer region).
domain: amplicon
organism_class:
- bacterial
- archaeal
- eukaryote
- fungal
input_data:
- sra-accession-list
- short-reads-paired
- short-reads-single
- rfam-clan-file
- rfam-covariance-models
source:
  ecosystem: iwc
  workflow: MGnify's amplicon pipeline v5.0
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/amplicon/amplicon-mgnify/mgnify-amplicon-pipeline-v5-complete
  version: '0.3'
  license: Apache-2.0
tools:
- fastq-dl
- fastp
- trimmomatic
- SeqPrep
- PRINSEQ
- FastQC
- MultiQC
- Infernal-cmsearch
- cmsearch-deoverlap
- MAPseq
- biom
- krona
tags:
- amplicon
- 16S
- 18S
- LSU
- SSU
- ITS
- rRNA
- SILVA
- UNITE
- ITSoneDB
- MGnify
- metabarcoding
- OTU
test_data:
- role: sra_accession_list
  url: https://zenodo.org/records/13710235/files/accessions.csv
  sha1: cfffa4732996831d4b8521bc90b9b5e7ab77dd6f
- role: clan_information_file
  url: ftp://ftp.ebi.ac.uk/pub/databases/metagenomics/pipeline-5.0/ref-dbs/rfam_models/ribosomal_models/ribo.claninfo
  sha1: ac1d31c511c0726873c0fd7cad5ab207fed3228c
expected_output:
- role: single_end_multiqc_report
  description: Content assertions for `Single-end MultiQC report`.
  assertions:
  - 'that: has_text'
  - 'text: DRR010481_ambiguous_base_filtering'
  - 'that: has_text'
  - 'text: 84.0'
  - 'that: has_text'
  - 'text: DRR010481_initial_reads'
  - 'that: has_text'
  - 'text: 84.8'
  - 'that: has_text'
  - 'text: DRR010481_length_filtering'
  - 'that: has_text'
  - 'text: DRR010481_trimming'
- role: single_end_multiqc_statistics
  description: Content assertions for `Single-end MultiQC statistics`.
  assertions:
  - 'that: has_text'
  - "text: DRR010481_ambiguous_base_filtering\t84.0\t47.0\t242.02\t244\t40.0\t2.4999999999999998e-05"
  - 'that: has_text'
  - "text: DRR010481_initial_reads\t84.84848484848484\t47.0\t545.0454545454545\t550\t\
    40.0\t3.2999999999999996e-05"
  - 'that: has_text'
  - "text: DRR010481_length_filtering\t84.0\t47.0\t242.02\t244\t40.0\t2.4999999999999998e-05"
  - 'that: has_text'
  - "text: DRR010481_trimming\t84.0\t47.0\t242.02\t244\t40.0\t2.4999999999999998e-05"
- role: paired_end_multiqc_report
  description: Content assertions for `Paired-end MultiQC report`.
  assertions:
  - 'that: has_text'
  - 'text: ERR2715528_ambiguous_base_filtering'
  - 'that: has_text'
  - 'text: ERR2715528_initial_reads'
  - 'that: has_text'
  - 'text: ERR2715528_length_filtering'
  - 'that: has_text'
  - 'text: ERR2715528_trimming'
  - 'that: has_text'
  - 'text: 92.2'
- role: ssu_taxonomic_classifications_using_silva_db
  description: Content assertions for `SSU taxonomic classifications using SILVA DB`.
  assertions:
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: # mapseq v1.2.6 (Jan 20 2023)'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: SILVA'
  - 'ERR2715528: that: has_n_columns'
  - 'ERR2715528: comment: #'
  - 'ERR2715528: n: 15'
- role: ssu_otu_tables_silva_db
  description: Content assertions for `SSU OTU tables (SILVA DB)`.
  assertions:
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: # Constructed from biom file'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: # OTU ID'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: Unspecified'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: taxonomy'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: taxid'
  - 'ERR2715528: that: has_n_columns'
  - 'ERR2715528: comment: #'
  - 'ERR2715528: n: 4'
- role: lsu_otu_tables_silva_db
  description: Content assertions for `LSU OTU tables (SILVA DB)`.
  assertions:
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: # Constructed from biom file'
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: # OTU ID'
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: Unspecified'
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: taxonomy'
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: taxid'
  - 'DRR010481: that: has_n_columns'
  - 'DRR010481: comment: #'
  - 'DRR010481: n: 4'
- role: ssu_otu_tables_in_hdf5_format_silva_db
  description: Content assertions for `SSU OTU tables in HDF5 format (SILVA DB)`.
  assertions:
  - 'ERR2715528: that: has_size'
  - 'ERR2715528: value: 37000'
  - 'ERR2715528: delta: 10000'
- role: ssu_otu_tables_in_json_format_silva_db
  description: Content assertions for `SSU OTU tables in JSON format (SILVA DB)`.
  assertions:
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: "type": "OTU table"'
- role: ssu_taxonomic_abundance_pie_charts_silva_db
  description: Content assertions for `SSU taxonomic abundance pie charts (SILVA DB)`.
  assertions:
  - 'that: has_text'
  - 'text: ERR2715528'
- role: lsu_otu_tables_in_hdf5_format_silva_db
  description: Content assertions for `LSU OTU tables in HDF5 format (SILVA DB)`.
  assertions:
  - 'DRR010481: that: has_size'
  - 'DRR010481: value: 37000'
  - 'DRR010481: delta: 10000'
- role: lsu_otu_tables_in_json_format_silva_db
  description: Content assertions for `LSU OTU tables in JSON format (SILVA DB)`.
  assertions:
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: "type": "OTU table"'
- role: lsu_taxonomic_abundance_pie_charts_silva_db
  description: Content assertions for `LSU taxonomic abundance pie charts (SILVA DB)`.
  assertions:
  - 'that: has_text'
  - 'text: DRR010481'
- role: lsu_taxonomic_classifications_using_silva_db
  description: Content assertions for `LSU taxonomic classifications using SILVA DB`.
  assertions:
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: # mapseq v1.2.6 (Jan 20 2023)'
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: SILVA'
  - 'DRR010481: that: has_n_columns'
  - 'DRR010481: comment: #'
  - 'DRR010481: n: 15'
- role: its_taxonomic_classifications_using_itsonedb
  description: Content assertions for `ITS taxonomic classifications using ITSoneDB`.
  assertions:
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: # mapseq v1.2.6 (Jan 20 2023)'
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: ITSone'
  - 'DRR010481: that: has_n_columns'
  - 'DRR010481: comment: #'
  - 'DRR010481: n: 15'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: # mapseq v1.2.6 (Jan 20 2023)'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: ITSone'
  - 'ERR2715528: that: has_n_columns'
  - 'ERR2715528: comment: #'
  - 'ERR2715528: n: 15'
- role: its_otu_tables_in_json_format_unite_db
  description: Content assertions for `ITS OTU tables in JSON format (UNITE DB)`.
  assertions:
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: "type": "OTU table"'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: "type": "OTU table"'
- role: its_taxonomic_abundance_pie_charts_unite_db
  description: Content assertions for `ITS taxonomic abundance pie charts (UNITE DB)`.
  assertions:
  - 'that: has_text'
  - 'text: DRR010481'
  - 'that: has_text'
  - 'text: ERR2715528'
- role: its_otu_tables_in_hdf5_format_unite_db
  description: Content assertions for `ITS OTU tables in HDF5 format (UNITE DB)`.
  assertions:
  - 'DRR010481: that: has_size'
  - 'DRR010481: value: 37000'
  - 'DRR010481: delta: 10000'
  - 'ERR2715528: that: has_size'
  - 'ERR2715528: value: 72000'
  - 'ERR2715528: delta: 10000'
- role: its_taxonomic_abundance_pie_charts_itsonedb
  description: Content assertions for `ITS taxonomic abundance pie charts (ITSoneDB)`.
  assertions:
  - 'that: has_text'
  - 'text: DRR010481'
  - 'that: has_text'
  - 'text: ERR2715528'
- role: its_otu_tables_in_json_format_itsonedb
  description: Content assertions for `ITS OTU tables in JSON format (ITSoneDB)`.
  assertions:
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: "type": "OTU table"'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: "type": "OTU table"'
- role: its_otu_tables_in_hdf5_format_itsonedb
  description: Content assertions for `ITS OTU tables in HDF5 format (ITSoneDB)`.
  assertions:
  - 'DRR010481: that: has_size'
  - 'DRR010481: value: 37000'
  - 'DRR010481: delta: 10000'
  - 'ERR2715528: that: has_size'
  - 'ERR2715528: value: 72000'
  - 'ERR2715528: delta: 10000'
- role: its_taxonomic_classifications_using_unite_db
  description: Content assertions for `ITS taxonomic classifications using UNITE DB`.
  assertions:
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: # mapseq v1.2.6 (Jan 20 2023)'
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: UNITE'
  - 'DRR010481: that: has_n_columns'
  - 'DRR010481: comment: #'
  - 'DRR010481: n: 15'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: # mapseq v1.2.6 (Jan 20 2023)'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: UNITE'
  - 'ERR2715528: that: has_n_columns'
  - 'ERR2715528: comment: #'
  - 'ERR2715528: n: 15'
- role: its_otu_tables_unite_db
  description: Content assertions for `ITS OTU tables (UNITE DB)`.
  assertions:
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: # Constructed from biom file'
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: # OTU ID'
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: Unspecified'
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: taxonomy'
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: taxid'
  - 'DRR010481: that: has_n_columns'
  - 'DRR010481: comment: #'
  - 'DRR010481: n: 4'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: # Constructed from biom file'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: # OTU ID'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: Unspecified'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: taxonomy'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: taxid'
  - 'ERR2715528: that: has_n_columns'
  - 'ERR2715528: comment: #'
  - 'ERR2715528: n: 4'
- role: its_otu_tables_itsonedb
  description: Content assertions for `ITS OTU tables (ITSoneDB)`.
  assertions:
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: # Constructed from biom file'
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: # OTU ID'
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: Unspecified'
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: taxonomy'
  - 'DRR010481: that: has_text'
  - 'DRR010481: text: taxid'
  - 'DRR010481: that: has_n_columns'
  - 'DRR010481: comment: #'
  - 'DRR010481: n: 4'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: # Constructed from biom file'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: # OTU ID'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: Unspecified'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: taxonomy'
  - 'ERR2715528: that: has_text'
  - 'ERR2715528: text: taxid'
  - 'ERR2715528: that: has_n_columns'
  - 'ERR2715528: comment: #'
  - 'ERR2715528: n: 4'
- role: itsonedb_phylum_level_taxonomic_abundance_summary_table
  description: Content assertions for `ITSoneDB phylum level taxonomic abundance summary
    table`.
  assertions:
  - 'that: has_text'
  - "text: superkingdom\tkingdom\tphylum\tDRR010481\tERR2715528"
  - 'that: has_n_columns'
  - 'n: 5'
  - 'that: has_n_lines'
  - 'n: 10'
  - 'delta: 4'
- role: itsonedb_taxonomic_abundance_summary_table
  description: Content assertions for `ITSoneDB taxonomic abundance summary table`.
  assertions:
  - 'that: has_text'
  - "text: #SampleID\tDRR010481\tERR2715528"
  - 'that: has_n_columns'
  - 'n: 3'
  - 'that: has_n_lines'
  - 'n: 117'
  - 'delta: 17'
- role: lsu_phylum_level_taxonomic_abundance_summary_table
  description: Content assertions for `LSU phylum level taxonomic abundance summary
    table`.
  assertions:
  - 'that: has_text'
  - "text: superkingdom\tkingdom\tphylum\tDRR010481"
  - 'that: has_n_columns'
  - 'n: 4'
  - 'that: has_n_lines'
  - 'n: 6'
  - 'delta: 4'
- role: lsu_taxonomic_abundance_summary_table
  description: Content assertions for `LSU taxonomic abundance summary table`.
  assertions:
  - 'that: has_text'
  - "text: #SampleID\tDRR010481"
  - 'that: has_n_columns'
  - 'n: 2'
  - 'that: has_n_lines'
  - 'n: 6'
  - 'delta: 4'
- role: ssu_phylum_level_taxonomic_abundance_summary_table
  description: Content assertions for `SSU phylum level taxonomic abundance summary
    table`.
  assertions:
  - 'that: has_text'
  - "text: superkingdom\tkingdom\tphylum\tERR2715528"
  - 'that: has_n_columns'
  - 'n: 4'
  - 'that: has_n_lines'
  - 'n: 12'
  - 'delta: 4'
- role: ssu_taxonomic_abundance_summary_table
  description: Content assertions for `SSU taxonomic abundance summary table`.
  assertions:
  - 'that: has_text'
  - "text: #SampleID\tERR2715528"
  - 'that: has_n_columns'
  - 'n: 2'
  - 'that: has_n_lines'
  - 'n: 13'
  - 'delta: 4'
- role: its_unite_db_phylum_level_taxonomic_abundance_summary_table
  description: Content assertions for `ITS UNITE DB phylum level taxonomic abundance
    summary table`.
  assertions:
  - 'that: has_text'
  - "text: superkingdom\tkingdom\tphylum\tDRR010481\tERR2715528"
  - 'that: has_n_columns'
  - 'n: 5'
  - 'that: has_n_lines'
  - 'n: 13'
  - 'delta: 4'
- role: its_unite_db_taxonomic_abundance_summary_table
  description: Content assertions for `ITS UNITE DB taxonomic abundance summary table`.
  assertions:
  - 'that: has_text'
  - "text: #SampleID\tDRR010481\tERR2715528"
  - 'that: has_n_columns'
  - 'n: 3'
  - 'that: has_n_lines'
  - 'n: 130'
  - 'delta: 19'
---

# MGnify amplicon pipeline (rRNA + ITS taxonomy)

## When to use this sketch
- The user has amplicon / metabarcoding data (16S, 18S, ITS, or mixed rRNA amplicons) and wants taxonomic profiles and OTU tables.
- Input is either a list of SRA/ENA run accessions or raw Illumina FASTQ (single-end or paired-end); mixed SE+PE batches are fine.
- The user wants outputs against standard reference databases: SILVA (SSU + LSU), ITSoneDB, and UNITE, plus per-sample and project-level abundance tables and pie charts.
- The analysis should reproduce MGnify v5.0 amplicon results (quality control + rRNA/ITS classification via cmsearch + MAPseq) inside Galaxy.
- The user does not know the primer region in advance — this pipeline slices SSU/LSU/ITS from the reads using Rfam covariance models rather than assuming a target.

## Do not use when
- The user has shotgun metagenomic reads and wants taxonomic or functional profiling — use a shotgun metagenomics sketch instead.
- The user wants ASVs with DADA2/QIIME2-style exact-sequence-variant denoising and primer trimming — this pipeline is OTU/MAPseq-based, not an ASV workflow.
- The user has long-read amplicons (PacBio CCS, Nanopore 16S) — QC and merging steps here assume short Illumina reads.
- The user only needs raw read quality control (use a standalone QC sketch).
- The user wants whole-genome assembly, variant calling, or RNA-seq quantification.

## Analysis outline
1. Fetch raw reads from SRA/ENA accessions with **fastq-dl**, splitting into single-end and paired-end collections.
2. Sanitize FASTQ headers (awk) and normalize compression so downstream tools accept them as `fastqsanger(.gz)`.
3. **QC — single-end branch**: FastQC → Trimmomatic (SLIDINGWINDOW/LEADING/TRAILING/MINLEN) → Filter FASTQ by length → PRINSEQ ambiguous-base (N%) filter → FastQC/MultiQC → convert to FASTA.
4. **QC — paired-end branch**: FastQC → **fastp** (quality + length filter, optional base correction) → **SeqPrep (MGnify build)** to merge overlapping pairs → Trimmomatic on merged reads → length filter → PRINSEQ N% filter → FastQC/MultiQC → convert to FASTA.
5. Merge SE and PE post-QC FASTA collections into a single processed-sequences collection.
6. **rRNA prediction**: run **Infernal cmsearch** (`--hmmonly`) against the MGnify Rfam ribosomal covariance models, then **cmsearch-deoverlap** with the provided clan file to resolve overlapping hits.
7. Extract SSU and LSU subsequence regions (Query Tabular + bedtools-style slicing) into per-sample SSU and LSU FASTA files and a BED of rRNA regions.
8. **Taxonomic classification of SSU and LSU** with **MAPseq** against SILVA, then build per-sample OTU tables (tabular, BIOM JSON, BIOM HDF5) and Krona pie charts; collapse into project-level SSU/LSU abundance tables at full taxonomy and phylum level.
9. **ITS sub-workflow**: mask rRNA-matching regions and run MAPseq against **ITSoneDB** and **UNITE**, producing ITS FASTA, per-sample OTU tables (tabular/JSON/HDF5), pie charts, and project-level summary tables at full and phylum level for each database.
10. Emit a combined MultiQC report per read layout plus all taxonomic abundance summary tables as final outputs.

## Key parameters
- Input: `SRA accession list` (one accession per line) and the MGnify v5.0 `ribo.claninfo` clan file (plus the matching `ribo.cm` covariance models staged in the Galaxy data table as `mgnify_5_0_rfam`).
- Trimmomatic (SE and merged PE): `SLIDINGWINDOW window_size=4 required_quality=15`, `LEADING=3`, `TRAILING=3`, `MINLEN=100`, phred33.
- fastp (PE only): `qualified_quality_phred=20`, `unqualified_percent_limit=20`, `length_required=70`, `base_correction=false` by default.
- SeqPrep merge: `min_base_pair_overlap=15`, `max_mismatch_fraction=0.02`, `min_match_fraction=0.9`, adapter_a=`AGATCGGAAGAGCGGTTCAG`, adapter_b=`AGATCGGAAGAGCGTCGTGT`, quality_cutoff=13, min_length=30.
- Length filter (Filter FASTQ): `min_size=100`.
- PRINSEQ ambiguity filter: `N_percentage ≤ 10%` to keep a read.
- Infernal cmsearch: `--hmmonly`, `Z=1000`, `mxsize=128`, `smxsize=128`, database=`mgnify_5_0_rfam`, `noali=true`.
- cmsearch-deoverlap: uses the Rfam clan file to collapse overlapping SSU/LSU/5S/5.8S hits.
- MAPseq: run with MGnify v5.0 references for SILVA SSU, SILVA LSU, ITSoneDB, and UNITE; output is a 15-column classification plus per-sample BIOM.

## Test data
The test job supplies a two-accession CSV (`accessions.csv` from Zenodo 13710235) containing one single-end run (`DRR010481`) and one paired-end run (`ERR2715528`), plus the MGnify v5.0 `ribo.claninfo` clan file fetched from EBI FTP. Running the workflow is expected to produce per-layout MultiQC reports and stats where each sample appears at the `_initial_reads`, `_trimming`, `_length_filtering`, and `_ambiguous_base_filtering` stages; per-sample post-QC FASTA files (`DRR010481_SE.fasta`, `ERR2715528_PE.fasta`); SSU/LSU/ITS FASTA slices and BED regions; MAPseq classifications against SILVA, ITSoneDB, and UNITE (each with the `# mapseq v1.2.6` header and 15 columns); per-sample OTU tables in tabular, BIOM JSON, and BIOM HDF5 form (~37–72 kB); Krona pie charts mentioning the sample IDs; and project-level phylum-level and full taxonomic abundance summary tables for SSU, LSU, ITSoneDB, and UNITE with the expected `superkingdom\tkingdom\tphylum\t<samples>` / `#SampleID\t<samples>` headers.

## Reference workflow
Galaxy IWC — `workflows/amplicon/amplicon-mgnify/mgnify-amplicon-pipeline-v5-complete` (MGnify's amplicon pipeline v5.0), release 0.3, Apache-2.0. Upstream reference: EMBL-EBI MGnify amplicon pipeline v5.0.
