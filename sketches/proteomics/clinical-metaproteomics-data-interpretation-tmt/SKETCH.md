---
name: clinical-metaproteomics-data-interpretation-tmt
description: Use when you need to interpret quantified TMT-labeled clinical metaproteomics
  results from MaxQuant by separating microbial and host (human) protein groups, annotating
  microbial peptides taxonomically and functionally with Unipept, and running MSstatsTMT
  differential-abundance statistics with a user-supplied comparison matrix.
domain: proteomics
organism_class:
- human
- microbial-community
input_data:
- maxquant-evidence
- maxquant-protein-groups
- maxquant-quantified-peptides
- msstatstmt-annotation
- msstatstmt-comparison-matrix
source:
  ecosystem: iwc
  workflow: Clinical Metaproteomics Data Interpretation
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/proteomics/clinicalmp/clinicalmp-data-interpretation
  version: '0.1'
  license: CC-BY-4.0
  slug: proteomics--clinicalmp--clinicalmp-data-interpretation
tools:
- name: unipept
  version: 4.5.1
- name: msstatstmt
  version: 2.0.0+galaxy1
- name: galaxy-grep-select
tags:
- metaproteomics
- clinical
- tmt
- maxquant
- unipept
- msstats
- differential-abundance
- taxonomy
- functional-annotation
test_data: []
expected_output: []
---

# Clinical Metaproteomics Data Interpretation (TMT)

Fifth and final stage of the GalaxyP clinical metaproteomics series: take MaxQuant outputs from a TMT-labelled clinical experiment, annotate the microbial peptides with Unipept, split protein groups into microbial vs. human, and run MSstatsTMT differential-abundance statistics on each subset.

## When to use this sketch
- You already have MaxQuant outputs (evidence, proteinGroups, quantified peptides) from a clinical metaproteomics experiment using TMT isobaric labelling.
- The sample matrix mixes host (human) and microbial proteins and you need separate statistical models for each.
- You need Unipept taxonomic (lowest common ancestor) plus functional (EC, GO, InterPro) annotation of quantified microbial peptides.
- You need MSstatsTMT group comparisons with a user-defined annotation file and comparison matrix, producing volcano and comparison plots.
- You are working in Galaxy or want a Galaxy-compatible recipe.

## Do not use when
- You have label-free / DIA / DDA quantification without TMT — use a plain MSstats (non-TMT) sketch instead.
- You have raw RAW/mzML spectra and still need database search / quantification — run the upstream clinical-MP sketches (database generation, discovery, verification, quantitation with MaxQuant) first.
- You only want peptide-level taxonomy with no statistics — use a Unipept-only sketch.
- Your samples are pure host or pure single-organism proteomics — a standard MSstatsTMT sketch without the microbial/human split is simpler.

## Analysis outline
1. Ingest five MaxQuant-derived inputs: Quantified Peptides, Protein Groups, Evidence, MSstatsTMT Annotation, and MSstatsTMT Comparison Matrix.
2. Run Unipept (`peptinfo` API, full-peptide match, equate I/L) on quantified microbial peptides to emit taxonomy tree JSON, peptinfo TSV, and EC / GO / InterPro TSVs.
3. Use Galaxy `Select` (grep) on Protein Groups with pattern `(HUMAN)|(REV)|(CON)|(con)` inverted to produce the Microbial-Proteins table.
4. Use `Select` to keep rows matching `(HUMAN)`, then a second `Select` removing `(REV)|(con)` to produce the Human_Proteins table.
5. Run MSstatsTMT on the microbial protein groups against Evidence + Annotation + Comparison Matrix, producing quant, comparison result, volcano plot, and comparison plot.
6. Run MSstatsTMT a second time on the human protein groups with the same Evidence, Annotation, and Comparison Matrix.
7. Collect renamed outputs (Microbial Taxonomy Tree, Microbial EC/GO/InterPro, Microbial and Human volcano/comparison plots) as the final interpretation deliverables.

## Key parameters
- Unipept: `api: peptinfo`, `peptide_match: full`, `equate_il: true`, `extra: true`, `names: true`, `selected_outputs: [tsv, json, ipr_tsv, go_tsv, ec_tsv, ec_json]`, input column `1` of the tabular peptide file.
- Microbial protein filter (Galaxy Grep1): `pattern: "(HUMAN)|(REV)|(CON)|(con)"`, `invert: -v`, `keep_header: true`.
- Human protein filter: first Grep1 with `pattern: "(HUMAN)"` (no invert), then Grep1 with `pattern: "(REV)|(con)"` and `invert: -v`, both with `keep_header: true`.
- MSstatsTMT input source: `MaxQuant`, `proteinID: Proteins`, `useUniquePeptide: true`, `rmPSM_withfewMea_withinRun: true`, `summaryforMultipleRows: sum`.
- MSstatsTMT protein summarization: `method: msstats`, `global_norm: true`, `reference_norm: true`, `remove_norm_channel: true`, `remove_empty_channel: true`, `MBimpute: true`.
- MSstatsTMT group comparison: `group_comparison: true`, `use_comp_matrix: true` (external comparison matrix), `moderated: false`, `adj_method: none`, significance `sig: 0.05`, `logBase_pvalue: 10`, volcano + comparison plots enabled, `numProtein: 100`, `clustering: protein`.
- Run MSstatsTMT twice — once per filtered protein-group subset (microbial, human) — reusing the same Evidence, Annotation, and Comparison Matrix.

## Test data
The Galaxy test profile supplies five tabular inputs mirroring the real clinical-MP study: `Quantified-Peptides.tabular`, `MaxQuant_Protein_Groups.tabular`, `MaxQuant_Evidence.tabular`, `Annotation.tabular` (MSstatsTMT sample/condition/channel mapping), and `Comparison_Matrix.tabular` (group contrasts). Running the workflow is expected to produce the Unipept peptinfo TSV plus Microbial Taxonomy Tree JSON, Microbial EC Proteins Tree, Microbial EC / GO / InterPro tabular outputs, and two MSstatsTMT result bundles (microbial and human) each containing a quant table, comparison result table, volcano plot PDF, and comparison plot PDF. The filtered Microbial-Proteins and Human_Proteins tables are intermediate checkpoints confirming the host/microbe split.

## Reference workflow
Galaxy IWC — `workflows/proteomics/clinicalmp/clinicalmp-data-interpretation`, workflow "Clinical Metaproteomics Data Interpretation" release 0.1 (2024-11-19), CC-BY-4.0, by GalaxyP. Companion GTN tutorial: https://training.galaxyproject.org/training-material/topics/proteomics/tutorials/clinical-mp-5-data-interpretation/tutorial.html. Key tool versions: Unipept 4.5.1, MSstatsTMT 2.0.0+galaxy1, Galaxy Grep1 1.0.4.
