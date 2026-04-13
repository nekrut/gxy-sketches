---
name: scrna-pseudobulk-differential-expression
description: Use when you need to perform differential gene expression analysis between
  conditions on annotated single-cell RNA-seq data by aggregating cell-level counts
  into pseudobulk samples (per cell type / per donor) and testing with edgeR. Assumes
  you already have a clustered, cell-type-annotated AnnData object with raw counts
  and sample/condition metadata in obs.
domain: single-cell
organism_class:
- eukaryote
- vertebrate
input_data:
- anndata-h5ad
- cell-type-annotations
source:
  ecosystem: iwc
  workflow: Single-Cell Pseudobulk Differential Expression Analysis with edgeR
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/scRNAseq/pseudobulk-worflow-decoupler-edger
  version: 0.1.1
  license: CC-BY-4.0
tools:
- decoupler
- edger
- volcanoplot
- galaxy
tags:
- scrna-seq
- pseudobulk
- differential-expression
- edger
- decoupler
- anndata
- volcano-plot
test_data:
- role: source_anndata_file
  url: https://zenodo.org/records/13929549/files/Source%20AnnData%20file.h5ad
  filetype: h5ad
expected_output: []
---

# Single-cell pseudobulk differential expression with edgeR

## When to use this sketch
- You have an annotated AnnData (`.h5ad`) from an scRNA-seq experiment with raw counts stored in a named layer and cell-type / sample / condition labels in `obs`.
- You want to test condition effects (e.g. disease vs. control) **per cell type**, using a statistically sound pseudobulk approach rather than cell-level tests.
- You have multiple biological replicates (donors/samples) per condition — pseudobulk aggregation requires this to estimate dispersion.
- You want a bulk-style linear model with optional covariates (batch, sex, phase) and FDR-controlled gene lists plus volcano plots per contrast.

## Do not use when
- You want cell-level DE (use a Wilcoxon / MAST-based scanpy/Seurat marker workflow instead).
- You don't have replicates — pseudobulk collapses all cells of a sample into one observation, so N=1 per condition gives no power.
- You need trajectory/pseudotime-based differential expression (use tradeSeq / condiments).
- You need compositional analysis of cell-type abundance shifts (use scCODA / milo).
- Your starting point is raw FASTQ — run an upstream scRNA-seq quantification + clustering + annotation workflow first (e.g. Cell Ranger / Alevin-fry + scanpy).
- Your DE design would be better served by DESeq2 or limma-voom — this sketch is opinionated toward edgeR QLF with TMM normalization.

## Analysis outline
1. **Pseudobulk aggregation** — `decoupler_pseudobulk` sums raw counts from the named layer across cells sharing (sample_key × groupby), emitting a gene×pseudobulk count matrix, a samples-metadata (factor) table, a genes-metadata table, and QC plots (counts/cells per pseudobulk, filter-by-expression).
2. **Sanitize count matrix** — `Replace Text` strips characters `[ --+*^]+` from headers so edgeR's R formula parser doesn't choke on factor level names.
3. **Sanitize factors file** — same regex replacement on the samples metadata table.
4. **Clean gene annotation** — `Remove columns by header` drops `start`, `end`, `width` columns that otherwise confuse edgeR/DESeq2.
5. **Fix leading-digit factor levels** — `Replace Text in column` prefixes numeric-starting levels with `GG_` so they become valid R identifiers.
6. **Build contrast list** — an awk step enumerates all pairwise contrasts between levels of the primary factor.
7. **edgeR QLF differential expression** — `edgeR` tool runs TMM normalization, robust dispersion estimation, and a quasi-likelihood F-test under the user-supplied `~ 0 + factor[+ covariates]` design for each contrast, producing DEG tables and an HTML report.
8. **Extract volcano-ready tables** — `Remove columns` keeps `gene_symbol`, `logFC`, `PValue`, `FDR`.
9. **Per-contrast volcano plots** — contrast identifiers are split into a collection, passed as plot titles, and `Volcano Plot` renders one PDF per contrast with significant-gene labels.

## Key parameters
- **decoupler_pseudobulk**: `mode: sum`, `use_raw: false`, `layer: <raw counts layer name>`, `min_cells: 10`, `min_counts: 10`, `min_counts_per_sample: 20`, `min_total_counts: 1000`, `filter_expr: true`, `produce_plots: true`.
- **groupby**: the `obs` column defining the stratum to run DE within (typically `cell_type`).
- **sample_key**: the `obs` column identifying a biological replicate (e.g. `individual`, or a merged `sample_condition` field).
- **factor_fields**: first entry = primary contrast variable (e.g. `disease`); subsequent entries = covariates.
- **Formula**: no-intercept design such as `~ 0 + disease` or `~ 0 + disease + batch`; the `0 +` form is required so the downstream pairwise-contrast enumerator can reference each level directly.
- **edgeR adv**: `normalisationOption: TMM`, `robOption: true` (robust dispersion), `lrtOption: false` (use QLF), `pAdjust: BH`, `pVal: 0.05`, `lfc: 0.0`.
- **Volcano Plot**: `lfc_thresh: 0.58` (≈1.5× fold-change), `signif_thresh: 0.05` (FDR), top 40 significant genes labeled.

## Test data
A single annotated AnnData file (`Source AnnData file.h5ad`, hosted on Zenodo record 13929549) is the only data input. It contains per-cell raw counts in a layer named `counts`, with `obs` columns `cell_type`, `individual`, `disease`, and a `gene_symbol` column in `var`. The test job groups by `cell_type`, uses `individual` as the sample key, runs the design `~ 0 + disease`, and yields a pseudobulk count matrix (with known per-gene count vectors for e.g. `ACAP2`, `ACER3`), pseudobulk/filter QC PNGs, an edgeR HTML report, a per-contrast DEG table collection keyed e.g. `edgeR_normal-COVID_19` with ~1430 rows, reduced volcano-ready tables, and a per-contrast volcano plot PDF.

## Reference workflow
Galaxy IWC workflow *Single-Cell Pseudobulk Differential Expression Analysis with edgeR* v0.1.1 (`workflows/scRNAseq/pseudobulk-worflow-decoupler-edger`), derived from the Persist-SEQ consortium pseudobulk scRNA-seq pipeline. Tools: `decoupler_pseudobulk` 1.4.0+galaxy8, `edgeR` 3.36.0+galaxy5, `volcanoplot` 0.0.6.
