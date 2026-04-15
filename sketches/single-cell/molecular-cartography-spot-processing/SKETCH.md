---
name: molecular-cartography-spot-processing
description: 'Use when processing Resolve Bioscience Molecular Cartography (combinatorial
  FISH) data: you have per-FOV DAPI (and optional membrane) TIFFs plus an x,y,z,gene
  spot table and need grid-gap filling, cell segmentation, spot-to-cell assignment,
  and a cell-by-transcript matrix with spatial AnnData output.'
domain: single-cell
organism_class:
- eukaryote
input_data:
- fish-spot-table
- dapi-tiff
- membrane-tiff
source:
  ecosystem: nf-core
  workflow: nf-core/molkart
  url: https://github.com/nf-core/molkart
  version: 1.2.0
  license: MIT
  slug: molkart
tools:
- name: mindagap
  version: 0.0.2
- name: clahe
- name: cellpose
  version: 3.0.1_cv1
- name: mesmer
- name: stardist
- name: ilastik
- name: spot2cell
- name: anndata
- name: multiqc
tags:
- spatial-transcriptomics
- molecular-cartography
- resolve-bioscience
- fish
- cell-segmentation
- spot-assignment
- image-processing
test_data: []
expected_output: []
---

# Molecular Cartography spot-to-cell processing

## When to use this sketch
- Input is Resolve Bioscience Molecular Cartography (combinatorial FISH) output: per-FOV panorama TIFFs with characteristic tile grid gaps, plus a tab-separated spot table (x, y, z, gene; no header).
- You have at minimum a nuclear (DAPI/Hoechst) TIFF per FOV and optionally a second channel (e.g. WGA membrane) to improve cell segmentation.
- Goal is an end-to-end run producing filled images, cell segmentation masks, a deduplicated cell-by-transcript matrix, a spatial AnnData object, and QC metrics (spots per cell, assignment rate, mask size distribution).
- You want to compare or combine multiple segmentation backends (Mesmer, Cellpose, Stardist, ilastik) in a single run.
- You need an optional cropped training subset (TIFF for Cellpose, HDF5 for ilastik) to train custom segmentation models and then re-run the pipeline with those models.

## Do not use when
- Data comes from a different spatial platform without the Molecular Cartography grid pattern (e.g. Vizgen MERSCOPE, 10x Xenium, CosMx) — you can still use the pipeline but must set `--skip_mindagap`; prefer a platform-specific sketch if available.
- You only need sequencing-based spatial transcriptomics (Visium, Slide-seq) — use an `nf-core/spatialvi`-style sketch instead.
- You only need image segmentation without spot assignment — use a dedicated segmentation sketch (e.g. `nf-core/mcmicro`).
- You need downstream clustering, neighborhood analysis, or differential expression — this sketch stops at the AnnData object; hand it off to a Squidpy/Scanpy analysis sketch.
- You want raw FASTQ-based scRNA-seq processing — use a single-cell RNA-seq sketch.

## Analysis outline
1. Parse `samplesheet.csv` with columns `sample,nuclear_image,spot_table,membrane_image` (one row per FOV; membrane optional).
2. Fill tile grid lines in nuclear (and membrane) TIFFs with `mindagap` (skippable via `--skip_mindagap`).
3. Optionally apply contrast-limited adaptive histogram equalization (`CLAHE`, scikit-image) to gridfilled images; skippable via `--skip_clahe`.
4. If a membrane image is provided, stack nuclear + membrane channels into a multichannel OME-TIFF for segmentation input.
5. Run one or more segmentation backends in parallel as specified by `--segmentation_method` (comma-separated): `mesmer`, `cellpose`, `stardist`, `ilastik`.
6. Filter resulting masks by area using `segmentation_min_area` / `segmentation_max_area` to drop artifacts.
7. Run `mindagap duplicatefinder` on the spot table to flag duplicates near grid lines.
8. Assign deduplicated spots to segmented cells with the local `spot2cell` module, producing `*.cellxgene.csv` (counts + shape features: Area, MajorAxisLength, MinorAxisLength, Eccentricity, Solidity, Extent, Orientation).
9. Build a spatial AnnData `.adata` via `create_anndata` (expression in `X`, coordinates in `obsm`, shape features in `obs`).
10. Collect per-sample QC (`molkartqc`) and aggregate into a `MultiQC` HTML report plus `final_QC.all_samples.csv`.
11. (Optional) With `--create_training_subset`, emit random tissue-biased crops as TIFF (Cellpose GUI) and HDF5 (ilastik GUI) for model training; then re-run the pipeline pointing `--cellpose_custom_model` / `--ilastik_pixel_project` / `--ilastik_multicut_project` at the trained artifacts.

