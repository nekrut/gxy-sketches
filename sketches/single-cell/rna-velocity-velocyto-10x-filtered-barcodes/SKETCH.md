---
name: rna-velocity-velocyto-10x-filtered-barcodes
description: Use when you need to quantify spliced and unspliced transcript counts
  from 10X Genomics single-cell RNA-seq BAM files (from CellRanger or STARsolo) to
  enable RNA velocity analysis, and you already have a curated list of filtered cell
  barcodes. Produces a per-sample loom file consumable by scVelo for trajectory and
  cellular dynamics inference.
domain: single-cell
organism_class:
- eukaryote
input_data:
- 10x-scrna-bam
- filtered-barcodes-tsv
- gtf-annotation
source:
  ecosystem: iwc
  workflow: 'RNA Velocity Analysis: Velocyto for 10X Data with Filtered Barcodes'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/scRNAseq/velocyto
  version: '0.3'
  license: MIT
tools:
- velocyto
tags:
- single-cell
- rna-velocity
- 10x-genomics
- spliced-unspliced
- loom
- scvelo
- trajectory
test_data:
- role: gtf_file
  url: https://zenodo.org/record/6457007/files/Drosophila_melanogaster.BDGP6.32.109_UCSC.gtf.gz
  sha1: 3cbdd2f0eed28bd10af66cb83aa3f6d688779d51
  filetype: gtf
- role: bam_files_with_cb_and_ub__subsample
  url: https://zenodo.org/records/10572348/files/subsample.bam
  sha1: 0084c8b35be58ac58079ce79d7b57172602623a5
  filetype: bam
- role: filtered_barcodes__subsample
  url: https://zenodo.org/records/10572348/files/barcodes.tsv
  sha1: 332a0a5ac99b06315b2c946faa333c4684423b0b
  filetype: tsv
expected_output:
- role: velocyto_loom
  description: Content assertions for `velocyto loom`.
  assertions:
  - 'subsample: has_size: {''value'': 4639326, ''delta'': 400000}'
---

# RNA velocity quantification with Velocyto (10X, filtered barcodes)

## When to use this sketch
- You have 10X Genomics scRNA-seq BAM files carrying `CB` (cell barcode) and `UB` (UMI) tags, produced by CellRanger or STARsolo.
- You already have a curated `barcodes.tsv` of *filtered* (real cell) barcodes per sample — e.g. from STARsolo's filtered output or DropletUtils `emptyDrops`.
- You need a per-sample `.loom` file with separate spliced / unspliced / ambiguous count matrices as the upstream input for RNA velocity in scVelo (or velocyto.R).
- You want a lightweight Galaxy workflow that wraps `velocyto run10x` without rerunning alignment or cell calling.

## Do not use when
- Your starting point is raw FASTQ — run a 10X preprocessing workflow first (e.g. STARsolo / CellRanger-compatible pipeline) to generate a BAM with `CB`/`UB` tags and a filtered barcode list.
- You have the full bundled 10X filtered matrix output (barcodes + genes + matrix triplet) rather than a standalone `barcodes.tsv` — use the sibling sketch for Velocyto on 10X from bundled output instead.
- You are passing the unfiltered ~3 million-barcode whitelist — Velocyto will blow memory; restrict to called cells first.
- You need non-10X chemistries (Smart-seq2, plate-based) — use `velocyto run-smartseq2` or a different pipeline.
- You want the downstream velocity estimation / embedding itself — that is a scVelo step performed after this workflow.

## Analysis outline
1. Ingest a collection of per-sample BAM files (with `CB`/`UB` tags) and a matching collection of filtered `barcodes.tsv` files.
2. Ingest a gene annotation GTF matching the genome the BAMs were aligned to.
3. Run `velocyto CLI` in `run10x` mode, one invocation per sample, passing the BAM, filtered barcodes, and GTF; counts are typed as `uint16` with verbose logging.
4. Emit one `.loom` file per sample (layers: spliced, unspliced, ambiguous) as the workflow output `velocyto loom`, ready for scVelo.

## Key parameters
- `main.do`: `run10x` — 10X Genomics mode; assumes `CB`/`UB` BAM tags.
- `main.sample_definition.sample_definition_select`: `identifier` — derives sample name from the collection element identifier.
- `main.BAM`: per-sample BAM collection (must contain `CB` and `UB` tags).
- `main.barcodes`: per-sample filtered barcodes TSV (one per BAM; must be filtered, not the full whitelist).
- `main.gtffile`: gene annotation GTF matching the alignment reference.
- `main.M` (mask multi-mapping): `false` — no repeat/expressed-region mask supplied.
- `main.t` (count dtype): `uint16` — sufficient for typical per-cell per-gene counts and memory-friendly.
- `main.s` (repeat mask GTF) and `main.m` (metadata): left as runtime values (optional).
- `verbosity`: `-vv` — verbose logging for debugging memory / tag issues.
- Tool version pinned: `velocyto_cli 0.17.17+galaxy3`.

## Test data
The test profile uses a *Drosophila melanogaster* annotation (`Drosophila_melanogaster.BDGP6.32.109_UCSC.gtf.gz` from Zenodo 6457007, auto-decompressed) together with a single downsampled 10X BAM (`subsample.bam`) and its matching filtered `barcodes.tsv` (both from Zenodo 10572348), each wrapped as a one-element collection keyed by identifier `subsample`. Running the workflow is expected to produce a `velocyto loom` output collection containing one element `subsample` — a `.loom` file of approximately 4,639,326 bytes (±400,000), asserted by size only. No content-level golden file is compared; the check confirms Velocyto produced a plausibly sized loom for the sample.

## Reference workflow
Galaxy IWC — `workflows/scRNAseq/velocyto/Velocyto-on10X-filtered-barcodes.ga`, release 0.3 (2025-10-08), MIT-licensed, author Lucille Delisle. Wraps `toolshed.g2.bx.psu.edu/repos/iuc/velocyto_cli/velocyto_cli/0.17.17+galaxy3`.
