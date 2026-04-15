---
name: meerkat-pulsar-timing
description: Use when you need to process raw MeerKAT PTUSE fold-mode pulsar archives
  into cleaned, calibrated, decimated archives plus Times of Arrival (ToAs) for pulsar
  timing analysis (MeerTime project). Produces DM/RM measurements, timing residuals,
  and data-portal images for single pulsars or batches selected from PSRDB.
domain: other
organism_class:
- not-applicable
input_data:
- meerkat-fold-archives
- psrchive-ar
- pulsar-ephemeris
- pulsar-template
source:
  ecosystem: nf-core
  workflow: nf-core/meerpipe
  url: https://github.com/nf-core/meerpipe
  version: dev
  license: MIT
  slug: meerpipe
tools:
- name: psrchive
- name: meerguard
- name: pac
- name: pam
- name: dlyfix
- name: psrstat
- name: pdv
- name: tempo2
- name: rmfit
- name: pdmp
- name: pat
- name: psrplot
- name: scintools
- name: psrdb
tags:
- pulsar
- meerkat
- meertime
- timing
- toas
- psrchive
- radio-astronomy
- dm
- rm
- scintillation
test_data: []
expected_output: []
---

# MeerKAT pulsar timing (MeerTime / meerpipe)

## When to use this sketch
- You have raw MeerKAT PTUSE fold-mode pulsar archives (`.ar` files) laid out as `<input_dir>/<pulsar>/<utc>/<beam>/<freq>/*.ar` and want a cleaned, polarisation- and flux-calibrated archive plus timing products.
- You need per-observation DM and RM measurements, signal-to-noise and flux density diagnostics, and publication-style pulse-profile / phase-vs-time / phase-vs-frequency images.
- You need decimated archives (multiple nchan/npol/nsub combinations) and Times of Arrival (ToAs) generated with `pat` against project-specific ephemerides and templates for downstream tempo2 timing.
- You want to (optionally) upload images, `results.json`, ToAs and residuals to the MeerTime data portal (pulsars.org.au) via `psrdb`.
- You are selecting observations out of the MeerTime PSRDB by pulsar J-name, UTC range, and/or project code (PTA, TPA, Relbin, GC), or providing an `obs_csv` listing.

## Do not use when
- Your data are not MeerKAT/PTUSE fold-mode archives — generic `psrchive` timing pipelines outside the MeerTime ecosystem are more appropriate.
- You have search-mode filterbank data and need to fold or search for pulsars (use a pulsar search pipeline, not meerpipe).
- You want whole-telescope imaging / continuum calibration of MeerKAT visibilities — this is a pulsar-archive pipeline, not a radio-interferometry imaging pipeline.
- Your task is genomic variant calling, RNA-seq, or any biological sequencing analysis — this pipeline is astronomical despite living in nf-core.
- You do not have access to the MeerTime ephemeris/template repository and PSRDB credentials; without a template, only a raw archive is emitted and DM/RM/ToA steps are skipped.

## Analysis outline
1. **OBS_LIST** — query PSRDB with pulsar/utcs/utce/project filters (or read `obs_csv`), resolve ephemeris + template per pulsar/project, locate archive files under `input_dir`.
2. **PSRADD_CALIBRATE_CLEAN** — `psradd` raw subints (dropping first/last ~8 s unless `use_edge_subints`), RFI-clean with MeerGuard, polarisation-calibrate with `pac` using SARAO Jones matrices, apply ATNF rotation measure with `pam`, correct delays with `dlyfix`, flux-calibrate with `fluxcal_meerkat` (Calabretta 2014 sky map + bootstrap Tsky), then compute S/N with `psrstat` and flux density with `pdv`.
3. **DM_RM_CALC** — if S/N>20: `pam`-scrunch to 16 channels, make ToAs with `pat`, fit DM with tempo2 and RM with `rmfit`; if S/N≤20: DM via `pdmp`, skip RM; skip entirely if no template.
4. **GENERATE_IMAGE_RESULTS** — build `psrplot` diagnostics (profile_ftp/fts, phase_time, phase_freq, bandpass, SNR_cumulative/single, rmfit, dmfit) and scintools dynamic spectra; aggregate into `results.json`.
5. **UPLOAD_IMAGE_RESULTS** — push images + `results.json` to pulsars.org.au via `psrdb` (skip if `upload=false`).
6. **GRAB_ALL_PAIRS** — enumerate all (ephemeris, template) pairs per pulsar/project for project-specific ToA generation.
7. **DECIMATE** — `chop_edge_channels` then `pam` decimate to the cartesian product of `nchans` × `npols` × nsub types (1 / all / mode / max via `calc_max_nsub`).
8. **GENERATE_TOAS** — `pat` ToAs for decimations with `nchan < max_nchan_upload` (default 32) for each project.
9. **UPLOAD_TOAS** — upload ToAs to the MeerTime data portal.
10. **GENERATE_RESIDUALS** — once all ToA uploads finish, per pulsar/project: download all historical ToAs and fit residuals with tempo2, uploading residuals back to the portal.

