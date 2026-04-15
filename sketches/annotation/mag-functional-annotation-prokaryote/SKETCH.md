---
name: mag-functional-annotation-prokaryote
description: Use when you need to functionally annotate a collection of metagenome-assembled
  genomes (MAGs) or isolate bacterial assemblies in parallel, producing gene/CDS calls,
  plasmid replicons, insertion sequences, and integrons with a unified MultiQC summary
  across all genomes. Targets prokaryotes; archaea are not well supported.
domain: annotation
organism_class:
- bacterial
- prokaryote
- haploid
input_data:
- genome-assembly-fasta-collection
source:
  ecosystem: iwc
  workflow: MAG Genome Annotation Parallel
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/microbiome/mag-genome-annotation-parallel
  version: '0.2'
  license: MIT
  slug: microbiome--mag-genome-annotation-parallel
tools:
- name: bakta
- name: plasmidfinder
- name: isescan
- name: integron_finder
- name: tooldistillator
- name: multiqc
  version: 1.33+galaxy2
tags:
- mag
- metagenomics
- bacterial
- annotation
- plasmid
- insertion-sequence
- integron
- cds
- amr
- galaxy
test_data:
- role: bacterial_genomes__50contig_reads_binette_bin1_fasta
  url: https://zenodo.org/records/18635101/files/50contig_reads_binette_bin2.fasta
expected_output:
- role: multiqc_html_report
  description: Content assertions for `multiqc html report`.
  assertions:
  - 'that: has_text'
  - 'text: 50contig_reads_bin'
- role: isescan_merged_output
  description: Content assertions for `ISEScan Merged Output`.
  assertions:
  - 'that: has_n_lines'
  - 'n: 0'
- role: integron_finder_merged_output
  description: Content assertions for `Integron Finder Merged Output`.
  assertions:
  - 'that: has_n_lines'
  - 'n: 0'
- role: bakta_cut_annotation_summary
  description: Content assertions for `bakta cut annotation summary`.
  assertions:
  - 'that: has_n_lines'
  - 'n: 16'
  - 'that: has_n_columns'
  - 'n: 2'
- role: plasmidfinder_merged_summary
  description: Content assertions for `PlasmidFinder Merged Summary`.
  assertions:
  - 'that: has_text'
  - "text: Sample\tDatabase\tPlasmid\tIdentity\tQuery / Template length\tContig\t\
    Position in contig\tNote\tAccession number"
  - 'that: has_n_lines'
  - 'n: 1'
---

# Parallel functional annotation of bacterial MAGs

## When to use this sketch
- You already have assembled bacterial genomes (isolate assemblies or MAGs recovered from metagenomic binning) as FASTA and want a standardized annotation pass.
- You need CDS / rRNA / tRNA / ncRNA / CRISPR / sORF / pseudogene calls from Bakta together with mobile-element context: plasmid replicons (PlasmidFinder), insertion sequences (ISEScan), and integrons with attC sites and gene cassettes (Integron Finder).
- You are processing many genomes in one go and want per-MAG outputs plus merged cross-sample tables and a single MultiQC report summarizing annotation completeness and mobilome content.
- You want optional AMR gene annotation via Bakta's AMRFinderPlus integration.

## Do not use when
- You still need to assemble or bin the genomes first — run an assembly / binning workflow (e.g. a MAG recovery workflow with metaSPAdes/MEGAHIT + MetaBAT/Binette) before this sketch.
- You are annotating eukaryotic or archaeal genomes — Bakta and the mobilome tools here target bacteria and will miss many features in archaea; use a eukaryotic annotation pipeline instead.
- You want taxonomic assignment or MAG quality assessment (CheckM/GTDB-Tk) — use a dedicated MAG-QC/taxonomy sketch.
- You need viral or phage-specific annotation (geNomad, VIBRANT, Pharokka) — use a virome annotation sketch.
- Your goal is variant calling against a reference rather than de novo annotation — use a bacterial variant-calling sketch.

