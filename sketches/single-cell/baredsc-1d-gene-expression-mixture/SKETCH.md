---
name: baredsc-1d-gene-expression-mixture
description: Use when you need to infer the true probability density function (PDF)
  of a single gene's log-normalized expression across single cells using a Bayesian
  Gaussian mixture model, and decide how many subpopulations (1..N components) best
  describe it. Starts from a per-cell tabular count table (with nCount_RNA) rather
  than a full AnnData/Seurat object.
domain: single-cell
organism_class:
- eukaryote
input_data:
- scrna-count-table-tabular
source:
  ecosystem: iwc
  workflow: 'Single-Cell Mixture Analysis: baredSC 1D Log-Normalized Models'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/scRNAseq/baredsc
  version: '0.6'
  license: MIT
  slug: scRNAseq--baredsc--baredSC-2d-logNorm
tools:
- name: baredSC_1d
- name: baredSC_combine_1d
tags:
- single-cell
- scrna-seq
- bayesian
- mcmc
- gaussian-mixture
- gene-expression
- pdf
- subpopulations
- lognorm
test_data: []
expected_output:
- role: baredsc_numpy
  description: Content assertions for `baredsc_numpy`.
  assertions:
  - 'split_file_000000.tabular: has_size: {''value'': 1257919, ''delta'': 100000}'
  - 'split_file_000001.tabular: has_size: {''value'': 1601519, ''delta'': 100000}'
  - 'split_file_000002.tabular: has_size: {''value'': 2180423, ''delta'': 200000}'
  - 'split_file_000003.tabular: has_size: {''value'': 28234812, ''delta'': 2000000}'
- role: baredsc_neff
  description: Content assertions for `baredsc_neff`.
  assertions:
  - 'split_file_000000.tabular: has_n_lines: {''n'': 1}'
  - 'split_file_000000.tabular: has_line_matching: {''expression'': ''80[0-9][0-9].[0-9]*''}'
  - 'split_file_000001.tabular: has_n_lines: {''n'': 1}'
  - 'split_file_000001.tabular: has_line_matching: {''expression'': ''13[0-9][0-9].[0-9]*''}'
  - 'split_file_000002.tabular: has_n_lines: {''n'': 1}'
  - 'split_file_000002.tabular: has_line_matching: {''expression'': ''2[0-9][0-9].[0-9]*''}'
  - 'split_file_000003.tabular: has_n_lines: {''n'': 1}'
  - 'split_file_000003.tabular: has_line_matching: {''expression'': ''[7-9][0-9][0-9].[0-9]*''}'
- role: combined_other_outputs
  description: Content assertions for `combined_other_outputs`.
  assertions:
  - 'individuals: has_size: {''value'': 108407, ''delta'': 10000}'
  - 'means: has_n_lines: {''n'': 99998, ''delta'': 4000}'
  - 'means: has_line_matching: {''expression'': ''6.[0-9]*e-01''}'
  - 'posterior_andco: has_size: {''value'': 197980, ''delta'': 10000}'
  - 'posterior_individuals: has_size: {''value'': 105262, ''delta'': 10000}'
  - 'posterior_per_cell: has_n_lines: {''n'': 2362}'
  - 'posterior_per_cell: has_line_matching: {''expression'': ''mu\tsd''}'
  - 'with_posterior: has_size: {''value'': 234303, ''delta'': 20000}'
- role: combined_pdf
  description: Content assertions for `combined_pdf`.
  assertions:
  - "has_line: x\tlow\tmean\thigh\tmedian"
  - "has_text: 0.0125\t"
- role: combined_plot
  path: expected_output/combined_1d_plot.png
  description: Expected output `combined_plot` from the source workflow test.
  assertions: []
---

# baredSC 1D log-normalized gene expression mixture modeling

## When to use this sketch
- You already have a single-cell count matrix (e.g. from a Seurat/Scanpy object) and want a statistically principled PDF of one gene's expression, correcting for sampling noise.
- You suspect a gene of interest has bimodal or multimodal expression (e.g. on/off, graded subpopulations) and want Bayesian model-averaged evidence across 1..N Gaussian components.
- You can export a tabular file where rows are cells, with a header including `nCount_RNA` and the gene column (raw counts).
- You want the analysis delivered in log-normalized (Seurat-style, targetSum=10000) space, with combined posterior across all tested component counts.

