---
name: phylogenetic-placement-epa-ng
description: Use when you need to place query sequences (e.g. protein fragments, amplicons,
  metagenomic reads) onto an existing reference phylogeny using EPA-NG rather than
  building a new tree from scratch. Supports optional HMMER search-then-place mode
  and taxonomic classification of placements.
domain: phylogenetics
organism_class:
- any
input_data:
- query-fasta
- reference-alignment-fasta
- reference-newick
- optional-hmm-profile
- optional-taxonomy-tsv
source:
  ecosystem: nf-core
  workflow: nf-core/phyloplace
  url: https://github.com/nf-core/phyloplace
  version: 2.0.0
  license: MIT
  slug: phyloplace
tools:
- name: epa-ng
- name: gappa
- name: hmmer
- name: clustalo
- name: mafft
tags:
- phylogenetic-placement
- epa-ng
- gappa
- hmmer
- amplicon
- metagenomics
- reference-tree
- classification
test_data: []
expected_output: []
---

# Phylogenetic placement with EPA-NG

## When to use this sketch
- You already have a curated reference alignment + reference phylogeny and want to place new query sequences into it without re-inferring the whole tree.
- Query sequences are short, fragmentary, or very numerous (PCR amplicons, metagenomic contigs, protein family members) so full tree inference is impractical.
- You want per-query placement likelihoods, a grafted "comprehensive" tree, and optionally taxonomic classification of placements via a reference taxonomy.
- You want a single pipeline to optionally first HMMER-search a large FASTA against one or more profiles, then place the best hits onto per-profile reference trees ("search and place" mode).

## Do not use when
- You need to build the phylogeny itself from scratch — use a de novo tree inference workflow (RAxML/IQ-TREE based), not this sketch.
- You are doing 16S/ITS amplicon community profiling end-to-end from raw reads — prefer an amplicon-specific sketch (DADA2/QIIME2); this sketch assumes cleaned query sequences.
- You want whole-genome SNP phylogenies of bacterial isolates — use a core-genome/SNP phylogenomics sketch instead.
- You only need taxonomic classification without a reference tree — use a k-mer classifier (Kraken2, etc.).

## Analysis outline
1. (Optional, "search and place" mode) Run `hmmsearch` from HMMER against `--search_fasta` using one or more HMM profiles listed in `phylosearch_input`; retain best hits per profile as queries.
2. Align query sequences to the reference alignment using `hmmer` (hmmalign, default — realigns both ref and query against the profile), `clustalo`, or `mafft --keeplength`.
3. If MAFFT was used, split the combined alignment into query + reference FASTA with EPA-NG's split utility.
4. Run `EPA-NG` to compute placements of queries on `refphylogeny` under the specified evolutionary `model`, producing a `*.jplace` file.
5. Run `gappa examine graft` to graft queries onto the reference tree as a full Newick phylogeny.
6. Run `gappa examine heattree` to render placement density as coloured branches (SVG/PDF/Nexus).
7. If a reference `taxonomy` TSV is provided, run `gappa examine assign` to assign taxonomy strings to each query placement.
8. Aggregate logs and HMMER ranks via MultiQC.

## Key parameters
- `--phyloplace_input` CSV: `sample,queryseqfile,refseqfile,refphylogeny,model` — one row per independent placement job. Use this for direct placement.
- `--phylosearch_input` CSV + `--search_fasta`: `target,hmm,refseqfile,refphylogeny,model,taxonomy` — enables search-then-place; rows with empty ref columns act as decoy/search-only profiles.
- `--queryseqfile`, `--refseqfile`, `--refphylogeny`, `--model`: single-placement CLI equivalents (all four required if not using a samplesheet).
- `--model`: EPA-NG evolutionary model string, e.g. `LG`, `LG+F`, `LG+F+R6`, `GTR+G`. Must match how the reference tree was inferred.
- `--alignmethod`: one of `hmmer` (default), `clustalo`, `mafft`. If `--hmmfile` is supplied, `hmmer` is forced and the reference sequences must be *unaligned*.
- `--hmmfile`: optional pre-built HMM profile used to align both reference and query sequences.
- `--taxonomy`: TSV mapping reference sequence IDs to semicolon-delimited taxonomy strings; enables `gappa examine assign`.
- `--id`: analysis label used in output filenames (default `placement`).

## Test data
The bundled `test` profile places 3 query protein sequences (`PF14720_3_sequences.faa`) onto a small reference built from the PF14720 Pfam seed alignment (`PF14720_seed.alnfaa`) and its FastTree LG+CAT tree (`PF14720_seed.ft.LGCAT.newick`), using `model=LG` and a small Gappa example taxonomy TSV. The `test_full` profile scales this up with `queries.faa` against `reference.alnfaa` / `reference.newick` under `LG+F`. Expected outputs include an `epang/*.epa_result.jplace.gz` placement file, per-sample HMMER alignments under `hmmer/`, a grafted Newick tree and heattree renderings under `gappa/`, and — when `--taxonomy` is given — `gappa/*.taxonomy.*` classification tables, all summarised in a MultiQC report.

## Reference workflow
nf-core/phyloplace v2.0.0 — https://github.com/nf-core/phyloplace (DOI: 10.5281/zenodo.7643941). Core tools: EPA-NG (Barbera et al. 2019), Gappa (Czech et al. 2020), HMMER 3, Clustal Omega, MAFFT.
