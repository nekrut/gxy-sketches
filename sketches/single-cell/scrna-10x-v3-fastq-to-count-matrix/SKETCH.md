---
name: scrna-10x-v3-fastq-to-count-matrix
description: Use when you have raw 10X Genomics Chromium v3 single-cell RNA-seq FASTQs
  (paired R1 cell-barcode+UMI / R2 cDNA) and need to align, quantify, and produce
  filtered count matrices in CellRanger-like bundle format (matrix.mtx + barcodes.tsv
  + genes.tsv) ready for downstream Seurat Read10X or Scanpy read_10x_mtx analysis.
domain: single-cell
organism_class:
- eukaryote
input_data:
- 10x-scrna-fastq
- reference-genome-star-index
- gtf
source:
  ecosystem: iwc
  workflow: 'Single-Cell RNA-seq Preprocessing: 10X Genomics v3 to Seurat and Scanpy
    Compatible Format'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/scRNAseq/fastq-to-matrix-10x
  version: 0.6.5
  license: MIT
tools:
- starsolo
- dropletutils
- multiqc
tags:
- single-cell
- scrna-seq
- 10x-genomics
- chromium-v3
- starsolo
- emptydrops
- seurat
- scanpy
- read10x
test_data:
- role: fastq_pe_collection_gex__subsample__forward
  url: https://zenodo.org/records/10412836/files/GEX_R1.fastqsanger.gz
  sha1: c23fb98763b959fbf4ac51fc5ef6e690e378ef0d
  filetype: fastqsanger.gz
- role: fastq_pe_collection_gex__subsample__reverse
  url: https://zenodo.org/records/10412836/files/GEX_R2.fastqsanger.gz
  sha1: bba127e369535d226290a74858efafd7f359168e
  filetype: fastqsanger.gz
- role: gtf
  url: https://zenodo.org/record/6457007/files/Drosophila_melanogaster.BDGP6.32.109_UCSC.gtf.gz
  sha1: 3cbdd2f0eed28bd10af66cb83aa3f6d688779d51
  filetype: gtf
- role: fastq_pe_collection_cmo__subsample__forward
  url: https://zenodo.org/records/10412836/files/CMO_R1.fastqsanger.gz
  sha1: 277fd1637b8615f70081b72427b6920713c1aa14
  filetype: fastqsanger.gz
- role: fastq_pe_collection_cmo__subsample__reverse
  url: https://zenodo.org/records/10412836/files/CMO_R2.fastqsanger.gz
  sha1: f65316ed442c2d13e4ba5feace4adebcbc758420
  filetype: fastqsanger.gz
- role: sample_name_and_cmo_sequence_collection__subsample
  url: https://zenodo.org/records/10229382/files/CMO.csv
  sha1: 03a74c7c22810d354c4030fd0e4991cf9578f592
  filetype: csv
expected_output:
- role: multiqc_starsolo
  description: Content assertions for `MultiQC_STARsolo`.
  assertions:
  - 'has_text_matching: {''expression'': ''<span class="val">33.[0-9]<span class=[\''"]mqc_small_space[\''"]>''}'
- role: cite_seq_count_report
  description: Content assertions for `CITE-seq-Count report`.
  assertions:
  - 'subsample: that: has_line'
  - 'subsample: line: CITE-seq-Count Version: 1.4.4'
  - 'subsample: that: has_line'
  - 'subsample: line: Reads processed: 116993'
  - 'subsample: that: has_line'
  - 'subsample: line: Percentage mapped: 99'
  - 'subsample: that: has_line'
  - 'subsample: line: Percentage unmapped: 1'
---

# 10X Genomics v3 scRNA-seq: FASTQ to Seurat/Scanpy-ready count matrices

## When to use this sketch
- User has raw FASTQs from 10X Genomics Chromium Single Cell 3' v3 (or 5' v3) chemistry, with R1 carrying a 16 bp cell barcode + 12 bp UMI and R2 carrying the cDNA read.
- User wants a reproducible preprocessing pipeline that goes from FASTQ to a filtered gene-by-cell count matrix, emitted as a CellRanger-style bundle (`matrix.mtx`, `barcodes.tsv`, `genes.tsv`) consumable by `Seurat::Read10X` or `scanpy.read_10x_mtx`.
- User has multiple samples as a list of paired FASTQ collections and wants per-sample output sub-collections.
- User has (or can point to) a STAR genome index plus matching GTF gene annotation, and the 10X v3 barcode whitelist (`3M-february-2018.txt`).
- User needs empty-droplet removal (EmptyDrops) rather than a simple knee-point filter, and wants a MultiQC summary of mapping / gene assignment rates.

