---
name: metagenomic-gene-catalogue-short-read
description: Use when you need to build a gene catalogue from paired-end short-read
  metagenomic sequencing of a microbial community, assembling contigs, predicting
  CDSs, clustering non-redundant genes, and annotating them with functional, taxonomic,
  and antimicrobial resistance information. Supports either a full catalogue or an
  ARG-focused catalogue.
domain: metagenomics
organism_class:
- bacterial
- microbial-community
input_data:
- short-reads-paired
- trimmed-reads
source:
  ecosystem: iwc
  workflow: Metagenomic Genes Catalogue Analysis
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/microbiome/metagenomic-genes-catalogue
  version: 1.2.1
  license: GPL-3.0-or-later
tools:
- megahit
- quast
- prodigal
- mmseqs2
- eggnog-mapper
- amrfinderplus
- abricate
- staramr
- argnorm
- coverm
- krakentools
- krona
- multiqc
tags:
- metagenomics
- gene-catalogue
- assembly
- amr
- functional-annotation
- taxonomy
- abromics
- mmseqs2
- linclust
test_data:
- role: metagenomics_trimmed_reads__genes_catalogue_test__forward
  url: https://zenodo.org/records/17348100/files/genes_catalogue_R1.fastqsanger.gz
- role: metagenomics_trimmed_reads__genes_catalogue_test__reverse
  url: https://zenodo.org/records/17348100/files/genes_catalogue_R2.fastqsanger.gz
expected_output:
- role: mmseqs2_taxonomy_tabular
  description: Content assertions for `MMseqs2 Taxonomy Tabular`.
  assertions:
  - 'has_text: Bacteria'
  - 'has_n_columns: {''n'': 4}'
- role: eggnog_annotations
  description: Content assertions for `Eggnog Annotations`.
  assertions:
  - 'has_text: #query'
  - 'has_n_columns: {''n'': 21}'
- role: mmseqs2_taxonomy_kraken
  description: Content assertions for `MMseqs2 Taxonomy Kraken`.
  assertions:
  - 'has_text: cellular root'
  - 'has_n_columns: {''n'': 6}'
- role: argnorm_amrfinderplus_report
  description: Content assertions for `Argnorm AMRfinderplus Report`.
  assertions:
  - 'has_text: Protein identifier'
- role: resfinder
  description: Content assertions for `Resfinder`.
  assertions:
  - 'has_text: Isolate ID'
  - 'has_n_columns: {''n'': 13}'
- role: abricate_virulence_report
  description: Content assertions for `Abricate Virulence Report`.
  assertions:
  - 'has_text: #FILE'
  - 'has_n_columns: {''n'': 15}'
- role: multiqc_report
  description: Content assertions for `MultiQC Report`.
  assertions:
  - 'that: has_text'
  - 'text: AMRFinderPlus'
  - 'that: has_text'
  - 'text: ABRicate'
  - 'that: has_text'
  - 'text: starAMR'
  - 'that: has_text'
  - 'text: QUAST'
  - 'that: has_text'
  - 'text: MMseqs2 taxonomy'
  - 'that: has_text'
  - 'text: EggnogMapper'
---

# Metagenomic gene catalogue from short reads

## When to use this sketch
- Input is a paired collection of quality-trimmed, host-removed Illumina short reads from one or more microbial community samples (gut, soil, water, clinical swabs, etc.).
- Goal is to build a non-redundant catalogue of protein-coding genes across samples by assembling contigs and predicting CDSs de novo.
- Downstream questions include: what functions are encoded (eggNOG/COG/KEGG), what taxa contribute them (MMseqs2 taxonomy vs. a UniRef-like DB), per-sample gene abundance (CoverM), and what antimicrobial resistance / virulence genes are present (AMRFinderPlus + argNorm, ABRicate, starAMR).
- You want either (a) a full community gene catalogue, or (b) an ARG-centric sub-catalogue that also captures genes co-located on the same contigs as resistance genes (genomic context of ARGs).

## Do not use when
- You need per-genome MAGs with binning, checkm, GTDB-Tk taxonomy — use a metagenome-assembled-genomes / binning sketch instead.
- You only want taxonomic profiling from reads without assembly — use a read-based profiling sketch (Kraken2/Bracken, MetaPhlAn).
- Input is long reads (ONT/PacBio) — assembly parameters and tool choices differ; use a long-read metagenomic assembly sketch.
- You are calling AMR on isolate genomes of a single bacterium — use a bacterial isolate AMR-typing sketch.
- Raw reads are untrimmed / still contain host contamination — run a metagenomic read QC and host-removal sketch first; this workflow assumes clean reads.
- You want a targeted amplicon (16S/ITS) analysis — use an amplicon sketch.

