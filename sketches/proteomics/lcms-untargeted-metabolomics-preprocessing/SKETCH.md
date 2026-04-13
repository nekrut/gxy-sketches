---
name: lcms-untargeted-metabolomics-preprocessing
description: Use when preprocessing untargeted LC-MS metabolomics data (mzML/mzXML/mzData/netCDF)
  to produce a feature table (data matrix) of peak intensities with retention-time
  alignment, gap filling, and isotope/adduct annotation. Starts from centroided profile
  files plus a sample metadata table and ends at an annotated feature matrix ready
  for downstream statistics.
domain: proteomics
organism_class:
- eukaryote
- any
input_data:
- lcms-mzml-collection
- sample-metadata-tsv
source:
  ecosystem: iwc
  workflow: 'Mass spectrometry: LC-MS preprocessing with XCMS'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/metabolomics/lcms-preprocessing
  version: '1.1'
  license: MIT
tools:
- MSnbase
- xcms
- CAMERA
- checkFormat
- intensity_checks
tags:
- metabolomics
- lc-ms
- xcms
- camera
- untargeted
- peak-picking
- w4m
- workflow4metabolomics
test_data:
- role: samplemetadata
  url: https://zenodo.org/records/10130758/files/sampleMetadata_12samp_completed.tsv
  sha1: 9cda46eac7cbb29508975327e410f729a4f1681c
  filetype: tabular
- role: mass_spectrometry_dataset_collection__blanc05_mzml
  url: https://zenodo.org/record/10130758/files/Blanc05.mzML
  sha1: e98d5a4cd8849a145a032bdc31c348ad97cb59c3
  filetype: mzml
- role: mass_spectrometry_dataset_collection__blanc10_mzml
  url: https://zenodo.org/record/10130758/files/Blanc10.mzML
  sha1: f94160cbf0ad978addf22c4095bf71e63399b0ee
  filetype: mzml
- role: mass_spectrometry_dataset_collection__blanc16_mzml
  url: https://zenodo.org/record/10130758/files/Blanc16.mzML
  sha1: 3b02bc4fea276877085a8eb4c46e3640aa8a3805
  filetype: mzml
- role: mass_spectrometry_dataset_collection__hu_neg_048_mzml
  url: https://zenodo.org/record/10130758/files/HU_neg_048.mzML
  sha1: a15d71219866c685bd1d2a606d53ce1ea0e746af
  filetype: mzml
- role: mass_spectrometry_dataset_collection__hu_neg_090_mzml
  url: https://zenodo.org/record/10130758/files/HU_neg_090.mzML
  sha1: 5f74defa70257351e83d3fd023647efd6968d4c1
  filetype: mzml
- role: mass_spectrometry_dataset_collection__hu_neg_123_mzml
  url: https://zenodo.org/record/10130758/files/HU_neg_123.mzML
  sha1: f2bc442c5def3b43ed2b5d0016a70bf787003eb5
  filetype: mzml
- role: mass_spectrometry_dataset_collection__hu_neg_157_mzml
  url: https://zenodo.org/record/10130758/files/HU_neg_157.mzML
  sha1: dbd3f58bb565fea8e4e6931544714248e406f3a5
  filetype: mzml
- role: mass_spectrometry_dataset_collection__hu_neg_173_mzml
  url: https://zenodo.org/record/10130758/files/HU_neg_173.mzML
  sha1: e4563814b88ee417de98f8dfefa672a09f8360c3
  filetype: mzml
- role: mass_spectrometry_dataset_collection__hu_neg_192_mzml
  url: https://zenodo.org/record/10130758/files/HU_neg_192.mzML
  sha1: 9feab3fc9a93f3f27989273eb8949a31a10793ec
  filetype: mzml
- role: mass_spectrometry_dataset_collection__qc1_002_mzml
  url: https://zenodo.org/record/10130758/files/QC1_002.mzML
  sha1: 0a3b086d6cd18dde58545765dd04510db866d652
  filetype: mzml
- role: mass_spectrometry_dataset_collection__qc1_008_mzml
  url: https://zenodo.org/record/10130758/files/QC1_008.mzML
  sha1: 70f5050107061c5fe9e06395d886472ae71177e8
  filetype: mzml
- role: mass_spectrometry_dataset_collection__qc1_014_mzml
  url: https://zenodo.org/record/10130758/files/QC1_014.mzML
  sha1: 6440a20460d754aa984e75f371259eef0acef1c0
  filetype: mzml
expected_output: []
---

# LC-MS untargeted metabolomics preprocessing (XCMS + CAMERA)

## When to use this sketch
- You have raw LC-MS metabolomics acquisitions (mzML, mzXML, mzData, or netCDF) from a single polarity run and want a feature table suitable for statistics.
- You need the canonical Workflow4Metabolomics pipeline: peak picking → grouping → RT alignment → regrouping → gap filling → CAMERA isotope/adduct annotation.
- You have (or can build) a sampleMetadata TSV describing classes, batches, injection order, and sample types (pool/sample/blank).
- You are working with centroided profile data from a typical reversed-phase UHPLC-HRMS setup (Q-Exactive, Orbitrap, Q-TOF).
- You want QC diagnostics: TIC/BPC chromatograms before and after RT alignment, chrom peak density plots, and intensity checks.