## Key parameters
- `input`: path to samplesheet CSV (required).
- `outdir`: output directory (required).
- `segmentation_method`: `mesmer` (default), `cellpose`, `stardist`, `ilastik`, or comma-separated combination without whitespace.
- Mesmer: `mesmer_image_mpp` (default 0.138 µm/px), `mesmer_compartment` (`whole-cell` default, or `nuclear`).
- Cellpose: `cellpose_pretrained_model` (default `cyto`; e.g. `nuclei`), `cellpose_diameter` (30), `cellpose_chan` (0), `cellpose_chan2`, `cellpose_flow_threshold` (0.4), `cellpose_cellprob_threshold` (0), `cellpose_edge_exclude` (true), `cellpose_custom_model` (overrides pretrained when set), `cellpose_save_flows`.
- Stardist: `stardist_model` (one of `2D_versatile_fluo` [default], `2D_paper_dsb2018`, `2D_versatile_he`), `stardist_n_tiles_x` / `stardist_n_tiles_y` (3/3; increase for large images — Stardist is the only backend with native tiling). Nuclear-only; ignores membrane channel.
- ilastik: `ilastik_pixel_project` and `ilastik_multicut_project` `.ilp` files required; training data axes must match input axes.
- Mindagap: `mindagap_tilesize` (2144 default — matches Molecular Cartography tile pitch), `mindagap_boxsize` (3), `mindagap_loopnum` (40), `mindagap_edges`, `skip_mindagap`.
- CLAHE: `clahe_cliplimit` (0.01), `clahe_nbins` (256), `clahe_pixel_size` (0.138), `clahe_kernel` (25), `clahe_pyramid_tile` (1072, must be divisible by 16), `skip_clahe`.
- Mask filtering: `segmentation_min_area`, `segmentation_max_area` (pixels).
- Training subset: `create_training_subset`, `crop_size_x`/`crop_size_y` (400), `crop_amount` (4), `crop_nonzero_fraction` (0.4).
- Conda is **not** supported; run with `-profile docker` or `-profile singularity`.

## Test data
The bundled `test` profile consumes a small Molecular Cartography samplesheet with a membrane channel (`samplesheet_membrane.csv` from `nf-core/test-datasets/molkart`), each row pointing at a nuclear TIFF, a tab-separated spot table, and a membrane TIFF. Mindagap is tuned for the tiny fixtures (`mindagap_tilesize=90`, `mindagap_boxsize=7`, `mindagap_loopnum=100`, `clahe_pyramid_tile=368`) and all three of `mesmer,cellpose,stardist` are run in parallel. A successful run should populate `mindagap/` gridfilled TIFFs and `*_markedDups.txt`, `clahe/*_clahe.tiff`, stacked OME-TIFFs under `stack/`, per-backend masks under `segmentation/{cellpose,mesmer,stardist}/` plus `filtered_masks/`, `spot2cell/*.cellxgene.csv`, `anndata/*.adata`, `molkartqc/*.spot_QC.csv`, and a `multiqc/multiqc_report.html` with `final_QC.all_samples.csv`. The `test_full` profile uses `samplesheet_full_test.csv`, `cellpose_pretrained_model=nuclei`, and bumps `stardist_n_tiles_{x,y}=20` for a realistic FOV.

## Reference workflow
nf-core/molkart v1.2.0 — https://github.com/nf-core/molkart (MIT). Cite via Zenodo DOI 10.5281/zenodo.10650748 and the underlying tools (Mindagap, Cellpose, Mesmer, Stardist, ilastik, anndata, MultiQC) as listed in `CITATIONS.md`.
