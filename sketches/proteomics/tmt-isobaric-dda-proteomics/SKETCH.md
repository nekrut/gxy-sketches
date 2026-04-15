---
name: tmt-isobaric-dda-proteomics
description: Use when you need to identify and quantify proteins from data-dependent
  acquisition (DDA) LC-MS/MS runs labelled with isobaric tags (TMT6/10/11plex or iTRAQ),
  producing PSM, peptide, protein and gene tables with per-channel quantifications
  against a target protein FASTA.
domain: proteomics
organism_class:
- eukaryote
- vertebrate
input_data:
- mzml-dda
- protein-fasta
- modifications-file
source:
  ecosystem: nf-core
  workflow: nf-core/ddamsproteomics
  url: https://github.com/nf-core/ddamsproteomics
  version: dev
  license: MIT
  slug: ddamsproteomics
tools:
- name: msgf+
- name: percolator
- name: openms
- name: hardklor
- name: kronik
- name: msstitch
tags:
- proteomics
- dda
- tmt
- isobaric
- label-based
- shotgun
- quantitative
- lehtio
test_data: []
expected_output: []
---

# TMT isobaric DDA shotgun proteomics

## When to use this sketch
- You have centroided `.mzML` files from a DDA shotgun proteomics experiment on an Orbitrap-class instrument (e.g. Q Exactive, Fusion).
- Samples are multiplexed with isobaric tags — TMT6/10/11plex or iTRAQ4/8plex — and you want per-channel reporter-ion intensities rolled up to peptide, protein and gene level.
- You have a target protein FASTA (e.g. SwissProt, Ensembl `pep.all.fa`) and want tryptic-reverse decoys generated automatically with a T-TDC concatenated search.
- You want standard Lehtio-lab style output: MSGF+ identifications, Percolator rescoring, OpenMS isobaric quant, optional Hardklor/Kronik MS1 precursor quant, and Msstitch post-processing with q-values and protein groups.
- Optionally your samples were pre-fractionated by HiRIEF / high-pH RP and you want fraction metadata respected during FDR and quant roll-up.

## Do not use when
- Your data is DIA (SWATH, diaPASEF) — use a DIA-specific sketch (e.g. DIA-NN / OpenSwath) instead.
- Your data is label-free quantification with MaxLFQ-style intensity comparisons — use an LFQ DDA sketch.
- Your data is SILAC or other MS1-based metabolic labelling — this pipeline is built around isobaric reporter-ion quant.
- You need PTM site localisation with Ascore/PTMProphet as the primary readout — this sketch emits standard variable-mod search output only.
- You want a currently-maintained nf-core proteomics pipeline: prefer `nf-core/quantms`; this sketch documents the legacy `nf-core/ddamsproteomics` recipe.

## Analysis outline
1. Stage `.mzML` spectra from `--mzmls` glob or a tab-delimited `--mzmldef` manifest (path, sample/set, optional plate, optional fraction number).
2. Build a target-decoy concatenated database by tryptic-reverse decoy generation from `--tdb`.
3. Run MSGF+ peptide identification against the concatenated DB using the modifications defined in `--mods`.
4. Rescore target/decoy PSMs with Percolator to obtain PEP and q-values.
5. Extract isobaric reporter-ion intensities per PSM with OpenMS `IsobaricAnalyzer` for the chosen `--isobaric` plex.
6. (Optional) Quantify MS1 precursor peptide features with Hardklor + Kronik for label-free/precursor summaries.
7. Merge IDs and quant, infer proteins and protein groups, and emit PSM/peptide/protein/gene tables with Msstitch, applying per-set denominator normalisation (`--denoms`) and optional median centering (`--normalize`).
8. Collect QC metrics and a MultiQC report into `--outdir`.

## Key parameters
- `--mzmls '*.mzML'` or `--mzmldef manifest.txt` — spectrum inputs; manifest is TSV `path\tsample\t[plate]\t[fraction]`.
- `--tdb /path/to/target.fasta` — target protein FASTA; decoys are generated internally (tryptic-reverse, concatenated).
- `--mods assets/tmtmods.txt` — MSGF+ modifications file; ship the TMT variant for isobaric runs (fixed TMT on K and peptide N-term, variable Met oxidation, fixed Cys carbamidomethyl).
- `--isobaric tmt10plex` — selects reporter-ion channels; also accepts `tmt6plex`, `tmt11plex`, `itraq4plex`, `itraq8plex`.
- `--denoms 'set1:126 set2:131'` — per-set denominator channel(s) used to compute ratios before roll-up.
- `--normalize true` — median-centre channel ratios across PSMs.
- `--hirief true` — treat inputs as HiRIEF-fractionated; consumes plate/fraction columns from the mzML manifest.
- `--genes true` — additionally emit gene-level quant tables (requires gene symbols parseable from FASTA headers).
- `-profile docker|singularity|conda` — container/runtime selection; combine with `test` for the bundled CI profile.

## Test data
The `test` profile stages two public `.mzML` files, `set1_518_scans_QE_tmt10_fasp_cellines_human.mzML` and `set2_518_scans_QE_tmt10_fasp_cellines_human.mzML`, which are 518-scan Q Exactive DDA slices of TMT10plex-labelled human cell-line FASP digests, each tagged with HiRIEF plate `3.7-4.9` and fraction `08`. Searches run against the `HUMAN_2014_concat.fasta` target database from `nf-core/test-datasets`, with `assets/tmtmods.txt` modifications, `--isobaric tmt10plex`, denominators `set1:126 set2:131`, median normalisation on, and HiRIEF + gene-level output enabled. A successful run produces MSGF+/Percolator PSM tables plus Msstitch peptide, protein and gene tables containing TMT10 reporter-ion quantities per channel and a MultiQC report under `results/`.

## Reference workflow
`nf-core/ddamsproteomics` (dev branch; last maintained release ~1.x), MIT licensed. Upstream note: the pipeline is no longer maintained — for new projects prefer `nf-core/quantms`, which supersedes it with the same DDA+TMT functionality plus DIA and LFQ support.
