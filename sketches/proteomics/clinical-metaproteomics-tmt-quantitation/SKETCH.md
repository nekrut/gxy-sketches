---
name: clinical-metaproteomics-tmt-quantitation
description: Use when you need to quantify microbial proteins and peptides from clinical
  metaproteomics TMT-labeled LC-MS/MS data against a curated (human + microbial) protein
  database using MaxQuant, then filter out human/contaminant/decoy hits to produce
  microbial-only quantified protein and peptide tables. Assumes Thermo .raw files
  with TMT11-plex reporter-ion MS2 labeling.
domain: proteomics
organism_class:
- human
- microbiome
input_data:
- thermo-raw-msms
- protein-fasta-database
- maxquant-experimental-design
source:
  ecosystem: iwc
  workflow: Clinical Metaproteomics Quantitation
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/proteomics/clinicalmp/clinicalmp-quantitation
  version: '0.1'
  license: CC-BY-4.0
tools:
- maxquant
- galaxy-text-utilities
tags:
- metaproteomics
- clinical
- tmt
- quantitation
- maxquant
- microbiome
- reporter-ion
- ms2
- galaxyp
test_data:
- role: quantitation_database_for_maxquant
  url: https://zenodo.org/records/10720030/files/Quantitation_Database_for_MaxQuant.fasta
  sha1: 9e9fb4fe077313f4cf5e50c3d9d0710f76df695d
  filetype: fasta
- role: experimental_design_discovery_maxquant
  url: https://zenodo.org/records/10720030/files/Experimental-Design_Discovery_MaxQuant.tabular
  sha1: d7fd3857af8d391031261a385b76ba90be4084b0
  filetype: tabular
- role: input_raw_files__ptrc_skubitz_plex2_f15_9aug19_rage_rep_19_06_08_raw
  url: https://zenodo.org/records/10720030/files/PTRC_Skubitz_Plex2_F15_9Aug19_Rage_Rep-19-06-08.raw
  sha1: 811dd78a211e9c9bf2fafdb85d6f1fa4cd93d44e
- role: input_raw_files__ptrc_skubitz_plex2_f13_9aug19_rage_rep_19_06_08_raw
  url: https://zenodo.org/records/10720030/files/PTRC_Skubitz_Plex2_F13_9Aug19_Rage_Rep-19-06-08.raw
  sha1: 47a94441c642f09f928cbdc919f63bcfb541eef5
- role: input_raw_files__ptrc_skubitz_plex2_f11_9aug19_rage_rep_19_06_08_raw
  url: https://zenodo.org/records/10720030/files/PTRC_Skubitz_Plex2_F11_9Aug19_Rage_Rep-19-06-08.raw
  sha1: 1a43f2d47279794cd30bf4adb052bf824583ea83
- role: input_raw_files__ptrc_skubitz_plex2_f10_9aug19_rage_rep_19_06_08_raw
  url: https://zenodo.org/records/10720030/files/PTRC_Skubitz_Plex2_F10_9Aug19_Rage_Rep-19-06-08.raw
  sha1: 1d4eec13f0efd6d13d9cc9c4f3ee8c1103d6f5b8
expected_output:
- role: quantified_proteins
  path: expected_output/Quantified-Proteins.tabular
  description: Expected output `Quantified-Proteins` from the source workflow test.
  assertions: []
- role: quantified_peptides
  path: expected_output/Quantified-Peptides.tabular
  description: Expected output `Quantified-Peptides` from the source workflow test.
  assertions: []
---

# Clinical metaproteomics TMT quantitation (microbial protein/peptide)

## When to use this sketch
- You have Thermo `.raw` LC-MS/MS files from a clinical sample (e.g. tumor, tissue, stool) that contains both host (human) and microbial proteins.
- The experiment uses TMT11-plex isobaric reporter-ion labeling and you want reporter-ion MS2 quantitation.
- You already have a curated protein FASTA (typically the refined "quantitation database" produced by the earlier clinical metaproteomics steps: discovery → verification → database generation) and a MaxQuant experimental-design tabular file.
- You want per-sample quantified tables for the *microbial* subset of proteins and peptides, with human, contaminant, and reversed-decoy entries filtered out.
- You are following the Galaxy clinical metaproteomics GTN and need the final (step 4) quantitation workflow.

