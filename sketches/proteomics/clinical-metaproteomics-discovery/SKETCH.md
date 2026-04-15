---
name: clinical-metaproteomics-discovery
description: Use when you need to discover microbial peptides from clinical tandem
  mass spectrometry (MS/MS) data by searching TMT-labeled Thermo RAW files against
  a compact MetaNovo-derived human+microbial+cRAP protein database using parallel
  SearchGUI/PeptideShaker and MaxQuant searches, then extracting non-human (microbial)
  distinct peptides for downstream verification.
domain: proteomics
organism_class:
- human
- microbiome
input_data:
- thermo-raw-msms
- protein-database-fasta
- experimental-design-tabular
source:
  ecosystem: iwc
  workflow: Clinical Metaproteomics Discovery Workflow
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/proteomics/clinicalmp/clinicalmp-discovery
  version: '0.1'
  license: CC-BY-4.0
  slug: proteomics--clinicalmp--clinicalmp-discovery
tools:
- name: msconvert
  version: 3.0.20287.2
- name: searchgui
  version: 4.0.41+galaxy1
- name: peptideshaker
  version: 2.0.33+galaxy1
- name: maxquant
  version: 2.0.3.0+galaxy0
- name: fastacli
  version: 4.0.41+galaxy1
- name: dbbuilder
  version: 0.3.4
- name: fasta_merge_files_and_filter_unique_sequences
  version: 1.2.0
- name: query_tabular
  version: 3.3.0
- name: filter_tabular
  version: 3.3.0
tags:
- metaproteomics
- clinical
- tmt
- microbiome
- peptide-identification
- discovery
- galaxy
test_data:
- role: human_uniprot_microbial_proteins_from_metanovo_and_crap
  url: https://zenodo.org/records/10720030/files/Human_UniProt_Microbial_Proteins_(from_MetaNovo)_and_cRAP.fasta
  sha1: 72bc60bb5733ba38866f3f4cfc5583ed823e6446
  filetype: fasta
- role: tandem_mass_spectrometry_msms_files__ptrc_skubitz_plex2_f10_9aug19_rage_rep_19_06_08_raw
  url: https://zenodo.org/records/14182981/files/PTRC_Skubitz_Plex2_F10_9Aug19_Rage_Rep-19-06-08.raw
  sha1: 1d4eec13f0efd6d13d9cc9c4f3ee8c1103d6f5b8
expected_output:
- role: sgps_mq_peptides
  description: Content assertions for `SGPS MQ Peptides`.
  assertions:
  - 'has_n_columns: {''n'': 1}'
  - 'has_text: AAFPNVTAMNITTNNGK'
---

# Clinical Metaproteomics Discovery

## When to use this sketch
- You have clinical TMT 11-plex labeled Thermo `.raw` MS/MS files and want to identify microbial peptides present alongside the human proteome.
- You already have (or can build) a compact MetaNovo-derived FASTA that merges human SwissProt, microbial proteins, and cRAP contaminants (~21k sequences).
- You want parallel, orthogonal database searching via both SearchGUI/PeptideShaker (X!Tandem + MS-GF+) and MaxQuant, with results consolidated into a single distinct microbial peptide list.
- You are at the *discovery* stage of a clinical metaproteomics study and need a candidate peptide list to feed a downstream verification/quantification workflow.

## Do not use when
- You need to *build* the MetaNovo sequence database from raw spectra — use the upstream `clinicalmp-database-generation` sketch instead.
- You need to *verify* or quantify an already-discovered microbial peptide list — use the `clinicalmp-verification` / `clinicalmp-quantitation` sketches instead.
- Your data is label-free or uses SILAC/iTRAQ rather than TMT 11-plex — TMT-specific fixed modifications and reporter-ion quant settings here won't match.
- You are working on a single organism proteome (pure human, pure bacterial isolate) — a standard proteomics identification workflow is simpler and more appropriate.
- Your input is already centroided mzML/MGF and doesn't need vendor peak picking — you can skip msconvert but most of the plumbing here assumes Thermo RAW input.

