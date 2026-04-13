---
name: goseq-go-kegg-enrichment-rnaseq
description: Use when you have a list of differentially expressed genes from a bulk
  RNA-seq experiment and want to test for over-represented Gene Ontology terms (BP,
  MF, CC) and KEGG pathways while correcting for gene-length bias using GOseq's Wallenius
  approximation. Requires a supported model organism with GO annotations available
  via getgo (e.g. mouse mm10, human hg38).
domain: rna-seq
organism_class:
- eukaryote
- vertebrate
input_data:
- deg-table-tabular
- gene-length-table
- kegg-pathway-table
source:
  ecosystem: iwc
  workflow: Gene Ontology and KEGG Pathway Enrichment Analysis
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/transcriptomics/goseq
  version: '0.1'
  license: MIT
tools:
- goseq
- galaxy-join
tags:
- enrichment
- gene-ontology
- kegg
- functional-analysis
- rna-seq
- pathway
- goseq
- wallenius
test_data:
- role: differential_expression_result
  url: https://zenodo.org/records/14033254/files/de-result.tabular
  sha1: 34770cded41b8a39b0056aa8bff47b6382a3c558
  filetype: tabular
- role: gene_length
  url: https://zenodo.org/records/14033254/files/gene-length.tabular
  sha1: bab691634c770bf6b150251c66278d90c727123c
  filetype: tabular
- role: kegg_pathways
  url: https://zenodo.org/records/14033254/files/kegg-pathways.tabular
  sha1: 9807280a33f5842b965eb82826f90c9c54597c27
  filetype: tabular
expected_output:
- role: goseq_enrichment_table_cellular_component
  description: Content assertions for `goseq Enrichment Table (Cellular Component)`.
  assertions:
  - 'that: has_text_matching'
  - "expression: category\tover_represented_pvalue\tunder_represented_pvalue\tnumDEInCat\t\
    numInCat\tterm\tontology\tp_adjust_over_represented\tp_adjust_under_represented"
  - 'that: has_text_matching'
  - "expression: GO:0005737\t4.79[0-9]+e-08\t1\t4810\t8312\tcytoplasm\tCC\t9.31[0-9]+e-05\t\
    1"
  - 'that: has_text_matching'
  - 'expression: over_represented_pvalue'
  - 'that: has_text_matching'
  - 'expression: under_represented_pvalue'
- role: goseq_top_categories_plot_cellular_component
  description: Content assertions for `goseq Top Categories plot (Cellular Component)`.
  assertions:
  - 'that: has_size'
  - 'size: 7078'
- role: goseq_differential_genes_in_each_category_cellular_component
  description: Content assertions for `goseq Differential Genes in each Category (Cellular
    Component)`.
  assertions:
  - 'that: has_text_matching'
  - "expression: category\tde_genes"
  - 'that: has_text_matching'
  - "expression: GO:0005737\tENSMUSG00000045545,ENSMUSG00000029802,ENSMUSG00000058056"
- role: goseq_differential_genes_in_each_category_biological_process
  description: Content assertions for `goseq Differential Genes in each Category (Biological
    Process)`.
  assertions:
  - 'that: has_text_matching'
  - "expression: category\tde_genes"
  - 'that: has_text_matching'
  - "expression: GO:0043254\tENSMUSG00000023951,ENSMUSG00000032060,ENSMUSG00000031284,"
- role: goseq_top_categories_plot_biological_process
  description: Content assertions for `goseq Top Categories plot (Biological Process)`.
  assertions:
  - 'that: has_size'
  - 'size: 7092'
