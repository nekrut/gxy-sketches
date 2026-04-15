---
name: protein-sip-metaproteomics
description: Use when you need to quantify stable isotope incorporation rates (e.g.
  13C, 15N, 2H, 18O) in peptides/proteins from an LC-MS/MS protein-SIP experiment
  on a microbial community, to infer which taxa/functions metabolized a labeled substrate.
  Expects centroided mzML spectra and a metaproteomics FASTA database.
domain: proteomics
organism_class:
- bacterial
- eukaryote
- microbial-community
input_data:
- centroided-lc-msms-mzml
- protein-fasta
source:
  ecosystem: iwc
  workflow: MetaProSIP OpenMS
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/proteomics/openms-metaprosip
  version: '0.3'
  license: MIT
  slug: proteomics--openms-metaprosip
tools:
- name: OpenMS
- name: DecoyDatabase
  version: 3.1+galaxy0
- name: MSGFPlusAdapter
  version: 3.1+galaxy0
- name: FeatureFinderMultiplex
  version: 3.1+galaxy0
- name: PeptideIndexer
  version: 3.1+galaxy0
- name: FalseDiscoveryRate
  version: 3.1+galaxy0
- name: IDMapper
  version: 3.1+galaxy0
- name: MetaProSIP
  version: 3.1+galaxy0
tags:
- protein-sip
- metaproteomics
- stable-isotope-probing
- openms
- metaprosip
- functional-microbiome
- 13C
- 15N
- labeling
test_data:
- role: fasta_database
  url: https://abibuilder.cs.uni-tuebingen.de/archive/openms/galaxy-testdata/metaprosip/Zeitz_1and2_454AllContigs_HEX.fasta
  sha1: 2aa683a162aef61679d46e14508ca0cecf16e24a
  filetype: fasta
- role: centroided_lc_ms_datasets__zeitz_sip_13_ii_020_picked_mzml
  url: https://abibuilder.cs.uni-tuebingen.de/archive/openms/galaxy-testdata/metaprosip/Zeitz_SIP_13-II_020_picked.mzML
  sha1: cda64713a3466f7bf74af2a42da97351aaff691b
  filetype: mzml
expected_output:
- role: peptide_centric_result
  description: Content assertions for `Peptide centric result`.
  assertions:
  - 'Zeitz_SIP_13-II_020_picked.mzML: that: has_n_lines'
  - 'Zeitz_SIP_13-II_020_picked.mzML: n: 85'
  - 'Zeitz_SIP_13-II_020_picked.mzML: that: has_text'
  - 'Zeitz_SIP_13-II_020_picked.mzML: text: Peptide Sequence'
  - 'Zeitz_SIP_13-II_020_picked.mzML: that: has_text'
  - 'Zeitz_SIP_13-II_020_picked.mzML: text: AATGTPSPAGSPPPIVPAPK'
- role: feature_fitting_result
  description: Content assertions for `Feature fitting result`.
  assertions:
  - 'Zeitz_SIP_13-II_020_picked.mzML: that: has_n_lines'
  - 'Zeitz_SIP_13-II_020_picked.mzML: n: 4091'
  - 'Zeitz_SIP_13-II_020_picked.mzML: that: has_text'
  - 'Zeitz_SIP_13-II_020_picked.mzML: text: Group 1'
  - 'Zeitz_SIP_13-II_020_picked.mzML: that: has_text'
  - 'Zeitz_SIP_13-II_020_picked.mzML: text: LYSFHTLHQTYMK'
---

# Protein-SIP metaproteomics with MetaProSIP (OpenMS)

## When to use this sketch
- You have an LC-MS/MS protein stable isotope probing (protein-SIP) experiment where a microbial community was fed a heavy-isotope-labeled substrate (13C, 15N, 2H, or 18O) and you need to estimate the relative isotope abundance (RIA) and labeling ratio per peptide/protein.
- Inputs are centroided high-resolution spectra (mzML, ms2, mgf, or mzXML; MetaProSIP is primarily validated on Orbitrap data) plus a metaproteomics protein FASTA (e.g. a metagenome-derived ORF catalogue).
- You want a reproducible OpenMS pipeline that handles decoy generation, MSGF+ database search, FDR control, feature finding of isotopologue envelopes, and downstream MetaProSIP quantification in one pass.
- You need both a feature-centric and a peptide-centric CSV summarizing incorporation for functional interpretation of a microbial community.

## Do not use when
- Your samples are metabolically labeled but you want SILAC-style pairwise ratio quantification between fully-light and fully-heavy channels — use a dedicated SILAC / label-based quant workflow instead.
- You are doing label-free shotgun metaproteomics without any heavy isotope tracer — use a standard OpenMS/MaxQuant LFQ metaproteomics sketch.
- You are analyzing DNA/RNA stable isotope probing (e.g. density-gradient fractionated 13C-DNA) — use a nucleic-acid SIP sketch, not this proteomics one.
- Your spectra are profile-mode — peak-pick/centroid them first (e.g. PeakPickerHiRes) before entering this workflow.
- You need TMT/iTRAQ isobaric quantification — use an isobaric-labeling proteomics workflow.

