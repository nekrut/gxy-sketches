---
name: two-condition-rnaseq-differential-expression
description: Use when you already have per-sample gene count tables from a bulk RNA-seq
  experiment with exactly two conditions (e.g. treated vs control, knockdown vs wildtype)
  and need DESeq2-based differential expression calls plus publication-ready volcano
  plot and heatmaps. Requires at least two replicates per condition.
domain: rna-seq
organism_class:
- eukaryote
input_data:
- gene-count-tables
- gtf-annotation
source:
  ecosystem: iwc
  workflow: RNA-Seq Differential Expression Analysis with Visualization
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/transcriptomics/rnaseq-de
  version: '0.8'
  license: MIT
  slug: transcriptomics--rnaseq-de
tools:
- name: deseq2
  version: 2.11.40.8+galaxy2
- name: deg_annotate
  version: 1.1.0+galaxy1
- name: volcanoplot
  version: 4.0.2+galaxy0
- name: ggplot2_heatmap2
  version: 3.3.0+galaxy0
tags:
- rnaseq
- differential-expression
- deseq2
- volcano-plot
- heatmap
- bulk-rnaseq
- two-condition
test_data:
- role: gene_annotaton
  url: https://zenodo.org/records/14056162/files/Saccharomyces_cerevisiae.R64-1-1.113.gtf
  filetype: gtf
- role: counts_from_changed_condition__srr5085169_counts_table
  url: https://zenodo.org/records/14056162/files/SRR5085169.tabular
- role: counts_from_changed_condition__srr5085170_counts_table
  url: https://zenodo.org/records/14056162/files/SRR5085170.tabular
- role: counts_from_reference_condition__srr5085167_counts_table
  url: https://zenodo.org/records/14056162/files/SRR5085167.tabular
- role: counts_from_reference_condition__srr5085168_counts_table
  url: https://zenodo.org/records/14056162/files/SRR5085168.tabular
expected_output: []
---

# Two-condition bulk RNA-seq differential expression with visualization

## When to use this sketch
- User already has per-sample gene-level count tables (from featureCounts, HTSeq, or RNA-STAR GeneCounts) and wants differential expression results.
- Experimental design is exactly two groups (e.g. treated vs untreated, KO vs WT, mutant vs wildtype) with at least two replicates per group.
- User wants an annotated DE gene table plus diagnostic plots: volcano plot, MA plot, and heatmaps of normalized counts and row Z-scores.
- Annotation GTF is available (same one used during read counting) so genes can be labeled with chromosome coordinates, biotype, and gene symbols.

## Do not use when
- The user has raw FASTQ reads and no counts yet — first run an alignment+quantification workflow (e.g. STAR/HISAT2 + featureCounts) to produce count tables.
- The design has more than two conditions, batch factors as the primary contrast, time courses, or interaction terms — use a multi-factor DESeq2 or limma-voom workflow instead.
- Single-cell RNA-seq data — use a scRNA-seq differential expression sketch.
- Transcript-level or isoform-level differential expression — use a tximport + DESeq2 or sleuth-based workflow.
- Differential exon usage / alternative splicing — use DEXSeq or rMATS.
- Fewer than two replicates per condition (DESeq2 dispersion estimation is unreliable).

## Analysis outline
1. Collect two input collections of count tables: one per condition (changed vs reference).
2. Run DESeq2 with `datasets_per_level` mode, factor name `DEFactor`, levels `MainFactor` (changed) and `BaseFactor` (reference); emit normalized counts and diagnostic PDF plots.
3. Annotate the DESeq2 results table with gene coordinates, biotype and gene symbol via `deg_annotate` using the same GTF supplied to counting.
4. Filter the annotated table on adjusted p-value (column 7) then on absolute log2 fold change (column 3) to produce the significant-DE gene list.
5. Generate a volcano plot via the Galaxy `volcanoplot` tool, labeling the top 10 most significant genes.
6. Join DESeq2 normalized counts with the filtered DE gene list and cut the count columns to build the heatmap input.
7. Render two heatmaps with `ggplot2_heatmap2`: one of log2(x+1) normalized counts (white→red) and one of per-row Z-scores (blue→white→red).

## Key parameters
- DESeq2 `fit_type`: `local` (value `1` in the tool state).
- DESeq2 `output_selector`: `pdf,normCounts` (emit diagnostic plots and normalized counts).
- DESeq2 `tximport`: off — inputs are already count tables, not transcript abundances.
- `Count files have header`: true for featureCounts output, false for RNA-STAR `ReadsPerGene.out.tab`.
- `Adjusted p-value threshold`: default `0.05`; filter expression `c7 < <alpha>`.
- `log2 fold change threshold`: default `1.0`; filter expression `abs(c3) > <lfc>`.
- Volcano plot columns: fdr=7, pval=6, lfc=3, label=13; top 10 significant genes labeled.
- `deg_annotate` mode: `degseq`, feature type `exon`, id attribute `gene_id`, extra attributes `gene_biotype, gene_name`.
- Heatmaps: hierarchical clustering on both axes, Euclidean distance, complete linkage; counts heatmap uses `log2plus1` transform, Z-score heatmap uses per-row scaling.

## Test data
The reference test uses a *Saccharomyces cerevisiae* two-condition experiment: two "changed" samples (SRR5085169, SRR5085170) and two "reference" samples (SRR5085167, SRR5085168), each as a featureCounts-style tabular count table, plus the matching Ensembl R64-1-1 release 113 GTF. Parameters are `Count files have header = true`, adjusted p-value threshold `0.1`, log2 fold change threshold `0.5`. Running the workflow should yield an annotated DESeq2 results table containing the row for PHO84 (`YML123C`) with log2FC ≈ −1.67 and padj ≈ 5e-something, a DESeq2 normalized counts table with PHO84 values around 210/180/48/52, a multi-page DESeq2 diagnostic PDF (~1.19 MB), a volcano plot PDF (~300 KB), and two heatmap PDFs (~19.5 KB each) for log-transformed counts and Z-scores.

## Reference workflow
Galaxy IWC `workflows/transcriptomics/rnaseq-de` — "RNA-Seq Differential Expression Analysis with Visualization", release 0.8 (file `rnaseq-de-filtering-plotting.ga`), MIT licensed, authored by Pavankumar Videm.
