---
name: average-bigwig-replicates-epigenomics
description: Use when you have multiple normalized BigWig coverage tracks from replicate
  samples (ATAC-seq, ChIP-seq, CUT&RUN, RNA-seq) and need to collapse them into a
  single per-condition mean-signal BigWig. Requires replicate identifiers formatted
  as `sample_name_replicateID` so the workflow can group by sample prefix before averaging.
domain: epigenomics
organism_class:
- eukaryote
input_data:
- bigwig-collection
source:
  ecosystem: iwc
  workflow: BigWig Replicates Averaging Workflow
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/epigenetics/average-bigwig-between-replicates
  version: '0.2'
  license: MIT
  slug: epigenetics--average-bigwig-between-replicates
tools:
- name: deeptools-bigwigAverage
  version: 3.5.4+galaxy0
- name: galaxy-apply-rules
tags:
- bigwig
- coverage
- replicates
- atac-seq
- chip-seq
- cut-and-run
- rna-seq
- deeptools
- averaging
test_data:
- role: bigwig_to_average__atac_hh19_pt_rep1
  url: https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSM6152756&format=file&file=GSM6152756%5FATAC%5FHH19%5FPT%5Frep1%2Ebigwig
  sha1: 85e05349f1d3353cf5c56221c2d8d90ced1ca6b3
  filetype: bigwig
- role: bigwig_to_average__atac_hh19_pt_rep2
  url: https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSM6152757&format=file&file=GSM6152757%5FATAC%5FHH19%5FPT%5Frep2%2Ebigwig
  sha1: d709cb76a683fcd2f98cd467535cdbeff82cb851
  filetype: bigwig
- role: bigwig_to_average__atac_hh35_ds_rep1
  url: https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSM6152758&format=file&file=GSM6152758%5FATAC%5FHH35%5FDS%5Frep1%2Ebigwig
  sha1: 86ac9190cc7971cec4f63509cf3b2b7fc2f56157
  filetype: bigwig
- role: bigwig_to_average__atac_hh35_ds_rep2
  url: https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSM6152759&format=file&file=GSM6152759%5FATAC%5FHH35%5FDS%5Frep2%2Ebigwig
  sha1: fa3a2c20757ab94d0c9618d2186a108329e206cf
  filetype: bigwig
expected_output:
- role: average_bigwigs
  description: Content assertions for `average_bigwigs`.
  assertions:
  - 'ATAC_HH19_PT: has_size: {''value'': 140203524, ''delta'': 10000000}'
  - 'ATAC_HH35_DS: has_size: {''value'': 124599299, ''delta'': 10000000}'
---

# Average BigWig Across Replicates

## When to use this sketch
- You already have per-replicate normalized BigWig coverage tracks and want one consolidated BigWig per sample/condition.
- Your replicate files are named with a common sample prefix plus a replicate suffix after the last underscore (e.g. `ATAC_HH19_PT_rep1`, `ATAC_HH19_PT_rep2`).
- Applies to any coverage-track modality: ATAC-seq, ChIP-seq, CUT&RUN, CUT&Tag, or stranded/unstranded RNA-seq BigWigs.
- You want a lightweight downstream aggregation step that feeds genome browser tracks, heatmaps, or metaprofiles.

## Do not use when
- You still have raw reads or BAMs — run the upstream ATAC/ChIP/RNA-seq alignment + normalization workflow first to produce BigWigs.
- You need peak calling, differential binding, or statistical replicate comparison — use MACS2/DiffBind/csaw-style sketches instead.
- Your replicate identifiers are not of the form `sample_name_replicateID`; the Apply Rules step relies on splitting on the last underscore and will mis-group files.
- You want a weighted or median combination across replicates — `bigwigAverage` computes an unweighted mean only (with optional per-file scale factors).

## Analysis outline
1. Collect normalized per-replicate BigWigs into a single Galaxy list collection, using element identifiers of the form `<sample>_<replicateID>`.
2. Apply Rules (Galaxy `__APPLY_RULES__`) to restructure the flat list into a nested `list:list` collection by regex-splitting each identifier on the final underscore into `<sample>` and `<replicateID>`.
3. Run deepTools `bigwigAverage` on each inner replicate list to compute the mean signal per genomic bin, emitting one averaged BigWig per sample.
4. Publish the `average_bigwigs` output collection for downstream visualization (IGV, pyGenomeTracks, deepTools `plotHeatmap`/`computeMatrix`).

## Key parameters
- `bin_size` (required input): resolution of the averaged signal. Use `5` bp for RNA-seq coverage; use `50` bp for ATAC-seq / ChIP-seq / CUT&RUN / CUT&Tag.
- `bigwigAverage` advanced options: `scaleFactors=1` (no extra scaling — inputs are assumed already normalized), `skipNAs=false`, `outFileFormat=bigwig`, optional `blackListFileName` for excluding problematic regions.
- Apply Rules regex: `^(.*)_([^_]*)$` — splits each element identifier into sample prefix (group 1) and replicate ID (group 2); the prefix becomes the inner-list name used for the output BigWig.
- Tool version pinned: `deeptools_bigwig_average` `3.5.4+galaxy0` (workflow release 0.2).

## Test data
The test profile provides a single Galaxy list collection of four public ATAC-seq BigWigs downloaded from GEO (GSM6152756–GSM6152759): two replicates for condition `ATAC_HH19_PT` and two replicates for `ATAC_HH35_DS`, with `bin_size=50`. Running the workflow should yield an `average_bigwigs` list collection containing exactly two elements, `ATAC_HH19_PT` and `ATAC_HH35_DS`, each a BigWig whose file size is within 10 MB of the reference sizes (~140.2 MB and ~124.6 MB respectively). No golden file comparison is performed — only size assertions via `has_size`.

## Reference workflow
Galaxy IWC — `workflows/epigenetics/average-bigwig-between-replicates` (`BigWig Replicates Averaging Workflow`, release 0.2, MIT, by Lucille Delisle). Source: https://github.com/galaxyproject/iwc/tree/main/workflows/epigenetics/average-bigwig-between-replicates
