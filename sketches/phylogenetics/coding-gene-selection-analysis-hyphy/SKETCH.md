---
name: coding-gene-selection-analysis-hyphy
description: Use when you have a multiple sequence alignment of a coding gene plus
  a phylogenetic tree and you need to test for selection (positive, purifying, episodic,
  directional, relaxed/intensified), detect recombination breakpoints, or identify
  coevolving sites using HyPhy methods such as aBSREL, BUSTED, FEL, FUBAR, MEME, SLAC,
  RELAX, FADE, BGM, or GARD.
domain: phylogenetics
organism_class:
- eukaryote
- viral
- bacterial
input_data:
- codon-alignment-fasta
- newick-tree
source:
  ecosystem: nf-core
  workflow: nf-core/genephylomodeler
  url: https://github.com/nf-core/genephylomodeler
  version: dev
  license: MIT
tools:
- hyphy
- absrel
- busted
- fel
- fubar
- meme
- slac
- relax
- fade
- bgm
- gard
tags:
- phylogenetics
- selection
- dn-ds
- hyphy
- codon-alignment
- recombination
- positive-selection
- episodic-selection
test_data: []
expected_output: []
---

# Coding gene selection analysis with HyPhy

## When to use this sketch
- You already have a codon-aware multiple sequence alignment (nucleotide FASTA, in-frame) for one or more protein-coding genes.
- You already have a phylogenetic tree (Newick) for each alignment; some methods (BUSTED, RELAX, FADE) additionally require branch labels distinguishing test vs. reference branches.
- You want to answer evolutionary-hypothesis questions such as: which sites are under pervasive positive or purifying selection (FEL, FUBAR, SLAC), which branches experienced episodic diversifying selection (aBSREL, BUSTED), which sites show episodic selection (MEME), whether selection has been relaxed or intensified on a clade (RELAX), which residues show directional bias (FADE), which sites coevolve (BGM), or where recombination breakpoints lie (GARD).
- You want to run several HyPhy methods across many genes in a single reproducible sweep and collect per-gene JSON + text logs.

## Do not use when
- You still need to build the alignment or the tree from raw sequences — this pipeline is strictly downstream of alignment/tree inference. Use an MSA + tree-building workflow first.
- You are calling variants, assembling, or doing read-level analysis — this pipeline does not touch reads.
- You need codeml/PAML branch-site models specifically; this pipeline currently exposes only HyPhy methods.
- You want whole-genome scans of non-coding regions — HyPhy selection methods assume codon alignments of coding genes.

## Analysis outline
1. Author a samplesheet CSV with one row per (gene, tool) combination: `gene_name,alignment,tree,suite,tool`.
2. For each row, the pipeline dispatches the requested HyPhy analysis (`suite=hyphy`, `tool` ∈ {absrel, bgm, busted, fade, fel, fubar, gard, meme, relax, slac}) against the provided codon alignment and Newick tree.
3. HyPhy runs the selected method and emits a per-gene `*_<METHOD>.json` results file plus a `*_<METHOD>_output.txt` run log into a per-tool output subdirectory.
4. Nextflow collects execution reports, software versions, and the validated samplesheet under `pipeline_info/`.

## Key parameters
- `--input` (required): path to the samplesheet CSV. Columns: `gene_name`, `alignment` (nucleotide FASTA codon alignment), `tree` (Newick; labeled branches required for BUSTED/RELAX/FADE), `suite` (`hyphy`), `tool` (one of the ten HyPhy methods above).
- `--outdir` (required): absolute path for results; one subdirectory per method (`absrel/`, `busted/`, `fel/`, …).
- Per-analysis selection is driven entirely by the `tool` column in the samplesheet — add multiple rows for the same gene to run several methods. Spaces in `gene_name` are normalized to underscores in output filenames.
- Use `-profile docker`/`singularity`/`conda` for container backends; `-profile test` loads a bundled minimal samplesheet.
- Tool-specific HyPhy flags (e.g. branch sets for RELAX, grid sizes for FUBAR) are not first-class pipeline parameters; supply them via module `ext.args` in a custom Nextflow config if needed.

## Test data
The `test` profile points at `samplesheet/test_samplesheet.csv` in the nf-core test-datasets `genephylomodeler` branch, which uses a primate KSR2 (kinase suppressor of RAS-2) codon alignment and tree from Enard et al. 2016 (eLife). Running `-profile test` is expected to exercise representative HyPhy tools against this single gene and produce per-tool subdirectories containing `KSR2_<METHOD>.json` and `KSR2_<METHOD>_output.txt` files along with the standard nf-core `pipeline_info/` reports. A larger `test_full` profile points at `samplesheet/test_full_samplesheet.csv` for AWS full-size CI.

## Reference workflow
nf-core/genephylomodeler (dev, template 3.4.1) — https://github.com/nf-core/genephylomodeler. Wraps HyPhy 2.5 (Kosakovsky Pond et al., MBE 2020) methods: aBSREL, BGM, BUSTED, FADE, FEL, FUBAR, GARD, MEME, RELAX, SLAC.
