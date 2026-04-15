---
name: scrna-seq-scanpy-clustering-10x
description: 'Use when you need to preprocess and cluster a 10x Genomics single-cell
  RNA-seq count matrix (Matrix Market .mtx + barcodes + genes/features) with the Scanpy/AnnData
  ecosystem: QC filtering, normalization, HVG selection, PCA, neighborhood graph,
  UMAP, Louvain clustering, Wilcoxon marker gene detection, and optional manual cell-type
  annotation. Targets standard droplet-based scRNA-seq from a single sample.'
domain: single-cell
organism_class:
- eukaryote
- vertebrate
input_data:
- 10x-scrna-mtx
- barcodes-tsv
- genes-tsv
source:
  ecosystem: iwc
  workflow: 'Single-Cell RNA-seq Analysis: Scanpy Preprocessing and Clustering'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/scRNAseq/scanpy-clustering
  version: '0.1'
  license: CC-BY-4.0
  slug: scRNAseq--scanpy-clustering
tools:
- name: scanpy
  version: 1.10.2+galaxy0
- name: anndata
  version: 0.10.9+galaxy0
- name: louvain
- name: umap
- name: wilcoxon
tags:
- scrna-seq
- single-cell
- 10x
- pbmc
- clustering
- umap
- louvain
- scanpy
- marker-genes
test_data:
- role: barcodes
  url: https://zenodo.org/record/3581213/files/barcodes.tsv
  filetype: txt
- role: genes
  url: https://zenodo.org/record/3581213/files/genes.tsv
  filetype: tabular
- role: matrix
  url: https://zenodo.org/record/3581213/files/matrix.mtx
  filetype: mtx
expected_output:
- role: anndata_with_celltype_annotation
  description: Content assertions for `Anndata with Celltype Annotation`.
  assertions:
  - 'has_h5_keys: {''keys'': ''uns/rank_genes_groups''}'
- role: initial_anndata_general_info
  description: Content assertions for `Initial Anndata General Info`.
  assertions:
  - "has_text: AnnData object with n_obs \xD7 n_vars = 2700 \xD7 32738"
- role: ranked_genes_with_wilcoxon_test
  description: Content assertions for `Ranked genes with Wilcoxon test`.
  assertions:
  - "has_line: LDHB\tLYZ\tCD74\tCCL5\tLST1\tNKG7\tHLA-DPA1\tPF4"
- role: anndata_with_raw_attribute
  description: Content assertions for `Anndata with raw attribute`.
  assertions:
  - 'has_h5_keys: {''keys'': ''uns/log1p''}'
- role: general_information_about_the_final_anndata_object
  path: expected_output/General information about the final Anndata object.txt
  description: Expected output `General information about the final Anndata object`
    from the source workflow test.
  assertions: []
- role: number_of_cells_per_cluster
  description: Content assertions for `Number of cells per cluster`.
  assertions:
  - "has_line: 6\t34"
---

# Single-cell RNA-seq preprocessing and clustering with Scanpy (10x)

## When to use this sketch
- User has a 10x Genomics-style single-sample scRNA-seq count matrix in Matrix Market Exchange format (`matrix.mtx` + `barcodes.tsv` + `genes.tsv`/`features.tsv`), from Cell Ranger v2 or v3+.
- Goal is an end-to-end exploratory analysis: QC, normalization, dimensionality reduction, clustering, and marker gene identification — the classic Scanpy PBMC 3k recipe.
- User wants a UMAP colored by Louvain clusters, ranked marker genes per cluster (Wilcoxon), and optionally a UMAP with manually annotated cell types.
- Single sample, no batch correction / integration required.
- Organism is one where mitochondrial genes follow a known prefix (e.g. `MT-` for human, `mt-` for mouse).

## Do not use when
- You have raw FASTQs and still need to generate the count matrix — run a Cell Ranger / STARsolo / Alevin quantification sketch first.
- You need to integrate multiple samples / batches or remove batch effects (use a Harmony/BBKNN/scVI integration sketch).
- The assay is spatial transcriptomics, CITE-seq with ADT panels, multiome ATAC+GEX, or Smart-seq full-length — those need assay-specific sketches.
- You need trajectory/pseudotime analysis, RNA velocity, or differential abundance testing — those are downstream sketches that assume a clustered AnnData already exists.
- You want Seurat (R) outputs rather than an AnnData `.h5ad`.

