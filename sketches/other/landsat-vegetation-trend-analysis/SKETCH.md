---
name: landsat-vegetation-trend-analysis
description: Use when you need to derive long-term vegetation trends and land-cover
  change signals from a multi-year Landsat (or Sentinel-2) archive over a defined
  rangeland / ecosystem area of interest, producing atmospherically corrected ARD,
  spectral unmixing fractions, and time-series trend mosaics via the FORCE toolchain.
domain: other
organism_class:
- non-biological
- earth-observation
input_data:
- landsat-level1-scenes
- digital-elevation-model
- water-vapor-database
- datacube-definition-prj
- aoi-vector
- endmember-txt
source:
  ecosystem: nf-core
  workflow: nf-core/rangeland
  url: https://github.com/nf-core/rangeland
  version: 1.0.0
  license: MIT
  slug: rangeland
tools:
- name: FORCE
- name: force-level1-csd
- name: force-tile-extent
- name: force-cube
- name: force-parameter
- name: force-l2ps
- name: force-higher-level
- name: force-mosaic
- name: force-pyramid
- name: MultiQC
  version: 1.25.1
tags:
- remote-sensing
- satellite
- landsat
- sentinel-2
- rangeland
- vegetation
- time-series
- spectral-unmixing
- ndvi
- geospatial
- force
test_data: []
expected_output: []
---

# Landsat long-term vegetation trend analysis (FORCE)

## When to use this sketch
- User has a multi-year stack of Landsat Level-1 scenes (LT04/LT05/LE07/LC08/LC09) or Sentinel-2 scenes covering a rangeland, savanna, forest or other terrestrial area of interest.
- Goal is to derive **long-term vegetation trends**, land-cover change indicators, or sub-pixel vegetation fractions over years/decades.
- User wants analysis-ready data (ARD, FORCE level-2): atmospheric + topographic correction with cloud/shadow masking.
- User wants time-series analyses of spectral indices (NDVI, EVI, NBR, tasseled-cap, etc.) and/or spectral unmixing against a provided endmember library.
- Output should be tiled trend files plus mosaic and pyramid visualizations suitable for GIS inspection.
- Scenes are organized in the canonical FORCE `path/row/scene-id/*.TIF` layout (as produced by `force-level1-csd`).

## Do not use when
- The task is calling genetic variants, assembling genomes, or any wet-lab sequencing analysis — this pipeline has nothing to do with NGS reads; pick a variant-calling, assembly, or rna-seq sketch instead.
- The user only needs a single-scene NDVI map or ad-hoc raster math — running the full FORCE pipeline is overkill; use a plain GDAL/rasterio script.
- Inputs are already FORCE level-2 ARD and only higher-level TSA is required — this sketch runs preprocessing too; a bespoke `force-higher-level` call is cheaper.
- Data are SAR-only (Sentinel-1), MODIS-only, or commercial very-high-resolution imagery not supported by FORCE level-2 processing.
- User wants per-object classification, deep-learning segmentation, or crop-type mapping from labeled samples — use a dedicated ML/geospatial sketch.

## Analysis outline
1. **Ingest inputs** — satellite scene directory (or tarball), DEM (`.vrt` + tile `.tif`s), water-vapor database, datacube `.prj`, AOI vector (`.gpkg`/`.shp`), and endmember `.txt`; tarballs are auto-extracted via the `UNTAR` module.
2. **Preparation** — `force-tile-extent` derives the allow-list of FORCE tiles covering the AOI; `force-cube` rasterizes the AOI into per-tile analysis masks (`aoi.tif`).
3. **Parameter generation** — `force-parameter` emits one FORCE level-2 parameter file per sensor per tile.
4. **Level-2 preprocessing** — `force-l2ps` per scene: cloud/shadow/water detection, atmospheric correction using the water-vapor DB, topographic correction via the DEM, resampling to the datacube grid, yielding ARD reflectance + quality `.tif`s.
5. **Temporal/spatial merging** — spatially/temporally overlapping ARD tiles are grouped (batch size controlled by `group_size`) and merged.
6. **Higher-level TSA** — `force-higher-level` runs spectral unmixing against the endmember library plus time-series analysis on the configured indices/bands, producing trend files (and optionally a time-series stack `TSS`).
7. **Visualization** — `force-mosaic` builds a full-resolution virtual raster mosaic of trend products; `force-pyramid` builds downsampled overviews per trend and tile.
8. **Reporting** — MultiQC aggregates tool versions and run metadata into a single HTML report.

## Key parameters
- `--input` / `--dem` / `--wvdb` / `--data_cube` / `--aoi` / `--endmember` / `--outdir`: all required; directories or tarballs accepted for the first three.
- `--sensors_level2`: FORCE sensor codes for higher-level processing, space-separated. Default `"LND04 LND05 LND07"`. Common values: `LND04`, `LND05`, `LND07`, `LND08`, `LND09`, `SEN2A`, `SEN2B`. Must be a subset of what is actually in `--input`.
- `--start_date` / `--end_date`: `YYYY-MM-DD` temporal window. Defaults `1984-01-01` → `2006-12-31`.
- `--resolution`: target pixel size in metres. Default `30` (native Landsat).
- `--indexes`: space-separated FORCE index/band codes fed to TSA. Default `"NDVI BLUE GREEN RED NIR SWIR1 SWIR2"`. Spectral unmixing is always on regardless.
- `--return_tss` (bool, default `false`): emit full per-date time-series stacks in addition to trend files.
- `--mosaic_visualization` (default `true`) and `--pyramid_visualization` (default `true`): toggle the two viz outputs. `mosaic_visualization` must stay on for the `test`/`test_full` profiles because golden-output checks rely on it.
- `--save_ard` / `--save_tsa` (both default `false`): publish level-2 ARD and level-3 TSA `.tif`s to `outdir`. Enable only if you need the intermediates — they are large.
- `--group_size`: tiles-per-merge batch. Default `100`; lower for I/O-bound clusters, higher for compute-bound ones.
- `--publish_dir_enabled` (default `true`): global kill-switch for all module outputs.
- `-profile`: pick a container profile (`docker`, `singularity`, `conda`, …); never run bare.

## Test data
The `test` profile pulls a downsampled Landsat 4/5 collection-2 archive, a matching DEM, and a global water-vapor database as three `.tar.gz` files from the `nf-core/test-datasets` `rangeland` branch, together with a datacube `.prj`, an `aoi.gpkg` vector, and the Hostert-2003 six-column endmember `.txt`. It restricts processing to `1987-01-01`–`1989-12-31`, sensors `LND04 LND05`, and uses `group_size = 10` with mosaic visualization enabled. Running it exercises untarring, tile-extent/cube preparation, FORCE level-2 preprocessing, higher-level TSA with spectral unmixing, and mosaic generation; expected outputs include `preparation/tile_allow.txt`, per-tile AOI masks, a `trend/mosaic/<product>/mosaic/` virtual raster, and a `multiqc/multiqc_report.html`. The `test_full` profile runs the same layout against a larger `1986–1989` archive on `s3://ngi-igenomes/test-data/rangeland/` and additionally sets `return_tss = true`.

## Reference workflow
[nf-core/rangeland v1.0.0](https://github.com/nf-core/rangeland) — built on the FORCE toolchain ([Frantz 2019, *Remote Sensing*](https://www.mdpi.com/2072-4292/11/9/1124)) and the FORCE-on-Nextflow design from Lehmann et al., CIKM Workshops 2021. See the [usage](https://nf-co.re/rangeland/usage) and [parameters](https://nf-co.re/rangeland/parameters) pages on nf-co.re for authoritative parameter definitions.