## Do not use when
- You are doing label-free quantitation (LFQ), SILAC, or iTRAQ instead of TMT11-plex — change MaxQuant's `quant_method` accordingly or pick a different sketch.
- You need the upstream discovery search, PSM verification, or to build the quantitation database itself — use the sibling `clinicalmp-discovery`, `clinicalmp-verification`, or `clinicalmp-database-generation` workflows instead.
- You are doing non-clinical, single-organism shotgun proteomics with no host background — a standard MaxQuant LFQ or TMT workflow is simpler and you don't need the microbial-vs-human filter step.
- Your input is DIA (e.g. DIA-NN, Spectronaut) or timsTOF PASEF data that requires a different search engine.
- You need pathway/functional or taxonomic interpretation downstream — this sketch stops at quantified tables.

## Analysis outline
1. **MaxQuant search + quantitation** (`maxquant` 2.0.3): search all input `.raw` files against the quantitation FASTA using the supplied experimental-design template; reporter-ion MS2 with TMT11-plex; Trypsin/P, up to 2 missed cleavages; fixed Carbamidomethyl (C), variable Oxidation (M); peptide length 8–50; PSM and protein FDR 0.01; match-between-runs enabled. Emits `proteinGroups`, `peptides`, `evidence`, `msms`, and `mqpar` tables.
2. **Filter microbial proteins** (`Grep1` Select, invert match): drop rows from `proteinGroups` matching `(_HUMAN)|(_REVERSED)|(CON)|(con)` to keep only microbial protein groups.
3. **Filter microbial peptides** (`Grep1` Select, invert match): apply the same regex to the `peptides` table.
4. **Extract accession column** (`Cut1`): keep column 1 (protein/peptide identifier) from each filtered table.
5. **Collapse duplicates** (`Grouping1`, group on column 1): deduplicate identifiers to produce the final `Quantified-Proteins` and `Quantified-Peptides` tabular outputs.

## Key parameters
- MaxQuant input type: `.thermo.raw`
- `quant_method`: `reporter_ion_ms2` with `iso_labels.labeling = tmt11plex`
- Enzyme: `Trypsin/P`, `maxMissedCleavages = 2`, `digestion_mode = 0` (specific)
- Fixed modifications: `Carbamidomethyl (C)`; variable: `Oxidation (M)`
- Peptide length: `min_peptide_len = 8`, `max_pep_length = 50`; `max_peptide_mass = 4600`
- FDR: `psm_fdr = 0.01`, `protein_fdr = 0.01`; `decoy_mode = revert`; contaminants off
- Match-between-runs: `True`, `matching_time_window = 0.7` min, `alignment_time_window = 20` min
- Protein quant: `peptides_for_quantification = 1`, use only unmodified + Oxidation (M) peptides, discard unmodified counterpart peptides
- Identifier parse rule: `>([^\s]*)`; description parse rule: `>(.*)`
- Microbial filter regex (invert): `(_HUMAN)|(_REVERSED)|(CON)|(con)` — this is the linchpin; it assumes human headers carry `_HUMAN`, decoys are prefixed `_REVERSED`, and contaminants are tagged `CON`/`con`. The quantitation database must follow that header convention.
- Group tool: `groupcol = 1` on the cut accession column.

## Test data
The published test uses four Thermo `.raw` files from the PTRC Skubitz TMT11-plex plex-2 run (`PTRC_Skubitz_Plex2_F10/F11/F13/F15_9Aug19_Rage_Rep-19-06-08.raw`) staged as a Galaxy list collection, together with `Quantitation_Database_for_MaxQuant.fasta` (the refined host+microbial protein database from the upstream clinical metaproteomics steps) and `Experimental-Design_Discovery_MaxQuant.tabular` describing the MaxQuant experimental layout; all three are hosted on Zenodo record 10720030. A successful run is expected to reproduce two tabular outputs, `Quantified-Proteins.tabular` and `Quantified-Peptides.tabular`, each containing only microbial accessions (no `_HUMAN`, `_REVERSED`, `CON`, or `con` rows) with one row per unique identifier.

## Reference workflow
Galaxy IWC — `workflows/proteomics/clinicalmp/clinicalmp-quantitation` (Clinical Metaproteomics 4: Quantitation), release 0.1, CC-BY-4.0, maintained by GalaxyP. Companion Galaxy Training Network tutorial: `training.galaxyproject.org/training-material/topics/proteomics/tutorials/clinical-mp-4-quantitation`.
