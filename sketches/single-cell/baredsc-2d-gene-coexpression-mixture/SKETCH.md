---
name: baredsc-2d-gene-coexpression-mixture
description: Use when you need to quantify and deconvolve the joint expression distribution
  of two genes across single cells using Bayesian Gaussian mixture models on log-normalized
  counts, identifying co-expression subpopulations and the optimal number of components
  while accounting for sampling noise in sparse scRNA-seq data.
domain: single-cell
organism_class:
- eukaryote
input_data:
- scrna-counts-tabular
source:
  ecosystem: iwc
  workflow: 'Single-Cell Mixture Analysis: baredSC 2D Log-Normalized Models'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/scRNAseq/baredsc
  version: '0.6'
  license: MIT
tools:
- baredSC
- baredsc_2d
- baredsc_combine_2d
tags:
- single-cell
- scRNA-seq
- gaussian-mixture
- bayesian
- MCMC
- co-expression
- subpopulations
- log-normalized
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

# baredSC 2D Gaussian mixture for gene co-expression

## When to use this sketch
- You have single-cell RNA-seq counts and want to model the joint probability density of two genes while correcting for Poisson sampling noise.
- You want to discover co-expression subpopulations (e.g. double-positive, double-negative, single-positive cells) without hard clustering.
- You want a principled Bayesian comparison across mixture models with 1..N 2D Gaussians and a combined posterior across model sizes.
- Your input is a tabular file where rows are cells and columns include `nCount_RNA` plus raw counts for the two genes of interest (e.g. exported from a Seurat object).
- You need log-normalized-scale output (Seurat-style, targetSum=10000) rather than raw-count scale.

## Do not use when
- You only care about a single gene's distribution — use the sibling `baredsc-1d-gene-expression-mixture` sketch instead.
- You want standard clustering / UMAP / marker detection — use a Scanpy or Seurat clustering workflow.
- You need differential expression between predefined groups — use a pseudobulk or MAST-style DE workflow.
- Your input is a full AnnData/10x matrix and you have not yet extracted a per-cell tabular with `nCount_RNA` and the two target gene columns.
- You need raw-count-scale modeling rather than log-normalized modeling.

## Analysis outline
1. Accept a tabular of per-cell raw counts with a header row containing at least `nCount_RNA`, the x-axis gene column, and the y-axis gene column.
2. Generate a parameter list of integers 1..N (the `generate_param_list_one_to_number` subworkflow) to drive one baredSC run per candidate component count.
3. For each k in 1..N, run `baredSC 2d` (MCMC) on the tabular with Seurat log-normalization (targetSum=10000), a 25x25 grid, xmin/ymin=0, and user-supplied xmax/ymax, producing per-model QC plots, the MCMC numpy archive, effective sample size (neff), and 2D PDFs. Automatic restart is enabled with `minNeff=200`.
4. Run `Combine multiple 2D Models` (`baredsc_combine_2d`) across all per-k outputs to produce a single combined 2D PDF, flat PDF table, combined plot, and (optionally) a p-value assessment of deviation from independence.
5. Emit QC plots, neff, numpy archives, combined 2D PDF tables, and the combined plot as workflow outputs.

## Key parameters
- `geneXColName` / `geneYColName`: exact column names in the tabular header for the two genes (must also contain `nCount_RNA`).
- `xmax` / `ymax`: maximum log-normalized value explored on each axis; set large enough that the PDF is ~0 at the boundary. Typical range 2–4.
- `nnorm` (per run): number of 2D Gaussians; driven by the 1..N sweep. `N ≈ 4` is usually sufficient.
- `scale.type = Seurat`, `targetSum = 10000`: log-normalization scheme (fixed).
- Grid: `nx = ny = 25`, `xmin = ymin = 0`, `minScalex = minScaley = 0.1` (fixed defaults from the workflow).
- MCMC: `nsampMCMC = 100000`, `seed = 1`, `automaticRestart.minNeff = 200`.
- `advanced.getPVal` (combine step): boolean — enable to compute an independence p-value (uses fewer samples for plots).
- Plotting: `nsampInPlot = 100000`, `image_file_format = png`.

## Test data
The test profile uses `test-data/nih3t3_generated_2d_2.txt`, a synthetic NIH/3T3-style per-cell tabular with an `nCount_RNA` column plus gene columns named like `0.5_0_0_0.5_x` (the 1D test uses that column; the 2D variant is driven by analogous synthetic gene columns). The sweep goes up to 4 Gaussians with an xmax of 2.5 on the log-normalized axis. Expected outputs include a collection of per-k baredSC numpy archives (sizes growing with k, from ~1.3 MB at k=1 to ~28 MB at k=4), per-k QC plots (convergence, corner, posterior `p`), per-k `neff` text files each containing a single numeric line in the expected order-of-magnitude ranges, and combined outputs: `combined_pdf` (tabular with header `x\tlow\tmean\thigh\tmedian` and a `0.0125` grid point), `combined_other_outputs` (individuals, means with ~99998 lines, posterior_andco, posterior_individuals, posterior_per_cell, with_posterior), and `combined_plot` compared against `test-data/combined_1d_plot.png` with `sim_size` similarity.

## Reference workflow
IWC `scRNAseq/baredsc/baredSC-2d-logNorm.ga`, release 0.6 (2025-03-10), by Lucille Delisle. Tools: `baredsc_2d` 1.1.3+galaxy0 and `baredsc_combine_2d` 1.1.3+galaxy0 from the IUC toolshed; driven by the embedded `generate_param_list_one_to_number` subworkflow (text_processing 9.5+galaxy0, addValue 1.0.0, Cut1 1.0.2, split_file_to_collection 0.5.2, param_value_from_file 0.1.0). Upstream baredSC method: Delisle et al., baredSC Bayesian approach to single-cell RNA-seq gene expression distributions.
