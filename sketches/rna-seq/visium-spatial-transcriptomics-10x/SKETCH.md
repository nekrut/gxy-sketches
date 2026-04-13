---
name: visium-spatial-transcriptomics-10x
description: "Use when you need to process and analyze 10x Genomics Visium (v1/v2/HD)\
  \ spatial transcriptomics data \u2014 either from raw FASTQ + tissue images via\
  \ Space Ranger or from already-processed Space Ranger outputs \u2014 producing QC,\
  \ normalization, clustering and spatially variable genes per sample."
domain: rna-seq
organism_class:
- vertebrate
- eukaryote
input_data:
- 10x-visium-fastq
- tissue-image
- spaceranger-outs
source:
  ecosystem: nf-core
  workflow: nf-core/spatialvi
  url: https://github.com/nf-core/spatialvi
  version: dev
  license: MIT
tools:
- spaceranger
- scanpy
- anndata
- spatialdata
- squidpy
- quarto
- multiqc
tags:
- spatial-transcriptomics
- visium
- 10x
- visium-hd
- cytassist
- ffpe
- scanpy
- squidpy
- spatialdata
test_data: []
expected_output: []
---

# 10x Visium spatial transcriptomics analysis

## When to use this sketch
- User has 10x Genomics Visium spatial transcriptomics data (Visium v1, v2, or Visium HD) from human or mouse tissue sections.
- Input is either raw FASTQ directories plus tissue images (brightfield, Cytassist, fluorescence) that need Space Ranger, or already-processed Space Ranger `outs/` directories.
- Tissue types include FFPE, fresh-frozen, or Cytassist samples with brightfield/fluorescence imagery.
- Goal is per-spot QC and filtering, normalization, dimensionality reduction, Leiden clustering, and detection of spatially variable genes, with per-sample HTML reports.
- Optional per-experiment aggregation: merging or batch-integrating multiple Visium samples into a single SpatialData object.

## Do not use when
- Data is single-cell RNA-seq without spatial coordinates (use a scRNA-seq sketch, e.g. Cell Ranger / Scanpy-based).
- Data is from a non-Visium spatial platform (Slide-seq, MERFISH, Xenium, Stereo-seq, Visium CytAssist HD for a platform-specific pipeline).
- You need bulk RNA-seq quantification and differential expression (use an `rna-seq-bulk` sketch).
- Organism is not human or mouse AND you need to run Space Ranger — Space Ranger only officially supports human/mouse references.
- You only need to run Space Ranger with no downstream analysis — call `spaceranger count` directly.

## Analysis outline
1. Parse samplesheet; auto-detect whether it describes raw data (`fastq_dir` + image + slide/area) or pre-processed data (`spaceranger_dir`).
2. If raw: optionally un-tar FASTQ archives, then run **Space Ranger** `count` with the given slide/area (or `--unknown-slide`), probeset (FFPE/Cytassist), and reference (auto-downloads GRCh38 by default).
3. Load Space Ranger `outs/` into a **SpatialData**/**AnnData** object; for Visium HD, select the bin size via `--hd_bin_size` (2, 8, or 16 µm).
4. **Quality control & filtering** with Scanpy: drop spots below UMI/gene thresholds, drop genes expressed in too few spots, filter on mitochondrial/ribosomal/hemoglobin content. Rendered as a Quarto HTML report.
5. **Normalization, HVG selection, PCA, neighbors, UMAP, Leiden clustering** with Scanpy (Quarto clustering report).
6. **Spatially variable genes** via Squidpy using Moran's I (default) or Geary's C; top N genes plotted in a Quarto report.
7. Write per-sample `sdata_processed.zarr`, `adata_processed.h5ad`, and `spatially_variable_genes.csv`.
8. Optionally **merge** (`--merge_sdata`) or **integrate** (`--integrate_sdata`) per-sample SpatialData objects into one combined object with its own integration/clustering report.
9. Aggregate QC metrics with **MultiQC** and emit Nextflow execution reports.

## Key parameters
- `input`: CSV samplesheet. Raw-data columns: `sample,fastq_dir,image|cytaimage|darkimage|colorizedimage,slide,area` (optional `manual_alignment`, `slidefile`). Processed-data columns: `sample,spaceranger_dir`.
- `spaceranger_reference`: path or URL to a 10x reference tarball; defaults to `refdata-gex-GRCh38-2020-A.tar.gz`.
- `spaceranger_probeset`: required for FFPE / Cytassist runs.
- `hd_bin_size`: `2`, `8` (default), or `16` — only for Visium HD.
- `qc_min_counts` (default 500), `qc_min_genes` (250), `qc_min_spots` (1): spot/gene filters.
- `qc_mito_threshold` (default 20; set to 100 to disable), `qc_ribo_threshold` (0), `qc_hb_threshold` (100): content-based spot filters.
- `cluster_n_hvgs` (2000), `cluster_resolution` (1.0): Leiden clustering controls.
- `svg_autocorr_method`: `moran` (default) or `geary`; `n_top_svgs` (14): SVG reporting.
- `merge_sdata`, `integrate_sdata`, `integration_n_hvgs` (2000), `integration_cluster_resolution` (1.0): multi-sample aggregation.
- Space Ranger typically needs ~64 GB RAM and 8 CPUs per sample; plan resources accordingly.

## Test data
The pipeline's `test` profile uses a single human brain cancer 11 mm FFPE Cytassist Visium v2 sample hosted on `nf-core/test-datasets` (branch `spatialvi`): a samplesheet pointing at raw FASTQs plus a Cytassist tissue image, a provided `probe_set.csv`, and a downsampled chr22-only `homo_sapiens_chr22_reference.tar.gz` Space Ranger reference. QC thresholds are loosened (`qc_min_counts=5`, `qc_min_genes=3`) so the tiny subset passes filtering. A successful run produces, under `results/<SAMPLE>/`, a Space Ranger `outs/` tree, `data/sdata_processed.zarr` and `adata_processed.h5ad`, `data/spatially_variable_genes.csv`, and rendered Quarto reports `reports/quality_controls.html`, `reports/clustering.html`, and `reports/spatially_variable_genes.html`, plus a top-level `multiqc/multiqc_report.html` and `pipeline_info/` execution reports. The `test_full` profile runs the same workflow on a full-size public Visium sample for AWS CI.

## Reference workflow
nf-core/spatialvi (dev, template 3.5.1) — https://github.com/nf-core/spatialvi. Core tools: Space Ranger 2.x, Scanpy, AnnData, SpatialData, Squidpy, Quarto, MultiQC.
