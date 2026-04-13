---
name: hyphy-codon-selection-viral
description: Use when you need to detect codon-level selection pressure (positive/purifying/episodic)
  across a panel of viral coding sequences using HyPhy's MEME, FEL, BUSTED, and PRIME
  methods. Takes a multi-gene reference CDS plus a collection of unaligned viral assemblies
  and produces per-gene codon-aware alignments, ML gene trees, and JSON selection
  results.
domain: phylogenetics
organism_class:
- viral
input_data:
- cds-fasta-collection
- reference-cds-fasta
source:
  ecosystem: iwc
  workflow: 'HyPhy: Core'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/comparative_genomics/hyphy
  version: '0.1'
  license: MIT
tools:
- cawlign
- iqtree
- hyphy-meme
- hyphy-fel
- hyphy-busted
- hyphy-prime
- hyphy-cln
- remove_terminal_stop_codons
tags:
- selection
- dnds
- codon
- hyphy
- viral
- comparative-genomics
- positive-selection
test_data: []
expected_output:
- role: combined_summary
  description: Content assertions for `combined_summary`.
  assertions:
  - 'has_text: omega'
  - 'has_n_columns: {''n'': 9}'
---

# HyPhy codon selection analysis for viral CDS

## When to use this sketch
- You have a collection of viral assemblies (e.g. DENV, SARS-CoV-2, influenza) and a reference multi-gene CDS FASTA and want per-gene dN/dS-style selection tests.
- You need site-level selection results: MEME (episodic positive selection), FEL (pervasive per-site selection), BUSTED (gene-wide episodic diversifying selection), PRIME (property-informed selection on physicochemical axes).
- Codon-aware alignment against a reference is appropriate (no internal stop codons, minimal recombination).
- You want one JSON result per gene per method, suitable for HyPhy Vision or programmatic parsing.

## Do not use when
- You need branch-comparison tests (foreground vs background) such as RELAX or Contrast-FEL — use the sibling `hyphy-branch-comparison-viral` sketch (CAPHEINE Compare module), which adds foreground labeling via regex or ID list.
- You are working with bacterial or eukaryotic genomes with introns, paralogs, or ongoing recombination — results will be unreliable.
- You only have protein sequences or non-coding regions — HyPhy requires in-frame codon alignments.
- You want a simple multiple-sequence alignment or phylogeny without selection testing — use a generic alignment/tree sketch instead.
- Your genes contain internal stop codons or frameshifts; preprocessing will drop or mangle them.

## Analysis outline
1. Strip terminal stop codons from the reference CDS (`remove_terminal_stop_codons`, genetic code 1).
2. Split the reference CDS by gene into one FASTA per gene (`faSplit byname`).
3. Collapse the input sample collection into a single multi-FASTA (`collapse_collections`).
4. For each reference gene, run codon-aware alignment of all samples against that gene (`cawlign`, codon BLOSUM62, local-alignment `trim`).
5. Filter ambiguous/gappy sequences (awk: drop records where gap+N fraction > 0.5) and convert back to FASTA.
6. Clean alignments with `HyPhy-CLN` (universal genetic code, filtering Yes/Yes).
7. Build a per-gene ML phylogeny with `IQ-TREE` (DNA, ModelFinder, default tree search).
8. Run HyPhy selection methods per gene using the cleaned alignment + gene tree: `HyPhy-MEME`, `HyPhy-FEL`, `HyPhy-BUSTED`, `HyPhy-PRIME`.
9. Emit per-gene JSON result collections (MEME/FEL/BUSTED/PRIME) and markdown reports; element IDs are harmonized across alignments, trees, and all four result collections.

## Key parameters
- `gencodeid: Universal` — genetic code 1 across HyPhy-CLN, MEME, FEL, BUSTED, PRIME.
- `cawlign`: `datatype=codon`, `scoring_matrix=BLOSUM62`, `local_alignment=trim`, `format=refmap`, `reverse_complement=none`.
- Ambiguity filter: drop sequences whose `(gaps+N)/length > 0.5`.
- `HyPhy-CLN`: `filtering_method=Yes/Yes`.
- `IQ-TREE`: `seqtype=DNA`, automatic ModelFinder (AIC), `ninit=100`, `ntop=20`, `nbest=5`, `nstop=100`.
- MEME: `p_value=0.1`, `rates=2`, `branch_sel=All`, `kill_zero_lengths=Yes`, `full_model=true`.
- FEL: `p_value=0.1`, `include_srv=Yes`, `branch_sel=All`, `kill_zero_lengths=Yes`.
- BUSTED: `syn_rates=3`, `rates=3`, `grid_size=250`, `starting_points=1`, `error_sink=true`, `branch_sel=All`, `kill_zero_lengths=Yes`.
- PRIME: `p_value=0.1`, `prop_set=Atchley`, `branch_sel=All`, `kill_zero_lengths=Yes`.

## Test data
The source workflow ships a Dengue virus 1 reference CDS (`denv1_ref_cds.fasta`) plus a `unaligned_seqs/` directory of 39 single-sample DENV1 FASTA files drawn from public GenBank accessions (e.g. `AB178040.1|2002`, `AB195673.1|2003`, `PP563838.1|2023-09-30`). The Core-only test scenario uses a reduced subset of five assemblies and asserts that the combined per-gene summary table contains columns for `gene`, `BUSTED`, `MEME`, `pval`, and `omega`, with nine columns total — confirming that all four HyPhy methods ran and produced parseable per-gene selection statistics.

## Reference workflow
Galaxy IWC — `workflows/comparative_genomics/hyphy/hyphy-core.ga` (HyPhy: Core, release 0.1), used as the Core module of the CAPHEINE combined pipeline (inspired by veg/capheine v1.1.0). HyPhy tool versions: 2.5.96+galaxy0; cawlign 0.1.15+galaxy0; IQ-TREE 2.4.0+galaxy1.
