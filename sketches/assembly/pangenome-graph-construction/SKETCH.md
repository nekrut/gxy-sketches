---
name: pangenome-graph-construction
description: Use when you need to build a pangenome variation graph from a collection
  of related whole-genome sequences (haplotypes, assemblies, or long contigs) to capture
  large-scale variation, produce a locally directed-acyclic graph, visualize it in
  1D/2D, and deconstruct variants (SNPs/indels/SVs) against one or more reference
  paths. Assumes input sequences are reasonably homologous (same species or closely
  related) and named per PanSN-spec.
domain: assembly
organism_class:
- eukaryote
- bacterial
- viral
- plant
- vertebrate
input_data:
- multi-sample-fasta-bgzipped
source:
  ecosystem: nf-core
  workflow: nf-core/pangenome
  url: https://github.com/nf-core/pangenome
  version: 1.1.3
  license: MIT
  slug: pangenome
tools:
- name: wfmash
  version: 0.10.4
- name: seqwish
- name: smoothxg
  version: 0.8.0
- name: gfaffix
  version: 0.1.5b
- name: odgi
- name: vg
- name: multiqc
  version: '1.27'
tags:
- pangenome
- variation-graph
- pggb
- gfa
- graph-genome
- structural-variation
- all-vs-all-alignment
test_data: []
expected_output: []
---

# Pangenome graph construction (PGGB-style)

## When to use this sketch
- You have a multi-FASTA containing N assembled haplotypes/genomes of the same (or very closely related) species and want a pangenome variation graph rather than a linear reference plus VCF.
- You want to capture large structural variation, inversions, and complex loci (e.g. MHC, acrocentrics, plant centromeres) in a single graph structure.
- You need GFA output plus 1D/2D visualizations (`odgi viz`, `odgi draw`) and a VCF deconstructed against one or more reference paths (`vg deconstruct`).
- You want to scale the compute-heavy all-vs-all alignment over an HPC cluster via chunking.
- You can (and must) rename sequences to PanSN-spec (`sample#hap#contig`).

## Do not use when
- You are calling small variants from short reads against a single linear reference — use a read-based variant-calling sketch instead.
- You only have raw sequencing reads and no assemblies — assemble first (e.g. with a long-read assembly sketch) before feeding contigs here.
- Your sequences are highly divergent / unrelated (cross-species survey) — a pangenome graph will be dominated by a giant tangled component; use a whole-genome alignment / synteny tool instead.
- You want per-sample structural variant calls from long reads against a reference — use a structural-variants sketch.
- Your goal is metagenomic assembly or strain deconvolution from reads — use a metagenomics sketch.

## Analysis outline
1. Prepare input: rename sequences to PanSN-spec (`sample#hap#contig`), `bgzip` and `samtools faidx` the combined FASTA.
2. (Optional) Community detection: `wfmash` approximate map → `paf2net` → `net2communities` (Leiden) → split FASTA into per-community subsets to avoid one giant connected component.
3. All-vs-all alignment with `wfmash` in mashmap approximate + base-level WFA mode, optionally splitting base-level alignment into N chunks (`--wfmash_chunks`) distributed across the cluster.
4. Graph induction from alignments with `seqwish` (lossless PAF → GFA).
5. Graph normalization/smoothing with `smoothxg` (block-wise POA passes at successive target lengths).
6. Redundancy collapse of shared affixes with `gfaffix`.
7. Graph processing with `odgi`: `build` → `unchop` → `sort` (PG-SGD `Y`, groom `g`, topological `s`) → `stats`, `viz` (1D), `layout`+`draw` (2D), optional `squeeze` to merge per-community graphs.
8. Variant deconstruction vs chosen reference path(s) with `vg deconstruct` (`--vcf_spec`), producing raw and decomposed VCFs with stats.
9. Aggregate QC and visualizations into a `MultiQC` report.

## Key parameters
- `--input`: path to the **bgzipped** combined FASTA (`.fa.gz`), PanSN-named.
- `--n_haplotypes`: total number of haplotypes in the input; drives `wfmash_n_mappings = n_haplotypes - 1`. Required.
- `--wfmash_map_pct_id` (default `90`): expected pairwise %identity; estimate with `mash triangle` and tune to your divergence.
- `--wfmash_segment_length` (default `5000`): minimum collinear segment; raise to ~`50000` for human-scale genomes with long repeats, lower (e.g. `500`) for short loci like MHC/DRB1.
- `--wfmash_block_length`: block-length filter (default ≈ 5× segment length).
- `--wfmash_chunks` (default `1`): number of base-level alignment shards — set to your available cluster nodes for scale-out.
- `--wfmash_exclude_delim` (e.g. `#`): skip self-mappings between contigs from the same sample when names follow PanSN.
- `--seqwish_min_match_length` (default `23`): filter short noisy matches; ~`47` around 5% divergence, up to `~311` for human haplotypes.
- `--seqwish_transclose_batch` (default `10000000`): lower if seqwish OOMs.
- `--smoothxg_poa_length` (default `700,900,1100`): comma-separated POA target lengths; one smoothxg pass per value. Raise for low-diversity / long-repeat pangenomes (watch RAM).
- `--smoothxg_poa_params` (default `1,19,39,3,81,1` = `asm5`): POA scoring, also accepts `asm10`/`asm15`/`asm20` presets matching expected divergence.
- `--skip_smoothxg`: skip the smoothing stage entirely.
- `--communities`: enable Leiden community detection and per-community graph builds; recommended when inputs span multiple chromosomes or you expect a giant component.
- `--vcf_spec`: e.g. `"chm13,grch38:50000"` — which path(s) to use as VCF reference(s) and optional max allele length for decomposition.
- `--wfmash_only`: stop after the wfmash alignment stage (useful on clusters before a downstream local run).

## Test data
The `test` profile runs on the `DRB1-3123.fa.gz` MHC-class-II locus from the nf-core test-datasets repo, containing 12 haplotypes (`n_haplotypes = 12`); it exercises the full default wfmash → seqwish → smoothxg → gfaffix → odgi → vg deconstruct → MultiQC path on a single small region in under an hour with 4 CPUs / 15 GB RAM. The `test_full` profile uses the 8-haplotype `scerevisiae8.fasta.gz` *S. cerevisiae* pangenome with `communities = true`, exercising Leiden community detection and per-community graph construction. Expected outputs include the final sorted ODGI graph (`*.Ygs.og`), the final GFAv1, `odgi stats` YAML, 1D `odgi viz` and 2D `odgi draw` PNGs, a deconstructed VCF plus stats from `vg deconstruct`, and a consolidated `multiqc_report.html`.

## Reference workflow
nf-core/pangenome v1.1.3 (https://github.com/nf-core/pangenome), a Nextflow port of PGGB (Garrison et al., bioRxiv 2023.04.05.535718; Heumos et al., Bioinformatics 2024, doi:10.1093/bioinformatics/btae609).