## Analysis outline
1. Accept a Galaxy collection of bacterial genome FASTA files (one per MAG / isolate) and fan out the rest of the steps per genome.
2. Run Bakta (optional, gated by a `Run Bakta` boolean) for full structural + functional annotation using a user-selected Bakta DB and AMRFinderPlus DB; emits GFF3, GenBank, EMBL, TSV, FAA/FFN/FNA, hypothetical-protein tables, summary text, and a circular plot.
3. Run PlasmidFinder against a chosen plasmid database to identify plasmid replicon sequences and type the contigs.
4. Run ISEScan to detect insertion-sequence elements and report IS family/subgroup, ORFs, and GFF annotations.
5. Run Integron Finder (local_max mode, with attI promoter search) to detect integrons, integrases, attC sites, and gene cassettes.
6. Normalize each tool's tabular output with small awk / Convert-characters steps (strip leading `#`, reformat Bakta summary into a two-column Annotation/Count table, convert spaces to tabs for IS/Integron results).
7. Collapse per-MAG results across the collection: Column-join for Bakta summaries, Collapse Collection for PlasmidFinder, ISEScan, and Integron Finder tables, tagged with the genome name.
8. Feed the per-tool outputs to ToolDistillator and ToolDistillator Summarize (two branches: one with Bakta, one without) to produce standardized JSON annotation summaries.
9. Generate a single MultiQC HTML report aggregating Bakta summaries plus custom-content tables for Integron Finder, ISEScan, and PlasmidFinder across all genomes.

## Key parameters
- `Bacterial Genomes`: Galaxy list collection of FASTA assemblies, one element per MAG/isolate. Required.
- `Run Bakta`: boolean, default `true`. Set to `false` to skip the Bakta branch when runtime is a concern — PlasmidFinder/ISEScan/Integron Finder still run.
- `Bacterial genome annotation database`: cached Bakta DB version (e.g. `V5.0_2023-02-20`). Required when `Run Bakta=true`.
- `AMRFinderPlus database`: cached AMRFinderPlus DB (e.g. `amrfinderplus_V3.12_2024-05-02.2`). Wired into Bakta's `input_option.amrfinder_db_select`.
- `Plasmid detection database`: cached PlasmidFinder DB (e.g. `plasmidfinder_1307168_2019_08_28`).
- Bakta is invoked with `translation_table=11`, `complete=false`, `meta=false`, `compliant=false`, all output files enabled; organism/genus/species/strain left unset so annotation is generic-bacterial.
- PlasmidFinder thresholds: `min_cov=0.6`, `threshold=0.95` (default sensitivity/specificity tradeoff).
- Integron Finder: `local_max=true`, `promoter_attI=true`, `dist_thresh=4000`, `calin_threshold=2`, `min_attc_size=40`, `max_attc_size=200`, `keep_palindromes=false`, `no_proteins=false`; `topology_file` and `type_replicon` left as runtime values so the tool auto-detects.
- ISEScan: `log_activate=true`, `remove_short_is=false`.

## Test data
The test profile supplies a single-element Galaxy collection containing one bacterial MAG FASTA (`50contig_reads_binette_bin1.fasta`, a 50-contig bin hosted on Zenodo record 18635101) together with pinned Bakta (`V5.0_2023-02-20`), AMRFinderPlus (`amrfinderplus_V3.12_2024-05-02.2`), and PlasmidFinder (`plasmidfinder_1307168_2019_08_28`) databases and `Run Bakta=true`. The expected MultiQC HTML report contains the text `50contig_reads_bin`, confirming the genome was processed end-to-end. The merged ISEScan and Integron Finder tables are expected to be empty (0 lines) for this bin, the PlasmidFinder merged summary is expected to have exactly 1 line with the canonical header `Sample\tDatabase\tPlasmid\tIdentity\tQuery / Template length\tContig\tPosition in contig\tNote\tAccession number`, and the Bakta cut annotation summary is expected to be a 16-line, 2-column Annotation/Count table. These are assertions-only checks, so no golden files are shipped.

## Reference workflow
Galaxy IWC `workflows/microbiome/mag-genome-annotation-parallel`, release 0.2 (MIT). Wraps the `Bacterial Genome Annotation - IWC` subworkflow by ABRomics. Key tool versions: Bakta 1.9.4+galaxy1, PlasmidFinder 2.1.6+galaxy2, ISEScan 1.7.3+galaxy0, Integron Finder 2.0.5+galaxy1, ToolDistillator 1.0.5+galaxy1, MultiQC 1.33+galaxy2.
