---
name: tissue-microarray-cyclic-if-analysis
description: Use when you have raw cyclic immunofluorescence (CyCIF / multiplex tissue
  imaging) cycle images of a tissue microarray (TMA) and need an end-to-end pipeline
  that performs illumination correction, whole-slide stitching, TMA core dearraying,
  nuclear segmentation, single-cell feature quantification, and automated cell phenotyping,
  producing an interactive Vitessce dashboard and h5ad tables for downstream spatial/single-cell
  analysis.
domain: other
organism_class:
- vertebrate
- eukaryote
input_data:
- multiplex-if-cycle-images-ome-tiff
- markers-csv
- scimap-phenotype-csv
source:
  ecosystem: iwc
  workflow: End-to-End Tissue Microarray Analysis
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/imaging/tissue-microarray-analysis/tissue-microarray-analysis
  version: 0.1.1
  license: MIT
  slug: imaging--tissue-microarray-analysis--tissue-microarray-analysis
tools:
- name: basic-illumination
  version: 1.1.1+galaxy2
- name: ashlar
  version: 1.18.0+galaxy1
- name: unet-coreograph
  version: 2.2.8+galaxy1
- name: mesmer
  version: 0.12.3+galaxy3
- name: mcquant
- name: scimap
  version: 2.1.0+galaxy2
- name: vitessce
  version: 3.5.1+galaxy0
- name: bfconvert
tags:
- imaging
- multiplex
- tissue-microarray
- cycif
- mcmicro
- spatial
- immunofluorescence
- single-cell
test_data:
- role: raw_cycle_images__exemplar_001_cycle_04
  url: https://zenodo.org/records/15203994/files/exemplar-001-cycle-04.ome.tiff?download=1
  sha1: 2871acf4534e55b73d2387a32a8e28e38a4d9026
  filetype: ome.tiff
- role: raw_cycle_images__exemplar_001_cycle_05
  url: https://zenodo.org/records/15203994/files/exemplar-001-cycle-05.ome.tiff?download=1
  sha1: 2871acf4534e55b73d2387a32a8e28e38a4d9026
  filetype: ome.tiff
- role: raw_cycle_images__exemplar_001_cycle_06
  url: https://zenodo.org/records/15203994/files/exemplar-001-cycle-06.ome.tiff?download=1
  sha1: 2871acf4534e55b73d2387a32a8e28e38a4d9026
  filetype: ome.tiff
- role: raw_cycle_images__exemplar_001_cycle_07
  url: https://zenodo.org/records/15203994/files/exemplar-001-cycle-07.ome.tiff?download=1
  sha1: 2871acf4534e55b73d2387a32a8e28e38a4d9026
  filetype: ome.tiff
- role: raw_cycle_images__exemplar_001_cycle_08
  url: https://zenodo.org/records/15203994/files/exemplar-001-cycle-08.ome.tiff?download=1
  sha1: 9c53b7098f2cb6ed4dd75206aa68cad44015f22a
  filetype: ome.tiff
expected_output: []
---

# End-to-End Tissue Microarray (Cyclic IF) Analysis

## When to use this sketch
- You have raw, unstitched cyclic immunofluorescence (CyCIF/t-CyCIF, mIHC, or similar) cycle images of a **tissue microarray** slide, one TIFF/OME-TIFF per round, in round order.
- You need to go from raw cycle images all the way to a quantified, phenotyped single-cell table and an interactive viewer in a single run.
- Your slide is a TMA (multiple small cores on one slide) and you need each core automatically detected and cropped before downstream per-core analysis.
- You have a Rarecyte-style dataset (or similar) with image resolution ~0.65 microns/pixel and a DAPI-like nuclear reference channel at channel index 0.
- You want outputs compatible with downstream Scanpy/Squidpy/Scimap spatial analysis (h5ad) and a Vitessce dashboard for visual QC.

## Do not use when
- Your slide is a single whole-tissue section rather than a microarray — use the sibling `multiplex-tissue-imaging-mcmicro` / whole-slide MTI sketch instead, which skips UNetCoreograph dearraying.
- You already have a stitched, registered OME-TIFF and just need segmentation/quantification — use a downstream-only segmentation+quantification sketch.
- Your data is H&E brightfield, IMC (mass cytometry imaging), or CODEX/PhenoCycler without matching Bio-Formats support — those need different preprocessing.
- You require whole-cell (membrane) segmentation rather than nuclear-only segmentation — Mesmer is configured here in nuclear-only mode.
- Your markers show poor bimodal distributions and you need publication-grade phenotyping — this workflow runs automated GMM gating via Scimap; use GateFinder-based manual gating instead.
- Your pixel size, alignment channel, or nuclear channel differ from the presets and you cannot edit the workflow.