## Analysis outline
1. Import the `.mtx` + barcodes + genes/features into an AnnData object (`anndata_import`, choosing the Cell Ranger v2 `legacy_10x` or v3 `v3_10x` loader based on a boolean parameter).
2. Filter genes expressed in fewer than `min_cells` cells (`sc.pp.filter_genes`).
3. Flag mitochondrial genes by symbol prefix and compute QC metrics with `sc.pp.calculate_qc_metrics` (`qc_vars=mito`, `log1p=True`).
4. Draw QC diagnostics: scatter `n_genes_by_counts` vs `pct_counts_mito`, scatter `total_counts` vs `n_genes_by_counts`, and a violin of `n_genes_by_counts`/`total_counts`/`pct_counts_mito`.
5. Filter cells by `min_genes`, then by `max_genes`, then drop cells with `pct_counts_mito >= 5`.
6. Normalize to `target_sum=10000` (`sc.pp.normalize_total`) and log-transform (`sc.pp.log1p`); freeze the result into `adata.raw`.
7. Annotate highly variable genes with the Seurat flavor (`min_mean=0.0125`, `max_mean=3.0`, `min_disp=0.5`) and subset to HVGs.
8. Regress out `total_counts` and `pct_counts_mito`, then scale to unit variance with `max_value=10`.
9. PCA with `n_comps=50` and plot loadings, PCA overview, and variance-ratio elbow.
10. Build the neighborhood graph (`sc.pp.neighbors`, `n_neighbors`, `n_pcs`), embed with UMAP (`min_dist=0.5`), and cluster with Louvain (`vtraag` flavor, configurable `resolution`).
11. Rank marker genes per Louvain cluster with `sc.tl.rank_genes_groups` using `method=wilcoxon` and `benjamini-hochberg` correction, keeping the top 100 per cluster.
12. Visualize markers: UMAP colored by `louvain`, rank-genes plot, stacked violin, dotplot, heatmap of top 20 genes, per-cluster violin of top markers.
13. Optionally rename Louvain categories to user-provided cell-type labels and re-plot the UMAP with cell-type annotations.

## Key parameters
- `min_cells` (gene filter): default **3**.
- `min_genes` / `max_genes` (cell filter): defaults **200** and **2500**.
- Mitochondrial prefix: default **`MT-`** (use `mt-` for mouse).
- `pct_counts_mito` cutoff: **< 5%** (hard-coded in workflow).
- `normalize_total` target sum: **10000**; followed by `log1p`.
- HVG (Seurat flavor): `min_mean=0.0125`, `max_mean=3.0`, `min_disp=0.5`, `n_bins=20`.
- `regress_out` keys: `total_counts`, `pct_counts_mito`; `scale` with `max_value=10`, `zero_center=True`.
- PCA: `n_comps=50`, `random_state=0`.
- Neighbors: `n_neighbors` default **15**, `n_pcs` default **10**, `metric=euclidean`.
- UMAP: `min_dist=0.5`, `spread=1.0`, `random_state=0`.
- Louvain: `flavor=vtraag`, `resolution` default **1.0** (lower = fewer/larger clusters).
- Marker genes: `sc.tl.rank_genes_groups` with `method=wilcoxon`, `corr_method=benjamini-hochberg`, `n_genes=100`, `use_raw=True`, grouped by `louvain`.

## Test data
The reference test uses the classic 10x Genomics PBMC 3k dataset hosted on Zenodo record 3581213: `matrix.mtx`, `barcodes.tsv`, and `genes.tsv` (Cell Ranger v2 layout, so the v2/legacy loader is selected). The raw AnnData is expected to contain 2700 cells × 32738 genes (asserted via the "Initial Anndata General Info" text output). Test parameters set `min_cells=3`, `min_genes=200`, `max_genes=2500`, mito prefix `MT-`, `n_neighbors=10`, `n_pcs=10`, and Louvain `resolution=0.45`, with manual annotation enabled using the labels `CD4+ T, CD14+, B, CD8+ T, FCGR3A+, NK, Dendritic, Megakaryocytes`. Expected outputs include an h5ad with `obs/louvain`, `var/highly_variable`, and `uns/rank_genes_groups` populated; a tabular of Wilcoxon-ranked marker genes whose top row per cluster starts `LDHB\tLYZ\tCD74\tCCL5\tLST1\tNKG7\tHLA-DPA1\tPF4`; a per-cluster cell-count table (e.g. cluster `6` has 34 cells); plus QC, PCA, UMAP, dotplot, violin, and heatmap PNGs whose pixel dimensions and file sizes are checked within deltas.

## Reference workflow
Galaxy IWC — `workflows/scRNAseq/scanpy-clustering/Preprocessing-and-Clustering-of-single-cell-RNA-seq-data-with-Scanpy.ga`, release 0.1 (CC-BY-4.0). Mirrors the Scanpy legacy PBMC 3k clustering tutorial (https://scanpy.readthedocs.io/en/stable/tutorials/basics/clustering-2017.html) and the Galaxy Training Network scrna-scanpy-pbmc3k tutorial.
