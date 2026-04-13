---
name: codon-aware-alignment-and-gene-trees-viral
description: Use when you need to turn a collection of unaligned viral CDS sequences
  plus a multi-gene reference CDS into codon-aware per-gene alignments and matching
  per-gene ML phylogenies, ready as inputs for downstream HyPhy selection analyses
  (MEME, FEL, BUSTED, PRIME, CFEL, RELAX). Tuned for viruses; splits the reference
  by gene and emits one alignment + one Newick tree per gene.
domain: phylogenetics
organism_class:
- viral
input_data:
- cds-fasta-collection
- reference-cds-fasta
source:
  ecosystem: iwc
  workflow: 'HyPhy: Preprocessing '
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/comparative_genomics/hyphy
  version: '0.1'
  license: MIT
tools:
- cawlign
- iqtree
- hyphy-cln
- remove_terminal_stop_codons
- fasplit
tags:
- hyphy
- codon-alignment
- selection-analysis
- gene-tree
- viral
- preprocessing
- capheine
test_data: []
expected_output:
- role: combined_summary
  description: Content assertions for `combined_summary`.
  assertions:
  - 'has_text: omega'
  - 'has_n_columns: {''n'': 9}'
---

# Codon-aware alignment and gene trees for viral HyPhy preprocessing

## When to use this sketch
- You have a list collection of unaligned viral sample FASTAs (one file per sample) and a multi-gene reference CDS FASTA (e.g. a Dengue, SARS-CoV-2, or other viral polyprotein downloaded from NCBI) and want one codon-aware alignment and one ML tree per gene.
- You are preparing inputs for HyPhy selection tests (MEME, FEL, BUSTED, PRIME, CFEL, RELAX) and need alignment/tree element identifiers that match gene-by-gene.
- You want terminal stop codons stripped, ambiguous/gappy sequences filtered, and HyPhy-CLN cleanup applied before tree inference.
- Your genes are free of internal stop codons and do not exhibit ongoing recombination.

## Do not use when
- You only need a plain nucleotide multiple sequence alignment with no codon awareness — use a generic MAFFT/MUSCLE sketch instead.
- You already have per-gene alignments and trees and just want to run the selection tests — use the downstream `hyphy-selection-analysis` sketch (CAPHEINE Core / Compare) directly.
- Your sequences are non-coding, contain frequent internal stop codons, or show strong recombination signal — codon-aware alignment and single-tree inference will mislead downstream dN/dS estimates.
- Working with bacterial or eukaryotic coding genes without carefully validated, recombination-free inputs — the workflow is tuned for viruses and bacterial/eukaryotic runs are explicitly flagged as risky by the authors.
- You need whole-genome variant calling, assembly, or transcript quantification — wrong domain entirely.

## Analysis outline
1. Strip terminal stop codons from the reference CDS with `remove_terminal_stop_codons` (genetic code 1, universal).
2. Split the cleaned reference CDS by record name into one FASTA per gene with UCSC `faSplit` (`byname`).
3. Collapse the input list collection of per-sample FASTAs into a single concatenated FASTA with `Collapse Collection`.
4. For each reference gene, run `cawlign` to produce a codon-aware alignment of every sample against that gene (codon scoring, BLOSUM62, `local_alignment=trim`, `format=refmap`).
5. Drop sequences whose gap/`N` fraction exceeds 0.5 using an awk filter, then recast output as FASTA.
6. Run `HyPhy-CLN` on the filtered alignment (universal genetic code, filtering method Yes/Yes) to remove problematic sequences and harmonize identifiers.
7. Infer a per-gene ML phylogeny with `IQ-TREE` 2 (DNA, automatic model selection, default UFBoot settings) and emit `treefile` as the per-gene Newick output.
8. Pair each cleaned per-gene alignment with its matching per-gene tree by element identifier and hand both collections off to downstream HyPhy tools.

## Key parameters
- `remove_terminal_stop_codons.genetic_code`: `1` (universal).
- `faSplit.O.split_type`: `byname` — one output FASTA per reference gene record.
- `cawlign.scoring_matrix_cond.datatype`: `codon`; `scoring_matrix`: `BLOSUM62`.
- `cawlign.local_alignment`: `trim`; `format`: `refmap`; `affine_gap`: `false`; `reverse_complement`: `none`.
- Ambiguity filter threshold: gap/`N` fraction `<= 0.5` (awk `VAR1=0.5`).
- `HyPhy-CLN.gencodeid`: `Universal`; `filtering_method`: `Yes/Yes`.
- `IQ-TREE.seqtype`: `DNA`; automatic model selection (`msub=nuclear`, `cmin=2`, `cmax=10`, `merit=AIC`); default tree search (`ninit=100`, `ntop=20`, `nbest=5`, `nstop=100`, `radius=6`, `perturb=0.5`); UFBoot defaults (`nmax=1000`, `bcor=0.99`, `nstep=100`, `beps=0.5`).

## Test data
The parent CAPHEINE test suite exercises this preprocessing subworkflow with a Dengue virus 1 (DENV1) reference CDS (`denv1_ref_cds.fasta`) plus a list collection of unaligned per-sample DENV1 FASTAs drawn from NCBI accessions such as `AB178040.1|2002`, `AB195673.1|2003`, `AB204803.1|2004`, `AF298807.1|1998`, and `AF298808.1|1998` (Core-only scenario), and adds more recent 2023 PP-series accessions when branch-comparison scenarios are run. Running the full CAPHEINE pipeline on these inputs is expected to yield a `combined_summary` table that contains per-gene rows with columns including `gene`, `BUSTED`, `MEME`, `pval`, and `omega` (9 columns in the Core-only scenario), confirming that the preprocessing stage successfully produced matched per-gene alignments and trees consumable by HyPhy. This subworkflow's own outputs are the cleaned per-gene FASTA alignment collection (from HyPhy-CLN) and the per-gene Newick `treefile` collection (from IQ-TREE).

## Reference workflow
Galaxy IWC `workflows/comparative_genomics/hyphy/hyphy-preprocessing.ga`, release 0.1 (2026-02-26), part of the CAPHEINE HyPhy workflow suite inspired by veg/capheine 1.1.0. Key tool versions: `remove_terminal_stop_codons` 1.0.0+galaxy0, `ucsc_fasplit` 482, `collapse_collections` 5.1.0, `cawlign` 0.1.15+galaxy0, `hyphy_cln` 2.5.96+galaxy0, `iqtree` 2.4.0+galaxy1.
