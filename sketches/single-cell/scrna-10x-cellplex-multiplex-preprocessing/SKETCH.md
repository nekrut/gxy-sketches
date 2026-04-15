---
name: scrna-10x-cellplex-multiplex-preprocessing
description: Use when preprocessing 10X Genomics Chromium v3 CellPlex multiplexed
  single-cell RNA-seq FASTQs into filtered gene-expression and CMO count matrices
  ready for Seurat/Scanpy Read10X. Handles both the gene expression library (STARsolo
  + DropletUtils) and the CMO hashing library (CITE-seq-Count) including the mandatory
  v2-to-v1 barcode translation step.
domain: single-cell
organism_class:
- eukaryote
input_data:
- 10x-scrna-fastq
- 10x-cmo-fastq
- reference-genome-star-index
- gene-annotation-gtf
- cellranger-barcode-whitelist
- cmo-sample-sheet-csv
source:
  ecosystem: iwc
  workflow: 'Single-Cell RNA-seq Preprocessing: 10X Genomics CellPlex Multiplexed
    Samples'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/scRNAseq/fastq-to-matrix-10x
  version: 0.6.5
  license: MIT
  slug: scRNAseq--fastq-to-matrix-10x--scrna-seq-fastq-to-matrix-10x-v3
tools:
- name: STARsolo
- name: DropletUtils
  version: 1.10.0+galaxy2
- name: CITE-seq-Count
- name: MultiQC
  version: 1.33+galaxy2
tags:
- single-cell
- scrna-seq
- 10x
- cellplex
- cmo
- multiplexing
- hashing
- preprocessing
- read10x
- chromium-v3
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

# 10X Genomics CellPlex multiplexed scRNA-seq preprocessing

## When to use this sketch
- Raw 10X Chromium **v3** chemistry FASTQs from a CellPlex experiment where multiple biological samples were pooled using Cell Multiplexing Oligos (CMOs).
- You have two FASTQ libraries per pool: a gene-expression (GEX) library and a CMO (feature-barcoding) library, plus a CSV sheet mapping CMO sequences to sample names.
- You need analysis-ready `matrix.mtx` / `barcodes.tsv` / `genes.tsv` bundles (CellRanger-like) for both GEX and CMO, loadable directly with `Seurat::Read10X` or `scanpy.read_10x_mtx`, so downstream demultiplexing (e.g. HTODemux, hashsolo) can assign cells to samples.
- A STAR index is available for your reference genome and you have a matching gene-annotation GTF.

## Do not use when
- Your 10X run is a **standard single-library-per-sample** experiment with no CMO hashing — use the sibling `scrna-10x-standard-preprocessing` sketch (same pipeline, GEX arm only).
- You used antibody-derived tags for CITE-seq surface protein quantification rather than sample multiplexing — the CMO-to-GEX barcode translation step here is CellPlex-specific and will corrupt CITE-seq ADT barcodes.
- You have 10X **v2** chemistry, 5′ assays, Visium spatial, or Multiome ATAC+GEX data.
- You need alignment-free pseudoalignment (kallisto|bustools, alevin-fry, salmon); this workflow hard-codes STARsolo.
- Input is long-read single-cell (ONT/PacBio) or non-10X droplet chemistry (Drop-seq, inDrops).
- You want downstream clustering, dimensionality reduction, or sample demultiplexing in the same run — this sketch stops at the count-matrix bundle.