## Do not use when
- You have GC-MS data — use a GC-MS/eRah-style preprocessing sketch instead.
- You have DIA/SWATH or targeted MRM acquisitions — use a Skyline/OpenSWATH sketch.
- You want MS/MS-based compound identification (GNPS, SIRIUS, MetFrag) — this workflow stops at feature-level isotope/adduct grouping, not structural ID.
- You need shotgun proteomics (peptide identification) — use an OpenMS/MaxQuant proteomics sketch.
- You only need statistical analysis of an already-processed dataMatrix/variableMetadata/sampleMetadata triplet — use a W4M statistics sketch (Univariate, Multivariate, Biosigner).
- Your data is in vendor formats (.raw, .d, .wiff) without prior conversion — convert to mzML with msconvert first.

## Analysis outline
1. **MSnbase readMSData** — load the mzML collection into an MSnbase OnDiskMSnExp R object.
2. **xcms plot chromatogram** — render raw TIC and BPC PDFs for pre-processing QC.
3. **xcms findChromPeaks (xcmsSet)** — peak picking with the CentWave algorithm per sample.
4. **xcms findChromPeaks Merger** — merge per-sample peak results into a single xcmsSet using sampleMetadata.
5. **xcms groupChromPeaks (group)** — first grouping across samples using PeakDensity.
6. **xcms adjustRtime (retcor)** — retention-time alignment via PeakGroups + loess.
7. **xcms plot chromatogram** — TIC/BPC after alignment, to confirm RT correction.
8. **xcms groupChromPeaks (group)** — second grouping after RT adjustment.
9. **xcms fillChromPeaks (fillPeaks)** — integrate missing peaks to reduce NAs in the matrix.
10. **Check Format + Intensity Check** — sanity-check the dataMatrix/sampleMetadata/variableMetadata triplet and profile intensities per class.
11. **CAMERA.annotate** — group features by FWHM, annotate isotopes and adducts, export annotated variableMetadata.

## Key parameters
- **CentWave peak picking**: `ppm: 3.0`, `peakwidth: 5,20`, `snthresh: 10`, `prefilter: 3,5000`, `mzdiff: -0.001`, `noise: 1000`, `mzCenterFun: wMean`, `integrate: 1`. Tune `ppm` and `peakwidth` to instrument mass accuracy and chromatographic peak width.
- **groupChromPeaks (PeakDensity)**: `bw: 5.0`, `minFraction: 0.9`, `minSamples: 1`, `binSize: 0.01`, `maxFeatures: 50`. Lower `bw` after RT alignment if needed; relax `minFraction` for heterogeneous cohorts.
- **adjustRtime (PeakGroups / loess)**: `minFraction: 0.7`, `extraPeaks: 1`, `smooth: loess`, `span: 0.2`, `family: gaussian`.
- **fillChromPeaks**: `expandMz: 0`, `expandRt: 0`, `ppm: 0` (use detection-time peak bounds).
- **Peak list export**: `intval: into` (integrated intensity), `naTOzero: true`, `numDigitsMZ: 4`, `numDigitsRT: 0`.
- **CAMERA.annotate**: `sigma: 6`, `perfwhm: 0.6`, `maxcharge: 2`, `maxiso: 4`, `minfrac: 0.5`, `ppm: 5`, `mzabs: 0.015`, `quick: TRUE` (fast adduct/isotope grouping without diffreport). Set polarity to match acquisition when not using quick mode.
- **sampleMetadata** must contain a `class` column; classes drive the Intensity Check per-class stats and W4M downstream statistics.

## Test data
The bundled test uses 12 mzML files from Zenodo record 10130758: three procedural blanks (`Blanc05/10/16`), three pooled QC injections (`QC1_002/008/014`), and six study samples (`HU_neg_048/090/123/157/173/192`), all acquired in negative mode on a reversed-phase LC-HRMS system. A matching `sampleMetadata_12samp_completed.tsv` labels classes, injection order and sample types. Running the workflow produces an annotated feature table — the primary deliverables are the gap-filled `dataMatrix` (features × samples of integrated intensities) and the CAMERA `variableMetadata` enriched with isotope group, adduct and pseudo-spectrum columns; QC PDFs (raw and adjusted TIC/BPC, chrom peak density, raw-vs-adjusted RT, intensity check graphs) are produced alongside.

## Reference workflow
Galaxy IWC — `workflows/metabolomics/lcms-preprocessing` — "Mass spectrometry: LC-MS preprocessing with XCMS", release 1.1 (Workflow4Metabolomics). Based on xcms 3.12 (Smith et al., 2006) and CAMERA 1.48 (Kuhl et al., 2012); see the GTN tutorial `metabolomics/tutorials/lcms-preprocessing` for parameter rationale.
