---
name: gcms-untargeted-metabolomics-metams
description: Use when you need to process GC-MS (gas chromatography-mass spectrometry)
  raw data for untargeted metabolomics, producing pseudo-spectra, a peak/data matrix,
  and multivariate (PCA) exploration of samples. Assumes low-resolution GC-MS profile
  data in open formats (mzXML, mzML, mzData, netCDF) with a companion sampleMetadata
  table.
domain: proteomics
organism_class:
- eukaryote
input_data:
- gcms-raw-spectra
- sample-metadata-tsv
source:
  ecosystem: iwc
  workflow: 'Mass spectrometry: GCMS with metaMS'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/metabolomics/gcms-metams
  version: '0.2'
  license: MIT
  slug: metabolomics--gcms-metams
tools:
- name: MSnbase
  version: 2.16.1+galaxy3
- name: xcms
  version: 3.12.0+galaxy3
- name: metaMS
  version: 3.0.0+metaMS1.24.0-galaxy0
- name: CAMERA
- name: Workflow4Metabolomics-checkFormat
- name: Workflow4Metabolomics-Multivariate
tags:
- metabolomics
- GC-MS
- untargeted
- workflow4metabolomics
- W4M
- pseudo-spectra
- PCA
- xcms
- metaMS
test_data:
- role: samplemetadata
  url: https://zenodo.org/record/3631074/files/sampleMetadata.tsv
  sha1: f53ce5d942cb0a100271d9d30522f7907fe73539
  filetype: tabular
- role: mass_spectrometry_dataset_collection__alg11_mzdata
  url: https://zenodo.org/record/3631074/files/alg11.mzData
  sha1: a22551846483b168a0f3e1e5b96dc92546cffea0
  filetype: mzdata
- role: mass_spectrometry_dataset_collection__alg2_mzdata
  url: https://zenodo.org/record/3631074/files/alg2.mzData
  sha1: 0518c82e67395a56d5d7682beca956822ce1181e
  filetype: mzdata
- role: mass_spectrometry_dataset_collection__alg3_mzdata
  url: https://zenodo.org/record/3631074/files/alg3.mzData
  sha1: 97ba20db9d6fe759390c81ff75b52dbdaf1bcd4b
  filetype: mzdata
- role: mass_spectrometry_dataset_collection__alg7_mzdata
  url: https://zenodo.org/record/3631074/files/alg7.mzData
  sha1: 089fd36d4e2c9071a3279e84b741422b374a482d
  filetype: mzdata
- role: mass_spectrometry_dataset_collection__alg8_mzdata
  url: https://zenodo.org/record/3631074/files/alg8.mzData
  sha1: bc11441555d93ce2188aae82ae0c40a390426ddf
  filetype: mzdata
- role: mass_spectrometry_dataset_collection__alg9_mzdata
  url: https://zenodo.org/record/3631074/files/alg9.mzData
  sha1: dba9cbd014e0e15f4188d7ac18a133b27497953d
  filetype: mzdata
expected_output:
- role: metams_rungc_datamatrix
  path: expected_output/metaMS.runGC_dataMatrix.tabular
  description: Expected output `metaMS.runGC dataMatrix` from the source workflow
    test.
  assertions: []
- role: multivariate_variablemetadata
  description: Content assertions for `Multivariate variableMetadata`.
  assertions:
  - 'that: has_n_lines'
  - 'n: 42'
  - 'that: has_text'
  - "text: Unknown 1\tUnknown\t0.0046\t19.499\t-0.17"
  - 'that: has_text'
  - "text: Unknown 41\tUnknown\t0.0039\t14.857\t-0.08"
- role: multivariate_samplemetadata
  description: Content assertions for `Multivariate sampleMetadata`.
  assertions:
  - 'that: has_n_lines'
  - 'n: 7'
  - 'that: has_text'
  - "text: alg11\tFWS_100perNaCl\t-6."
  - 'that: has_text'
  - "text: alg8\tFWS_5percNaCL\t-0.6"
---

# GC-MS untargeted metabolomics with metaMS

## When to use this sketch
- You have GC-MS raw files (mzXML, mzML, mzData, or netCDF) from an untargeted metabolomics experiment and want to go from raw spectra to a ready-to-analyse data matrix.
- You need pseudo-spectra reconstruction via the metaMS `runGC` workflow (component detection, spectra clustering, optional RI filtering and DB matching).
- You need peak picking tuned for unit-resolution GC-MS data using the xcms `MatchedFilter` method (not centWave).
- You want an end-to-end W4M pipeline that also produces TIC/BPI chromatogram QC plots and a PCA-based multivariate overview of samples.
- A sampleMetadata table describing classes/batches/conditions per raw file is (or can be) provided alongside the spectra.

