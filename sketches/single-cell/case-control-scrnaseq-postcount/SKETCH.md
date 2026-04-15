---
name: case-control-scrnaseq-postcount
description: 'Use when you have post-demultiplex sparse gene-cell count matrices (e.g.
  CellRanger raw_feature_bc_matrix outputs) from multiple human or mouse single-cell
  / single-nucleus RNA-seq samples and need a full case/control secondary analysis:
  per-sample QC, ambient-RNA and doublet removal, merge, LIGER batch integration,
  UMAP/tSNE, Leiden/Louvain clustering, automated cell-type annotation, per-cell-type
  differential expression, pathway enrichment, and Dirichlet cell-composition modeling.'
domain: single-cell
organism_class:
- human
- mouse
- eukaryote
input_data:
- 10x-cellranger-matrix
- sample-sheet-tsv
- manifest-tsv
- celltype-reference-ctd
source:
  ecosystem: nf-core
  workflow: nf-core/scflow
  url: https://github.com/nf-core/scflow
  version: dev
  license: MIT
  slug: scflow
tools:
- name: scFlow
- name: emptyDrops
- name: DoubletFinder
- name: LIGER
- name: uwot-UMAP
- name: Rtsne
- name: Leiden
- name: Louvain
- name: EWCE
- name: MAST
- name: WebGestaltR
- name: DirichletReg
tags:
- scrna-seq
- snrna-seq
- case-control
- dge
- pathway-enrichment
- celltype-annotation
- batch-integration
- nf-core
- deprecated
test_data: []
expected_output: []
---

# Case/control single-cell RNA-seq secondary analysis (post-count matrices)

> Note: the source pipeline nf-core/scflow was deprecated on 2024-06-13 in favour of nf-core/scdownstream. The recipe below still captures the analytical class it implements; prefer nf-core/scdownstream for new work when available.

## When to use this sketch
- You already have gene-cell count matrices (CellRanger `raw_feature_bc_matrix` folders with `matrix.mtx.gz`, `features.tsv.gz`, `barcodes.tsv.gz`) from several human or mouse scRNA-seq / snRNA-seq samples.
- The experimental design is a case/control (or graded-exposure) comparison with per-sample metadata such as diagnosis, sex, age, batch/seqdate.
- You need the complete secondary-analysis arc: ambient-RNA filtering, doublet removal, merge + inter-sample QC, batch integration, dimensionality reduction, clustering, automated cell-type annotation, per-cell-type differential gene expression, impacted-pathway analysis, and differential cell-type composition (Dirichlet).
- You want interactive per-step HTML reports plus a fully annotated `SingleCellExperiment` object for downstream tertiary analysis in R/scFlow.

## Do not use when
- You are starting from raw FASTQs and still need alignment / UMI counting — run a pre-processing pipeline (e.g. nf-core/scrnaseq, Cell Ranger, Alevin-fry, STARsolo) first and feed its matrices in here.
- You have spatial transcriptomics, CITE-seq surface-protein panels, ATAC, or multiome data — pick a modality-specific sketch.
- You have only one or two samples and no case/control contrast — trim to a simpler per-sample QC + clustering sketch; the DGE/Dirichlet/IPA stages here require replication across groups.
- Your species is neither human nor mouse — scFlow only supports `species: human` or `species: mouse`.
- You want trajectory/pseudotime, RNA velocity, or cell-cell communication as the primary output — those are not modeled here.

## Analysis outline
1. `SCFLOW_CHECKINPUTS` — validate the manifest TSV (key → matrix filepath) against the sample-sheet TSV (per-sample metadata) and the parameter config.
2. `SCFLOW_QC` — per-sample QC on each matrix: ambient-RNA / empty-droplet profiling with emptyDrops, library-size / feature / mito / ribo thresholding (fixed or MAD-adaptive), doublet/multiplet calling with DoubletFinder, and a per-sample HTML QC report + post-QC `SingleCellExperiment`.
3. `SCFLOW_MERGEQCTABLES` + `SCFLOW_MERGE` — merge per-sample SCEs, compute inter-sample QC metrics, flag outlier samples, emit the merged QC report.
4. `SCFLOW_INTEGRATE` + `SCFLOW_REPORTINTEGRATED` — batch-correct / integrate with LIGER (iNMF) and produce an integration-performance report (qualitative + quantitative metrics across user-supplied categorical covariates).
5. `SCFLOW_REDUCEDIMS` — dimensionality reduction on the integrated embedding via UMAP (2D + 3D) and/or tSNE, with optional regression of nCount_RNA and pc_mito.
6. `SCFLOW_CLUSTER` — Leiden (default) or Louvain community detection on the reduced-dim kNN graph.
7. `SCFLOW_MAPCELLTYPES` + `SCFLOW_FINALIZE` — automated cell-type annotation using an EWCE cell-type reference (`ctd_path` zip), per-cluster marker-gene characterization, and emission of the final annotated SCE plus cell-type metrics HTML report. Cell-type labels can be manually curated by re-running with a revised `celltype_mappings.tsv`.
8. `SCFLOW_DGE` — per-cell-type differential gene expression (default MAST zlm with bayesglm) against a user-specified dependent variable, with confounders and optional pseudobulk.
9. `SCFLOW_IPA` — impacted-pathway / enrichment analysis on each DE gene list (default WebGestaltR ORA against GO Biological Process; KEGG, Reactome, WikiPathway, GO CC/MF, ROntoTools, enrichR also supported).
10. `SCFLOW_DIRICHLET` — Dirichlet regression modeling of relative cell-type proportions across the dependent variable, with a dedicated HTML report.

