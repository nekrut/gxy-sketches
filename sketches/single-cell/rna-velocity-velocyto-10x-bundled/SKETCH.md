---
name: rna-velocity-velocyto-10x-bundled
description: Use when you need to quantify spliced and unspliced transcript counts
  for RNA velocity analysis from 10X Genomics single-cell RNA-seq data, starting from
  CellRanger/STARsolo BAM files plus a bundled filtered matrix directory (barcodes/genes/matrix).
  Produces a per-sample loom file for downstream velocity/trajectory inference.
domain: single-cell
organism_class:
- eukaryote
input_data:
- 10x-scrna-bam
- 10x-bundled-matrix
- gtf-annotation
source:
  ecosystem: iwc
  workflow: 'RNA Velocity Analysis: Velocyto for 10X Data from Bundled Output'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/scRNAseq/velocyto
  version: '0.3'
  license: MIT
  slug: scRNAseq--velocyto--Velocyto-on10X-from-bundled
tools:
- name: velocyto
- name: galaxy-apply-rules
tags:
- scrna-seq
- rna-velocity
- 10x-genomics
- velocyto
- spliced-unspliced
- loom
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
- role: filtered_matrices_in_bundle__subsample__barcodes
  url: https://zenodo.org/records/10572348/files/barcodes.tsv
  sha1: 332a0a5ac99b06315b2c946faa333c4684423b0b
  filetype: tsv
- role: filtered_matrices_in_bundle__subsample__genes
  url: https://zenodo.org/records/10572348/files/genes.tsv
  sha1: 0050f249ab6c35024b9c5ada8f86381ec2a16646
  filetype: tsv
- role: filtered_matrices_in_bundle__subsample__matrix
  url: https://zenodo.org/records/10572348/files/matrix.mtx
  sha1: c84cc0a02031b55acbbb944a0f865af39aa3448d
  filetype: mtx
expected_output:
- role: velocyto_loom
  description: Content assertions for `velocyto loom`.
  assertions:
  - 'subsample: has_size: {''value'': 4639326, ''delta'': 400000}'
---

# RNA Velocity (Velocyto) from 10X bundled output

## When to use this sketch
- You have 10X Genomics single-cell RNA-seq data already processed through CellRanger or STARsolo and want to run RNA velocity analysis.
- You have per-sample BAM files that carry the `CB` (corrected cell barcode) and `UB` (corrected UMI) tags.
- You also have the standard 10X bundled filtered matrix output per sample: a directory/collection containing `barcodes.tsv`, `genes.tsv`, and `matrix.mtx` (for example, the output of a fastq-to-matrix-10x or STARsolo/DropletUtils workflow).
- You need a per-sample `.loom` file containing spliced, unspliced, and ambiguous count matrices to feed into downstream tools like scVelo or velocyto.py for trajectory / cellular dynamics analysis.
- The organism has a gene annotation GTF available (any eukaryote supported by 10X, e.g. human, mouse, Drosophila).

## Do not use when
- You already have a plain list of filtered cell barcodes (a single `barcodes.tsv` per sample) rather than the full 10X bundle — use the sibling sketch `rna-velocity-velocyto-10x-filtered-barcodes` instead, which skips the barcode-extraction step.
- You still need to go from raw FASTQ to a count matrix — run a 10X preprocessing workflow (CellRanger / STARsolo / fastq-to-matrix-10x) first; this sketch assumes aligned BAMs with `CB`/`UB` tags exist.
- Your BAMs do not have `CB` and `UB` tags (e.g. plain STAR output without solo mode) — velocyto cannot assign reads to cells/UMIs and will fail.
- You are working with non-10X single-cell chemistries (Smart-seq2, Drop-seq, inDrops, etc.) — velocyto has different run modes (`run-smartseq2`, `run`) that this workflow does not wire up.
- You want the full downstream velocity embedding / trajectory analysis — this sketch only produces the loom; pair it with a scVelo workflow afterwards.

## Analysis outline
1. Collect inputs: a collection of per-sample BAM files (with `CB`/`UB` tags), a collection of 10X bundled filtered matrix directories (each containing `barcodes.tsv`, `genes.tsv`, `matrix.mtx`), and a single GTF annotation file.
2. Apply Rules: extract only the `barcodes` element from each sample's bundled matrix collection, keyed by sample identifier, producing a per-sample filtered-barcodes collection.
3. Run `velocyto CLI` in `run10x` mode per sample, passing the BAM, the extracted filtered barcodes, and the GTF; sample identity is taken from the collection identifier.
4. Emit one `.loom` per sample containing spliced / unspliced / ambiguous count layers, ready for scVelo or similar downstream analysis.

## Key parameters
- Velocyto tool: `velocyto_cli` 0.17.17+galaxy3 (`toolshed.g2.bx.psu.edu/repos/iuc/velocyto_cli`).
- Mode: `main.do = run10x` (the 10X-specific entrypoint; expects CellRanger-style bundled output conventions).
- `sample_definition_select = identifier` — the sample name in the output loom is taken from the input collection element identifier.
- `main.BAM`: per-sample BAM with `CB` and `UB` tags (from CellRanger or STARsolo).
- `main.barcodes`: per-sample filtered `barcodes.tsv` (cells only, not the ~3M whitelist).
- `main.gtffile`: gene annotation GTF matching the reference used for alignment.
- `main.M = false`: do not mask repeats (no repeat-mask GFF supplied).
- `main.t = uint16`: dtype for count matrices in the loom.
- `s` (sample metadata table) and `m` (repeat-mask) are left as runtime/optional; typically unused.
- Verbosity: `-vv`.
- Apply Rules step filters the bundled collection's inner identifier to `barcodes`, preserving the outer sample identifier as the list key.

## Test data
The bundled test profile uses a single Drosophila melanogaster sample. Inputs are: a GTF annotation (`Drosophila_melanogaster.BDGP6.32.109_UCSC.gtf.gz`, auto-decompressed) from Zenodo record 6457007; a one-element BAM collection `subsample.bam` with `CB`/`UB` tags; and a list-of-lists collection `subsample` containing the three bundled matrix files `barcodes.tsv`, `genes.tsv`, and `matrix.mtx` (Zenodo record 10572348). The workflow extracts the `barcodes.tsv` element, runs velocyto `run10x`, and is expected to produce a `velocyto loom` collection whose `subsample` element is a loom file of roughly 4.64 MB (size asserted to ~4,639,326 bytes ±400 kB).

## Reference workflow
Galaxy IWC — `workflows/scRNAseq/velocyto/Velocyto-on10X-from-bundled.ga`, release 0.3 (2025-10-08), MIT-licensed, by Lucille Delisle. Uses `velocyto_cli` 0.17.17+galaxy3 from the IUC tool shed. See the sibling workflow `Velocyto-on10X-filtered-barcodes` for the variant that takes a pre-extracted filtered-barcodes collection instead of a bundled matrix.