- role: goseq_enrichment_table_biological_process
  description: Content assertions for `goseq Enrichment Table (Biological Process)`.
  assertions:
  - 'that: has_text_matching'
  - "expression: category\tover_represented_pvalue\tunder_represented_pvalue\tnumDEInCat\t\
    numInCat\tterm\tontology\tp_adjust_over_represented\tp_adjust_under_represented"
  - 'that: has_text_matching'
  - "expression: GO:0043254\t3.41[0-9]+e-07\t1\t239\t345\tregulation of protein-containing\
    \ complex assembly\tBP\t0.0034[0-9]+\t1"
  - 'that: has_text_matching'
  - 'expression: over_represented_pvalue'
  - 'that: has_text_matching'
  - 'expression: under_represented_pvalue'
- role: goseq_differential_genes_in_each_category_kegg
  description: Content assertions for `goseq Differential Genes in each Category (KEGG)`.
  assertions:
  - 'that: has_text_matching'
  - "expression: category\tde_genes"
  - 'that: has_text_matching'
  - "expression: 04540\tENSMUSG00000063358,ENSMUSG00000045136,ENSMUSG00000025856,ENSMUSG00000028019"
- role: goseq_top_categories_plot_molecular_function
  description: Content assertions for `goseq Top Categories plot (Molecular Function)`.
  assertions:
  - 'that: has_size'
  - 'size: 7166'
- role: goseq_enrichment_table_molecular_function
  description: Content assertions for `goseq Enrichment Table (Molecular Function)`.
  assertions:
  - 'that: has_text_matching'
  - "expression: category\tover_represented_pvalue\tunder_represented_pvalue\tnumDEInCat\t\
    numInCat\tterm\tontology\tp_adjust_over_represented\tp_adjust_under_represented"
  - 'that: has_text_matching'
  - "expression: GO:0005515\t1.4094[0-9]+e-07\t1\t3758\t6415\tprotein binding\tMF\t\
    0.0006[0-9]+\t1"
  - 'that: has_text_matching'
  - 'expression: over_represented_pvalue'
  - 'that: has_text_matching'
  - 'expression: under_represented_pvalue'
- role: goseq_differential_genes_in_each_category_molecular_function
  description: Content assertions for `goseq Differential Genes in each Category (Molecular
    Function)`.
  assertions:
  - 'that: has_text_matching'
  - "expression: category\tde_genes"
  - 'that: has_text_matching'
  - "expression: GO:0005515\tENSMUSG00000045545,ENSMUSG00000029802,ENSMUSG00000058056,ENSMUSG00000004044,"
- role: goseq_enrichment_table_kegg
  description: Content assertions for `goseq Enrichment Table (KEGG)`.
  assertions:
  - 'that: has_text_matching'
  - "expression: category\tover_represented_pvalue\tunder_represented_pvalue\tnumDEInCat\t\
    numInCat\tp_adjust_over_represented\tp_adjust_under_represented\tID\tName"
  - 'that: has_text_matching'
  - "expression: 04540\t0.0031[0-9]+\t0.99[0-9]+\t47\t61\t0.46[0-9]+\t1\t04540\tGap\
    \ junction - mmus"
---

# GOseq Gene Ontology and KEGG pathway enrichment for bulk RNA-seq

## When to use this sketch
- You already have a finished bulk RNA-seq differential expression analysis and now need a functional interpretation step.
- Your DE result can be reduced to a per-gene boolean (DE / not-DE) table — e.g. padj < 0.05 from DESeq2, edgeR, or limma.
- You care about correcting for the gene-length bias that affects standard Fisher/hypergeometric RNA-seq enrichment (longer genes are more likely to be called DE).
- The organism is supported by GOseq's built-in `getgo` (e.g. mouse `mm10`, human `hg38`) and you can supply gene IDs as Ensembl, Entrez, or gene symbol.
- You want GO enrichment across all three ontologies (Biological Process, Molecular Function, Cellular Component) and KEGG pathway enrichment in a single run.