## Do not use when
- You need the joint PDF of two genes or their correlation — use the sibling `baredsc-2d-gene-expression-mixture` sketch instead.
- You only need descriptive UMAP/violin plots of expression — use a standard Scanpy/Seurat QC/visualization workflow, baredSC is overkill.
- You want to call differentially expressed genes between clusters — use a DE workflow (e.g. Seurat FindMarkers, edgeR, DESeq2 pseudobulk), not baredSC.
- Your input is raw 10x FASTQ or a `.h5ad`/`.rds` that has not been reduced to a per-cell tabular of the gene(s) of interest — pre-process first.
- You want raw-count scale modeling rather than log-normalized — baredSC also supports a `raw` scale mode, but this sketch pins `scale=Seurat, targetSum=10000`.

## Analysis outline
1. Accept a tabular count table (one row per cell, header required, must contain `nCount_RNA` and the target gene column).
2. Generate a parameter list of integers 1..N (N = user-supplied max Gaussians) via a small text-processing subworkflow (`generate_param_list_one_to_number`).
3. Run `baredSC 1d` (MCMC Bayesian fit) once per component count, producing per-model PDF, QC plots, neff, log-evidence and a `.npz` numpy result.
4. Run `Combine multiple 1D Models` (`baredsc_combine_1d`) to merge all per-component fits into a single evidence-weighted posterior PDF and plot.
5. Inspect combined PDF table, per-cell posterior, and diagnostic plots to decide the effective number of modes.

## Key parameters
- `geneColName`: name of the gene column in the header (string, required).
- `MCMC.xmin`: `0.0` (log-normalized floor).
- `MCMC.xmax`: user-supplied maximum log-normalized expression to explore; must be large enough that the PDF has decayed to ~0.
- `MCMC.nx`: `100` (number of bins on the x axis).
- `MCMC.minScalex`: `0.1` (minimum Gaussian width).
- `MCMC.scale.type`: `Seurat` with `targetSum=10000` (log-normalization).
- `MCMC.nnorm`: iterated 1..N via the param-list subworkflow.
- `MCMC.nsampMCMC`: `100000` MCMC samples.
- `MCMC.automaticRestart.minNeff`: `200.0` — restart until effective sample size ≥ 200.
- `MCMC.seed`: `1` for reproducibility.
- `advanced.osampx`: `10`, `osampxpdf`: `5`, `nis`: `1000`, `coviscale`: `1.0`.
- `filter.nb`: `0` (no cell filtering on total counts).
- Max number of Gaussians `N`: typically `4` is enough (per README).

## Test data
The test job uses `test-data/nih3t3_generated_2d_2.txt`, a tabular file of simulated NIH3T3-like single-cell expression with a header including a `0.5_0_0_0.5_x` gene column. The workflow is run with `Gene name = 0.5_0_0_0.5_x`, `Maximum value in logNorm = 2.5` and `Maximum number of Gaussians to study = 4`, so baredSC_1d fits 1-, 2-, 3- and 4-Gaussian models and combines them. Expected outputs include a collection of four per-model `.npz` numpy results (sizes ~1.26 MB, 1.6 MB, 2.18 MB, 28.2 MB within tolerances), per-model QC plots (convergence, corner, p), neff files whose single line matches specific effective-sample-size regexes (e.g. ~8000 for the 1-Gaussian fit, ~1300 for 2-Gaussian, ~200+ for the larger models), a combined posterior PDF table with header `x\tlow\tmean\thigh\tmedian` containing the `0.0125` x bin, and a combined 1D PDF plot compared against a golden `combined_1d_plot.png` at 10% size tolerance.

## Reference workflow
IWC — `workflows/scRNAseq/baredsc/baredSC-1d-logNorm.ga`, release 0.6 (2025-03-10). Uses `baredsc_1d` and `baredsc_combine_1d` tools at version `1.1.3+galaxy0` from the IUC Galaxy Tool Shed. Author: Lucille Delisle (ORCID 0000-0002-1964-4960), MIT licensed.
