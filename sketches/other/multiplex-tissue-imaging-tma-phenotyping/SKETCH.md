---
name: multiplex-tissue-imaging-tma-phenotyping
description: Use when you have a collection of pre-registered multiplex (cyclic immunofluorescence
  / CyCIF-style) OME-TIFF tissue microarray core images and need to perform background
  subtraction, nuclear segmentation, single-cell feature quantification, hierarchical
  cell phenotyping, multi-sample composition and spatial neighborhood analysis, plus
  interactive Vitessce dashboards. Assumes images are already stitched and registered
  (e.g. by ASHLAR) and that a markers file and Scimap phenotyping/gating CSVs are
  available.
domain: other
organism_class:
- vertebrate
- eukaryote
input_data:
- multiplex-ome-tiff-registered
- markers-csv
- scimap-phenotype-workflow-csv
- manual-gates-csv
source:
  ecosystem: iwc
  workflow: Multiplex Tissue Microarray Analysis
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/imaging/tissue-microarray-analysis/multiplex-tissue-microarray-analysis
  version: 0.1.2
  license: MIT
  slug: imaging--tissue-microarray-analysis--multiplex-tissue-microarray-analysis
tools:
- name: backsub
  version: 0.4.1+galaxy0
- name: mesmer
  version: 0.12.3+galaxy3
- name: mcquant
- name: scimap
  version: 2.1.0+galaxy3
- name: squidpy
  version: 1.5.0+galaxy2
- name: anndata
  version: 1.9.3+galaxy1
- name: vitessce
  version: 3.5.1+galaxy3
tags:
- multiplex-imaging
- cycif
- tissue-microarray
- tma
- cell-segmentation
- cell-phenotyping
- spatial-analysis
- galaxy-me
- mcmicro
test_data:
- role: registered_images__image
  url: https://zenodo.org/records/15710828/files/Registered%20Images_registered%20image.ome.tiff?download=1
  sha1: 1e2e08fc7196d52db117ad30247b5431b56eed61
  filetype: ome.tiff
expected_output:
- role: spatial_scatterplot_montage
  description: Content assertions for `Spatial Scatterplot Montage`.
  assertions:
  - 'has_size: {''size'': ''181K'', ''delta'': ''50K''}'
- role: spatial_interaction_montage
  description: Content assertions for `Spatial Interaction Montage`.
  assertions:
  - 'has_size: {''size'': ''39K'', ''delta'': ''20K''}'
- role: merged_anndata
  description: Content assertions for `Merged anndata`.
  assertions:
  - 'has_h5_keys: {''keys'': ''obs/Area,obs/CellID,obs/Eccentricity,obs/Extent,obs/MajorAxisLength,obs/MinorAxisLength,obs/Orientation,obs/Solidity,obs/X_centroid,obs/Y_centroid,obs/imageid,obs/imageid/categories,obs/imageid/codes''}'
- role: multisample_barplot
  description: Content assertions for `Multisample barplot`.
  assertions:
  - 'has_size: {''size'': ''60K'', ''delta'': ''30K''}'
- role: background_subtracted_images
  description: Content assertions for `Background subtracted images`.
  assertions:
  - 'image: has_image_channels: {''channels'': 7}'
- role: background_subtracted_markers
  description: Content assertions for `Background subtracted markers`.
  assertions:
  - 'image: has_line: marker_name,background,exposure'
  - 'image: has_line: DNA_7,,'
- role: primary_mask_quantification
  description: Content assertions for `Primary Mask Quantification`.
  assertions:
  - 'image: has_line: CellID,DNA_7,CD11B,SMA,CD16,ECAD,FOXP3,NCAM,X_centroid,Y_centroid,Area,MajorAxisLength,MinorAxisLength,Eccentricity,Solidity,Extent,Orientation'
- role: segmented_multiplexed_mask
  description: Content assertions for `Segmented Multiplexed Mask`.
  assertions:
  - 'image: has_image_channels: {''channels'': 1}'