## Key parameters
- `--manifest` / `--input` — two-column `key`/`filepath` TSV pointing at CellRanger matrix folders, and the per-sample metadata TSV. `qc_key_colname` in the sample sheet must hold the same keys as `manifest`.
- `species: human | mouse` — only these two are supported.
- `qc_factor_vars` — comma-separated sample-sheet columns to force to factor (critical for numeric-looking batch columns like `seqdate`, `capdate`, `prepdate`).
- QC thresholds: `qc_min_library_size=250`, `qc_min_features=100`, `qc_max_library_size=adaptive`, `qc_max_features=adaptive`, `qc_max_mito=adaptive`, `qc_nmads=4` (MADs used for adaptive thresholding), `qc_drop_mito=true`, `qc_drop_ribo=false`, `qc_drop_unmapped=true`.
- Ambient RNA (emptyDrops): `amb_find_cells=true`, `amb_lower=100`, `amb_retain=auto`, `amb_alpha_cutoff=0.001`, `amb_niters=10000`, `amb_expect_cells=3000`.
- Doublets (DoubletFinder): `mult_singlets_method=doubletfinder`, `mult_vars_to_regress_out=nCount_RNA,pc_mito`, `mult_pca_dims=10`, `mult_var_features=2000`, `mult_dpk=8` (doublets-per-thousand, 10x rule of thumb; set `mult_doublet_rate` to a fixed fraction to override), `mult_pK=0.02`.
- Integration (LIGER): `integ_method=Liger`, `integ_unique_id_var=manifest`, `integ_num_genes=3000`, `integ_k=30`, `integ_lambda=5`, `integ_resolution=1`, `integ_categorical_covariates` should list the metadata columns you want evaluated for mixing (e.g. `manifest,diagnosis,sex,seqdate`).
- Dim-reduction: `reddim_input_reduced_dim=PCA,Liger`, `reddim_reduction_methods=tSNE,UMAP,UMAP3D`, `reddim_vars_to_regress_out=nCount_RNA,pc_mito`, `reddim_umap_pca_dims=30`, `reddim_umap_n_neighbors=35`, `reddim_umap_min_dist=0.4`.
- Clustering: `clust_cluster_method=leiden`, `clust_reduction_method=UMAP_Liger`, `clust_res=0.001`, `clust_k=50`.
- Cell-type annotation: `ctd_path` (EWCE cell-type data zip; default is the scFlow ctd_v1 on figshare), `cta_unique_id_var=individual`, `cta_celltype_var=cluster_celltype`, `cta_top_n=5`.
- DGE: `dge_de_method=MASTZLM`, `dge_mast_method=bayesglm`, `dge_dependent_var=group`, `dge_ref_class=Control`, `dge_confounding_vars=cngeneson,seqdate,pc_mito`, `dge_random_effects_var=NULL`, `dge_min_counts=1`, `dge_min_cells_pc=0.1`, `dge_pseudobulk=false`, `dge_fc_threshold=1.1`, `dge_pval_cutoff=0.05`.
- IPA: `ipa_enrichment_tool=WebGestaltR`, `ipa_enrichment_method=ORA`, `ipa_enrichment_database=GO_Biological_Process` (alternatives: KEGG, Reactome, Wikipathway, GO Cellular/Molecular).
- Dirichlet: `dirich_dependent_var=group`, `dirich_ref_class=Control`, `dirich_var_order=Control,Low,High`.
- Runtime: invoke via `nextflow run nf-core/scflow --manifest Manifest.tsv --input SampleSheet.tsv -c scflow_params.config -profile <docker|singularity|conda|institute>`; use `-resume` when tuning clustering / dim-reduction / QC parameters because all steps are cached.

## Test data
The `test` profile (`conf/test.config`) dynamically downloads a minimal scFlow test bundle from nf-core/test-datasets (`refs/Manifest.txt`, `refs/SampleSheet.tsv`, `refs/reddim_genes.yml`) together with the EWCE `ctd_v1.zip` cell-type reference and an ensembl-mappings TSV; resources are capped at 2 CPUs / 6.7 GB / 48 h so the run fits in GitHub Actions. A successful end-to-end test produces a populated `results/` tree containing per-sample QC HTML reports and post-QC SCEs under `quality_control/<key>/`, a merged QC report under `merged/` and `reports/merged_report/`, an integration report, a cell-type metrics report, a final annotated `SCE` under `final/SCE/final_sce` with `celltypes.tsv`, per-cell-type DGE tables and volcano plots under `DGE/<cluster_celltype>/`, pathway-enrichment outputs under `IPA/<cluster_celltype>/<enrichment_tool>/`, a Dirichlet composition report, reduced-dim gene-expression plots under `plots/reddim_gene_plots/`, a `tables/celltype_mappings/celltype_mappings.tsv`, and standard Nextflow pipeline-info reports. A `test_full` profile exercises the same graph on a full-sized AWS dataset.

## Reference workflow
nf-core/scflow (`dev`, MIT) — https://github.com/nf-core/scflow. Method described in Khozoie et al., _bioRxiv_ 2021, doi:10.22541/au.162912533.38489960/v1. The pipeline was deprecated on 2024-06-13; for new projects consider nf-core/scdownstream as the maintained successor, but the analytical recipe above remains the class this sketch selects on.
