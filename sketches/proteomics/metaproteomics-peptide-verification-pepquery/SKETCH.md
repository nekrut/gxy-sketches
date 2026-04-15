---
name: metaproteomics-peptide-verification-pepquery
description: Use when you have candidate microbial peptides from a clinical metaproteomics
  discovery search (SearchGUI/PeptideShaker and/or MaxQuant) and need to verify them
  against raw MS/MS spectra with PepQuery2, then build a verified protein database
  for downstream quantitation.
domain: proteomics
organism_class:
- human
- microbiome
input_data:
- ms2-mgf
- peptide-report-tabular
- distinct-peptide-list
- uniprot-human-fasta
- crap-fasta
source:
  ecosystem: iwc
  workflow: Clinical Metaproteomics Verification Workflow
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/proteomics/clinicalmp/clinicalmp-verification
  version: '0.2'
  license: CC-BY-4.0
  slug: proteomics--clinicalmp--clinicalmp-verification
tools:
- name: pepquery2
  version: 2.0.2+galaxy2
- name: dbbuilder
  version: 0.3.4
- name: fasta_merge_files_and_filter_unique_sequences
  version: 1.2.0
- name: query_tabular
  version: 3.3.2
- name: uniprotxml_downloader
  version: 2.5.0
- name: galaxy-text-utils
tags:
- metaproteomics
- clinical
- pepquery
- peptide-verification
- maxquant
- searchgui
- peptideshaker
- galaxy
- iwc
test_data:
- role: tandem_mass_spectrometry_ms_ms_datasets__ptrc_skubitz_plex2_f15_9aug19_rage_rep_19_06_08_mgf
  url: https://zenodo.org/records/14181725/files/PTRC_Skubitz_Plex2_F15_9Aug19_Rage_Rep-19-06-08.mgf
  sha1: 74b0db7ef696b05fa115190ffd0c854b8c420aca
- role: tandem_mass_spectrometry_ms_ms_datasets__ptrc_skubitz_plex2_f13_9aug19_rage_rep_19_06_08_mgf
  url: https://zenodo.org/records/14181725/files/PTRC_Skubitz_Plex2_F13_9Aug19_Rage_Rep-19-06-08.mgf
  sha1: 6320f5feb043422ddff8285f0496e4d9a016287c
- role: tandem_mass_spectrometry_ms_ms_datasets__ptrc_skubitz_plex2_f11_9aug19_rage_rep_19_06_08_mgf
  url: https://zenodo.org/records/14181725/files/PTRC_Skubitz_Plex2_F11_9Aug19_Rage_Rep-19-06-08.mgf
  sha1: 63d72e72e02c7c10fbb3248bfeed1d77c2ffc897
- role: tandem_mass_spectrometry_ms_ms_datasets__ptrc_skubitz_plex2_f10_9aug19_rage_rep_19_06_08_mgf
  url: https://zenodo.org/records/14181725/files/PTRC_Skubitz_Plex2_F10_9Aug19_Rage_Rep-19-06-08.mgf
  sha1: 7d8d9cfaf29b048929ff2f1f14b0ea474cae02c0
expected_output:
- role: human_uniprot_isoforms_fasta
  description: Content assertions for `Human UniProt+Isoforms FASTA`.
  assertions:
  - 'has_text: >sp'
- role: crap
  path: expected_output/cRAP.fasta
  description: Expected output `cRAP` from the source workflow test.
  assertions: []
- role: human_uniprot_isoforms_crap_fasta
  description: Content assertions for `Human UniProt+Isoforms+cRAP FASTA`.
  assertions:
  - 'has_text: >sp'
- role: peptide_and_protein_from_peptide_reports
  path: expected_output/Peptide_and_Protein_from_Peptide_Reports.tabular
  description: Expected output `Peptide and Protein from Peptide Reports` from the
    source workflow test.
  assertions: []
- role: uniprot_id_from_verified_peptides
  path: expected_output/Uniprot-ID_from_verified_Peptides.tabular
  description: Expected output `Uniprot ID from verified Peptides` from the source
    workflow test.
  assertions: []
- role: quantitation_database_for_maxquant
  description: Content assertions for `Quantitation Database for MaxQuant`.
  assertions:
  - 'has_text: >tr'
---

# Clinical metaproteomics peptide verification with PepQuery2

## When to use this sketch
- You already ran a clinical metaproteomics *discovery* search (SearchGUI/PeptideShaker and MaxQuant) and have peptide reports plus a shortlist of distinct candidate microbial peptides.
- You need to independently verify those candidate peptides against the original MS/MS spectra (MGF) before trusting them as microbial hits.
- You want to turn the verified peptides into a compact, targeted protein FASTA (Human UniProt + isoforms + cRAP + verified hits) suitable for a follow-on MaxQuant quantitation run.
- Inputs are clinical human samples with putative microbial peptides (e.g. Papanicolaou / ovarian-cancer pilot data) where false positives from a huge metaproteome search are a major concern.

