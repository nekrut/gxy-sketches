---
name: rna-velocity-velocyto-10x
description: Use when you need to quantify spliced and unspliced transcript counts
  from 10X Genomics single-cell RNA-seq BAM files (from CellRanger or STARsolo) to
  enable downstream RNA velocity / trajectory analysis in scVelo. Requires a pre-filtered
  cell barcode list and a GTF annotation.
domain: single-cell
organism_class:
- eukaryote
input_data:
- 10x-bam-with-cb-ub
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
- scrna-seq
- rna-velocity
- 10x
- velocyto
- spliced-unspliced
- loom
- scvelo
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

# RNA velocity quantification with Velocyto on 10X data

## When to use this sketch
- You already have 10X Genomics scRNA-seq BAM files produced by CellRanger or STARsolo that carry the `CB` (corrected cell barcode) and `UB` (corrected UMI) tags.
- You have an independently derived list of filtered/called cell barcodes (e.g. from STARsolo's filtered output or DropletUtils emptyDrops) and want to restrict quantification to real cells.
- The downstream goal is RNA velocity / trajectory inference in scVelo or velocyto.R, which requires a `.loom` file with separate `spliced`, `unspliced`, and `ambiguous` count layers.
- You have a matching GTF annotation so introns vs exons can be disambiguated.
- Inputs arrive as uploaded BAMs and a separate barcode TSV (not as a bundled CellRanger `filtered_feature_bc_matrix` directory).

## Do not use when
- You are starting from a bundled CellRanger/STARsolo `filtered_feature_bc_matrix` (barcodes.tsv + features.tsv + matrix.mtx). Use the sibling `rna-velocity-velocyto-10x-bundled` sketch, which extracts barcodes from the bundle first.
- You only have FASTQ files — run a 10X alignment workflow (CellRanger, STARsolo, or `scrnaseq-10x-starsolo`) first to produce a CB/UB-tagged BAM.
- Your data is SMART-seq2, Drop-seq, or any non-10X chemistry — `velocyto run10x` is not appropriate; use `velocyto run-smartseq2` or `velocyto run` variants instead.
- You want a full expression matrix only (no spliced/unspliced split) — a standard STARsolo/CellRanger count run is simpler.
- Your filtered barcode list is the raw ~3M-barcode whitelist rather than a called-cells list; Velocyto will exhaust memory.

## Analysis outline
1. Stage one BAM per sample (with `CB` and `UB` tags) as a collection, a matching filtered-barcodes TSV per sample as a parallel collection, and a single GTF annotation.
2. Run `velocyto CLI` in `run10x` mode, wiring BAM → `main|BAM`, barcodes → `main|barcodes`, GTF → `main|gtffile`, using per-sample identifiers to name outputs.
3. Collect the resulting per-sample `.loom` files containing `spliced`, `unspliced`, and `ambiguous` layers, ready for loading in scVelo/anndata for velocity estimation.

## Key parameters
- `main.do`: `run10x` (10X Genomics mode; assumes CB/UB tags and 10X directory conventions).
- `main.sample_definition.sample_definition_select`: `identifier` — name each loom after the dataset identifier in the collection so multi-sample runs stay disambiguated.
- `main.BAM`: per-sample BAM with `CB` (corrected cell barcode) and `UB` (corrected UMI) tags. Non-tagged BAMs will fail.
- `main.barcodes`: TSV of filtered/called cell barcodes only — never the full 10X whitelist (memory blow-up).
- `main.gtffile`: gene annotation GTF matching the reference the BAM was aligned to; required for intron/exon classification.
- `main.M`: mask GTF for repeat regions — left unset (false) by default; supply only if masking repetitive loci.
- `main.t`: counts dtype, `uint16` (default here; sufficient unless you expect >65k counts per gene per cell).
- `main.s` / `main.m`: runtime-provided optional sample metadata and mask; usually left empty.
- `verbosity`: `-vv` for full logging during debugging.

## Test data
A single-sample smoke test built from *Drosophila melanogaster* data: one BAM (`subsample.bam`) carrying 10X `CB`/`UB` tags and a matching filtered barcode list (`barcodes.tsv`), both from Zenodo record 10572348, plus the Ensembl BDGP6.32.109 GTF (UCSC-style chromosome names, gz-compressed on Zenodo record 6457007 and decompressed at load time). Running the workflow should emit a `velocyto loom` collection with one element named `subsample`; the test asserts the loom file is roughly 4.64 MB (4639326 bytes ± 400000), which is a structural sanity check that the spliced/unspliced/ambiguous layers were populated rather than an empty shell.

## Reference workflow
Galaxy IWC `workflows/scRNAseq/velocyto/Velocyto-on10X-filtered-barcodes.ga`, release 0.3 (2025-10-08), using `velocyto_cli` tool version `0.17.17+galaxy3`. Author: Lucille Delisle. License: MIT.
