---
name: scrna-downstream-integration-clustering
description: Use when you have already-quantified single-cell RNA-seq count matrices
  (10x CellRanger output, H5AD, SingleCellExperiment/Seurat RDS, or CSV) from multiple
  samples and need to perform QC, ambient RNA removal, doublet detection, batch integration,
  clustering, UMAP, and cell type annotation to produce an integrated atlas. Not for
  raw FASTQ-to-counts quantification.
domain: single-cell
organism_class:
- eukaryote
input_data:
- scrna-count-matrix-h5ad
- scrna-count-matrix-rds
- scrna-count-matrix-csv
- 10x-cellranger-output
source:
  ecosystem: nf-core
  workflow: nf-core/scdownstream
  url: https://github.com/nf-core/scdownstream
  version: dev
  license: MIT
  slug: scdownstream
tools:
- name: scanpy
- name: scvi-tools
- name: harmony
- name: bbknn
- name: combat
- name: seurat
- name: decontx
- name: cellbender
- name: soupx
- name: scar
- name: scrublet
- name: scdblfinder
- name: solo
- name: doubletdetection
- name: scds
- name: celltypist
- name: singler
- name: leiden
- name: umap
- name: multiqc
- name: quarto
tags:
- single-cell
- scrna-seq
- integration
- batch-correction
- doublet-detection
- ambient-rna
- clustering
- umap
- cell-type-annotation
- atlas
- h5ad
- anndata
test_data: []
expected_output: []
---

# Single-cell RNA-seq downstream: QC, integration, clustering

## When to use this sketch
- You already have per-sample count matrices from a scRNA-seq experiment (e.g. from CellRanger, nf-core/scrnaseq, STARsolo, alevin-fry) and need the *downstream* steps: QC, ambient RNA cleanup, doublet removal, batch integration across samples, clustering, UMAP, and cell type labeling.
- Multi-sample datasets where batch effects must be corrected and results merged into a single integrated AnnData/SingleCellExperiment object.
- Inputs are one of: 10x `filtered`/`raw` matrices (H5/H5AD), AnnData `.h5ad`, Seurat/SCE `.rds`, or a genes-by-cells `.csv`.
- Human or mouse data (bundled cell-cycle gene lists); other species supported via user-provided S/G2M gene lists.
- You want a publication-ready integrated object plus MultiQC and Quarto QC reports, optionally prepared for cellxgene visualization.
- Reference mapping: projecting new samples onto an existing scVI/scANVI latent space to extend an atlas or transfer labels.

## Do not use when
- You need to go from raw FASTQ to counts — use an upstream quantification pipeline (nf-core/scrnaseq with STARsolo/alevin-fry/cellranger) first, then feed its outputs here.
- Your data is spatial transcriptomics, bulk RNA-seq, ATAC-seq, or CITE-seq protein panels as the primary modality (scdownstream is RNA-count centric).
- You want de novo trajectory/pseudotime or RNA velocity as the main output — those are not part of this workflow.
- You only need a single sample with no batch correction — you can still run it, but most of the value (integration) does not apply.
- You are doing variant calling, assembly, or bulk differential expression.

## Analysis outline
1. **Format unification** — convert RDS/CSV/H5 inputs to H5AD; optionally unify gene symbols via Ensembl/MyGene.
2. **Empty droplet removal** — if only an `unfiltered` matrix is provided, run CellBender to produce a filtered matrix.
3. **Raw QC report** — per-sample metrics aggregated into MultiQC.
4. **Ambient RNA correction** — DecontX (default), SoupX, CellBender, or scAR; configurable per sample.
5. **Custom QC filtering** — apply `min_genes`, `min_cells`, `min_counts_cell`, `min_counts_gene`, `max_mito_percentage` (per-sample in samplesheet).
6. **Doublet detection** — Scrublet (default), SOLO, DoubletDetection, scDblFinder, SCDS; majority vote via `doublet_detection_threshold`.
7. **Cell cycle scoring** — Tirosh et al. S/G2M scores written to `adata.obs` (human/mouse bundled; custom gene lists supported).
8. **Merge samples** — produce `merged_inner.h5ad` (HVG intersection for integration) and `merged_outer.h5ad` (union, base for final object).
9. **Integration** — one or more of scVI, scANVI, Harmony, BBKNN, Combat, Seurat, PCA, scimilarity, expimap; stores low-dim embeddings in `obsm`.
10. **Cell type annotation** — CellTypist (pretrained models) and/or SingleR against celldex references.
11. **Neighbors + Leiden clustering + UMAP** — per integration method, at one or more resolutions; optionally per-label sub-UMAPs.
12. **Optional downstream** — rank_genes_groups, LIANA cell-cell communication, pseudobulk aggregation, cellxgene prep.
13. **Reporting** — Quarto HTML QC report + MultiQC + final `merged.h5ad`/`merged.rds`/`merged_metadata.csv`.