## Analysis outline
1. Sort the input mzML collection alphabetically to stabilize per-sample processing order (Galaxy `__SORTLIST__`).
2. Build a target-decoy protein database from the user FASTA with `DecoyDatabase` (reverse decoys, `DECOY_` prefix, trypsin).
3. Detect elution profiles / isotopologue features of (partially) labeled peptides across each mzML run with `FeatureFinderMultiplex`.
4. Identify peptides by searching each mzML against the decoyed FASTA with `MSGFPlusAdapter` (Trypsin/P, fully tryptic, reindexed).
5. Annotate peptide-to-protein mapping with `PeptideIndexer` against the same decoyed FASTA.
6. Control identification FDR at the PSM level with `FalseDiscoveryRate` and clean up orphaned proteins/spectra.
7. Map identified PSMs onto the FeatureFinderMultiplex featureXML with `IDMapper` (mz_tolerance=20 ppm, rt_tolerance=5 s).
8. Run `MetaProSIP` on the mzML + mapped featureXML + FASTA to compute RIA, labeling ratio, and incorporation patterns, emitting a feature-fitting CSV and a peptide-centric CSV.

## Key parameters
- `Precursor monoisotopic mass tolerance (ppm)`: shared input wired to both `MSGFPlusAdapter -precursor_mass_tolerance` and `MetaProSIP -mz_tolerance_ppm` (test uses 10.0 ppm).
- `Fixed modifications` / `Variable modifications`: free-text MSGF+ modification strings (test uses `Carbamidomethyl (C)` fixed, `Oxidation (M)` variable).
- `Labeled element`: single-letter code for the SIP tracer element, one of `C`, `N`, `H`, `O` (test uses `C` for 13C labeling).
- MSGFPlusAdapter: `enzyme=Trypsin/P`, `instrument=low_res`, `min_peptide_length=6`, `max_peptide_length=40`, `precursor_charge=2..3`, `isotope_error_range=0,1`, `matches_per_spec=1`, `add_features=true`, `reindex=true`.
- FeatureFinderMultiplex: `charge=1:4`, `isotopes_per_peptide=3:6`, `rt_typical=40 s`, `rt_min=2 s`, `mz_tolerance=6 ppm`, `intensity_cutoff=1000`, `averagine_type=peptide`, no multiplex labels set (treat as single-channel for SIP).
- DecoyDatabase: `method=reverse`, `decoy_string=DECOY_` prefix, `enzyme=Trypsin`, keep peptide N/C termini.
- FalseDiscoveryRate: PSM-level FDR with `PSM=1.0`, conservative algorithm, `remove_proteins_without_psms`, `remove_psms_without_proteins`, and `remove_spectra_without_psms` all enabled.
- IDMapper: `mz_reference=peptide`, `mz_tolerance=20 ppm`, `rt_tolerance=5 s`, `use_centroid_mz=true`.
- MetaProSIP: `correlation_threshold=0.7`, `decomposition_threshold=0.7`, `intensity_threshold=10.0`, `rt_tolerance_s=30`, `weight_merge_window=5`, `xic_threshold=0.7`, `pattern_*_TIC_threshold=0.95` per element, `min_consecutive_isotopes=2`, `observed_peak_fraction=0.5`, `plot_extension=png`.

## Test data
The source test profile runs on a single centroided Orbitrap mzML file, `Zeitz_SIP_13-II_020_picked.mzML`, supplied as a one-element input collection, paired with the metagenomics protein FASTA `Zeitz_1and2_454AllContigs_HEX.fasta` (both hosted at the Tübingen OpenMS galaxy-testdata archive). The tracer is 13C (`Labeled element = C`), precursor tolerance is 10.0 ppm, fixed modification `Carbamidomethyl (C)`, variable modification `Oxidation (M)`. A successful run produces two MetaProSIP CSVs: the peptide-centric result (~85 lines, containing the `Peptide Sequence` header and at least the peptide `AATGTPSPAGSPPPIVPAPK`) and the feature-fitting result (~4091 lines, containing a `Group 1` cluster and the peptide `LYSFHTLHQTYMK`). These assertions are the minimal evidence the full chain (decoy → MSGF+ → FDR → feature mapping → MetaProSIP) reached the labeling-inference stage.

## Reference workflow
Galaxy IWC workflow `MetaProSIP OpenMS` v0.3 (MIT), `workflows/proteomics/openms-metaprosip/metaprosip.ga`, using OpenMS 3.1 Galaxy tool wrappers (DecoyDatabase, FeatureFinderMultiplex, MSGFPlusAdapter, PeptideIndexer, FalseDiscoveryRate, IDMapper, MetaProSIP), authored by Matthias Bernt.