- role: phenotyped_adata
  description: Content assertions for `phenotyped adata`.
  assertions:
  - 'image: has_h5_keys: {''keys'': ''obs/Area,obs/CellID,obs/Eccentricity,obs/Extent,obs/MajorAxisLength,obs/MinorAxisLength,obs/Orientation,obs/Solidity,obs/X_centroid,obs/Y_centroid,obs/imageid,obs/imageid/categories,obs/imageid/codes''}'
- role: interaction_matrix_plot
  description: Content assertions for `Interaction Matrix Plot`.
  assertions:
  - 'image: has_size: {''size'': ''43K'', ''delta'': ''20K''}'
- role: interaction_matrix_anndata
  description: Content assertions for `Interaction Matrix Anndata`.
  assertions:
  - 'image: has_h5_keys: {''keys'': ''obs/Area,obs/CellID,obs/Eccentricity,obs/Extent,obs/MajorAxisLength,obs/MinorAxisLength,obs/Orientation,obs/Solidity,obs/X_centroid,obs/Y_centroid,obs/imageid,obs/imageid/categories,obs/imageid/codes''}'
- role: squidpy_spatial_scatterplots
  description: Content assertions for `Squidpy Spatial Scatterplots`.
  assertions:
  - 'image: has_size: {''size'': ''181K'', ''delta'': ''50K''}'
- role: vitessce_dashboard
  description: Content assertions for `Vitessce Dashboard`.
  assertions:
  - 'image: has_json_property_with_text: 1.0.17'
---

# Multiplex tissue microarray (TMA) image analysis and phenotyping

## When to use this sketch
- You have a collection of **pre-registered OME-TIFF** images of TMA cores (one per core) from a cyclic immunofluorescence / multiplex imaging platform (e.g. Rarecyte, CyCIF, mIHC).
- You need an end-to-end pipeline that goes from raw multiplex images to **single-cell spatial phenotypes** and interactive viewers.
- You want **hierarchical, gate-based cell phenotyping** driven by a Scimap phenotype workflow CSV plus optional manual gates, rather than unsupervised clustering only.
- You want multi-sample outputs: per-core segmentation masks, a merged phenotyped AnnData, cell-type composition barplots, spatial scatterplots, cell-type interaction matrices, and a Vitessce dashboard.
- Typical use cases: tumor microenvironment profiling, immune infiltration analysis across TMA cohorts, spatial biomarker discovery.

## Do not use when
- Images are **not yet registered / stitched** across cycles — first run an ASHLAR/MCMICRO registration workflow and then feed the outputs here.
- You only have a **single H&E brightfield** or standard IHC image — use a histopathology / QuPath-style sketch instead.
- You are doing **spatial transcriptomics** (Visium, Xenium, MERFISH, CosMx) — use a dedicated spatial-omics sketch.
- You want unsupervised clustering only with no marker-driven gating — adapt a Scanpy/Squidpy clustering sketch instead.
- Your images have a nuclear channel that is not channel `0`, or a resolution other than `0.65 µm/pixel`, and you are unwilling to edit those parameters (the workflow is hardcoded to these defaults).

