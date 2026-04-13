---
name: dia-proteomics-quantification
description: Use when you need to perform label-free quantitative analysis of data-independent
  acquisition (DIA / SWATH-MS) proteomics mzML files against a spectral library, including
  FDR-controlled peptide/protein quantification and optional MSstats statistical comparison
  across conditions. Handles library generation from matched DDA runs when no pre-built
  library exists.
domain: proteomics
organism_class:
- eukaryote
input_data:
- dia-mzml
- spectral-library
- irt-library
- dda-mzml-optional
- dda-identifications-optional
source:
  ecosystem: nf-core
  workflow: nf-core/diaproteomics
  url: https://github.com/nf-core/diaproteomics
  version: 1.2.4
  license: MIT
tools:
- OpenSwathWorkflow
- EasyPQP
- PyProphet
- DIAlignR
- MSstats
- OpenMS
tags:
- dia
- swath
- proteomics
- quantitative
- label-free
- mass-spectrometry
- pyprophet
- openswath
- msstats
test_data: []
expected_output: []
---

# DIA / SWATH-MS proteomics quantification

## When to use this sketch
- User has DIA (data-independent acquisition) / SWATH-MS proteomics runs in mzML (or raw) format and wants peptide and/or protein quantification.
- A spectral assay library is available, OR matched DDA runs with peptide identification results (pepXML / mzid / idXML) are available for on-the-fly library generation via EasyPQP.
- User wants FDR control at peakgroup, peptide, or protein level and condition-vs-condition statistical comparison across biological replicates.
- User asks about OpenSwathWorkflow, PyProphet, DIAlignR, or "SWATH quantification".

## Do not use when
- The data is DDA shotgun proteomics with database search — use a DDA label-free quantification sketch instead.
- The goal is de novo identification only without a library and without matched DDA — this pipeline requires either an input library or DDA inputs to build one.
- The experiment is targeted SRM/MRM on triple quads — OpenSwathWorkflow is tuned for SWATH windows.
- The user wants TMT/iTRAQ isobaric labelling quantification — not handled here.
- The user wants immunopeptidomics-specific HLA workflows — use a dedicated MHC/peptidomics sketch.

## Analysis outline
1. (Optional) Generate a spectral assay library from matched DDA mzML + identification results with EasyPQP.
2. (Optional) Derive pseudo-iRT peptides from the best-scoring DDA identifications for RT alignment.
3. (Optional) Merge and pairwise RT-align multiple per-batch libraries into a single library.
4. Generate decoy transitions (shuffle by default) and build the final PQP library.
5. Run OpenSwathWorkflow on each DIA mzML: RT-normalize against iRTs, extract MS1/MS2 transition chromatograms, score peakgroups → `.osw` + `chrom.mzML`.
6. Score target/decoy peakgroups with PyProphet (LDA or XGBoost), then aggregate to peptide and/or protein global FDR.
7. Align extracted ion chromatograms across runs with DIAlignR to recover missing peakgroups and emit a peptide quantity matrix.
8. Run MSstats for normalization, condition comparison, and visualization (volcano, heatmap, charge/RT QC plots).

## Key parameters
- `--input` sample sheet: `Sample`, `BatchID`, `MSstats_Condition`, `MSstats_BioReplicate` (optional), `Spectra_Filepath`.
- `--input_spectral_library` / `--irts`: library and iRT sheets, OR set `--generate_spectral_library --input_sheet_dda <dda.tsv> --generate_pseudo_irts`.
- Library merging across batches: `--merge_libraries --align_libraries --min_overlap_for_merging 100`.
- Extraction windows: `--mz_extraction_window 30 --mz_extraction_window_unit ppm`, `--mz_extraction_window_ms1 10`, `--rt_extraction_window 600` (seconds), `--use_ms1 true`.
- iRT RT normalization: `--irt_min_rsq 0.95 --irt_n_bins 10 --irt_min_bins_covered 8 --irt_alignment_method linear|lowess`.
- Library assay generation: `--min_transitions 4 --max_transitions 6 --decoy_method shuffle` (or `--skip_decoy_generation` if library already has decoys); `--n_irts 250` pseudo-iRTs.
- PyProphet FDR: `--pyprophet_classifier LDA` (use `XGBoost` carefully — overfit risk), `--pyprophet_fdr_ms_level ms1ms2`, `--pyprophet_global_fdr_level protein` (or `peptide`), `--pyprophet_peakgroup_fdr 0.01 --pyprophet_peptide_fdr 0.01 --pyprophet_protein_fdr 0.01`, `--pyprophet_pi0_start 0.1 --pyprophet_pi0_end 0.5 --pyprophet_pi0_steps 0.05`.
- DIAlignR: `--dialignr_global_align_fdr 0.01 --dialignr_analyte_fdr 0.01 --dialignr_unalign_fdr 0.01 --dialignr_align_fdr 0.05 --dialignr_query_fdr 0.05 --dialignr_xicfilter sgolay`.
- Output: `--run_msstats true --generate_plots true`; set `--mztab_export` only if downstream tools require it (DIA mzTab support is limited).
- Resource ceilings: `--max_cpus`, `--max_memory`, `--max_time`.
- For small/CI-sized data you must relax FDR cutoffs (see test profile) because statistics are meaningless at that scale.

## Test data
The `test` profile downloads tiny DIA sample and DDA library-building sheets plus a `unimod.xml` from `nf-core/test-datasets` (branch `diaproteomics`): `sample_sheet.tsv`, `dda_sheet.tsv`, `unimod.xml`. It exercises the full path — EasyPQP library build from DDA, pseudo-iRT generation (`n_irts=25`), library merging and alignment (`min_overlap_for_merging=10`), OpenSwathWorkflow with `force_option=true`, and PyProphet — but with all FDR thresholds opened to 1 and pi0 estimation disabled because the toy dataset is too small for meaningful target/decoy statistics; MSstats and plotting are turned off. The `test_full` profile uses the larger `sample_sheet_full.tsv` / `dda_sheet_full.tsv` / `irt_sheet_full.tsv` with production-grade FDR (0.01 at peakgroup/peptide/protein), `lowess` iRT alignment, `n_irts=250`, MSstats enabled, and `use_ms1=false`. Expected outputs are a peptide quantity CSV, per-run OpenSwath `.osw` / `chrom.mzML`, PyProphet target-decoy score PDFs, a merged PQP library, and (in full test) MSstats protein comparison tables plus volcano/heatmap PDFs under `results/`.

## Reference workflow
nf-core/diaproteomics v1.2.4 — https://github.com/nf-core/diaproteomics. Built on OpenSwathWorkflow (Röst et al., Nat Biotechnol 2014), EasyPQP, PyProphet (Rosenberger et al., Nat Methods 2017), DIAlignR (Gupta et al., MCP 2019) and MSstats (Choi et al., Bioinformatics 2014). See the DIAproteomics preprint (Bichmann et al., bioRxiv 2020.12.08.415844).