## Do not use when
- Reads come from 10X v2 chemistry (16 bp CB + 10 bp UMI) or from non-10X platforms (Drop-seq, inDrops, Smart-seq2, Parse, BD Rhapsody) — those need different barcode/UMI geometry and different whitelists.
- The library is CellPlex / hashtag-multiplexed with CMOs: use the sibling `scrna-10x-v3-cellplex-demultiplex` sketch, which adds CITE-seq-Count for CMO assignment.
- You already have a filtered count matrix / h5 / h5ad and just want clustering, integration, or annotation — use a downstream analysis sketch, not this preprocessing one.
- The data is single-nucleus RNA-seq where you must count intronic reads for pre-mRNA; this workflow uses `soloFeatures=Gene` (exonic) and does not emit a spliced/unspliced Velocyto matrix.
- You need a BAM file or allele-specific / WASP-filtered output — BAM is hidden here and WASP mode is off.
- The organism has no STAR-indexable reference genome + GTF available.

## Analysis outline
1. **Align & quantify with STARsolo** (`rna_starsolo`, STAR 2.7.11b) in `CB_UMI_Simple` mode, chemistry `Cv3`, using the supplied STAR index, GTF, and 10X v3 barcode whitelist; emits raw cell-barcode × gene count matrix plus per-sample logs and reads-per-gene tables.
2. **Aggregate QC with MultiQC** over the STARsolo logs and gene-count tables to produce a single HTML report covering mapping rate and fraction of reads assigned to genes.
3. **Call real cells with DropletUtils EmptyDrops** (`dropletutils` 1.10.0) on the raw matrix, with `lower=100`, `fdr_thresh=0.01`, `seed=100`, producing a filtered matrix/barcodes/genes triple per sample in 10X directory layout.
4. **Re-organize outputs into CellRanger-like bundles** via a subworkflow that relabels each per-sample `matrix.mtx`, `barcodes.tsv`, `genes.tsv`, merges them, and applies collection rules so the final output is a nested `list:list` with one sub-collection per sample containing exactly those three files — directly loadable by `Read10X`.

## Key parameters
- STARsolo `solo_type = CB_UMI_Simple`, `chemistry = Cv3` (16 bp CB + 12 bp UMI).
- STARsolo `soloCBwhitelist` = 10X v3 whitelist `3M-february-2018.txt` (from https://zenodo.org/record/3457880/files/3M-february-2018.txt.gz).
- STARsolo `soloBarcodeReadLength` = boolean user input — set `true` when R1 length equals CB+UMI (28 bp) exactly; set `false` if R1 has trailing A's or is longer.
- STARsolo `soloUMIdedup = 1MM_CR`, `soloCBmatchWLtype = 1MM_multi`, `soloStrand = Forward`, `soloFeatures = Gene`, `sjdbOverhang = 100`, `sjdbGTFfeatureExon = exon`.
- STARsolo filter mode: `no_filter` with `output_raw=true` — filtering is deferred to DropletUtils, not STAR's built-in EmptyDrops/Knee.
- DropletUtils: `method = emptydrops`, `lower = 100` UMIs, `fdr_thresh = 0.01`, `seed = 100`, `outformat = directory`.
- Reference inputs: a STAR-indexed `genomeDir` plus a matching gene GTF; both must use the same chromosome naming.

## Test data
The CI test uses a single paired-end sample `subsample` with `GEX_R1.fastqsanger.gz` and `GEX_R2.fastqsanger.gz` from Zenodo record 10412836, aligned against the *Drosophila melanogaster* `dm6` STAR index with the `Drosophila_melanogaster.BDGP6.32.109_UCSC.gtf.gz` annotation and a trimmed 10X v3 barcode whitelist (`all_cell_barcodes_both_versions.txt`). `Barcode Size is same size of the Read` is set to `false` because the R1 reads carry trailing bases. A successful run is expected to produce a MultiQC report whose STARsolo section shows a mapping rate around 33.x%, and a nested `list:list` Seurat-ready collection where the `subsample` sub-collection contains a `matrix.mtx` with header line `23932 3 1171`, a `barcodes.tsv` containing barcode `CACATGATCATAAGGA`, and a `genes.tsv` containing the entry `FBgn0250732\tgfzf`. (Note: the parsed manifest lists CellPlex-style CMO inputs from the sibling workflow's test file; this sketch's own test uses only the GEX pair, GTF, and whitelist.)

## Reference workflow
Galaxy IWC — `workflows/scRNAseq/fastq-to-matrix-10x/scrna-seq-fastq-to-matrix-10x-v3.ga`, release 0.6.5 (MIT), using `rna_starsolo` 2.7.11b+galaxy0, `dropletutils` 1.10.0+galaxy2, and `multiqc` 1.33+galaxy2. Inspired by the Galaxy Training Network tutorial *scrna-preprocessing-tenx*.
