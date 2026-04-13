---
name: codon-selection-hyphy-viral
description: Use when you need to detect episodic, pervasive, or branch-specific positive/negative
  selection on viral coding sequences (e.g. dengue, SARS-CoV-2, influenza) using HyPhy
  methods (MEME, FEL, BUSTED, PRIME) with optional Contrast-FEL/RELAX branch comparisons
  between a user-defined foreground clade and the remaining reference branches.
domain: phylogenetics
organism_class:
- viral
input_data:
- cds-fasta-collection
- reference-cds-fasta
- foreground-list-optional
source:
  ecosystem: iwc
  workflow: 'CAPHEINE: Combined HyPhy Core and Compare'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/comparative_genomics/hyphy
  version: '0.1'
  license: MIT
tools:
- cawlign
- hyphy-cln
- iqtree
- hyphy-meme
- hyphy-fel
- hyphy-busted
- hyphy-prime
- hyphy-annotate
- hyphy-cfel
- hyphy-relax
- drhip
tags:
- hyphy
- selection
- dn-ds
- codon
- capheine
- viral
- comparative-genomics
- branch-test
- contrast-fel
- relax
test_data: []
expected_output:
- role: combined_summary
  description: Content assertions for `combined_summary`.
  assertions:
  - 'has_text: omega'
  - 'has_n_columns: {''n'': 9}'
---

# CAPHEINE HyPhy codon selection analysis (viral)

## When to use this sketch
- You have a panel of unaligned viral coding sequences (one FASTA per sample) and a multi-gene reference CDS (e.g. a RefSeq/GenBank polyprotein split into genes) and want per-gene codon-aware alignments, ML gene trees, and HyPhy selection calls.
- You want site-level tests for pervasive (FEL) and episodic (MEME) positive selection, gene-level gene-wide episodic selection (BUSTED), and property-informed selection (PRIME), all run per gene with identical element identifiers.
- You optionally want a branch-comparison analysis between a foreground clade (defined by a regex on tip labels or an explicit identifier list) and the remaining reference branches, using HyPhy Annotate → Contrast-FEL (site-level dN/dS contrast) and RELAX (test for relaxed vs intensified selection).
- You want a single combined summary table (via DRHIP) merging MEME/FEL/BUSTED/PRIME (and optionally CFEL/RELAX) across genes for downstream interpretation.
- Dataset is clean viral CDS: no internal stop codons, minimal ongoing recombination, and tip labels can be cleaned to `[0-9A-Za-z_]` (HyPhy CLN convention).

## Do not use when
- You want raw variant calls against a reference genome rather than codon selection inference — use a variant-calling sketch instead.
- Your inputs are bacterial or eukaryotic genes with introns, frequent internal stops, or strong recombination; codon-aware alignment and HyPhy assumptions break down and results become misleading.
- You only need a single-method selection test on an already-aligned codon MSA with a prebuilt tree — invoke HyPhy MEME/FEL/BUSTED directly rather than running the full CAPHEINE preprocessing stack.
- You need whole-genome phylogenetic placement, tree dating, or recombination detection — use dedicated phylogenetics sketches.
- Your foreground/reference split is defined by a trait/phenotype table rather than sequence-name matching; this workflow only supports list- or regex-based tip selection.

## Analysis outline
1. Split the reference CDS into per-gene FASTAs (faSplit byname) and strip terminal stop codons (remove_terminal_stop_codons, genetic code 1).
2. Collapse the unaligned sample collection into a single FASTA and, for every reference gene, run codon-aware alignment against all samples with `cawlign` (codon datatype, BLOSUM62, `local_alignment=trim`, `format=refmap`).
3. Drop sequences whose gap/ambiguity fraction exceeds 0.5 (awk filter) and sanitize headers/records with `HyPhy-CLN` (Universal code, filtering Yes/Yes).
4. Build a per-gene ML phylogeny with `IQ-TREE` 2.4 (DNA, ModelFinder auto, default tree search; produces `.treefile`).
5. Run the four Core HyPhy selection methods on each (alignment, tree) pair: `HyPhy-MEME` (p=0.1), `HyPhy-FEL` (p=0.1, SRV on), `HyPhy-BUSTED` (error sink on, 3 rate classes), `HyPhy-PRIME` (Atchley properties, p=0.1). All four use `branch_sel=All`, `gencodeid=Universal`, `kill_zero_lengths=Yes`.
6. (Optional Compare) If a foreground regex is supplied, grep it against cleaned sequence identifiers to derive a foreground list; otherwise use the user-supplied list. If both are given, regex wins and the explicit list is ignored.
7. (Optional Compare) Clean the foreground list the same way HyPhy CLN cleaned the tree tips, then run `HyPhy-Annotate` twice — once to label matching branches `{Foreground}` and once (inverted) to label the rest `{Reference}`.
8. (Optional Compare) On each labeled tree, run `HyPhy-CFEL` (Foreground vs Reference, p=0.05, q=0.2, SRV on) and `HyPhy-RELAX` (test=Foreground, reference=Reference, classic mode, all models).
9. Aggregate every per-gene JSON across MEME/FEL/BUSTED/PRIME (+ CFEL/RELAX when available) with `DRHIP` into combined summary and per-site tables.

