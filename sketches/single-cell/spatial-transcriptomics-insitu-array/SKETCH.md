---
name: spatial-transcriptomics-insitu-array
description: Use when processing sequencing-based spatial transcriptomics data from
  in-situ barcoded arrays (paired-end FASTQ with spatial barcodes + UMIs) and you
  need spatially-resolved gene-by-spot count matrices in AnnData H5AD format. Requires
  an NVIDIA GPU for QUIK barcode calling.
domain: single-cell
organism_class:
- vertebrate
- eukaryote
input_data:
- short-reads-paired
- reference-fasta
- gtf-annotation
- spatial-barcode-coords-csv
source:
  ecosystem: nf-core
  workflow: nf-core/panoramaseq
  url: https://github.com/nf-core/panoramaseq
  version: dev
  license: MIT
  slug: panoramaseq
tools:
- name: fastqc
  version: 0.12.1
- name: seqtk
- name: quik
- name: umi-tools
- name: cutadapt
- name: star
- name: subread-featurecounts
- name: samtools
- name: anndata
- name: multiqc
  version: '1.27'
tags:
- spatial-transcriptomics
- in-situ-array
- barcode-calling
- umi
- h5ad
- gpu
- scanpy
test_data: []
expected_output: []
---

# Spatial transcriptomics from in-situ barcoded arrays

## When to use this sketch
- Paired-end Illumina FASTQ from sequencing-based spatial transcriptomics experiments using in-situ barcoded arrays (e.g. ~34,500 spatial barcodes, 36 bp barcode length).
- A per-array CSV of spatial barcode sequences with (x, y) coordinates is available for each sample.
- The goal is a spatially-resolved gene-by-spot count matrix in AnnData H5AD format, ready for Scanpy / Seurat downstream analysis.
- An NVIDIA GPU with CUDA 12.6+ drivers and Singularity/Apptainer are available for GPU-accelerated QUIK barcode calling.
- Reads follow the expected layout: UMI at the read start (9 Ns by default) and a 36 bp spatial barcode beginning at position 9.

## Do not use when
- Input is 10x Visium, Slide-seq, Stereo-seq, or any other vendor-specific spatial platform — use the platform-native pipeline (e.g. Space Ranger, stpipeline) instead.
- Input is droplet-based single-cell RNA-seq without spatial coordinates — use a scRNA-seq quantification sketch (Cell Ranger / nf-core/scrnaseq / STARsolo).
- Input is bulk RNA-seq — use a bulk rna-seq sketch (nf-core/rnaseq).
- Input is imaging-based spatial transcriptomics (MERFISH, seqFISH, Xenium, CosMx) — this pipeline only handles sequencing-based arrays.
- No GPU is available; QUIK requires a pre-built CUDA container and will not run CPU-only.
- Barcodes are not 36 bp or the rejection threshold must differ from 8 — the QUIK container is compiled with fixed `SEQUENCE_LENGTH=36` and `REJECTION_THRESHOLD=8` and must be rebuilt from `containers/quik_cuda_prebuilt.def`.

## Analysis outline
1. Raw read QC with FastQC.
2. Optional read subsampling with seqtk (`--sample_size`) for quick test runs.
3. GPU-accelerated spatial barcode calling with QUIK against the array's barcode coordinate CSV.
4. UMI extraction from read 1 with UMI-tools (`extract`).
5. Multi-stage adapter and quality trimming with Cutadapt.
6. Alignment to reference genome with STAR (pre-built index or built from FASTA+GTF on the fly).
7. Gene assignment with subread featureCounts against the provided GTF.
8. UMI deduplication and per-gene UMI counting with UMI-tools `count`.
9. AnnData H5AD generation merging per-spot counts with (x, y) coordinates from the barcode CSV.
10. H5AD structural validation and MultiQC aggregation of all QC metrics.

## Key parameters
- `input`: samplesheet CSV with columns `sample,fastq_1,fastq_2,N_barcodes,barcode_file` (e.g. `N_barcodes=34500`).
- Reference: either `--star_genome_dir` + `--star_gtf`, or `--fasta` + `--star_gtf` (index is built), or `--genome GRCh38` via iGenomes.
- `--barcode_start 9`: zero-based start of the 36 bp spatial barcode in the read.
- `--strategy 4_7_mer_gpu_v1`: QUIK barcode matching strategy.
- `--distance_measure SEQUENCE_LEVENSHTEIN`: alternatives `LEVENSHTEIN`, `PSEUDO_DISTANCE`.
- `--umitools_bc_pattern NNNNNNNNN` and `--umitools_extract_method string`: 9 nt UMI at the read start.
- `--sample_size 400000`: optional seqtk downsampling per FASTQ.
- `--mergecounts true`: merge all samples into one H5AD (requires `--coords_csv` when merging across the array).
- `--validate_h5ad true`: run H5AD structural validation after generation.
- `-profile singularity` (required — QUIK container is `oras://quay.io/francoaps/quik-cuda:prebuilt-36bp-v2`) plus a `use_gpu` process label with `--gpus=1` and `--nv` container options.

## Test data
The `test` profile pulls a samplesheet from the nf-core `panoramaseq` test-datasets branch and runs against a small *Homo sapiens* reference (`genome.fasta` + `genome.gtf` from nf-core/test-datasets/modules), subsampling each FASTQ to 400,000 reads via seqtk and building the STAR index on the fly. A successful test run produces FastQC reports at raw/post-UMI/post-trim stages, QUIK barcode-calling statistics, STAR BAMs, per-gene UMI count TSVs, per-sample and/or merged H5AD files in `h5ad/` passing structural validation, and a `multiqc/multiqc_report.html` aggregating metrics. The `test_full` profile runs the same pipeline against the full-size samplesheet with a pre-built STAR index for GRCh38 and enables `mergecounts` and `validate_h5ad`.

## Reference workflow
nf-core/panoramaseq (version `dev`, template 1.0.0dev). Key citation: Uphoff et al. (2025), *QUIK: GPU-accelerated barcode calling for spatial transcriptomics*, bioRxiv 10.1101/2025.05.12.653416. See the pipeline README for the full tool citation list (FastQC, seqtk, UMI-tools, Cutadapt, STAR, subread/featureCounts, SAMtools, AnnData, MultiQC).
