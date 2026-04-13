---
name: bulk-rnaseq-differential-expression
description: Use when you have a gene-level count matrix from bulk RNA-seq (e.g. nf-core/rnaseq
  output) plus a sample sheet and want DESeq2-based differential expression across
  defined contrasts, with exploratory QC, volcano plots, optional GSEA/g:Profiler
  pathway enrichment, and an HTML/Shiny report. Assumes groups of samples with replicates
  and no need for raw read processing.
domain: rna-seq
organism_class:
- eukaryote
input_data:
- gene-count-matrix
- sample-sheet
- contrasts-csv
- gtf
source:
  ecosystem: nf-core
  workflow: nf-core/differentialabundance
  url: https://github.com/nf-core/differentialabundance
  version: 1.5.0
  license: MIT
tools:
- DESeq2
- limma
- GSEA
- gprofiler2
- shinyngs
- RMarkdown
tags:
- rna-seq
- differential-expression
- deseq2
- gsea
- pathway-enrichment
- bulk
- transcriptomics
test_data: []
expected_output: []
---

# Bulk RNA-seq differential expression with DESeq2

## When to use this sketch
- You already have a gene-level count matrix (e.g. `salmon.merged.gene_counts.tsv` from nf-core/rnaseq, or any tximport-processed counts) and a sample sheet keyed by sample ID.
- You want group-wise differential expression between two or more conditions defined as contrasts, optionally with blocking/batch covariates.
- You want exploratory QC (PCA, sample dendrogram, density/boxplot, MAD outlier detection) plus standard differential outputs (volcano plots, filtered/unfiltered results tables).
- You optionally want gene set enrichment (GSEA with a GMT/GMX) and/or pathway over-representation (g:Profiler) on top of the DE results.
- You want a self-contained HTML report and optionally a ShinyNGS app for interactive exploration.

## Do not use when
- You are starting from raw FASTQs and still need alignment/quantification — run nf-core/rnaseq first and feed its gene counts into this sketch.
- Your data are Affymetrix CEL files or GEO SOFT matrices — use the microarray sibling sketch (`microarray-differential-expression-affy`) which invokes the same pipeline with `-profile affy` or `--study_type geo_soft_file`.
- Your data are MaxQuant `proteinGroups.txt` label-free proteomics — use the `maxquant-proteomics-differential-abundance` sibling sketch (`--study_type maxquant`, Proteus backend).
- You are doing single-cell differential expression — this sketch assumes bulk observations with replicates.
- You need transcript-level or isoform-switch analysis — this pipeline operates at the feature (gene) level only.

## Analysis outline
1. Parse sample sheet, contrasts file, gene count matrix, and GTF; cross-check sample IDs and feature IDs for consistency.
2. Derive a feature annotation table from the GTF (gene_id, gene_name, gene_biotype) unless a `--features` TSV is supplied.
3. Filter low-abundance features using `filtering_min_abundance` / `filtering_min_samples` (or proportion equivalents).
4. Run DESeq2 per contrast: `DESeq()` with Wald test, size-factor normalisation, optional transcript-length offset via `--transcript_length_matrix`, and `lfcShrink(type="ashr")` for shrunken fold changes.
5. Produce a variance-stabilised matrix (`vst` by default) for downstream exploratory plots.
6. Run exploratory analysis: PCA (2D/3D), sample-sample correlation dendrogram, density/boxplots, MAD outlier detection.
7. Produce differential plots (volcano) and write `*.deseq2.results.tsv` plus a filtered table using the fold-change / q-value thresholds.
8. Optionally run GSEA (phenotype permutation, Signal2Noise ranking) against user GMT files, and/or g:Profiler2 pathway enrichment with the filtered matrix as background.
9. Render the R Markdown HTML report and package an Rmd + inputs zip; optionally build (and deploy) a ShinyNGS app for interactive mining.

