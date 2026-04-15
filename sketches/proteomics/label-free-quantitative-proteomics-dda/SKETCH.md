---
name: label-free-quantitative-proteomics-dda
description: Use when you need to identify and quantify proteins from data-dependent
  acquisition (DDA) shotgun mass spectrometry runs using label-free quantification
  (LFQ) against a protein FASTA, starting from Thermo RAW or mzML spectra annotated
  via an SDRF sample sheet. Produces mzTab, MSstats tables, and a pmultiqc QC report.
domain: proteomics
organism_class:
- eukaryote
- any-organism
input_data:
- ms-spectra-raw
- ms-spectra-mzml
- protein-fasta
- sdrf-sample-sheet
source:
  ecosystem: nf-core
  workflow: nf-core/quantms
  url: https://github.com/nf-core/quantms
  version: 1.2.0
  license: MIT
  slug: quantms
tools:
- name: thermorawfileparser
- name: comet
- name: msgfplus
- name: sage
- name: percolator
- name: openms
- name: luciphor
- name: proteomicslfq
- name: msstats
- name: pmultiqc
tags:
- proteomics
- mass-spectrometry
- dda
- lfq
- label-free
- shotgun
- openms
- msstats
- sdrf
test_data: []
expected_output: []
---

# Label-free quantitative proteomics (DDA-LFQ)

## When to use this sketch
- Shotgun bottom-up proteomics experiment acquired in data-dependent acquisition (DDA) mode on an Orbitrap / Q-Exactive / similar high-resolution instrument.
- Quantification is label-free (MS1 feature intensities), not isobaric tags and not DIA.
- Inputs are Thermo `.raw` files (or already-converted `.mzML`) plus a protein FASTA database and an SDRF sample-to-data sheet that encodes the experimental design, modifications, enzyme, and tolerances.
- You want peptide/protein identifications with FDR control plus a differential-expression-ready quantity matrix for MSstats.
- Typical deliverables: `out.mzTab`, `out_msstats.csv`, protein/peptide TSVs, and a pmultiqc HTML report.

## Do not use when
- Samples are labeled with isobaric tags (TMT6/10/11/16, iTRAQ4/8). Use the sibling sketch `isobaric-labeling-quantitative-proteomics-dda` (same pipeline, `labelling_type: tmt*` / `itraq*`, IsobaricAnalyzer branch).
- Acquisition is data-independent (DIA / SWATH / diaPASEF). Use the sibling sketch `dia-label-free-quantitative-proteomics` which routes through DIA-NN.
- You only need peptide identification without quantification — a plain database-search workflow is lighter weight.
- You need de novo sequencing, cross-linking MS, top-down proteomics, HDX-MS, or targeted SRM/PRM — none of those are covered here.
- Input is Bruker `.d` timsTOF data for DDA — this pipeline's `.d` support is DIA-only (`convert_dotd`).

## Analysis outline
1. Convert Thermo `.raw` to indexed `.mzML` with ThermoRawFileParser (skipped if mzML already provided); optional OpenMS PeakPickerHiRes for profile-mode spectra.
2. (Optional) Append decoys to the target FASTA with OpenMS DecoyDatabase (`add_decoys`, reverse or shuffle).
3. Database search per mzML with Comet and/or MS-GF+ and/or Sage via OpenMS adapters, using enzyme, precursor/fragment tolerances, fixed/variable mods from the SDRF.
4. Re-map PSMs to the FASTA with OpenMS PeptideIndexer (I/L equivalence on by default).
5. PSM rescoring with PSMFeatureExtractor + Percolator (default) or distribution-fitting (IDPosteriorErrorProbability).
6. If multiple engines were run, combine with OpenMS ConsensusID (`best` / `PEPMatrix` / `PEPIons`).
7. Per-run PSM/peptide-level FDR filter at `run_fdr_cutoff` (default 0.01).
8. Optional PTM site localization with Luciphor2 (phospho by default).
9. Feature finding, map alignment, linking, protein inference and experiment-wide protein-FDR-controlled LFQ with OpenMS ProteomicsLFQ (optionally with match-between-runs).
10. Statistical post-processing with MSstats: normalization, summarization (Tukey median polish), optional imputation, pairwise contrasts against a reference condition or a user-supplied contrast list.
11. QC report aggregation with pmultiqc (identifications, score distributions, quant coverage, contaminants).