## Analysis outline
1. **Background subtraction** of autofluorescence channels with `backsub`, driven by the markers CSV (which specifies background channels and markers to drop).
2. **Nuclear segmentation** per core with `Mesmer` (DeepCell) using the DNA channel to produce a single-channel nuclear mask TIFF.
3. **Single-cell feature quantification** with `MCQUANT`, producing a CSV of cells × (mean intensities + centroids + morphology).
4. **Convert** the MCQUANT CSV to `AnnData` (h5ad) via Scimap's `mcmicro_to_anndata`, splitting on `X_centroid` and dropping DNA channels.
5. **Hierarchical cell phenotyping** with `Scimap` using the provided phenotype workflow CSV plus optional manual gates (GMM auto-thresholding for unspecified markers).
6. **AnnData tidy-up** (`anndata_ops`) to normalize the `CellID` obs column.
7. **Per-sample spatial scatterplots** of phenotypes on centroid coordinates via `Squidpy scatter`, then a `GraphicsMagick` montage across samples.
8. **Spatial neighbors graph** and **cell-type interaction matrix** per sample via `Squidpy spatial` (generic coord type, radius 46 px ≈ 30 µm), then a montage of per-sample interaction plots.
9. **Concatenate** per-sample AnnData into a merged multi-sample AnnData and generate a **Scimap stacked barplot** of cell-type composition across samples.
10. **Interactive exploration**: build a per-sample `Vitessce` dashboard (image + masks + phenotyped AnnData with UMAP) and rewrite the JSON config for Galaxy serving.

## Key parameters
- Mesmer: `compartment: nuclear`, `nuclear_channels: 0`, `image_mpp: 0.65`, `maxima_threshold: 0.1`, `interior_threshold: 0.2`, `small_objects_threshold: 15`.
- MCQUANT: primary mask = Mesmer nuclear mask; channel names from the background-subtracted markers CSV.
- Scimap mcmicro_to_anndata: `remove_dna: true`, `split: X_centroid` (used as the image-id splitter), `CellId: CellID`.
- Scimap phenotyping: `log: true`, `random_state: 0`, consumes both the phenotype workflow CSV and the manual gates CSV.
- Squidpy spatial_neighbors: `coord_type: generic`, `n_neighs: 6`, `radius: 46` (≈30 µm at 0.65 µm/pixel); change radius if your mpp differs.
- Squidpy interaction_matrix: `cluster_key: phenotype`, `normalized: true`.
- Squidpy scatter: `color: phenotype`, `x_coord: X_centroid`, `y_coord: Y_centroid`, scale bar `0.65 µm`.
- Vitessce: `phenotyping_choice: add_h5ad`, UMAP embedding with `n_neighbors: 30`, `n_pcs: 10`.
- Markers CSV schema: columns `marker_name,background,exposure,remove`; set `remove=TRUE` for control channels and point real markers at their autofluorescence control via the `background` column.

## Test data
The bundled test job supplies one registered OME-TIFF core (downloaded from Zenodo record 15710828) as a single-element `Registered Images` collection, plus three small CSVs: a `Markers File` listing marker names with background controls and DNA channels flagged for removal, a `Phenotype workflow` CSV defining hierarchical Scimap gates, and a `Manual Gates` CSV of log1p intensity thresholds. Expected outputs include a 7-channel `Background subtracted images` collection, a 1-channel `Segmented Multiplexed Mask`, a `Primary Mask Quantification` CSV whose header is `CellID,DNA_7,CD11B,SMA,CD16,ECAD,FOXP3,NCAM,X_centroid,Y_centroid,Area,...,Orientation`, a `phenotyped adata` h5ad with the expected `obs/*` keys (Area, CellID, Eccentricity, centroids, imageid, etc.), a `Merged anndata` concatenated across samples, PNG montages for `Spatial Scatterplot Montage` (~181K) and `Spatial Interaction Montage` (~39K), a `Multisample barplot` PNG (~60K), an `Interaction Matrix Plot` (~43K), and a `Vitessce Dashboard` JSON with `version: 1.0.17`.

## Reference workflow
Galaxy IWC `workflows/imaging/tissue-microarray-analysis/multiplex-tissue-microarray-analysis` (Multiplex Tissue Microarray Analysis), release **0.1.2**. Built on Galaxy-ME / MCMICRO tooling (backsub, Mesmer, MCQUANT, Scimap, Squidpy, Vitessce); see the Galaxy Training Network tutorial `topics/imaging/tutorials/multiplex-tissue-imaging-TMA` for a walkthrough and example marker/gate files.
