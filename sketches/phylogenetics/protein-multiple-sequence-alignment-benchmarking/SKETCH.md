---
name: protein-multiple-sequence-alignment-benchmarking
description: Use when you need to compute and/or benchmark multiple sequence alignments
  (MSAs) of protein families from FASTA sequences and/or protein structures (PDB),
  optionally comparing several aligners and guide trees side-by-side with SP/TC/iRMSD/TCS
  metrics.
domain: phylogenetics
organism_class:
- eukaryote
- bacterial
- viral
input_data:
- protein-fasta
- protein-structures-pdb
source:
  ecosystem: nf-core
  workflow: nf-core/multiplesequencealign
  url: https://github.com/nf-core/multiplesequencealign
  version: 1.1.1
  license: MIT
tools:
- famsa
- clustalo
- mafft
- tcoffee
- muscle5
- kalign
- magus
- learnmsa
- upp
- regressive
- 3dcoffee
- foldmason
- mtm-align
- multiqc
tags:
- msa
- protein
- alignment
- benchmark
- guide-tree
- structure
- foldmason
- tcoffee
- famsa
test_data: []
expected_output: []
---

# Protein multiple sequence alignment and benchmarking

## When to use this sketch
- User has a set of homologous protein sequences (a protein family) in FASTA and wants a multiple sequence alignment.
- User has predicted or experimental protein structures (PDB files, e.g. AlphaFold2 outputs) and wants a structure-aware MSA via 3DCoffee, mTM-align, or FoldMason.
- User wants to benchmark several aligners and/or guide trees on the same dataset and compare quality metrics (Sum-of-Pairs, Total Column, iRMSD, TCS, gap counts).
- User wants an interactive report (MultiQC + Shiny + optional FoldMason HTML visualization) summarizing alignment quality and resource usage across tool combinations.
- User has reference alignments and wants reference-based scoring of candidate MSAs.

## Do not use when
- You need nucleotide MSAs for phylogeny of DNA/RNA loci — this pipeline is protein-focused.
- You need whole-genome alignment or synteny analysis.
- You want to build a phylogenetic tree from the alignment (this produces guide trees only, not species/gene trees for downstream inference).
- You only need a single quick alignment with no benchmarking — running one aligner standalone (e.g. MAFFT directly) may be simpler, though this pipeline supports a single-tool `easy_deploy` mode.
- Your inputs are raw sequencing reads — assemble/translate them first.

## Analysis outline
1. Validate and preprocess inputs (FASTA and/or PDB directory, optional reference MSAs and 3DCoffee templates).
2. Optional input stats: sequence length summaries, pairwise similarity (TCOFFEE), pLDDT extraction from AF2 structures.
3. Optional guide-tree construction with FAMSA, CLUSTALO, or MAFFT (each supporting alternative linkage/heuristic args).
4. Run one or many aligners per sample: sequence-based (FAMSA, CLUSTALO, MAFFT, KALIGN, MUSCLE5, TCOFFEE, REGRESSIVE, MAGUS, UPP, LEARNMSA), sequence+structure (3DCOFFEE), or pure structure (MTMALIGN, FOLDMASON).
5. Optional M-COFFEE consensus MSA across aligners (`--build_consensus`).
6. Evaluate MSAs: gaps, reference-based SP/TC via TCOFFEE, structure-based iRMSD, TCS consistency.
7. Aggregate into `complete_summary_eval.csv` and `complete_summary_stats_with_trace.csv`; render MultiQC report, Shiny app, and per-alignment FoldMason HTML visualization when structures are available.

## Key parameters
- `--input` samplesheet CSV (`id,fasta,reference,optional_data,template`) — one row per protein family; `fasta` or `optional_data` required.
- `--tools` toolsheet CSV (`tree,args_tree,aligner,args_aligner`) — one row per tree/aligner combination to benchmark; only `aligner` is mandatory.
- Single-tool shortcut: `--seqs <fasta>` or `--pdbs_dir <dir>` with `--aligner {FAMSA|CLUSTALO|MAFFT|KALIGN|MUSCLE5|TCOFFEE|REGRESSIVE|MAGUS|UPP|LEARNMSA|3DCOFFEE|MTMALIGN|FOLDMASON}` and optional `--tree`, `--args_tree`, `--args_aligner`.
- `--templates_suffix` (default `.pdb`) — file extension for structures in `optional_data`.
- `--use_gpu` — strongly recommended when using LEARNMSA.
- Stats toggles: `--calc_sim`, `--calc_seq_stats` (default on), `--extract_plddt`.
- Eval toggles: `--calc_sp` (default on), `--calc_tc` (default on), `--calc_gaps` (default on), `--calc_irmsd`, `--calc_tcs`.
- Reporting: `--build_consensus` for M-COFFEE, `--skip_multiqc`, `--skip_shiny`, `--skip_visualisation`.
- Profiles: always pair a container profile (`docker`, `singularity`, `conda`) with `test_tiny`, `test`, or `easy_deploy` as appropriate.

## Test data
The pipeline's `test` profile consumes `samplesheet_test_af2.csv` and `toolsheet_full.csv` from the nf-core/test-datasets `multiplesequencealign` branch. Inputs are small protein families (e.g. seatoxin, toxin) with FASTA sequences, reference alignments, and AlphaFold2-predicted PDB structures; the toolsheet exercises multiple tree/aligner combinations including FAMSA, TCOFFEE, REGRESSIVE, 3DCOFFEE, and FOLDMASON. Expected outputs include per-sample alignments under `alignments/{id}/`, optional guide trees under `trees/{id}/`, `evaluation/complete_summary_eval.csv` with SP/TC/iRMSD/TCS/gap scores, `stats/complete_summary_stats.csv`, a MultiQC HTML report, a Shiny app bundle, and FoldMason HTML visualizations for structure-aware alignments. A lighter `test_tiny` profile requires no user inputs and performs an end-to-end smoke test.

## Reference workflow
nf-core/multiplesequencealign v1.1.1 (https://github.com/nf-core/multiplesequencealign), MIT licensed, DOI 10.5281/zenodo.13889386. See `docs/usage.md` for the full tool and parameter matrix.