## Key parameters
- `--input`: path/URL to the SDRF (`.sdrf.tsv`) or OpenMS experimental design TSV. SDRF overrides `fixed_mods`, `variable_mods`, `precursor_mass_tolerance[_unit]`, `fragment_mass_tolerance[_unit]`, `fragment_method`, and `enzyme`.
- `--database`: target protein FASTA (include contaminants; include decoys yourself or set `--add_decoys`).
- `--acquisition_method dda` (default).
- `--labelling_type "label free sample"` — this is what pins the pipeline to the LFQ branch.
- `--search_engines comet` (default) or `comet,msgf` / `comet,msgf,sage` to combine engines; combined runs benefit from `--num_hits > 1`.
- `--enzyme Trypsin`, `--allowed_missed_cleavages 2`, `--num_enzyme_termini fully`.
- `--precursor_mass_tolerance 5 --precursor_mass_tolerance_unit ppm` and `--fragment_mass_tolerance 0.03 --fragment_mass_tolerance_unit Da` for high-res Orbitrap; adjust for low-res.
- `--fixed_mods "Carbamidomethyl (C)"`, `--variable_mods "Oxidation (M)"` (Unimod names; overridden by SDRF).
- `--min_peptide_length 6 --max_peptide_length 40`, `--min_precursor_charge 2 --max_precursor_charge 4`, `--max_mods 3`.
- `--posterior_probabilities percolator` with `--FDR_level peptide-level-fdrs` and `--run_fdr_cutoff 0.01`.
- `--protein_inference_method aggregation` (or `bayesian` = Epifany), `--protein_level_fdr_cutoff 0.01`, `--picked_fdr true`, `--protein_quant unique_peptides`.
- `--quantification_method feature_intensity`, `--targeted_only true` (set to `false` to enable match-between-runs), `--mass_recalibration`, `--lfq_intensity_threshold 10000`, `--alignment_order star`.
- `--enable_mod_localization` + `--mod_localization "Phospho (S),Phospho (T),Phospho (Y)"` for phosphoproteomics.
- `--skip_post_msstats false`, `--ref_condition` or `--contrasts "1-2;1-3;2-3"`, `--msstats_threshold 0.05`.
- `--enable_pmultiqc true` for the proteomics-aware QC report.

## Test data
The pipeline's LFQ CI profile uses a small public DDA-LFQ dataset referenced by a URL-hosted SDRF (e.g. a reduced UPS1/yeast or BSA-spike experiment from the proteomics-sample-metadata repository) together with a matching trimmed protein FASTA. The SDRF pins two or more conditions so that MSstats contrasts can be evaluated, and spectra are fetched from the URIs declared in the `comment[file uri]` column. A successful run produces per-mzML idXML files under `searchenginecomet/`, a merged `proteomicslfq/out.consensusXML`, `proteomicslfq/out.mzTab` with target protein quantities at ≤1% experiment-wide FDR, `proteomicslfq/out_msstats.csv`, an MSstats-normalized `msstats/out_msstats.mzTab` with pairwise contrast results, and a `multiqc/multiqc_report.html` generated by pmultiqc summarizing identification and quantification QC.

## Reference workflow
nf-core/quantms v1.2.0 — https://github.com/nf-core/quantms (DOI 10.5281/zenodo.7754148). Note: active development has moved to https://github.com/bigbio/quantms. Core tools: ThermoRawFileParser, OpenMS (CometAdapter, MSGFPlusAdapter, SageAdapter, PeptideIndexer, PSMFeatureExtractor, PercolatorAdapter, ConsensusID, IDFilter, LuciphorAdapter, ProteomicsLFQ), MSstats, pmultiqc.
