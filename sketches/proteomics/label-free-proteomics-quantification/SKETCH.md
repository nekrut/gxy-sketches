---
name: label-free-proteomics-quantification
description: Use when you need to identify and quantify proteins from label-free bottom-up
  shotgun proteomics data (Thermo RAW or mzML) using database search, FDR-controlled
  PSM rescoring, MS1 feature-based quantification, and MSstats group-wise statistical
  testing. Suited to DDA LFQ experiments with an OpenMS-style experimental design
  or a PRIDE SDRF.
domain: proteomics
organism_class:
- eukaryote
input_data:
- mass-spec-mzml
- thermo-raw
- protein-fasta
- experimental-design-tsv
source:
  ecosystem: nf-core
  workflow: nf-core/proteomicslfq
  url: https://github.com/nf-core/proteomicslfq
  version: 1.0.0
  license: MIT
tools:
- openms
- thermorawfileparser
- comet
- msgf+
- percolator
- luciphor2
- proteomicslfq
- msstats
- ptxqc
tags:
- proteomics
- lfq
- dda
- mass-spectrometry
- label-free
- msstats
- openms
- quantification
test_data: []
expected_output: []
---

# Label-free DDA proteomics quantification

## When to use this sketch
- Bottom-up shotgun proteomics experiments acquired in data-dependent acquisition (DDA) mode on Orbitrap-class or similar high-resolution instruments.
- Label-free quantification across multiple conditions / replicates / fractions where you want MS1 feature-based intensities and group-wise statistical contrasts.
- Input is either a set of Thermo `.raw` / `.mzML` spectra plus a protein FASTA and an OpenMS experimental design TSV, or a PRIDE SDRF file that describes the runs and factors.
- You need FDR-controlled peptide and protein identification (Comet and/or MS-GF+ with Percolator rescoring) followed by protein inference, alignment, and MSstats differential abundance.
- Optional phospho/PTM site localization via Luciphor2 and QC reporting via PTXQC are desired.

## Do not use when
- Data are isobaric-labeled (TMT/iTRAQ) or SILAC — this pipeline is label-free only; use a TMT/SILAC-specific proteomics sketch.
- You have DIA / SWATH spectra — use a DIA proteomics workflow (e.g. OpenSwath / DIA-NN) instead.
- You want top-down / intact protein analysis or cross-linking MS — not supported here.
- Your goal is only PTM discovery without quantification — run a dedicated PTM discovery pipeline.
- Your study is metaproteomics against a large metagenome-derived FASTA — this pipeline is tuned for single-organism reference databases.

## Analysis outline
1. (Optional) Convert Thermo `.raw` to indexed mzML with ThermoRawFileParser; if needed, peak-pick profile spectra with OpenMS `PeakPickerHiRes`.
2. (Optional) Append pseudo-reverse decoys to the target FASTA with OpenMS `DecoyDatabase` (`--add_decoys`).
3. Run database search with Comet and/or MS-GF+ via OpenMS `CometAdapter` / `MSGFPlusAdapter`, using the configured enzyme, precursor/fragment tolerances, and fixed/variable modifications.
4. Re-map peptides back to the database with OpenMS `PeptideIndexer` (I/L equivalence on by default) for consistent protein accessions and decoy flags.
5. Extract PSM features with `PSMFeatureExtractor` and rescore with Percolator, or alternatively fit target/decoy score distributions (PeptideProphet-style) when Percolator is unstable.
6. When multiple search engines are used, merge per-spectrum hits with OpenMS `ConsensusID` (algorithms: best / PEPMatrix / PEPIons) and apply a combined FDR filter.
7. Apply per-run PSM/peptide-level FDR filtering at `psm_pep_fdr_cutoff`.
8. (Optional) Localize variable modifications (e.g. Phospho S/T/Y) with Luciphor2 via its OpenMS adapter.
9. Run OpenMS `ProteomicsLFQ` for MS1 feature detection, retention-time alignment across runs, optional match-between-runs, protein inference (aggregation or Bayesian/Epifany), and experiment-wide protein-level FDR; emits consensusXML, an MSstats-ready CSV, and mzTab.
10. Run MSstats in R for normalization, imputation, and pairwise group contrasts, producing comparison/volcano/heatmap plots and a results table; optionally run PTXQC on the mzTab for QC.

## Key parameters
- `input`: glob of mzML/raw files or a PRIDE SDRF URL (mutually exclusive with manual `expdesign`).
- `database`: target (and optionally target+decoy) protein FASTA; `add_decoys: true` with `decoy_affix: "DECOY_"` / `"rev"` and `affix_type: prefix` to generate decoys.
- `search_engines`: `comet` (default), `msgf`, or `comet,msgf` for dual-engine ConsensusID.
- `enzyme: Trypsin`, `allowed_missed_cleavages: 2`, `num_enzyme_termini: fully`.
- `precursor_mass_tolerance: 5` with `precursor_mass_tolerance_unit: ppm`; `fragment_mass_tolerance: 0.03` with `fragment_mass_tolerance_unit: Da`; `instrument: high_res`.
- `fixed_mods: "Carbamidomethyl (C)"`, `variable_mods: "Oxidation (M)"`, `max_mods: 3`, `min_peptide_length: 6`, `max_peptide_length: 40`, `min_precursor_charge: 2`, `max_precursor_charge: 4`.
- `posterior_probabilities: percolator` (or `fit_distributions` as a fallback), with `FDR_level: peptide-level-fdrs`, `train_FDR: 0.05`, `test_FDR: 0.05`, `psm_pep_fdr_cutoff: 0.01` for production runs.
- `protein_inference: aggregation` (switch to `bayesian` for Epifany), `protein_level_fdr_cutoff: 0.05`, `protein_quant: unique_peptides`.
- `quantification_method: feature_intensity` (use `spectral_counting` only without MSstats), `targeted_only: true` by default; set to `false` to enable match-between-runs via `transfer_ids: mean`.
- `enable_mod_localization: true` with `mod_localization: "Phospho (S),Phospho (T),Phospho (Y)"` for phosphoproteomics.
- `ref_condition` / `contrasts` to drive MSstats pairwise tests; `skip_post_msstats: true` to bypass stats.
- `enable_qc: true` to produce a PTXQC HTML/PDF report.

## Test data
The bundled `test` profile runs six small BSA mzML files (`BSA1_F1`, `BSA1_F2`, `BSA2_F1`, `BSA2_F2`, `BSA3_F1`, `BSA3_F2`) organized as three samples with two fractions each, against an 18-protein target+decoy FASTA (`18Protein_SoCe_Tr_detergents_trace_target_decoy.fasta`) and an OpenMS experimental design `BSA_design.tsv`. It exercises MSGF+ search with distribution-fitting rescoring, `decoy_affix: rev`, a relaxed `protein_level_fdr_cutoff: 1.0`, and PTXQC enabled. Expected outputs are per-run `*.idXML` identifications, ProteomicsLFQ results (`out.consensusXML`, `out.csv`, `out.mzTab`), an MSstats folder (results CSV plus volcano/comparison/heatmap PDFs) and a PTXQC HTML/PDF report under `results/`. A larger `test_full` profile exists that downloads PXD001819 UPS1 spiked-yeast RAW files from PRIDE and runs Comet + Percolator with Bayesian inference and match-between-runs.

## Reference workflow
nf-core/proteomicslfq v1.0.0 — https://github.com/nf-core/proteomicslfq (OpenMS + MSstats label-free quantification pipeline).
