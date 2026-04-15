---
name: hyphy-branch-selection-comparison
description: "Use when you have codon-aware coding-sequence alignments and matching\
  \ gene phylogenies and need to contrast selection pressures between a user-defined\
  \ foreground branch set and the remaining reference branches \u2014 e.g. testing\
  \ whether a viral lineage, host-adapted clade, or treatment group shows relaxed/intensified\
  \ selection or site-level dN/dS differences versus the rest of the tree."
domain: phylogenetics
organism_class:
- viral
- eukaryote
input_data:
- codon-aware-alignment-fasta
- newick-tree
- foreground-id-list
source:
  ecosystem: iwc
  workflow: 'HyPhy: Compare'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/comparative_genomics/hyphy
  version: '0.1'
  license: MIT
  slug: comparative_genomics--hyphy--hyphy-preprocessing
tools:
- name: hyphy-annotate
- name: hyphy-cfel
- name: hyphy-relax
tags:
- hyphy
- selection
- dn-ds
- contrast-fel
- relax
- comparative-genomics
- branch-test
- viral-evolution
test_data: []
expected_output:
- role: combined_summary
  description: Content assertions for `combined_summary`.
  assertions:
  - 'has_text: omega'
  - 'has_n_columns: {''n'': 9}'
---

# HyPhy branch selection comparison (Contrast-FEL + RELAX)

## When to use this sketch
- You already have per-gene codon-aware alignments (FASTA) and matching IQ-TREE/RAxML phylogenies (Newick) with consistent element IDs across the two collections.
- You want to split tree branches into two classes — Foreground (a user-supplied list of tip names) vs Reference (everything else) — and ask whether selection differs between them.
- You need both site-level (Contrast-FEL: which codons differ in dN/dS between groups) and gene-level (RELAX: K test for relaxed vs intensified selection on foreground) answers.
- Typical use: viral surveillance comparing a recent lineage/outbreak clade to historical background (e.g. DENV1 2023 isolates vs older sequences), or any comparative-genomics setup where a clade label is known a priori.
- Inputs are assumed clean: no internal stop codons, minimal recombination, coding-frame preserved.

## Do not use when
- You only have raw unaligned CDS and no trees — run the HyPhy preprocessing / Core workflow first (sibling sketch: `hyphy-codon-alignment-and-core-selection`) to produce codon-aware alignments and gene trees.
- You want genome-wide scans for episodic positive selection without a pre-defined foreground — use MEME/BUSTED/FEL from the HyPhy Core sketch instead.
- Your sequences are non-coding, contain internal stops, or show substantial recombination — Contrast-FEL/RELAX assumptions will be violated.
- You want branch-site tests on a single a priori branch rather than a two-class partition — use aBSREL or BUSTED[S] directly.
- You are doing bulk dN/dS across populations without phylogeny — use population-genetics tools (e.g. SnIPRE, PAML codeml site models), not HyPhy branch tests.

## Analysis outline
1. Normalize the foreground identifier list (awk `gsub(/[^0-9A-Za-z_]/, "_")`) so names match the cleaned labels used in the alignment/tree leaves.
2. HyPhy Annotate (label-tree) pass 1: tag all tips matching the list with `{Foreground}`, propagating to internal nodes via `All descendants`.
3. HyPhy Annotate pass 2 on the already-labeled tree: with `invert=true`, tag the complement as `{Reference}`. Result is a fully-partitioned NHX tree.
4. HyPhy Contrast-FEL (CFEL) on each (alignment, labeled-tree) pair with branch sets `Foreground` and `Reference`, producing a JSON of per-site dN/dS contrasts and p/q-values.
5. HyPhy RELAX on each (alignment, labeled-tree) pair with `test=Foreground`, `reference=Reference`, returning the K selection-intensity parameter and LRT for relaxation vs intensification.
6. Collect per-gene CFEL and RELAX JSONs; downstream consumers summarize into per-gene and per-site tables.

## Key parameters
- Annotate: `selection_method=list`, `leaf_nodes=Label`, `internal_nodes=All descendants`; second pass uses `invert=true` with label `Reference`.
- Genetic code: `Universal` for both CFEL and RELAX (change only for mito/alt-code organisms).
- Contrast-FEL: `branch_labels=[Foreground, Reference]`, `pvalue=0.05`, `qvalue=0.2`, `srv=Yes` (synonymous rate variation on), `kill_zero_lengths=Yes`.
- RELAX: `test=Foreground`, `reference=Reference`, `models=All` (fits null + alternative + partitioned), `mode=Classic`, `grid_size=250`, `starting_points=1`, `syn_rates=3`, `rates=3`, `srv=No`, `kill_zero_lengths=Yes`. Interpretation: K<1 ⇒ relaxed selection on foreground, K>1 ⇒ intensified.
- Identifier hygiene: foreground list must use the same `[^0-9A-Za-z_]→_` sanitization the upstream alignment step applied, or Annotate will silently fail to mark tips.

## Test data
The upstream CAPHEINE test suite drives this Compare module using Dengue virus 1 (DENV1): a multi-gene reference CDS (`denv1_ref_cds.fasta`) plus a list collection of unaligned per-sample FASTAs drawn from NCBI (mix of older isolates like `AB178040.1|2002`, `AB195673.1|2003`, `AF298807.1|1998` and a 2023 outbreak cluster `PP563828`–`PP563841`). Foreground is defined either by the regex `_2023_09_` (matching the 2023 September isolates) or by the explicit `foreground_seqs_list.txt`; both routes should yield equivalent Foreground/Reference partitions. Successful runs produce labeled NHX trees plus per-gene CFEL and RELAX JSONs; the combined CAPHEINE summaries are asserted to contain the columns `gene`, `RELAX`, `pval`, and a per-gene `combined_comparison_summary` with `comparison_group`, `Foreground`, and `Reference` entries.

## Reference workflow
Galaxy IWC `HyPhy: Compare` (workflows/comparative_genomics/hyphy/hyphy-compare.ga), release 0.1, inspired by veg/capheine (Nextflow v1.1.0). Uses HyPhy tools at version 2.5.96+galaxy0 (hyphy_annotate, hyphy_cfel, hyphy_relax) from the IUC toolshed.