## Do not use when
- Your data are LC-MS (high-resolution Orbitrap/QTOF, centWave peak picking, CAMERA adduct/isotope annotation) — use an LC-MS / XCMS+CAMERA sketch instead.
- You are doing targeted quantification against a spike-in standard curve — use a targeted MRM/SRM sketch.
- You need shotgun / DDA bottom-up proteomics (MaxQuant, FragPipe, MSGF+) — use a proteomics sketch.
- You only need raw-file conversion or QC (msconvert, ThermoRawFileParser) without downstream peak picking.
- Your data come from MALDI imaging or ion mobility experiments.

## Analysis outline
1. **Read raw spectra** — `MSnbase readMSData` ingests the Dataset Collection of mzXML/mzML/mzData/netCDF files into an `OnDiskMSnExp` RData object.
2. **Peak picking** — `xcms findChromPeaks (xcmsSet)` with `method=MatchedFilter` extracts chromatographic peaks per sample.
3. **QC visualization** — `xcms plot chromatogram` generates TIC and BPI PDFs per sample, using the sampleMetadata for class coloring.
4. **Merge per-sample results** — `xcms findChromPeaks Merger` combines individual xcmsSet RData objects with the sampleMetadata into one xset.
5. **Pseudo-spectra construction** — `metaMS.runGC` groups co-eluting fragments into pseudo-spectra and emits `peaktable`, `dataMatrix`, `sampleMetadata`, `variableMetadata`, `peakspectra` (msp) and an RData object.
6. **Format sanity check** — W4M `Check Format` harmonises the dataMatrix / sampleMetadata / variableMetadata trio for downstream statistical tools.
7. **Multivariate analysis** — W4M `Multivariate` runs PCA (with standard scaling, 20 permutations, 3-fold CV) and outputs annotated metadata tables plus summary PDFs.

## Key parameters
- `xcms findChromPeaks`:
  - `method: MatchedFilter` (required for low-resolution GC-MS)
  - `fwhm: 5`
  - `binSize (step): 0.5`
  - `snthresh: 2`, `steps: 2`, `max: 500`, `mzdiff: 0.5`
- `metaMS.runGC` (user settings):
  - `rtdiff: 0.05` (retention time tolerance, minutes)
  - `minfeat: 5` (minimum features per pseudo-spectrum)
  - `simthreshold: 0.7` (spectral similarity cutoff)
  - `minclassfraction: 0.5`, `minclasssize: 3`
  - RI filter, RI calibration and DB matching left disabled by default.
- `Multivariate` (PCA):
  - `opcC: full`, `scaleC: standard`, `permI: 20`, `crossvalI: 3`, `orthoI: 0`, `algoC: default`.
- `Check Format`: `makeNameL: FALSE`.

## Test data
The reference test job uses six low-resolution GC-MS runs from the W4M GC-MS training dataset hosted on Zenodo record 3631074 (`alg2.mzData`, `alg3.mzData`, `alg7.mzData`, `alg8.mzData`, `alg9.mzData`, `alg11.mzData`) plus a companion `sampleMetadata.tsv` describing sample classes such as `FWS_100perNaCl` and `FWS_5percNaCL`. A successful run is expected to produce a `metaMS.runGC dataMatrix` tabular matching the golden `metaMS.runGC_dataMatrix.tabular` (allowing ~16 lines of diff for non-deterministic ordering), a `Multivariate variableMetadata` table of 42 lines containing rows for unknown pseudo-compounds such as `Unknown 1` and `Unknown 41`, and a `Multivariate sampleMetadata` table of 7 lines containing `alg11` (FWS_100perNaCl) and `alg8` (FWS_5percNaCL) with their PCA scores.

## Reference workflow
Galaxy IWC — `workflows/metabolomics/gcms-metams/Mass-spectrometry__GCMS-with-metaMS.ga`, release 0.2 (Workflow4Metabolomics, MIT). Based on the Galaxy Training Network tutorial *Mass spectrometry: GC-MS analysis with metaMS package* and built on xcms 3.12, MSnbase 2.16, metaMS 1.24, and the W4M `checkFormat` / `Multivariate` tools.
