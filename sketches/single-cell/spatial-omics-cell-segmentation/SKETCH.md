---
name: spatial-omics-cell-segmentation
description: "Use when you need to segment cells and build a unified SpatialData object\
  \ from raw image-based spatial omics runs (Xenium, MERSCOPE, CosMx, Visium HD, PhenoCycler,\
  \ MACSima, Hyperion, Molecular Cartography, OME-TIFF) \u2014 running Cellpose/Stardist/Baysor/Proseg/Comseg\
  \ segmentation, aggregating transcripts/channel intensities into cells, and emitting\
  \ a .zarr SpatialData directory plus a Xenium Explorer bundle for downstream single-cell\
  \ analysis."
domain: single-cell
organism_class:
- eukaryote
input_data:
- spatial-omics-raw
- xenium-bundle
- merscope-bundle
- cosmx-bundle
- visium-hd-bundle
- multiplex-imaging-ome-tif
source:
  ecosystem: nf-core
  workflow: nf-core/sopa
  url: https://github.com/nf-core/sopa
  version: dev
  license: MIT
  slug: sopa
tools:
- name: sopa
- name: spatialdata
- name: cellpose
- name: stardist
- name: baysor
- name: proseg
- name: comseg
- name: scanpy
- name: tangram
- name: spaceranger
tags:
- spatial-omics
- spatial-transcriptomics
- multiplex-imaging
- cell-segmentation
- xenium
- merscope
- visium-hd
- cosmx
- phenocycler
- zarr
test_data: []
expected_output: []
---

# Spatial omics cell segmentation and aggregation (Sopa)

## When to use this sketch
- You have a raw per-sample output directory from an image-based spatial omics platform (Xenium, MERSCOPE/Vizgen, CosMx, Visium HD, PhenoCycler/CODEX, MACSima, Hyperion, Molecular Cartography, or a generic OME-TIFF) and need a processed, single-cell resolution `SpatialData` object.
- You want standardized cell segmentation across technologies using one of Cellpose, Stardist, Baysor, Proseg, or Comseg (including combinations such as Cellpose-as-prior + Baysor, or Stardist-as-prior + Proseg).
- You need per-cell transcript counts and/or averaged channel intensities aggregated into an `AnnData` table, optionally followed by Scanpy log1p/HVG/UMAP/Leiden.
- You want a `.explorer` bundle for the 10x Xenium Explorer QC/visualization, plus an `adata.h5ad` extraction for downstream analysis.
- You optionally want cell-type annotation via Tangram (scRNA-seq reference) or a fluorescence marker-to-cell dictionary.

## Do not use when
- You only need to run Space Ranger on Visium/Visium HD FASTQs without segmentation or SpatialData integration — use a dedicated `spaceranger`/`spatialvi` sketch.
- You are working with sequencing-based spatial data that has no image or transcript-coordinate layer suitable for cell segmentation (e.g., Slide-seq, standard low-resolution Visium) — pick a spot-level spatial transcriptomics sketch.
- You already have a segmented SpatialData object and only need downstream clustering/DE/annotation — use a Scanpy/Squidpy analysis sketch.
- You are doing dissociated droplet scRNA-seq (10x Chromium, etc.) — use an scRNA-seq sketch such as `nf-core/scrnaseq`.
- You need H&E histology registration or deep learning pathology models without spatial omics modalities.

## Analysis outline
1. Parse `samplesheet.csv` listing `data_path` (and optional `sample`) per run; for Visium HD use the extended schema with `fastq_dir`, `image`, `cytaimage`, `slide`, `area`.
2. (Visium HD only) Run `spaceranger count` with the provided probeset and reference to produce the aligned spatial bundle.
3. Read the raw vendor bundle into a `SpatialData` object using the Sopa reader selected by `--technology`.
4. (Optional) Run tissue segmentation (`staining` or `saturation` mode) at a chosen image pyramid `level`.
5. Create image/transcript patches (`patch_width_pixel`/`patch_width_microns` with overlap ≈ 2× cell diameter) so segmentation can be parallelized.
6. Run cell segmentation with the tool(s) selected by the technology profile: Cellpose or Stardist on images; Baysor, Proseg, or Comseg on transcripts; optionally chaining an image-based prior into a transcript-based method.
7. Filter low-quality cells by `min_area_pixels2`/`min_area_microns2`, `min_transcripts`, and `min_intensity_ratio`.
8. Aggregate transcripts (counts) and/or channel intensities into each cell (`aggregate_genes`, `aggregate_channels`, `expand_radius_ratio`).
9. (Optional) Cell-type annotation via Tangram against an `.h5ad` scRNA-seq reference, or a fluorescence `marker_cell_dict`.
10. (Optional) Scanpy preprocessing: log1p, HVG, UMAP, Leiden clustering at `resolution`.
11. Write the full `SpatialData` object to `{sample}.zarr` and generate the `{sample}.explorer` bundle (`experiment.xenium`, `adata.h5ad`, `report.html`).