## Key parameters
- `--input samplesheet.csv` — columns `sample`, `filtered` and/or `unfiltered`; optional `batch_col`, `label_col`, `condition_col`, `min_genes`, `min_cells`, `min_counts_cell`, `min_counts_gene`, `max_mito_percentage`, `expected_cells`, `doublet_rate`, `ambient_correction`, `ambient_corrected_integration`.
- `--species` — `human` (default) or `mouse`; selects bundled cell-cycle gene lists. For other organisms pass `--s_genes` and `--g2m_genes`.
- `--ambient_correction` — `decontx` (default) | `cellbender` | `soupx` | `scar` | `none`. CellBender/SoupX/scAR require an `unfiltered` matrix.
- `--doublet_detection` — comma-separated list from `solo,scrublet,doubletdetection,scds,scdblfinder` (default `scrublet`); `--doublet_detection_threshold` sets the majority-vote count.
- `--integration_methods` — comma-separated from `scvi,scanvi,harmony,bbknn,combat,seurat,scimilarity,pca,expimap` (default `scvi`).
- `--integration_hvgs` — number of HVGs for integration (0 = auto, negative = all genes).
- scVI/scANVI tuning: `--scvi_n_latent` (30), `--scvi_n_hidden` (128), `--scvi_n_layers` (2), `--scvi_gene_likelihood` (`zinb`), `--scvi_dispersion` (`gene`), `--scvi_max_epochs`, `--scvi_categorical_covariates`, `--scvi_continuous_covariates` (e.g. `S_score,G2M_score` to regress out cell cycle).
- `--clustering_resolutions` — e.g. `0.5,1.0` (default); `--cluster_per_label` for per-cell-type sub-clusterings.
- `--celltypist_model` — one or more CellTypist model names (e.g. `Adult_Human_Skin`).
- `--celldex_reference` — CSV describing SingleR celldex references (columns `id,label,reference,version` or path to tar).
- Reference mapping: `--scvi_model` / `--scanvi_model` (pretrained `.pt`), `--base_adata` (prior integrated `.h5ad`), `--base_embeddings`, `--base_label_col`, `--base_condition_col`.
- Pipeline toggles: `--qc_only` (stop after QC), `--skip_liana`, `--skip_rankgenesgroups`, `--pseudobulk`, `--prep_cellxgene`, `--use_gpu` (with `-profile gpu`).

## Test data
The bundled `test` profile pulls a small multi-sample scRNA-seq samplesheet from `nf-core/test-datasets` (branch `scdownstream`) containing already-quantified count matrices, together with a SingleR celldex reference CSV. It runs integration with `scvi,harmony,bbknn,combat`, doublet detection with `solo,scrublet,scds,scdblfinder`, CellTypist model `Adult_Human_Skin`, 500 HVGs, and drastically reduced neural-net training (`scvi_max_epochs=2`, CellBender `--epochs 2`) to fit within 4 CPUs / 15 GB RAM / 1 h. Running `-profile test,docker` is expected to produce per-sample preprocessing outputs under `preprocess/`, merged and integrated H5ADs under `combine/`, CellTypist and SingleR annotations under `celltypes/`, Leiden/UMAP results under `cluster_dimred/`, a final `finalize/merged.h5ad`, `finalize/merged.rds`, `finalize/merged_metadata.csv`, plus a `multiqc/multiqc_report.html` and a Quarto `reports/qc-report.html`.

## Reference workflow
nf-core/scdownstream (development version, template 3.5.1; https://github.com/nf-core/scdownstream). Based on learnings from panpipes, scFlow, scRAFIKI/SIMBA, and YASCP. Requires Nextflow ≥ 25.10.0 and a container engine (Docker, Singularity, Apptainer, Podman, Charliecloud, Shifter, or Conda).