## Analysis outline
1. Per-sample metagenomic assembly of paired reads into contigs with MEGAHIT (k-list 21..141, min-contig 200).
2. Assembly QC with QUAST in metagenome mode (per-sample report, tabular + HTML).
3. Rewrite contig headers to prepend sample name (fasta→tabular, add input name as column, tabular→fasta) so IDs are globally unique, then concatenate contigs across samples.
4. CDS prediction on the concatenated contigs with Prodigal in `meta` procedure, translation table 11, producing nucleotide (fnn), protein (faa), and GFF.
5. AMR / virulence screening on predicted CDSs: AMRFinderPlus (nucleotide mode) + argNorm normalization, ABRicate (virulence DB, default 80% id / 80% cov), and starAMR (resfinder/pointfinder/plasmidfinder).
6. Branch on the `Full genes catalogue` boolean:
   - True → cluster all predicted nucleotide CDSs with MMseqs2 easy-linclust at 95% identity / 80% coverage to obtain non-redundant representative genes.
   - False → subworkflow extracts contig IDs of contigs carrying an ARG hit (from all three AMR tools), pulls every Prodigal CDS on those contigs (ARGs + neighbours), and clusters only the ARG CDSs with MMseqs2 linclust.
7. Functional annotation of the representative (or ARG-neighbour) CDSs with eggNOG-mapper (DIAMOND, CDS input, 70% query/subject coverage, 80% pident, e-value 1e-30).
8. Taxonomic assignment of the representative CDSs with MMseqs2 taxonomy against a UniRef-style protein+taxonomy DB; produce tabular + Kraken-style report + Krona chart via KrakenTools.
9. Per-sample abundance of representative genes by mapping trimmed reads back with CoverM contig (minimap2-sr, mean coverage, 10% min covered fraction), then join per-sample coverage columns.
10. Aggregate QUAST, AMR reports, CoverM, eggNOG, and MMseqs2 taxonomy into a single MultiQC HTML report.

## Key parameters
- MEGAHIT: `k-list 21,29,39,59,79,99,119,141`, `min-count 2`, `min-contig-len 200`, input mode `paired_collection` / `individual` batching.
- QUAST: `--type metagenome`, `min-contig 1500`, `min-identity 95`, no reference (`max_ref_num 0` as of 1.2.1).
- Prodigal: `procedure=meta`, `trans_table=11`, GFF output.
- MMseqs2 easy-linclust (both full and ARG paths): `min-seq-id 0.95`, `cov 0.8`, `cov-mode 0`, `cluster-mode 0`, alphabet nucleotide.
- AMRFinderPlus: nucleotide input, `coverage_min 0.5`, `translation_table 11`; followed by argNorm in `amrfinderplus` mode.
- ABRicate: `min_dna_id 80`, `min_cov 80`, DB selectable at runtime (e.g. `resfinder` for the test).
- starAMR: `pid_threshold 98`, `percent_length_overlap_resfinder 60`, pointfinder disabled by default.
- eggNOG-mapper: DIAMOND `--sensmode fast`, `query_cover 70`, `subject_cover 70`, `pident 80`, `evalue 1e-30`, input type `CDS` with `translate=true`.
- MMseqs2 taxonomy: amino-acid taxonomy DB, `lca_mode 3`, `majority 0.5`, Kraken report on, Krona off (Krona generated downstream from KrakenTools conversion).
- CoverM contig: `methods=mean`, `min_covered_fraction 10`, mapper `minimap2-sr`, paired collection input.
- Workflow switch: `Full genes catalogue` (boolean). `true` → whole-community catalogue; `false` → ARG-focused catalogue with genomic context.

## Test data
The test profile runs a single paired-end sample `genes_catalogue_test` with forward/reverse FASTQ files hosted at Zenodo record 17348100 (`genes_catalogue_R1.fastqsanger.gz` / `genes_catalogue_R2.fastqsanger.gz`), i.e. already trimmed metagenomic short reads. Database selectors are pinned to `eggNOG 5.0.2`, `mmseqs2 taxonomy UniRef50-17-b804f-07112025`, `staramr_downloaded_07042025` (resfinder/pointfinder/plasmidfinder), ABRicate virulence DB `resfinder`, and AMRFinderPlus DB `amrfinderplus_V3.12_2024-05-02.2`. The `Full genes catalogue` boolean is set to `false`, so the ARG-focused branch is exercised. Assertions check that MMseqs2 taxonomy output contains `Bacteria` with 4 columns, the Kraken-style report contains `cellular root` with 6 columns, eggNOG annotations contain the `#query` header and a hit like `Beta-lactamase class A` across 21 columns, argNorm/AMRFinderPlus report contains `Protein identifier`, the starAMR Resfinder table contains `Isolate ID` with 13 columns, the ABRicate virulence report contains `#FILE` with 15 columns, and the final MultiQC HTML mentions AMRFinderPlus, ABRicate, starAMR, QUAST, MMseqs2 taxonomy, and EggnogMapper sections.

## Reference workflow
Galaxy IWC workflow `Metagenomic Genes Catalogue Analysis` v1.2.1 by ABRomics (GPL-3.0-or-later), `workflows/microbiome/metagenomic-genes-catalogue` in `galaxyproject/iwc`.