## Key parameters
- Genetic code: `Universal` (HyPhy `gencodeid=Universal`, remove_terminal_stop_codons `genetic_code=1`). Change only for mitochondrial/alternative-code viruses.
- Ambiguity filter threshold: gap/N fraction ≤ `0.5` in the post-cawlign awk cleanup.
- HyPhy Core significance: `p_value=0.1` for MEME, FEL, PRIME (liberal, as is standard for exploratory HyPhy scans); BUSTED rate classes = 3 with error sink enabled.
- HyPhy FEL/BUSTED/PRIME/MEME: `branch_sel=All`, `kill_zero_lengths=Yes`, `full_model=true` where applicable.
- cawlign: `datatype=codon`, builtin `BLOSUM62`, `local_alignment=trim`, `format=refmap`, reference supplied from history (split reference).
- IQ-TREE: `seqtype=DNA`, automatic ModelFinder (`merit=AIC`, `cmin=2`, `cmax=10`), default `ninit=100`, `ntop=20`, `nbest=5`, `nstop=100`, `perturb=0.5`, `radius=6`.
- Contrast-FEL: `pvalue=0.05`, `qvalue=0.2`, branch labels `Foreground` and `Reference`, SRV on.
- RELAX: `test=Foreground`, `reference=Reference`, `models=All`, classic mode, 3 synonymous + 3 nonsynonymous rate classes, SRV off.
- Foreground regex: applied *after* HyPhy CLN name sanitization, so match against `_`-delimited cleaned names (e.g. `_2023_09_` not `|2023-09-`).
- Routing logic: no regex and no list → Core only; regex present (with or without list) → regex builds foreground; list only → list used verbatim.

## Test data
Four Planemo scenarios ship with the workflow, all using a DENV1 multi-gene reference CDS (`denv1_ref_cds.fasta`) plus 5–8 unaligned dengue virus 1 sample FASTAs drawn from a pool of 39 GenBank accessions (e.g. `AB178040.1|2002`, `AB195673.1|2003`, `PP563838.1|2023-09-30`). Scenario 1 runs Core only (5 samples, no foreground) and asserts that the DRHIP `combined_summary` table contains `gene`, `BUSTED`, `MEME`, `pval`, and `omega` columns with 9 columns total. Scenarios 2–4 exercise the Compare module by supplying a regex (`_2023_09_`), an explicit `foreground_seqs_list.txt`, or both; they additionally assert that `combined_summary` widens to 12 columns (adding `RELAX`) and that `combined_comparison_summary` has 6 columns including `gene`, `comparison_group`, `Foreground`, and `Reference`. Scenario 4 verifies that when both regex and list are supplied, the regex takes precedence.

## Reference workflow
Galaxy IWC `workflows/comparative_genomics/hyphy/capheine-core-and-compare.ga`, release 0.1 (CAPHEINE: Combined HyPhy Core and Compare), MIT-licensed. Mirrors the logic of the upstream Nextflow `veg/capheine` v1.1.0. Core HyPhy tools are all from the `iuc` tool shed at HyPhy 2.5.96+galaxy0; alignment uses `cawlign` 0.1.15+galaxy0 and tree inference uses `iqtree` 2.4.0+galaxy1; cross-gene aggregation uses `drhip` 0.1.4+galaxy0.
