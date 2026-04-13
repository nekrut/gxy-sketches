---
name: sars-cov-2-consensus-from-variation
description: Use when you need to build masked viral consensus FASTA sequences for
  SARS-CoV-2 (or similar segmented/single-chromosome RNA viruses) from already-called
  per-sample VCFs plus their alignment BAMs, applying allele-frequency thresholds
  for consensus vs ambiguous variants and hard-masking low-coverage regions with Ns.
domain: variant-calling
organism_class:
- viral
- haploid
input_data:
- vcf-collection
- bam-collection
- reference-fasta
source:
  ecosystem: iwc
  workflow: 'COVID-19: consensus construction'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/sars-cov-2-variant-calling/sars-cov-2-consensus-from-variation
  version: 0.4.3
  license: MIT
tools:
- bcftools
- bedtools
- snpsift
- compose_text_param
- column_maker
tags:
- sars-cov-2
- covid-19
- consensus
- viral
- masking
- allele-frequency
- iwc
- galaxy
test_data:
- role: reference_genome
  url: https://zenodo.org/record/4555735/files/NC_045512.2_reference.fasta?download=1
  sha1: db3759c2e1d9ce8827ba4aa1749e759313591240
expected_output: []
---

# SARS-CoV-2 consensus sequence construction from variant calls

## When to use this sketch
- You already have per-sample VCFs (with `DP` and `DP4` INFO fields) from an upstream SARS-CoV-2 variant-calling workflow (e.g. lofreq or medaka) and the corresponding aligned-read BAMs.
- You need per-sample masked consensus FASTAs plus a single multisample FASTA for downstream lineage assignment (Pangolin, Nextclade) or phylogenetics.
- You want transparent, tunable allele-frequency gating: consensus variants above a high-AF threshold, ambiguous sites between two AF thresholds masked with N, and low-coverage regions masked with N unless they are consensus variant sites.
- Works for ARTIC tiled-amplicon or WGS data as long as the BAMs are the fully processed alignments used for calling (for ARTIC, BAMs must NOT have been run through `ivar removereads`).

## Do not use when
- You still need to call variants from raw reads — run one of the sibling `sars-cov-2-variant-calling-*` workflows (Illumina ARTIC, Illumina WGS, ONT ARTIC) first to produce the VCF + BAM inputs.
- You are calling diploid/polyploid variants or non-viral organisms — use a diploid variant-calling sketch instead.
- You want de novo assembly of the viral genome rather than reference-guided consensus — use a viral assembly sketch.
- You want lineage assignment itself — feed the output of this sketch into Pangolin/Nextclade.

## Analysis outline
1. Split each input VCF into two subsets with `SnpSift Filter`: consensus variants (FILTER=PASS and `(DP4[2]+DP4[3])/DP >= consensus_af`) and filter-failed/ambiguous variants (AF between `non_consensus_af` and `consensus_af`). AF is recomputed from DP4/DP to avoid lofreq's biased AF reporting.
2. Compute per-base genome coverage from the aligned BAMs with `bedtools genomecoveragebed -bg` (with `zero_regions=true`).
3. Identify low-coverage regions by filtering the bedgraph for `c4 < depth_threshold`.
4. Convert consensus-variant and filter-failed variant tables (via `SnpSift Extract Fields` + `Compute`) into BED intervals of variant sites.
5. Concatenate low-coverage regions with filter-failed variant sites, then `Merge` overlapping intervals to produce candidate masking regions.
6. `Subtract` consensus variant sites from those masking regions so that consensus variants are never masked even if they sit in a low-coverage window.
7. Convert the resulting BED to 1-based intervals for bcftools and run `bcftools consensus` with `--mask` and the reference FASTA, applying only the consensus VCF.
8. `Collapse Collection` of per-sample consensus FASTAs into a single multisample FASTA.

## Key parameters
- `min-AF for consensus variant` (consensus_af_threshold): default `0.75`. Variants with recomputed `(DP4[2]+DP4[3])/DP` strictly greater than this, and FILTER=PASS (or missing), become consensus calls.
- `min-AF for failed variants` (non_consensus_af_threshold): default `0.25`. Variants with AF in `(non_consensus_af, consensus_af]` cause their sites to be N-masked.
- `Depth-threshold for masking` (depth_threshold): default `5`. Sites with coverage below this are N-masked unless they are consensus variant sites.
- `bcftools consensus`: run with `--mask <1-based BED>`, `rename=true`, no IUPAC codes — hard Ns only.
- `bedtools genomecoveragebed`: `-bg`, `zero_regions=true`, `split=true` to correctly report uncovered regions.

## Test data
The workflow's bundled test profile supplies the NC_045512.2 SARS-CoV-2 reference FASTA (from Zenodo record 4555735), a one-sample BAM collection (`SRR11578257` aligned reads) for coverage calculation, and a matching one-sample VCF collection of snpEff-annotated variant calls. Running with defaults (consensus_af=0.75, non_consensus_af=0.25, depth_threshold=5) is expected to yield a multisample consensus FASTA (`multisample_consensus_fasta`) byte-identical to `test-data/masked_consensus.fa`, with N-masking of low-coverage and ambiguous positions and reference-to-ALT substitutions at consensus variant sites.

## Reference workflow
Galaxy IWC `sars-cov-2-variant-calling/sars-cov-2-consensus-from-variation`, release 0.4.3 (MIT). Author: Wolfgang Maier. Part of the covid19.galaxyproject.org variant-calling suite; pair with the upstream `sars-cov-2-variant-calling-*` sibling workflows to go from raw reads to consensus sequences.
