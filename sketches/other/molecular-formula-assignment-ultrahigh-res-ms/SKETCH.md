---
name: molecular-formula-assignment-ultrahigh-res-ms
description: Use when you need to assign multi-element molecular formulas (CHO, CHNOS,
  etc.) to ultrahigh-resolution mass spectra (FT-ICR MS, Orbitrap) from a peak list
  of mass/intensity, including noise estimation, isotope filtering, and mass recalibration
  via the MFAssignR R package. Suited to non-targeted environmental or natural organic
  matter (NOM, DOM) metabolomics.
domain: other
organism_class:
- environmental
- non-targeted
input_data:
- ms-peak-list-tabular
source:
  ecosystem: iwc
  workflow: Molecular formula assignment and recalibration with MFAssignR package.
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/metabolomics/mfassignr
  version: '0.1'
  license: MIT
tools:
- MFAssignR
- KMDNoise
- HistNoise
- SNplot
- IsoFiltR
- MFAssignCHO
- RecalList
- FindRecalSeries
- Recal
- MFAssign
tags:
- metabolomics
- mass-spectrometry
- FTICR
- orbitrap
- molecular-formula
- recalibration
- noise-estimation
- van-krevelen
- NOM
- DOM
test_data: []
expected_output:
- role: recal_series
  path: expected_output/recal_series.tabular
  description: Expected output `recal_series` from the source workflow test.
  assertions: []
- role: final_series
  path: expected_output/final_series.tabular
  description: Expected output `final_series` from the source workflow test.
  assertions: []
- role: none
  path: expected_output/None.tabular
  description: Expected output `None` from the source workflow test.
  assertions: []
- role: ambig
  path: expected_output/Ambig.tabular
  description: Expected output `Ambig` from the source workflow test.
  assertions: []
- role: unambig
  path: expected_output/Unambig.tabular
  description: Expected output `Unambig` from the source workflow test.
  assertions: []
---

# Molecular formula assignment and recalibration for ultrahigh-resolution MS

## When to use this sketch
- You have a peak list (mass, intensity, optional retention time) from an ultrahigh-resolution mass spectrometer (FT-ICR MS or Orbitrap) and want to assign multi-element molecular formulas (C, H, O, and optionally N, S, P, halogens) to each peak.
- The data is non-targeted — typically dissolved/natural organic matter (DOM/NOM), environmental, or petroleomics samples — where CHO-dominant assignments and Van Krevelen diagrams are the expected deliverable.
- You need to estimate a signal-to-noise threshold from the spectrum itself (KMD- or histogram-based) rather than trusting vendor noise.
- You want to recalibrate the mass axis using unambiguous CHO assignments as internal calibrants before producing the final formula list.
- You are running on Galaxy (RECETOX MFAssignR tool suite) or are happy to call the underlying MFAssignR R package directly.

## Do not use when
- You have raw vendor files (.raw, .mzML, .d) and still need peak picking — run a centroiding/peak-picking workflow first, then feed the peak list here.
- You are doing LC-MS/MS small-molecule identification against spectral libraries (use an MS2 library-search sketch instead).
- You are doing targeted quantification of known metabolites (use an LC-MS targeted quant sketch).
- You need de novo structural elucidation beyond a molecular formula (SIRIUS/CSI:FingerID is the right tool).
- Your instrument is unit- or low-resolution (quadrupole, ion trap) — the KMD/ppm logic in MFAssignR assumes sub-ppm accuracy.
- You are working with proteomics or lipidomics pipelines with dedicated databases.