## Do not use when
- You are at the *discovery* stage and still need to run SearchGUI/PeptideShaker or MaxQuant against a metaproteome database — use the sibling `clinical-metaproteomics-discovery` workflow instead.
- You want label-free / TMT *quantitation* of already-verified peptides — use the sibling `clinical-metaproteomics-quantitation` workflow.
- You are doing generic single-organism proteomics (no microbial component) — a standard SearchGUI/PeptideShaker or MaxQuant sketch is simpler.
- Your input is raw vendor files (Thermo `.raw`, Bruker `.d`) without conversion — convert to MGF (e.g. via msconvert) first.
- You have no candidate peptide list to verify; PepQuery is a targeted validator, not a de-novo search engine.

## Analysis outline
1. **Build target FASTA for PepQuery**: download Human UniProt + isoforms (`dbbuilder`, taxon 9606, keyword KW-1185) and cRAP, then merge with `FASTA Merge Files and Filter Unique Sequences` → `Human UniProt+Isoforms+cRAP FASTA`.
2. **PepQuery2 verification**: run `pepquery2` with `input_type=peptide`, the distinct candidate peptide list, the merged human+cRAP FASTA as the reference database, and the MGF spectrum collection. Task type `novel` — a peptide only passes if it scores better than any match to the reference proteome.
3. **Aggregate PepQuery PSM ranks**: `Collapse Collection` on `psm_rank.txt`, then `Filter` rows where the confident column (`c20=='Yes'`) to keep only verified peptides; strip header with `Remove beginning` and `Cut` column 1 to get the verified peptide list.
4. **Join verified peptides to protein accessions**: `Cut`/`Remove beginning` the SGPS and MaxQuant peptide reports to `(peptide, protein)` pairs, `Concatenate` them, then `Query Tabular` with an INNER JOIN between the verified peptide list and the combined peptide→protein table to produce `Peptide and Protein from Peptide Reports`.
5. **Extract unique UniProt accessions**: `Remove beginning` + `Group` by peptide, then a second `Query Tabular` that normalizes `;`/`,`-separated protein columns and strips `sp|`/`tr|` prefixes to yield `Uniprot ID from verified Peptides`.
6. **Fetch verified protein sequences**: `UniProt XML downloader` (`uniprotxml_downloader` 2.5.0) in FASTA mode on those accessions.
7. **Build quantitation FASTA**: `FASTA Merge Files and Filter Unique Sequences` on Human UniProt+isoforms, cRAP, and the verified-peptide proteome to produce `Quantitation Database for MaxQuant`, the input for the downstream quantitation workflow.

## Key parameters
- `dbbuilder` human source: `from=uniprot`, `taxon=9606`, `set=keyword:KW-1185` (reference proteome), `include_isoform=true`.
- `pepquery2` digestion: `enzyme=1` (trypsin), `max_missed_cleavages=2`.
- `pepquery2` modifications: `fixed_mod=[1,13,14]` (Carbamidomethyl C + TMT-style fixed mods), `var_mod=[2]` (Oxidation M), `unmodified=true`, `aa=true`.
- `pepquery2` MS tolerances: `precursor_tolerance=10 ppm`, fragment `tolerance=0.6` Da; `frag_method=1` (HCD), `scoring_method=1` (HyperScore).
- `pepquery2` charge range: `min_charge=2`, `max_charge=6`; `indexType=2`; `validation.task_type=novel`; output = `psm_rank.txt`.
- Confidence filter: keep rows where PepQuery `confident` column (c20) equals `Yes`.
- FASTA merging: `uniqueness_criterion=sequence`, `processmode=individual`.

## Test data
Four Papanicolaou-smear MS/MS runs in MGF format from the PTRC Skubitz Plex2 pilot dataset (`PTRC_Skubitz_Plex2_F10/F11/F13/F15_9Aug19_Rage_Rep-19-06-08.mgf`, hosted on Zenodo record 14181725) are supplied as the MS/MS input collection, along with three pre-computed tabular peptide reports: `SGPS_peptide-report.tabular` (SearchGUI/PeptideShaker), `MaxQuant-peptide-report.tabular`, and `Distinct_Peptides_for_PepQuery.tabular` (the candidate microbial peptides to verify). The Human UniProt+isoforms FASTA and cRAP FASTA are fetched fresh by `dbbuilder` at runtime. Expected outputs include a cRAP FASTA matching `test-data/cRAP.fasta`, golden tabular files `Peptide_and_Protein_from_Peptide_Reports.tabular` and `Uniprot-ID_from_verified_Peptides.tabular`, and text-assertion checks that the merged human+cRAP and final quantitation FASTAs contain `>sp` and `>tr` headers respectively.

## Reference workflow
Galaxy IWC — `workflows/proteomics/clinicalmp/clinicalmp-verification` (Clinical Metaproteomics Verification Workflow, release 0.2, CC-BY-4.0). Companion tutorial: Galaxy Training Network, *Clinical Metaproteomics 3: Verification*. Part of a three-workflow clinicalMP series (discovery → verification → quantitation).