## Key parameters
- `study_type: rnaseq` and `-profile rnaseq` — selects DESeq2 backend and RNA-seq assay naming.
- `--input samplesheet.csv` with `observations_id_col` (default `sample`) matching matrix column headers.
- `--matrix gene_counts.tsv` plus `--transcript_length_matrix gene_lengths.tsv` when feeding raw nf-core/rnaseq counts (≥3.12.0); otherwise use `gene_counts_length_scaled.tsv`.
- `--contrasts contrasts.csv` with columns `id,variable,reference,target,blocking` (blocking is semicolon-delimited, may be empty); optional `exclude_samples_col` / `exclude_samples_values`.
- `--gtf species.gtf` for feature annotation; `features_id_col: gene_id`, `features_name_col: gene_name`.
- Filtering: `filtering_min_abundance` (default 1), `filtering_min_samples` (default 1), `filtering_grouping_var` for group-aware minimums.
- DESeq2: `deseq2_test: Wald`, `deseq2_fit_type: parametric`, `deseq2_sf_type: ratio`, `deseq2_alpha: 0.1`, `deseq2_vs_method: vst`, `deseq2_vst_nsub: 1000` (lower for small test matrices), `deseq2_shrink_lfc: true`.
- Differential thresholds for reporting/volcano: `differential_min_fold_change: 2`, `differential_max_qval: 0.05`, `differential_fc_column: log2FoldChange`, `differential_qval_column: padj`.
- Large-cohort speedups: `--differential_subset_to_contrast_samples` and disabling `PLOT_*`/`RMARKDOWNNOTEBOOK`/`SHINYNGS_APP` via `ext.when = false`.
- Enrichment: `gsea_run: true` + `--gene_sets_files *.gmt` (uses phenotype permutation, Signal2Noise metric), or `gprofiler2_run: true` + `gprofiler2_organism: hsapiens|mmusculus|…`.
- Reporting: `shinyngs_build_app: true` (default) writes `shinyngs_app/<study>/app.R`; set `shinyngs_deploy_to_shinyapps_io` with `SHINYAPPS_TOKEN`/`SHINYAPPS_SECRET` secrets to publish.

## Test data
The `test` profile pulls a cut-down nf-core/rnaseq output for SRP254919 (Mus musculus): `SRP254919.samplesheet.csv` (sample, condition, replicate, batch columns), `SRP254919.salmon.merged.gene_counts.top1000cov.tsv` (top-1000-coverage gene count matrix), a spoofed `SRP254919.spoofed_lengths.tsv` transcript-length matrix, a `SRP254919.contrasts.csv` defining the condition contrast, plus the Ensembl `Mus_musculus.GRCm38.81.gtf.gz` and an MSigDB `mh.all.v2022.1.Mm.symbols.gmt` hallmark set for GSEA. Running with `-profile test,docker` exercises filtering (`filtering_min_abundance=10`), DESeq2 differential analysis (`deseq2_vst_nsub=500` for the small matrix), GSEA, the HTML report, and a ShinyNGS app bundle. Expected outputs include `report/<study_name>.html`, `tables/differential/*.deseq2.results.tsv` (and `*_filtered.tsv`), `tables/processed_abundance/*.normalised_counts.tsv` and `*.vst.tsv`, `plots/exploratory/<var>/png/{pca2d,pca3d,boxplot,density,sample_dendrogram,mad_correlation}.png`, `plots/differential/<contrast>/png/volcano.png`, `tables/gsea/<contrast>/<contrast>.gsea_report_for_*.tsv`, and `shinyngs_app/<study_name>/{app.R,data.rds}`.

## Reference workflow
nf-core/differentialabundance v1.5.0 (MIT) — https://github.com/nf-core/differentialabundance. Invoke with `nextflow run nf-core/differentialabundance -r 1.5.0 -profile rnaseq,<container> --input samplesheet.csv --contrasts contrasts.csv --matrix gene_counts.tsv --gtf species.gtf --outdir results`. See the pipeline's `docs/usage.md` and `nextflow_schema.json` for the full parameter surface; DESeq2 (Love et al. 2014) is the core differential engine, with optional GSEA (Subramanian et al. 2005) and gprofiler2 (Kolberg et al. 2020) for enrichment.