## Key parameters
- Observation selection: `--pulsar <Jname>`, `--utcs`/`--utce` (YYYY-MM-DD-HH:MM:SS), `--project` (PTA/TPA/Relbin/GC), or `--obs_csv <file>`.
- `--input_dir` (default `/fred/oz005/timing`) and `--outdir` (default `/fred/oz005/timing_processed`) — must match the `<pulsar>/<utc>/<beam>/<freq>` layout.
- `--ephemeris` / `--template` — override repo-resolved `.par` / `.std` for single-observation runs.
- `--chop_edge true` (default) — strip edge frequency channels before decimation.
- `--nchans '1,8,16,32,928'`, `--npols '1,4'` — decimation grid; must include the channel counts you need ToAs at.
- `--use_max_nsub true`, `--use_all_nsub true`, `--use_mode_nsub true` — which nsub strategies to emit; `--tos_sn 12` sets the target ToA S/N used by `calc_max_nsub` ($nsub = (S/N / S/N_D)^2 / nchan$, floor 480 s per subint).
- `--max_nchan_upload 32` — cap on decimation nchan that is turned into ToAs/residuals.
- `--use_prev_ar` / `--refold_prev_ar` — reuse previously cleaned archives to skip the expensive calibrate/clean stage.
- `--upload true` with `PSRDB_URL` / `PSRDB_TOKEN` env vars — enables portal upload; set `upload=false` for local-only runs.

## Test data
The `test` profile points at `tests/test_data/obs_short_test.csv`, a minimal PSRDB-style observation manifest with columns `Obs ID, Pulsar Jname, UTC Start, Project Short Name, Beam #, Observing Band, Duration (s), Mode Duration (s), Nchan, Nbin, Calibration Location`. It resolves a handful of short MeerKAT L-band fold archives for TPA/PTA pulsars such as J1410-7404, J1418-3921, J1534-5334, J1013-5934 and J0437-4715; `upload` is forced to false and resources are capped at 2 CPUs / 6 GB / 6 h. The `test_full` profile uses `obs_variety_of_pulsars.csv` covering a broader set. Expected outputs (per `<pulsar>/<utc>/<beam>` directory) are a cleaned zap archive `<pulsar>_<utc>_zap.ar` (or `_raw.ar` when no template is available), a `results.json` with S/N, flux, DM and RM, an `images/` directory with the `cleaned_*` png diagnostics, a `decimated/` directory populated with the nchan×npol×nsub grid of `.ar` files, and `timing/<project>/` subdirectories containing `<pulsar>.par`, `<pulsar>.std` and per-decimation `.tim` ToA files.

## Reference workflow
nf-core/meerpipe (dev), https://github.com/nf-core/meerpipe — built on the OZGrav meerpipe processing recipe for the MeerTime project (Bailes et al. 2020, PASA 37, 28), using psrchive, MeerGuard, tempo2 and scintools. See `docs/usage.md` and `docs/output.md` in the repo for the full parameter and output reference.