## Do not use when
- You have no DE analysis yet — run a DE workflow first (e.g. a DESeq2 or limma-voom sketch) to produce the input.
- You want GSEA-style ranked enrichment on a full gene ranking rather than a DE / non-DE split — use a fgsea/clusterProfiler GSEA sketch instead.
- Your organism is not in GOseq's supported genomes and you have no custom category mapping to supply.
- You are analyzing single-cell RNA-seq cluster markers — use a scRNA-specific enrichment sketch; length bias correction behaves differently there.
- You need pathway topology analysis (e.g. SPIA, Pathview visualizations) — GOseq only tests over-representation.

## Analysis outline
1. Prepare a two-column DEG table: column 1 gene identifier, column 2 boolean (TRUE/FALSE) indicating differential expression.
2. Prepare a two-column gene-length table (gene id, length) — produced by the `Gene length and GC content` tool from a GTF, or by featureCounts with the gene-length output option.
3. Fetch a KEGG pathway ID→name table for the organism of interest from the KEGG REST API (`https://rest.kegg.jp/list/pathway/<orgcode>`).
4. Run `goseq` with `fetchcats: GO:CC` to compute Cellular Component enrichment (Wallenius method, BH adjustment, Top GO plot + per-category DE genes).
5. Run `goseq` with `fetchcats: GO:BP` to compute Biological Process enrichment (same settings).
6. Run `goseq` with `fetchcats: GO:MF` to compute Molecular Function enrichment (same settings).
7. Run `goseq` with `fetchcats: KEGG` to compute KEGG pathway enrichment (plots disabled; KEGG categories have no topGO layout).
8. Join the KEGG enrichment table to the KEGG pathway name table on pathway ID (`join1`, outer join with header) to produce a human-readable KEGG enrichment table.

## Key parameters
- `categorySource.catSource`: `getgo` — use GOseq's built-in org.*.db mapping.
- `categorySource.genome`: organism code passed to getgo (e.g. `mm10`, `hg38`).
- `categorySource.gene_id`: gene ID format — one of `ensGene`, `knownGene` (Entrez), or `geneSymbol`; must match the IDs in the DEG and length tables.
- `categorySource.fetchcats`: one of `GO:CC`, `GO:BP`, `GO:MF`, `KEGG` — one goseq invocation per category class.
- `methods.wallenius`: `true` (length-bias-corrected Wallenius approximation; this is the whole point of goseq).
- `methods.hypergeometric`: `false`; `methods.repcnt`: `0` (no sampling-based p-values).
- `adv.p_adj_method`: `BH` (Benjamini–Hochberg FDR).
- `adv.use_genes_without_cat`: `false` — exclude genes lacking any GO/KEGG annotation from the background.
- `out.topgo_plot`: `true` for GO runs, `false` for the KEGG run; `out.cat_genes`: `true` to emit the per-category DE-gene list.

## Test data
The source workflow ships a mouse (mm10, Ensembl gene IDs) test case hosted on Zenodo record 14033254: a tabular DE result (`de-result.tabular`) with gene-level TRUE/FALSE DE flags, a gene length table (`gene-length.tabular`), and a KEGG pathway ID→name table for `mmu` (`kegg-pathways.tabular`). Running the workflow with `Select genome to use = mm10` and `Select gene ID format = ensGene` is expected to produce GO enrichment tables for CC, BP, and MF (with header `category  over_represented_pvalue  under_represented_pvalue  numDEInCat  numInCat  term  ontology  p_adjust_over_represented  p_adjust_under_represented` and significant hits such as GO:0005737 `cytoplasm` for CC, GO:0043254 `regulation of protein-containing complex assembly` for BP, and GO:0005515 `protein binding` for MF), matching top-categories PDF plots, per-category DE gene lists, and a joined KEGG enrichment table in which pathway `04540` (`Gap junction - mmus`) appears with 47/61 DE genes.

## Reference workflow
Galaxy IWC `workflows/transcriptomics/goseq/goseq-go-kegg-enrichment-analsis.ga`, release 0.1 (2024-11-03), using `toolshed.g2.bx.psu.edu/repos/iuc/goseq/goseq` version `1.50.0+galaxy0`.