## Analysis outline
1. **Ingest peak list** — tabular file with columns `mass`, `intensity`, optional `retention_time`.
2. **Noise estimation (KMDNoise)** — estimate the noise level from the Kendrick mass defect slice between `lower_y=0.05` and `upper_y=0.2`.
3. **Noise estimation cross-check (HistNoise)** — histogram-based noise estimate (bin `0.01`) as a sanity check against KMDNoise.
4. **SN diagnostic plot (SNplot)** — visualise the S/N cutoff around a reference mass (`mass=301`, `sn_ratio=6`) to confirm the chosen threshold.
5. **Isotope filtering (IsoFiltR)** — split peaks into monoisotopic (`mono_out`) and isotopologue (`iso_out`) tables using 13C/34S abundance checks.
6. **Initial CHO assignment (MFAssignCHO)** — assign CHO-only formulas to the monoisotopic peaks within `lowMW=50`–`highMW=1000`, ppm window `3`, negative ion mode, using `Ox=30`, H/C 0.1–3.0, O/C 0.0–2.5, DBE-O −13 to 13, five iteration loops.
7. **Build recalibration candidate list (RecalList)** — from unambiguous CHO hits, produce a candidate series list for mass recalibration.
8. **Select recalibration series (FindRecalSeries)** — pick best homologous series by coverage (≥90%), abundance score (≥100), and peak-distance threshold (2.0); up to 5 combinations across the full mass range.
9. **Recalibrate (Recal)** — apply the chosen series to the mono + iso peaks with a 50 Da rolling window, H2 step 5, O step 3, producing recalibrated Mono/Iso tables plus an `MZplot`.
10. **Final multi-element assignment (MFAssign)** — re-run formula assignment on recalibrated peaks, now allowing N, S, P and other heteroatoms per project needs, with isotope error `3` ppm, sulfur check on, N3 correction on, and produce Unambig/Ambig/None outputs plus Van Krevelen and MS-assignment plots.

## Key parameters
- `ionmode`: `neg` (workflow default; flip to `pos` for ESI+).
- `sn_ratio`: `6` — global S/N cutoff used across noise, isotope filtering, assignment, and recalibration steps.
- `ppm_err`: `3` — mass accuracy tolerance for MFAssignCHO and MFAssign.
- `lowMW` / `highMW`: `50` / `1000` Da — assignment mass window.
- `kmdn`: `346` — Kendrick mass defect normalisation reference used in IsoFiltR, MFAssignCHO, Recal, and MFAssign (must be consistent across steps).
- `Ox=30`, `H/C=0.1–3.0`, `O/C=0.0–2.5`, `DBE-O=-13..13`, `nLoop=5`, `max_def=0.9`, `min_def=0.5`, `NMScut=on` — MFAssignCHO/MFAssign chemistry constraints.
- IsoFiltR: `Carbrat=60`, `Carberr=5`, `Sulfrat=30`, `Sulferr=5` — 13C/34S abundance tolerance windows.
- KMDNoise: `lower_y=0.05`, `upper_y=0.2` — KMD band used for noise estimation.
- FindRecalSeries: `coverage_threshold=90`, `abundance_score_threshold=100`, `peak_distance_threshold=2.0`, `number_of_combinations=5`, `global_min=0`, `global_max=1000`.
- Recal: `CalPeak=150`, `mzRange=50`, `step_H2=5`, `step_O=3` — rolling recalibration window and homologous step sizes.
- MFAssign heteroatoms: leave `Nx/Sx/Px=0` for a CHO-only final pass, or raise them (with corresponding valences `Sval=2`, `Nval=3`, `Pval=5`) for CHNOS(P) assignments; `SulfCheck=on`, `N3corr=on` are recommended defaults.

## Test data
The reference test job feeds a single tabular peak list — `mfassignr_input.txt` fetched from Zenodo (record 13768009, SHA-1 `3df0ba47c756a4b90f39b73f19471cb595823e23`) — into the workflow as the `Feature table` input. Expected tabular outputs (golden files under `test-data/`) are `recal_series.tabular` and `final_series.tabular` from the recalibration-series selection, plus the final `Unambig.tabular`, `Ambig.tabular`, and `None.tabular` assignment tables from MFAssign. Image outputs (`SNplot.png`, `MZplot.png`, and the `plots`/`plots (CHO)` collections containing `MSgroups`, `VK`, `errorMZ`, `msassign`) are validated by file-size assertions (e.g. SNplot ≈ 58 KB, MZplot ≈ 85 KB, Van Krevelen ≈ 866–898 KB) rather than pixel-level comparison.

## Reference workflow
Galaxy IWC: `workflows/metabolomics/mfassignr` — "Molecular formula assignment and recalibration with MFAssignR package" v0.1, maintained by RECETOX (Masaryk University). Built on the RECETOX MFAssignR Galaxy tool suite (`mfassignr_*` tools at version `1.1.2+galaxy{0,1}`), which wraps the MFAssignR R package.
