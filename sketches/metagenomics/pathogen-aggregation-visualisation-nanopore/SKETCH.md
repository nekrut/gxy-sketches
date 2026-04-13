---
name: pathogen-aggregation-visualisation-nanopore
description: Use when you have per-sample AMR and virulence-factor (VF) gene hits
  plus contigs from multiple nanopore foodborne-pathogen samples (e.g. from the PathoGFAIR
  gene-based and allele-based identification workflows) and need to aggregate them
  into a cross-sample presence/absence heatmap, AMR/VF count tables, and phylogenetic
  trees relating samples and individual pathogenic genes.
domain: metagenomics
organism_class:
- bacterial
- microbial-community
input_data:
- abricate-amr-tabular-collection
- abricate-vfdb-tabular-collection
- contigs-fasta-collection
- qc-summary-tabular
source:
  ecosystem: iwc
  workflow: Pathogen Detection PathoGFAIR Samples Aggregation and Visualisation
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/microbiome/pathogen-identification/pathogen-detection-pathogfair-samples-aggregation-and-visualisation
  version: '0.1'
  license: MIT
tools:
- abricate
- bedtools
- clustalw
- fasttree
- newick_utils
- ggplot2
- collapse_collections
- text_processing
tags:
- pathogen
- amr
- virulence-factors
- heatmap
- phylogenetic-tree
- nanopore
- foodborne
- pathogfair
- cross-sample
test_data: []
expected_output: []
---

# PathoGFAIR cross-sample pathogen aggregation and visualisation

## When to use this sketch
- You already ran per-sample pathogen identification on nanopore reads (PathoGFAIR gene-based and allele-based workflows) and now need a single cross-sample view.
- You have ABRicate output collections against AMRFinder/NCBI and VFDB, plus assembled contigs per sample, and you want a presence/absence heatmap of VF genes across samples.
- You want phylogenetic trees built from contigs carrying AMR or VF genes, both globally across samples and per individual gene, to ask "which samples share which pathogenic gene variants".
- You want per-sample QC bar charts summarising host removal, mapping depth/coverage, and variant counts for a foodborne surveillance report.

## Do not use when
- You have raw FASTQ only and have not yet called AMR/VF genes or assembled contigs — run the PathoGFAIR preprocessing and gene-based/allele-based identification workflows first.
- You only have a single sample — cross-sample aggregation, heatmaps, and multi-sample trees are pointless; use the per-sample identification sketches instead.
- You need taxonomic profiling or read-based classification (Kraken2/Bracken) rather than gene-level pathogen tracking — use a metagenomic taxonomic profiling sketch.
- Your data is Illumina short-read WGS of a single isolate — use a bacterial assembly + MLST/AMR typing sketch.

## Analysis outline
1. Filter failed datasets from every input collection (AMR-NCBI, VFDB, AMRs, VFs, contigs) with `__FILTER_FAILED_DATASETS__`.
2. Strip the ABRicate header row from each per-sample table with `Remove beginning` (num_lines=1).
3. Build per-sample AMR and VF gene count tables with `Count` on the gene column, then `Cut` to keep gene names and `Collapse Collection` across samples.
4. Fill missing counts with 0 using `Column Regex Find And Replace` (`^$` → `0`) to produce `amrs_count` and `vfs_count`.
5. Group VFDB hits by gene and use `Column join` across samples to build the sample×gene presence/absence matrix; relabel the header with `Column Regex Find And Replace` to produce `heatmap_table`.
6. Render the cross-sample VF heatmap with `ggplot2 Heatmap` (clustered, whrd colorscheme, PNG+PDF).
7. `Multi-Join` the AMR and VF count tables and clean column names with `Replace Text` to produce the combined `vfs_amrs_count_table`.
8. Merge all sample contigs into one FASTA with `Collapse Collection`; extract contig regions carrying AMR or VF hits with `bedtools getfasta` using per-sample BED-style coordinates cut from the ABRicate tables.
9. Per gene: split the merged VF table by gene name with `Split by group`, extract sequences, then run `ClustalW` → `FASTTREE (-nt -gtr)` → `Newick Display` to draw one tree per VF gene (`newick_genes_tree_graphs_collection`).
10. All-samples tree: concatenate the per-contig extracted FASTAs, deduplicate with `FASTA Merge Files and Filter Unique Sequences`, align with `ClustalW`, infer the tree with `FASTTREE`, render with `Newick Display` to produce `all_samples_phylogenetic_tree_based_amrs` and `all_samples_phylogenetic_tree_based_vfs`.
11. Keep the QC tabulars (host removal %, mapping mean depth, mapping coverage %, variant counts, optional metadata) as pass-through inputs for downstream bar-chart / Jupyter visualisation.

## Key parameters
- `Remove beginning`: `num_lines: 1` (drop the ABRicate header).
- `Count`: `column: 1`, `delim: T`, `sorting: value` (gene frequency per sample).
- `Cut` for BED extraction: `columnList: c2,c3,c4` with output datatype forced to `bed`.
- `Column Regex Find And Replace`: `^$` → `0` on column 2 of the count tables; `#KEY` → `key` on column 1 of the heatmap table.
- `Column join`: `identifier_column: 1`, `fill_char: 0`, `output_header: true`.
- `ggplot2 Heatmap`: `header=TRUE`, `row_names_index=1`, `cluster=true`, `colorscheme=whrd`, size 70×70 cm at 1000 dpi, PNG+PDF.
- `ClustalW`: DNA, IUB matrix, aligned output order, FASTA output.
- `FASTTREE`: `-nt -gtr`, minimise (`maximize: min`).
- `Newick Display`: SVG, width 2000, scalebar on, leaf size 10px.
- `FASTA Merge Files and Filter Unique Sequences`: `uniqueness_criterion: sequence`, `processmode: merge`.
- `metadata` input is optional.

## Test data
The Planemo test job supplies two-sample collections for AMR and VF tables, contigs, and ABRicate-by-VFDB/NCBI outputs (identifiers `collection_of_all_samples_Spike3bBarcode10.fastq.gz` and `...Barcode12.fastq.gz`, plus `split_file_000000/000001` for the raw AMR/VF/contig lists), alongside four single tabulars from the nanopore preprocessing and allele-based steps (`removed_hosts_percentage_tabular`, `mapping_mean_depth_per_sample`, `mapping_coverage_percentage_per_sample`, `number_of_variants_per_sample`) and an empty optional `metadata` input. The asserted output is the `adjusted_abricate_vfs_tabular_part1` collection, specifically the element `YP_001006764` matching a golden tabular under `test-data/`. A successful run should additionally materialise the cross-sample VF heatmap PNG/PDF, the AMR and VF count tables, the combined `vfs_amrs_count_table`, the per-gene Newick SVG collection, and the two all-samples phylogenetic tree SVGs.

## Reference workflow
IWC `workflows/microbiome/pathogen-identification/pathogen-detection-pathogfair-samples-aggregation-and-visualisation` (Galaxy `.ga`, release 0.1, 2024-04-24), part of the PathoGFAIR suite and the GTN tutorial *Pathogen detection from nanopore foodborne data*. Authors: Engy Nasr, Bérénice Batut, Paul Zierep. License MIT.