## Analysis outline
1. **BaSiC Illumination** — compute per-tile dark-field (DFP) and flat-field (FFP) correction profiles from the raw cycle images.
2. **ASHLAR** — stitch and register all cycles into a single pyramidal OME-TIFF, applying BaSiC DFP/FFP correction and assigning channel names from the markers CSV.
3. **UNetCoreograph** — detect TMA cores on the registered image and crop each core into its own TIFF (batch-processed downstream).
4. **Convert Image (bfconvert)** — convert each cropped core TIFF back to pyramidal OME-TIFF (tiled 512×512, 4 pyramid levels).
5. **Rename OME-TIFF channels** — restore marker names on the per-core OME-TIFFs using the markers CSV.
6. **Mesmer** — run nuclear segmentation on each core, producing a per-core nuclear mask TIFF.
7. **MCQUANT** — quantify mean marker intensities, spatial centroids, and morphological features per cell, emitting a CSV of cells × features per core.
8. **Scimap mcmicro→anndata** — convert the MCQUANT CSV to an `.h5ad` AnnData object (log-transformed, split on `X_centroid`).
9. **Scimap Single Cell Phenotyping** — apply a hierarchical Scimap phenotype workflow (GMM-based automated gating) to label each cell.
10. **Vitessce** — build an interactive dashboard tying the pyramidal OME-TIFF, nuclear masks, and phenotyped h5ad (UMAP + phenotype categories) together.

## Key parameters
- ASHLAR `align_channel`: `0` (nuclear/DAPI reference channel for registration).
- ASHLAR `max_shift`: `30` pixels.
- ASHLAR `rename`: enabled, using the input `markers.csv`.
- UNetCoreograph `channel`: `0`; `downsamplefactor`: `5`; `buffer`: `2.0`; `sensitivity`: `0.3`; `tissue`: false (TMA mode).
- Mesmer `compartment`: `nuclear`; `nuclear_channels`: `0`; `image_mpp`: `0.65` microns/pixel; `maxima_threshold`: `0.1`; `interior_threshold`: `0.2`; `small_objects_threshold`: `15`; `fill_holes_threshold`: `15`.
- bfconvert: output `ome.tiff`, pyramid generate=true, resolutions=`4`, scale=`2`, tiles `512×512`.
- Scimap AnnData conversion: `log=true`, split column = `X_centroid`, CellID column = `CellID`.
- Scimap phenotyping: `log=true`, `random_state=0`, manual gates optional (omitted → GMM auto-gating).
- Vitessce: embedding `umap` with `n_neighbors=30`, `n_pcs=10`, knn=true; scatterplot colored by `phenotype`.
- Assumed image resolution: `0.65` µm/pixel throughout; edit the workflow if your scanner differs.

## Test data
The bundled test uses five Rarecyte exemplar-001 cycle images (`exemplar-001-cycle-04` through `exemplar-001-cycle-08`) fetched as OME-TIFFs from Zenodo record 15203994, together with a small `markers.csv` and a Scimap `phenotypes.csv` gating workflow. Running the pipeline should yield a registered multi-channel OME-TIFF (~6 MB), per-cycle DFP/FFP correction images, a TMA dearray map, at least one dearrayed core with its nuclear mask and renamed OME-TIFF, an MCQUANT primary-mask quantification CSV, and an AnnData feature table whose `obs` contains morphology keys (`Area`, `Eccentricity`, `Extent`, `MajorAxisLength`, `MinorAxisLength`, `Orientation`, `Solidity`, `X_centroid`, `Y_centroid`, `CellID`, `imageid`). The Scimap phenotyping step preserves those keys on the phenotyped h5ad, and the final Vitessce config JSON should report `version` = `1.0.17`.

## Reference workflow
Galaxy IWC — `workflows/imaging/tissue-microarray-analysis/tissue-microarray-analysis` ("End-to-End Tissue Microarray Analysis"), release 0.1.1, MIT-licensed. Built on the MCMICRO toolchain (BaSiC, ASHLAR, UNetCoreograph, MCQUANT), Mesmer (DeepCell), Scimap, and Vitessce, and accompanies the Galaxy Training Network tutorial "Multiplex tissue imaging — TMA".