## Analysis outline
1. **Convert RAW to MGF** with `msconvert` using vendor peak picking at MS levels 1+.
2. **Build search database**: download Human SwissProt and cRAP via `dbbuilder`, merge them with `fasta_merge_files_and_filter_unique_sequences`, and separately wrap the provided MetaNovo+cRAP FASTA in decoys with `FastaCLI` (`_REVERSED` tag).
3. **Configure SearchGUI identification parameters** via PeptideShaker `ident_params` (tryptic, TMT 11-plex fixed, Oxidation (M) variable, 10 ppm precursor / 0.6 Da fragment).
4. **SearchGUI** run against the decoyed database using X!Tandem + MS-GF+ engines over the MGF peak lists.
5. **PeptideShaker** to validate PSMs/peptides/proteins and export tabular reports + mzIdentML.
6. **MaxQuant** parallel search: same RAW files, same FASTA, TMT 11-plex reporter-ion MS2 quant, trypsin/P, MBR enabled, PSM/protein FDR 0.01.
7. **Extract microbial hits** from both engines: `Grep` out any rows matching `_HUMAN|_REVERSED|CON|con` from PeptideShaker peptides/PSMs and MaxQuant peptides.
8. **Filter to confident PSMs/peptides** (PeptideShaker `Confident` flag in c17/c24).
9. **Reconcile SGPS peptides against the accession list** using `Query Tabular` SQL to keep only PSMs whose proteins are NOT in the human SwissProt+cRAP accession table (true microbial-only).
10. **Deduplicate and union**: `Group` distinct peptides from each engine, `Concatenate` SGPS + MQ, then `Group` again to produce the final distinct microbial peptide list.

## Key parameters
- **SearchGUI engines**: X!Tandem and MS-GF+ (two engines are required; other engines left at defaults).
- **Enzyme / cleavage**: Trypsin, 2 missed cleavages, specific digestion.
- **Precursor tolerance**: 10 ppm. **Fragment tolerance**: 0.6 Da.
- **Charge range**: 2–6.
- **Peptide length**: 8–30 aa (SGPS) / 8–50 aa (MaxQuant).
- **Fixed modifications**: Carbamidomethylation of C, TMT 11-plex of K, TMT 11-plex of peptide N-term.
- **Variable modifications**: Oxidation of M.
- **MaxQuant quant**: reporter-ion MS2, TMT 11-plex, PIF filter 0.75, MBR on (0.7 min window).
- **FDR**: PSM/peptide/protein FDR 1% in MaxQuant; SGPS PeptideShaker confidence column filtered to `Confident`.
- **Decoy tag**: `_REVERSED`, concatenated target-decoy.
- **Microbial filter regex**: `(_HUMAN)|(_REVERSED)|(CON)|(con)` (inverted match).

## Test data
The test uses a single TMT-labeled Thermo RAW file, `PTRC_Skubitz_Plex2_F10_9Aug19_Rage_Rep-19-06-08.raw`, from a Zenodo deposit (record 14182981), paired with the pre-built `Human_UniProt_Microbial_Proteins_(from_MetaNovo)_and_cRAP.fasta` database (Zenodo record 10720030) and a small tabular MaxQuant experimental design file shipped alongside the workflow. The workflow is expected to produce a consolidated `SGPS MQ Peptides` tabular output of distinct microbial peptide sequences — a single-column table that must contain the peptide `AAFPNVTAMNITTNNGK` as a representative microbial hit. Intermediate outputs also include per-engine microbial peptide/PSM tables, the decoyed search database, and the human SwissProt+cRAP merged FASTA.

## Reference workflow
Galaxy IWC: `workflows/proteomics/clinicalmp/clinicalmp-discovery` — *Clinical Metaproteomics Discovery Workflow* v0.1 (CC-BY-4.0), by Subina Mehta. Companion Galaxy Training Network tutorial: `training-material/topics/proteomics/tutorials/clinical-mp-2-discovery`. Part of the `clinicalMP` suite (database generation → discovery → verification → quantitation).
