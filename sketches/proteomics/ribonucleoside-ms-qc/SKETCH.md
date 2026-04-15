---
name: ribonucleoside-ms-qc
description: Use when you need automated quality control of ribonucleoside (modified
  RNA nucleoside) analysis by LC-MS on Thermo instruments, monitoring mass spectrometer
  performance from Thermo .raw files using a predefined analyte panel with theoretical
  retention times and m/z values.
domain: proteomics
organism_class:
- not-applicable
input_data:
- thermo-raw-ms
- analytes-tsv
source:
  ecosystem: nf-core
  workflow: nf-core/ribomsqc
  url: https://github.com/nf-core/ribomsqc
  version: 1.0.0
  license: MIT
  slug: ribomsqc
tools:
- name: ThermoRawFileParser
  version: 1.4.5
- name: MSnbase
- name: MultiQC
  version: '1.31'
tags:
- mass-spectrometry
- qc
- ribonucleosides
- rna-modifications
- xic
- lc-ms
- thermo-raw
- instrument-performance
test_data: []
expected_output: []
---

# Ribonucleoside LC-MS instrument QC

## When to use this sketch
- You are running LC-MS(/MS) assays on modified ribonucleosides (e.g. C, U, m3C, m5C, Cm, m5U, I, m1A, G, m7G) and need to monitor instrument performance over time.
- Input data are Thermo `.raw` files from a targeted ribonucleoside QC standard mix with known theoretical retention times.
- You want per-sample QC metrics (Δm/z in ppm, FWHM, log2 total peak area, observed RT) extracted from XICs of a defined analyte panel and summarised in a MultiQC report.
- You have (or can produce) a TSV listing analytes with `short_name`, `long_name`, `mz_M0`, optional `mz_M1`/`mz_M2`/`ms2_mz`, and `rt_teoretical` (seconds) calibrated to your own chromatography.
- Use case is longitudinal instrument/column health monitoring, not discovery quantification of RNA modifications in biological samples.

## Do not use when
- You need quantitative profiling of RNA modifications in biological samples (this sketch is QC of the instrument, not biology) — use a dedicated RNA modification quantification workflow.
- Your raw data come from a non-Thermo vendor (Bruker, Sciex, Waters, Agilent): ThermoRawFileParser only handles Thermo `.raw`. Convert to mzML upstream or use a vendor-appropriate pipeline.
- You are doing bottom-up or top-down proteomics QC — use nf-core/quantms or proteomics-specific QC pipelines (PTXQC, QCloud) instead.
- You are doing metabolomics QC at large (untargeted) — use an untargeted LC-MS pipeline; this sketch is strictly targeted XIC on a small ribonucleoside panel.
- You only need format conversion — run ThermoRawFileParser directly rather than the full QC pipeline.

## Analysis outline
1. **Ingest samplesheet** (`samplesheet.csv` with `id,raw_file` columns) listing one or more Thermo `.raw` files.
2. **ThermoRawFileParser** — convert each `.raw` to open-format `.mzML`.
3. **MSnbase XIC extraction** (R/Bioconductor) — for each sample × analyte, extract XIC at `mz_M0 ± mz_tolerance` ppm within `rt_teoretical ± rt_tolerance` seconds at the configured `ms_level`; compute Δm/z (ppm), observed RT, peak area, and FWHM; emit one `*_mqc.json` per metric per sample.
4. **Merge JSONs** — consolidate per-sample metric fragments into `dmz_ppm_merged_mqc.json`, `FWHM_merged_mqc.json`, `Log2_Total_Area_merged_mqc.json`, `Observed_RT_sec_merged_mqc.json`.
5. **MultiQC** — render an interactive HTML report aggregating the merged QC metric tables across samples for longitudinal review.

## Key parameters
- `--input` — samplesheet CSV with `id,raw_file` (Thermo `.raw` paths).
- `--analytes_tsv` — tab-separated analyte panel; mandatory columns `short_name`, `long_name`, `mz_M0`, `rt_teoretical`; optional `mz_M1`, `mz_M2`, `ms2_mz`. You must recalibrate `rt_teoretical` to your own chromatography.
- `--analyte` — `all` to process every row of the TSV, or a specific `short_name` such as `m3C`.
- `--ms_level` — `1` for MS1-level XICs (precursor `mz_M0`), `2` for MS2-level XICs (uses `ms2_mz`). Default `2`.
- `--mz_tolerance` — ppm window around `mz_M0` (default `20`; tighten to ~7 ppm on high-resolution Orbitraps).
- `--rt_tolerance` — seconds around `rt_teoretical` (default `150`).
- `--plot_xic_ms1` / `--plot_xic_ms2` — toggle PDF XIC plots; `--plot_output_path` names the PDF.
- `--overwrite_tsv` — if true, accumulate XIC results into a progressively updated TSV alongside the input analytes file.
- `--outdir` — results directory (contains `thermorawfileparser/`, `msnbasexic/`, `mergejsons/`, `multiqc/`, `pipeline_info/`).
- `-profile` — `singularity`/`docker`/`conda` for reproducible execution.

## Test data
The pipeline's built-in `test` profile points at the nf-core test-datasets repo (`ribomsqc/pipelines/ribomsqc/testdata/`) and consists of a `samplesheet.csv` referencing one or more small Thermo `.raw` files plus an `analytes.tsv` defining the ribonucleoside panel. The test profile fixes `--analyte C`, `--ms_level 1`, and enables `test_mode = true` so the pipeline does not fail when analytes are absent from a minimal CI dataset. A successful run produces converted `*.mzML` files under `thermorawfileparser/`, per-sample metric JSONs under `msnbasexic/`, the four merged `*_mqc.json` summaries under `mergejsons/` (`dmz_ppm`, `FWHM`, `Log2_Total_Area`, `Observed_RT_sec`), and a `multiqc/multiqc_report.html` aggregating them.

## Reference workflow
[nf-core/ribomsqc v1.0.0](https://github.com/nf-core/ribomsqc) — QC pipeline that monitors mass spectrometer performance in ribonucleoside analysis (ThermoRawFileParser → MSnbase XIC → JSON merge → MultiQC). Originally written by Roger Olivella.
