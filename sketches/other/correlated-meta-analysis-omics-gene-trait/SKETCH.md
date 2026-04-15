---
name: correlated-meta-analysis-omics-gene-trait
description: Use when you need to integrate multiple omics-based gene-trait association
  studies (GWAS, TWAS, and other per-gene p-value sources) into a single correlated
  meta-analysis at the gene level, accounting for sample overlap and hidden non-independence
  between studies, and then run module/GO enrichment on the meta-result. Typical inputs
  are GWAS summary statistics plus TWAS phenotype files for one or more traits.
domain: other
organism_class:
- human
- diploid
input_data:
- gwas-summary-stats
- twas-phenotype-csv
- additional-gene-pvalue-sources
- gene-annotation
- ld-reference-panel
source:
  ecosystem: nf-core
  workflow: nf-core/omicsgenetraitassociation
  url: https://github.com/nf-core/omicsgenetraitassociation
  version: dev
  license: MIT
  slug: omicsgenetraitassociation
tools:
- name: PascalX
- name: MMAP
- name: corrmeta
- name: WebGestaltR
tags:
- gwas
- twas
- meta-analysis
- gene-level
- enrichment
- gene-ontology
- multi-omics
- correlated-meta-analysis
test_data: []
expected_output: []
---

# Correlated meta-analysis of multi-omics gene-trait associations

## When to use this sketch
- You have gene-level association evidence for one or more traits coming from multiple, potentially overlapping studies (e.g. GWAS summary stats via LLFS and FHS cohorts) and need a single combined per-gene p-value.
- You need to account for hidden correlation between studies (shared/related samples) rather than assuming independence, so a naive Fisher/Stouffer combination is inappropriate.
- Your primary unit of inference is the gene (not SNP, transcript, or peptide), and you want to follow up the combined signal with module enrichment and GO enrichment.
- You start from raw GWAS summary statistics (needing SNP→gene aggregation) and/or TWAS-style phenotype tables, and optionally additional per-gene p-value files from other omics layers.

## Do not use when
- You only have a single study / single source of gene p-values — a correlated meta-analysis is unnecessary; use PascalX or a single-study enrichment workflow directly.
- You are doing SNP-level meta-analysis across independent cohorts without needing gene aggregation — use METAL or GWAMA instead.
- You need eQTL-based TWAS model fitting from scratch (e.g. FUSION, S-PrediXcan) — this pipeline consumes already-computed TWAS outputs, it does not fit them.
- Your goal is variant calling, differential expression, pathway scoring from expression matrices, or any non-meta-analysis task — pick a domain-specific sketch.
- Organism is not human / lacks a usable LD reference panel and gene annotation compatible with PascalX.

## Analysis outline
1. Parse the samplesheet: one row per (sample, trait) with paths to GWAS, TWAS, and optional `additional_sources` list.
2. Gene-level aggregation of GWAS summary statistics with **PascalX** using a gene annotation file and an LD reference panel (e.g. EUR), producing per-gene p-values and a Manhattan plot.
3. Gene-trait linear mixed model association with **MMAP**, using a phenotype file, pedigree, and kinship/covariance matrix; parse the per-gene LMM outputs into a single CSV.
4. Harmonize PASCAL, MMAP, and any additional gene p-value sources into a common gene × source matrix per trait.
5. Correlated meta-analysis with **corrmeta** (Province 2005): estimate tetrachoric correlations between sources and combine into a single `meta_p` per gene, writing `CMA_meta.csv` and `tetrachor_sigma.txt`.
6. Module Enrichment Analysis (**MEA**) over precomputed gene modules using the `meta_p` column and a Bonferroni-style threshold from `numtests` and `alpha`.
7. Gene Ontology enrichment with **WebGestaltR** on significant genes/modules; emit `master_summary_<sample>.csv`.

## Key parameters
- `input`: samplesheet CSV with columns `sample,trait,pascal,twas,additional_sources` (last may be blank).
- `trait`: trait name, must match a column in the TWAS phenotype file.
- PascalX inputs: `pascal_gwas_file`, `pascal_gene_annotation`, `pascal_ref_panel` (tarballed LD panel, e.g. `EUR_simulated.tar.gz`).
- `pascal_header` (default `0`), `pascal_pval_col` (default `1`) — describe the raw GWAS file layout.
- MMAP inputs: `mmap_gene_list`, `mmap_pheno_file`, `mmap_pedigree_file`, `mmap_cov_matrix_file` (binary kinship).
- MMAP parsing: `mmap_header=1`, `mmap_pval_col='p_vals'`, `mmap_beta_col='betas_genes'`, `mmap_se_genes='se_genes'`.
- CMA selector: `cma_test` one of `two_traits`, `three_complete_corr`, `three_missing_obs`; controls how many sources are combined and how missingness is handled.
- MEA: `gene_col_name='markname'`, `pval_col_name='meta_p'`, `numtests=17551` (genome-wide gene count for Bonferroni), `alpha=0.05`, `module_file_dir` pointing at a cherry-picked module set, `pipeline='cma'`.

## Test data
The bundled `test` profile points at a minimal dataset on `s3://brentlab-nextflow-testdata/omicsgenetraitassociation/`. Inputs include a tiny samplesheet for trait `fhshdl`, a PascalX bundle (`gwasA.csv.gz`, `gene_annotation.tsv`, `EUR_simulated.tar.gz` LD panel), MMAP fixtures (`demo_gene_list.txt`, `demo_phenotype.csv`, `pedigree.csv`, `demo.kinship.bin`), CMA fixtures for `two_traits`, `three-traits/test_category_complete_correlation`, and `three-traits/test_category_missing_observations`, plus a `cherryPickModules/` module directory for MEA. Running with `-profile test,docker` should produce, per sample, a `pascal/pascal_out.tsv` with a Manhattan plot, `mmap/parsed_output_mmap_results.csv`, `cma/CMA_meta.csv` and `cma/tetrachor_sigma.txt`, and `mea/master_summary_<sample>.csv`, all completing within the 2-CPU / 6 GB / 6 h CI limits.

## Reference workflow
nf-core/omicsgenetraitassociation (dev) — https://github.com/nf-core/omicsgenetraitassociation. Core methods: PascalX (Bergmann lab), MMAP (mmap.github.io), corrmeta implementing Province MA, *Meta-analyses of correlated genomic scans*, Genet Epidemiol 2005, and WebGestaltR for GO enrichment.