## Analysis outline
1. **GEX alignment & quantification** — RNA STARsolo aligns the GEX R2 reads to the indexed reference, extracts CB+UMI from R1 using the 3M-february-2018 whitelist, and emits a raw gene × cell matrix (`soloFeatures: Gene`, `chemistry: Cv3`, `soloUMIdedup: 1MM_CR`, `soloCBmatchWLtype: 1MM_multi`).
2. **Alignment QC** — MultiQC aggregates the STAR log and per-gene read counts into an HTML report.
3. **Empty-droplet filtering** — DropletUtils `emptyDrops` filters the raw STARsolo matrix (`lower=100`, `fdr_thresh=0.01`, `seed=100`) to keep real cell barcodes.
4. **GEX bundle assembly** — a Re-organize-STAR-solo-output subworkflow relabels and merges the filtered matrix/barcodes/genes into a nested `list:list` collection, one sub-collection per sample with `matrix.mtx`/`barcodes.tsv`/`genes.tsv` (Read10X-ready).
5. **CMO counting** — CITE-seq-Count processes the CMO FASTQ pair against the CMO-sequence CSV tag list (`chemistry: v3`, `max_error: 2`, `bc_collapsing_dist: 1`, `umi_collapsing_dist: 2`) using the same 3M-february-2018 whitelist and the expected-cells parameter.
6. **CellPlex barcode translation (critical)** — an awk reformatter complement-swaps positions 8 and 9 of each 16 nt CMO cell barcode to translate the v2 whitelist used by CITE-seq-Count to the v1 whitelist used by STARsolo, so GEX and CMO barcodes align per cell (per 10X KB article on the 3M-february-2018 discrepancy).
7. **CMO bundle assembly** — the same Re-organize subworkflow packages the filtered CMO matrix/features/translated-barcodes into a Read10X-compatible nested collection labelled `Seurat input for CMO (UMI)`.

## Key parameters
- `reference genome`: STAR-indexed genome identifier (e.g. `dm6`, `hg38`, `mm10`).
- `gtf`: gene annotation GTF matching the reference.
- `cellranger_barcodes_3M-february-2018.txt`: 10X v3 cell-barcode whitelist (Zenodo 3457880).
- `Barcode Size is same size of the Read`: `false` if GEX R1 has trailing A padding past CB+UMI, `true` if R1 length exactly equals CB(16)+UMI(12)=28 nt.
- `Number of expected cells`: integer passed to CITE-seq-Count; keep realistic (e.g. 500–24000) — setting it too high disables cell-barcode correction for CMO demultiplexing.
- STARsolo fixed: `solo_type=CB_UMI_Simple`, `chemistry=Cv3`, `soloStrand=Forward`, `soloFeatures=Gene`, `filter_type=no_filter` (raw matrix; filtering handled by DropletUtils).
- DropletUtils fixed: `method=emptydrops`, `lower=100`, `fdr_thresh=0.01`.
- CITE-seq-Count fixed: `chemistry=v3`, `max_error=2`, `bc_collapsing_dist=1`, `umi_collapsing_dist=2`, `start_trim=0`.
- CellPlex barcode translation is hard-coded (complement positions 8 and 9 of the 16 nt barcode) — do not disable it for CellPlex data.

## Test data
A single paired CellPlex subsample (`subsample`) with four gzipped FASTQs hosted on Zenodo 10412836: `GEX_R1`/`GEX_R2` (gene expression) and `CMO_R1`/`CMO_R2` (Cell Multiplexing Oligo library), a *Drosophila melanogaster* BDGP6.32.109 GTF (Zenodo 6457007, decompressed), a trimmed 10X barcode whitelist (`all_cell_barcodes_both_versions.txt`), and a CMO sample sheet CSV from Zenodo 10229382. The reference genome parameter is `dm6` and expected-cells is set to 500. Running the workflow should yield a MultiQC STARsolo report with uniquely-mapped rate in the 33.x % range, a filtered GEX Read10X bundle whose `matrix.mtx` header is `23932 3 1171` and contains barcode `CACATGATCATAAGGA` and gene line `FBgn0250732\tgfzf`, a CITE-seq-Count v1.4.4 report with 116993 reads processed at ~99 % mapped, and a CMO Read10X bundle (`8 1218 2289`) whose translated barcodes include `CACATGATCATAAGGA` and whose features include `mESC.rep1-CGCGATATGGTCGGA`.

## Reference workflow
Galaxy IWC `workflows/scRNAseq/fastq-to-matrix-10x/scrna-seq-fastq-to-matrix-10x-cellplex.ga`, release 0.6.5 (MIT). Built on RNA STARsolo 2.7.11b+galaxy0, DropletUtils 1.10.0+galaxy2, CITE-seq-Count 1.4.4+galaxy0, and MultiQC 1.33+galaxy2. Inspired by the Galaxy Training Network tutorial *scrna-preprocessing-tenx*. See the 10X Genomics knowledge-base article on the 3M-february-2018 whitelist discrepancy for the rationale behind the CMO barcode translation step.