## Key parameters
- `--technology`: one of `xenium`, `merscope`, `cosmx`, `visium_hd`, `molecular_cartography`, `macsima`, `phenocycler`, `hyperion`, `ome_tif`, `toy_dataset`. Drives which reader runs.
- Technology profile (via `-profile`): pick a preset such as `xenium_cellpose`, `xenium_baysor`, `xenium_cellpose_baysor`, `xenium_proseg`, `merscope_cellpose`, `merscope_baysor_cellpose`, `merscope_baysor_vizgen`, `merscope_proseg`, `cosmx_cellpose`, `cosmx_baysor`, `cosmx_cellpose_baysor`, `cosmx_proseg`, `visium_hd_stardist`, `visium_hd_proseg`, `visium_hd_stardist_proseg`, `phenocycler_base_{10X,20X,40X}`, `hyperion_base`, `macsima_base`. These fix the patching, segmentation, and aggregation defaults.
- Patching: `patch_width_pixel` / `patch_width_microns` (use `-1` to disable patching on small/toy inputs), `patch_overlap_pixel` ≈ 2× cell diameter.
- Segmentation selection flags: `use_cellpose`, `use_stardist`, `use_baysor`, `use_proseg`, `use_comseg` (typically set by the profile). `prior_shapes_key` chains a prior (auto-set to `cellpose_boundaries` or `stardist_boundaries` when combining).
- Cellpose: `cellpose_diameter`, `cellpose_channels`, `flow_threshold`, `cellprob_threshold`, `cellpose_model_type`, `cellpose_use_gpu`.
- Stardist: `stardist_model_type`, `prob_thresh`, `nms_thresh`, `stardist_channels`.
- Baysor: `baysor_scale`, `baysor_scale_std` (default `25%`), `prior_segmentation_confidence` (default `0.2`), `min_molecules_per_cell` (default `20`), `force_2d` (default `true`).
- Proseg: `use_proseg`, `infer_presets`, `command_line_suffix`, `visium_hd_prior_shapes_key`.
- Comseg: `mean_cell_diameter` (10), `max_cell_radius` (15), `alpha` (0.5), `min_rna_per_cell`.
- Filtering: `min_transcripts`, `min_area_pixels2`, `min_area_microns2`, `min_intensity_ratio`.
- Aggregation: `aggregate_genes`, `aggregate_channels`, `expand_radius_ratio`.
- Explorer: `pixel_size` (default `0.2125` µm/px — must match the instrument or scales break), `lazy`, `ram_threshold_gb` (default `4`).
- Visium HD / Space Ranger: `--spaceranger_probeset`, `--spaceranger_reference` (defaults to GRCh38 2020-A).
- Optional downstream: `use_scanpy_preprocessing`, `resolution`, `hvg`; `use_tangram` with `sc_reference_path` + `tangram_cell_type_key`; `use_fluorescence_annotation` with `marker_cell_dict`.

## Test data
The built-in `test` profile uses Sopa's synthetic `toy_dataset` reader with a samplesheet under `tests/samplesheet.csv`, disables patching (`patch_width_microns = -1`, `prior_shapes_key = "auto"`), runs Proseg segmentation, aggregates channel intensities with `min_transcripts = 5`, runs fluorescence annotation with `marker_cell_dict = {"CK": "Tumoral cell", "CD3": "T cell", "CD20": "B cell"}`, and finishes with Scanpy preprocessing — producing a `{sample}.zarr` SpatialData object plus a `{sample}.explorer` directory containing `adata.h5ad`, `experiment.xenium`, and a Sopa QC `report.html`. The `test_full` profile exercises the Visium HD path on the public `Visium_HD_Human_Lung_Cancer` FFPE sample, pulling FASTQs and microscopy images from `nf-core/test-datasets` along with the matching probeset CSV and a GRCh38 Space Ranger reference tarball; it runs Space Ranger, then Stardist-as-prior + Proseg segmentation with `min_transcripts = 10`, and emits the same `.zarr` / `.explorer` outputs plus a `{sample}_spaceranger/outs` directory.

## Reference workflow
nf-core/sopa (dev), https://github.com/nf-core/sopa — the Nextflow wrapper around Sopa (Blampey et al., Nat Commun 2024, doi:10.1038/s41467-024-48981-z) built on scverse SpatialData. See `docs/usage.md` for technology profiles and `nextflow_schema.json` for the authoritative parameter list.
