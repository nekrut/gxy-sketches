---
name: lcms-untargeted-metabolomics-preprocessing-nextflow
description: Use when you need to go from raw LC-MS mzML files to a table of aligned,
  quantified, and (optionally) identified metabolite features for untargeted metabolomics.
  Covers feature detection, adduct deconvolution, RT alignment, cross-sample linking,
  gap-filling, and MS2-based identification via SIRIUS/CSI:FingerID and MS2Query.
  Assumes high-resolution MS1 (and optional MS2) data in a single polarity.
domain: other
organism_class:
- eukaryote
- any
input_data:
- mzml-ms1
- mzml-ms2
- samplesheet-csv
source:
  ecosystem: nf-core
  workflow: nf-core/metaboigniter
  url: https://github.com/nf-core/metaboigniter
  version: 2.0.1
  license: MIT
  slug: metaboigniter
tools:
- name: openms
- name: featurefindermetabo
- name: metaboliteadductdecharger
- name: mapalignerposeclustering
- name: featurelinkerunlabeledkd
- name: featurefindermetaboident
- name: sirius
- name: csi-fingerid
- name: ms2query
- name: pyopenms
tags:
- metabolomics
- lc-ms
- untargeted
- mass-spectrometry
- feature-detection
- adduct-detection
- ms2
- compound-identification
- openms
test_data: []
expected_output: []
---

# Untargeted LC-MS metabolomics preprocessing and identification

## When to use this sketch
- User has raw high-resolution LC-MS data in **mzML** format (profile or already-centroided) and wants a feature table across samples.
- Experiment is **untargeted metabolomics / small-molecule profiling** on an Orbitrap, Q-TOF, or FT-ICR instrument.
- A **single polarity** per run (positive OR negative) with optional dedicated MS2/DDA acquisitions for identification.
- User wants any combination of: peak picking, feature detection, adduct deconvolution, RT alignment, feature linking across samples, gap-filling ("requantification"), and compound ID via **SIRIUS + CSI:FingerID** and/or **MS2Query**.
- Samples are described in a simple CSV samplesheet with columns `sample,level,type,msfile` where `level` is one of `MS1`, `MS2`, `MS12`.

## Do not use when
- Data is targeted/SRM/MRM quantification against known standards with calibration curves — this pipeline does not do absolute quantification.
- Input is raw vendor format (.raw, .d, .wiff). Convert to mzML first (e.g. with ThermoRawFileParser or msconvert) before invoking.
- You need **proteomics** identification from MS2 (peptides/proteins) — use a proteomics pipeline instead.
- You need **lipidomics-specific** class annotation beyond generic feature finding — consider a dedicated lipidomics workflow.
- You need GC-MS / EI deconvolution — this is LC-MS/ESI oriented.
- You want statistical analysis, normalization, or biomarker discovery on the feature table — that is downstream of this sketch.

## Analysis outline
1. **(Optional) Centroiding** of profile-mode spectra with OpenMS `PeakPickerHiRes` (skipped by default via `skip_centroiding=true`; enable only for profile data).
2. **Feature (mass trace) detection** per MS1/MS12 file with OpenMS `FeatureFinderMetabo`, producing `*.featureXML`.
3. **Adduct detection / charge deconvolution** with `MetaboliteAdductDecharger` using a polarity-specific adduct list.
4. **Retention time alignment** across maps with `MapAlignerPoseClustering` (can be disabled with `skip_alignment`).
5. **Cross-sample feature linking** into a consensus map with `FeatureLinkerUnlabeledKD`; optionally partitioned (`parallel_linking`) for large cohorts.
6. **(Optional) Gap-filling / requantification** with `FeatureFinderMetaboIdent` to recover missing values across samples (adapted from UmetaFlow).
7. **MS2–feature mapping** using pyOpenMS, exporting MGF; parallelizable via `split_consensus_parts` and `mgf_splitmgf_pyopenms`.
8. **Compound identification** (optional, `--identification`):
   - **SIRIUS** for molecular formula (`run_sirius`), optionally followed by **CSI:FingerID** for structure (`sirius_runfid`, requires SIRIUS account credentials).
   - **MS2Query** analogue search against an MS2Query model library (`run_ms2query`).
