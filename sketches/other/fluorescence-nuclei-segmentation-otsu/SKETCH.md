---
name: fluorescence-nuclei-segmentation-otsu
description: Use when you need to segment and count cell nuclei in 2D single-channel
  fluorescence microscopy images using classical Otsu thresholding. Produces a label
  map, an overlay visualization, and a total object count. Assumes nuclei are well-separated
  and the input is a single channel containing only the nuclei signal.
domain: other
organism_class:
- eukaryote
input_data:
- fluorescence-microscopy-image-2d
- single-channel-tiff
source:
  ecosystem: iwc
  workflow: Segmentation and counting of cell nuclei in fluorescence microscopy images
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/imaging/fluorescence-nuclei-segmentation-and-counting
  version: '0.2'
  license: MIT
  slug: imaging--fluorescence-nuclei-segmentation-and-counting
tools:
- name: scikit-image
- name: bfconvert
- name: imgteam-2d-filter
- name: imgteam-2d-auto-threshold
- name: imgteam-binary2labelimage
- name: imgteam-count-objects
- name: imgteam-overlay-images
tags:
- imaging
- microscopy
- segmentation
- nuclei
- otsu
- cell-counting
- bioimage-analysis
test_data: []
expected_output:
- role: overlay_image
  path: expected_output/overlay_image.png
  description: Expected output `overlay_image` from the source workflow test.
  assertions: []
- role: objects_count
  path: expected_output/objects_count.tabular
  description: Expected output `objects_count` from the source workflow test.
  assertions: []
- role: label_image
  path: expected_output/label_image.tiff
  description: Expected output `label_image` from the source workflow test.
  assertions: []
---

# Fluorescence nuclei segmentation and counting (Otsu)

## When to use this sketch
- User has 2D fluorescence microscopy images (TIFF) of DAPI/Hoechst-stained (or equivalent) cell nuclei and wants to count them.
- Input is already reduced to the single channel containing the nuclei signal.
- Nuclei are reasonably bright against a dark background and mostly non-touching, so a global Otsu threshold followed by connected-component labeling is sufficient.
- User wants a quick, interpretable classical pipeline (no deep learning, no training data required) and an overlay image for visual QC.

## Do not use when
- Nuclei are densely clustered or touching and must be separated into individual objects — prefer a watershed- or StarDist/Cellpose-based segmentation sketch instead.
- Input is brightfield / phase contrast / H&E — this workflow assumes fluorescence with a dark background; use a stain-specific or deep-learning segmentation sketch.
- You need 3D volumetric segmentation, time-lapse tracking, or multi-channel co-localization — this is strictly a 2D, single-channel pipeline.
- You need per-object morphological features (area, eccentricity, intensity) beyond a simple count — use a downstream region-properties workflow on top of the label map.

## Analysis outline
1. Load the single-channel fluorescence TIFF as `input_image`.
2. Smooth the image with a 2D Gaussian filter (imgteam `2d_simple_filter`) to suppress noise before thresholding.
3. In parallel, apply CLAHE histogram equalization (imgteam `2d_histogram_equalization`) to the original image for a contrast-enhanced version used only for visualization.
4. Apply Otsu automatic thresholding (imgteam `2d_auto_threshold`, method `otsu`, `dark_bg=true`) to the smoothed image to obtain a binary foreground mask.
5. Convert the CLAHE-equalized image to PNG via `bfconvert` so it can be used as a display background.
6. Convert the binary mask to a label map via connected-component analysis (imgteam `binary2labelimage`, mode `cca`), producing one unique integer label per nucleus.
7. Overlay the label-map contours onto the PNG background (imgteam `overlay_images`, method `seg_contour`, red outlines with yellow numeric labels) for visual QC.
8. Count the labeled objects (imgteam `count_objects`) to produce a one-row tabular file with the total nuclei count.

## Key parameters
- Gaussian filter: `filter_type: gaussian`, `size: 3.0` — controls how aggressively noise is smoothed; increase for noisier images.
- Histogram equalization: `h_type: clahe` — contrast enhancement for the display channel only, does not affect the segmentation path.
- Auto-threshold: `th_method: otsu`, `dark_bg: true`, `invert_output: false` — assumes bright nuclei on dark background; flip `dark_bg` for inverted intensity conventions.
- Binary-to-label: `mode: cca` (connected-component analysis) — each connected foreground region becomes one object.
- Overlay: `method: seg_contour`, `thickness: 2`, `color: #ff0000`, `show_label: true`, `label_color: #ffff00`.
- bfconvert output format: `png` with `noflat: true` for the overlay background.

## Test data
The reference test supplies a single 2D fluorescence TIFF, `input_image.tiff` (SHA-1 `42c34939d896d133ce9f0f2af6efd79b02ed52e6`), representing one field of view of stained cell nuclei. Running the workflow is expected to produce three outputs: `label_image.tiff` (the integer label map, compared against a golden file by intersection-over-union), `overlay_image.png` (the CLAHE background with red contours and yellow numeric labels, compared by image diff), and `objects_count.tabular` (a two-line TSV with header `objects` and a single integer row giving the total number of segmented nuclei, compared line-for-line with zero tolerance).

## Reference workflow
Galaxy IWC — `workflows/imaging/fluorescence-nuclei-segmentation-and-counting/segmentation-and-counting.ga`, release 0.2 (2024-11-07), authored by Leonid Kostrykin. Based on the Galaxy Training Network tutorial at https://training.galaxyproject.org/training-material/topics/imaging/tutorials/imaging-introduction/tutorial.html.
