---
name: multiplexed-tissue-imaging-single-cell
description: Use when you need to process highly-multiplexed whole-slide microscopy
  images (CyCIF, MIBI, CODEX, SeqIF, mIHC) into a registered mosaic OME-TIFF, a cell
  segmentation mask, and a single-cell x marker feature table. Assumes multi-channel,
  multi-cycle tissue imaging input with an accompanying marker sheet; not for standard
  H&E or bulk fluorescence microscopy.
domain: other
organism_class:
- eukaryote
- vertebrate
input_data:
- ome-tiff-multiplex-cycles
- marker-sheet-csv
source:
  ecosystem: nf-core
  workflow: nf-core/mcmicro
  url: https://github.com/nf-core/mcmicro
  version: dev
  license: MIT
  slug: mcmicro
tools:
- name: ashlar
  version: 1.18.0
- name: basicpy
- name: backsub
- name: coreograph
- name: cellpose
  version: 3.0.1_cv1
- name: mccellpose
- name: deepcell-mesmer
- name: mcquant
- name: multiqc
tags:
- imaging
- multiplexed
- cycif
- codex
- mibi
- seqif
- whole-slide
- segmentation
- single-cell
- spatial
test_data: []
expected_output: []
---

# Multiplexed tissue imaging to single-cell feature tables

## When to use this sketch
- Input is a multi-cycle, multi-channel whole-slide fluorescence imaging experiment (CyCIF, t-CyCIF, CODEX, MIBI, SeqIF, IMC-style mIHC) delivered as per-cycle OME-TIFFs.
- Goal is an end-to-end path from raw image tiles to (a) a registered pyramidal OME-TIFF, (b) a labelled cell segmentation mask, and (c) a `cells x markers` quantification CSV suitable for downstream spatial / single-cell analysis (e.g. SCIMAP, Scanpy).
- User has (or can produce) a marker sheet mapping `channel_number` and `cycle_number` to marker names, consistent across cycles.
- Optional needs supported: illumination/shading correction, background (autofluorescence) subtraction, tissue microarray (TMA) core dearraying, running several segmentation methods in parallel for comparison.
- Data are large whole-slide tiles where stitching and registration across cycles is the hard part; user wants a reproducible, containerized pipeline rather than ad-hoc ImageJ/QuPath scripting.

## Do not use when
- Input is standard H&E / brightfield histopathology — use a pathology / HoVer-Net style workflow instead.
- Input is single-cycle, single-channel fluorescence microscopy where registration across cycles is unnecessary — a direct Cellpose/StarDist call is simpler.
- Input is bulk RNA/DNA sequencing or spatial transcriptomics (Visium, Xenium, MERFISH) — use the appropriate sequencing or spatial-omics sketch; this pipeline does not handle transcript counts.
- You only need segmentation without registration and quantification — call a Cellpose or Mesmer module directly.
- User wants clustering, neighborhood analysis, or cell-type calling — those are downstream of this sketch; pass the MCQuant CSV into a spatial analysis workflow.

## Analysis outline
1. **Prelude / metadata QC** — parse OME-XML from each input TIFF, cross-check against the sample and marker sheets, and emit a MultiQC summary. Run once with `--prelude` first to validate inputs before committing compute.
2. **Illumination correction (optional)** — BaSiCPy estimates per-cycle dark-field (`*-dfp.tif`) and flat-field (`*-ffp.tif`) images for shading correction; applied per cycle when `--illumination basicpy` is set.
3. **Registration / stitching** — ASHLAR stitches tiles within each cycle and registers cycles to each other, producing a single pyramidal `{sample}.ome.tif` mosaic.
4. **Background subtraction (optional)** — `backsub` performs pixel-wise, exposure-scaled channel subtraction on the registered OME-TIFF and rewrites the marker sheet as `markers_bs.csv`.
5. **TMA dearraying (optional)** — Coreograph (UNet) detects cores on a TMA slide, emitting one `{core}.tif` and binary mask per core plus a `TMA_MAP.tif`; downstream steps then run per core.
6. **Segmentation** — one or more of `mccellpose` (RAM-efficient Cellpose, default), `cellpose` (optionally with a custom model via `--cellpose_model`), and `deepcell_mesmer` (whole-cell), each producing `{sample}_mask.(ome.)tif`. Multiple segmenters run in parallel when listed comma-separated.
7. **Quantification** — MCQuant takes the registered image + each segmentation mask and writes a per-segmenter `{sample}.csv` of single-cell mean intensities and morphological features.
8. **Reporting** — MultiQC aggregates the prelude validation tables and per-step metrics into `multiqc_report.html`.

## Key parameters
- `--input_cycle <csv>` *(or `--input_sample <csv>`)*: sample sheet. `input_cycle` has columns `sample,cycle_number,image_tiles` (one row per cycle); `input_sample` has `sample,image_directory`.
- `--marker_sheet <csv>`: **required**. Columns `channel_number,cycle_number,marker_name`; `cycle_number` values must match the sample sheet. Optional columns: `filter`, `excitation_wavelength`, `emission_wavelength`.
- `--outdir <dir>`: **required**.
- `--prelude` (bool): stop after metadata extraction + MultiQC validation; run this first on any new dataset.
- `--illumination basicpy`: enable BaSiCPy shading correction (only supported value today).
- `--backsub` (bool): enable exposure-scaled background subtraction after registration.
- `--tma_dearray` (bool): treat input as a TMA and run Coreograph before segmentation; typically speeds up processing and cuts RAM.
- `--segmentation`: comma-separated subset of `mccellpose,cellpose,mesmer`. Default is `mccellpose`. Prefer `mccellpose` over `cellpose` unless you need a custom model — it uses much less RAM.
- `--cellpose_model <path|url>`: pretrained Cellpose model, only meaningful when `cellpose` is in `--segmentation`.
- `-profile docker|singularity|conda|...`: containerization profile; Docker or Singularity strongly recommended.
- `-params-file params.yaml`: preferred way to pin parameters for reproducibility. Do **not** pass pipeline params via `-c`.

## Test data
The bundled `test` profile (`conf/test.config`) points at `assets/samplesheet-test.csv` and `assets/markers-test.csv` — a tiny CyCIF tonsil sample (e.g. `cycif-tonsil-cycle1.ome.tif` from `nf-core/test-datasets`) with a handful of channels (DNA, Na/K ATPase, CD3, CD45RO, ...). It runs in under an hour on 4 CPUs / 15 GB RAM and exercises the default path: ASHLAR registration → `mccellpose` segmentation → MCQuant. Expected outputs are a registered `registration/ashlar/{sample}.ome.tif`, a `segmentation/{segmenter}/{sample}_mask.ome.tif`, a `quantification/mcquant/{segmenter}/{sample}.csv` single-cell table, and a `multiqc/multiqc_report.html`. The `test_full` profile adds `illumination=basicpy`, `backsub=true`, and runs both `mesmer` and `cellpose` segmenters in parallel on a larger CyCIF dataset, additionally producing `illumination_correction/basicpy/{sample}-{d,f}fp.tif` and `backsub` outputs.

## Reference workflow
nf-core/mcmicro (`dev`, template 3.5.1), https://github.com/nf-core/mcmicro — an nf-core port of the labsyspharm MCMICRO pipeline (Schapiro et al., *Nat Methods* 2022, doi:10.1038/s41592-021-01308-y). See `docs/usage.md` and `docs/output.md` in that repo for the authoritative parameter and output reference.