9. **Output generation**: TSV tables under `TABLE_OUTPUT/` joined by a shared feature `id` column — quantification, SIRIUS formulas, FingerID structures, and MS2Query analogues.

## Key parameters
- `polarity`: `positive` or `negative` — governs which adduct list is used.
- `ms2_collection_model`: `paired` when MS2 is acquired in-line with every MS1 run; `separate` when MS2 is only in dedicated DDA files. Use `separate` whenever any samplesheet row has `level=MS2`.
- `adducts_pos` / `adducts_neg`: space-separated `adduct:charge:probability` triples (defaults `H:+:0.6 Na:+:0.1 NH4:+:0.1 H-1O-1:+:0.1 H-3O-2:+:0.1` and `H-1:-:0.8 H-3O-1:-:0.2`).
- `algorithm_mtd_mass_error_ppm_featurefindermetabo_openms`: MS1 mass accuracy for mass trace detection (default `20` ppm; tighten to 5–10 for Orbitrap/FT-ICR).
- `algorithm_common_chrom_fwhm_featurefindermetabo_openms`: expected chromatographic peak width in seconds (default `5`).
- `algorithm_ffm_charge_lower_bound` / `_upper_bound_featurefindermetabo_openms`: charge range (default 1/1; metabolomics is typically singly charged).
- `algorithm_ffm_isotope_filtering_model_featurefindermetabo_openms`: `metabolites (5% RMS)` by default; use `metabolites (2% RMS)` for very clean Orbitrap data.
- `algorithm_link_rt_tol` / `algorithm_link_mz_tol_featurelinkerunlabeledkd_openms`: linking tolerances (defaults 30 s / 10 ppm).
- `requantification`: enable to fill missing values.
- `identification`, `run_sirius`, `sirius_runfid`, `run_ms2query`: toggles for identification branches. `sirius_runfid` additionally requires `sirius_email` and `sirius_password`.
- `sirius_sirius_profile`: `default | qtof | orbitrap | fticr` — **set to match the instrument**.
- `sirius_sirius_ppm_max` (MS1) and `sirius_sirius_ppm_max_ms2` (MS2): SIRIUS mass tolerances (default 10 ppm each).
- Performance knobs for large studies: `parallel_linking` + `algorithm_nr_partitions_featurelinkerunlabeledkd_openms`, `split_consensus_parts`, `mgf_splitmgf_pyopenms`, `sirius_split`.

## Test data
The pipeline's `test` profile pulls a minimal samplesheet from the `nf-core/test-datasets` `metaboigniter` branch pointing at a handful of small mzML files (positive mode LC-MS MS1 replicates plus a pooled MS2 file) as described in the README example (`CONTROL_REP1/CONTROL_REP2` at `MS1` level and `POOL_MS2` at `MS2` level). It runs the preprocessing path only, constrained to a single charge state (`algorithm_ffm_charge_upper_bound_featurefindermetabo_openms=1`) and capped at 2 CPU / 6 GB RAM for CI. The `test_full` profile uses the same samplesheet but flips on `identification`, `requantification`, `run_sirius` (with `sirius_split` and `mgf_splitmgf_pyopenms=100`), and `run_ms2query` in `separate` MS2 mode. Expected outputs are per-sample `*.featureXML` files under `quantification/`, `annotation/`, `alignment/`, and `linking/*.consensusXML`, plus TSV tables under `TABLE_OUTPUT/` (`output_quantification_*.tsv` always; `output_sirius_*.tsv`, `output_fingerid_*.tsv`, and `output_ms2query_*.tsv` when the corresponding identification flags are enabled) joined by a shared `id` column.

## Reference workflow
nf-core/metaboigniter v2.0.1 (https://github.com/nf-core/metaboigniter, DOI 10.5281/zenodo.4743790). Built on OpenMS, SIRIUS 4/5 + CSI:FingerID, and MS2Query; identification and requantification logic adapted from UmetaFlow.
