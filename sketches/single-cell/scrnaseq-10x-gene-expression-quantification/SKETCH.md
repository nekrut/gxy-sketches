---
name: scrnaseq-10x-gene-expression-quantification
description: Use when you need to go from raw 10x Genomics droplet-based single-cell
  RNA-seq FASTQs to a filtered cell-by-gene count matrix (h5ad/Seurat/mtx) for downstream
  analysis. Handles 10x 3' v1-v4 chemistry and can also quantify Drop-seq or custom
  barcode-based protocols.
domain: single-cell
organism_class:
- eukaryote
- vertebrate
input_data:
- 10x-scrna-fastq
- reference-fasta
- gtf
source:
  ecosystem: nf-core
  workflow: nf-core/scrnaseq
  url: https://github.com/nf-core/scrnaseq
  version: 4.1.0
  license: MIT
  slug: scrnaseq
tools:
- name: fastqc
  version: 0.12.1
- name: simpleaf
- name: alevin-fry
- name: alevinqc
- name: starsolo
- name: kallisto
- name: bustools
- name: cellranger
- name: cellbender
- name: scanpy
- name: seurat
- name: multiqc
tags:
- scrna-seq
- 10x-genomics
- droplet
- count-matrix
- umi
- cellranger
- alevin-fry
- starsolo
- kallisto-bustools
test_data: []
expected_output: []
---

# 10x Genomics single-cell RNA-seq quantification

## When to use this sketch
- Input is droplet-based single-cell RNA-seq FASTQs from 10x Genomics Chromium (3' v1/v2/v3/v4) or a compatible barcode+UMI protocol (Drop-seq, custom `bc:umi:seq` strings).
- Goal is to produce a per-sample cell-by-gene count matrix (raw and/or filtered) in `.h5ad` (AnnData), `.rds` (Seurat), and `.mtx` formats, plus QC reports, for downstream clustering / annotation in scanpy or Seurat.
- User wants a choice between quantifiers: Alevin-fry/simpleaf (default), STARsolo, Kallisto|BUStools, or Cell Ranger, optionally followed by CellBender empty-droplet filtering.
- User has, or can obtain, a genome FASTA + GTF (or an nf-core iGenomes key like `GRCh38`/`GRCm38`).
- Multi-lane samples are allowed; rows with the same `sample` ID are concatenated automatically before quantification.

## Do not use when
- Data is plate-based **Smart-seq2 / full-length without UMIs** — route to a bulk-style pipeline such as nf-core/rnaseq instead (this sketch is barcode-based only).
- Data is **single-nucleus multiome (scATAC + GEX)** from 10x Multiome — that needs the `cellrangerarc` path with a `sample_type` / `fastq_barcode` samplesheet; treat as a sibling sketch (`scmultiome-atac-gex-cellranger-arc`).
- Data is **10x Cell Ranger Multi** style (VDJ, antibody/feature barcoding, CMO/FFPE/OCM multiplexing) — that needs `--aligner cellrangermulti` plus a second barcodes samplesheet; treat as a sibling sketch (`scrnaseq-10x-cellranger-multi-feature-barcoding`).
- You need **cell hashing / genotype demultiplexing** of pooled samples — use the `hadge` pipeline, not this one.
- You want variant calling, bulk differential expression, spatial, or long-read single-cell — wrong class entirely.

## Analysis outline
1. Parse samplesheet (`sample,fastq_1,fastq_2[,expected_cells,seq_center]`) and concatenate lanes per sample.
2. Run **FastQC** on raw reads (pre-barcode-trimming) and collect for MultiQC.
3. Build or reuse a reference index for the chosen aligner (simpleaf/piscem, STAR, Kallisto, or Cell Ranger) from `--fasta` + `--gtf`, or use `--genome` via iGenomes; indices can be cached with `--save_reference`.
4. Quantify per sample with the selected `--aligner`: **simpleaf** (Alevin-fry + AlevinQC, default), **star** (STARsolo), **kallisto** (kallisto|bustools), or **cellranger** (full 10x pipeline incl. BAM + filtered matrices).
5. (Optional) Run **CellBender remove-background** on the raw matrix to filter empty/ambient droplets; skipped by `--skip_cellbender`.
6. Convert all matrices to **AnnData `.h5ad`** (scanpy) and **Seurat `.rds`**, tagged `raw` / `filtered` / `cellbender_filter`, plus a `combined_matrix.h5ad` across samples.
7. Aggregate QC (FastQC + aligner metrics + AlevinQC/STARsolo/Cell Ranger summary) into a **MultiQC** report.

## Key parameters
- `--input`: CSV samplesheet. Required columns `sample,fastq_1,fastq_2`; optional `expected_cells`, `seq_center`. Repeat `sample` across rows to merge lanes.
- `--aligner`: one of `simpleaf` (default), `star`, `kallisto`, `cellranger`, `cellrangerarc`, `cellrangermulti`. For plain 10x GEX quantification pick `simpleaf`, `star`, `kallisto`, or `cellranger`.
- `--protocol`: `10XV1` | `10XV2` | `10XV3` | `10XV4` | `auto` (Cell Ranger only) | custom chemistry string passed verbatim to the aligner. Must be set explicitly for non-Cell Ranger aligners.
- `--fasta` + `--gtf`: genome FASTA and matching GTF. Alternatively `--genome GRCh38` (or similar) via iGenomes with `--igenomes_ignore` off.
- `--transcript_fasta` + `--txp2gene`: required for simpleaf / kallisto if you bring your own transcriptome and t2g mapping.
- `--simpleaf_index` / `--star_index` / `--kallisto_index` / `--cellranger_index`: skip index building by supplying a prebuilt index.
- `--simpleaf_umi_resolution`: `cr-like` (default), `cr-like-em`, `parsimony`, `parsimony-em`, `parsimony-gene`, `parsimony-gene-em`.
- `--star_feature`: `Gene` (default), `GeneFull` for single-nucleus / pre-mRNA, `Gene Velocyto` for RNA velocity layers.
- `--kb_workflow`: `standard` (default), `lamanno` (La Manno RNA velocity), `nac` (nascent + mature).
- `--barcode_whitelist`: only needed for non-10x protocols; 10x whitelists are bundled.
- `--skip_cellbender`: disable empty-droplet filtering (required for very small / test datasets).
- `--skip_fastqc`, `--skip_multiqc`: trim QC steps.
- `--save_reference`, `--save_align_intermeds`: persist indices and intermediate BAMs into `results/`.
- Samplesheet `expected_cells`: forwarded to Alevin-fry `--expect-cells`, STARsolo, and (legacy) Cell Ranger; note 10x no longer recommends setting it for Cell Ranger ≥ v7.

## Test data
The `test` profile runs on a tiny public dataset: a samplesheet at `https://github.com/nf-core/test-datasets/raw/scrnaseq/samplesheet-2-0.csv` against a chromosome-19-only mouse reference (`GRCm38.p6.genome.chr19.fa` + `gencode.vM19.annotation.chr19.gtf`), with `--aligner star`, `--protocol 10XV2`, and `--skip_cellbender true` (CellBender cannot converge on such a small matrix). A successful run is expected to produce, per sample: a STARsolo output directory with mapped BAM and Solo.out metrics, `mtx_conversions/*_raw_matrix.h5ad` and `*_raw_matrix.rds` plus a `combined_matrix.h5ad`, FastQC HTML/zip reports, and a `multiqc/multiqc_report.html` summarising the run. The `test_full` profile runs the same pipeline on a full-size human dataset using `--genome GRCh38`, `--aligner star`, `--protocol 10XV2`.

## Reference workflow
nf-core/scrnaseq v4.1.0 — https://github.com/nf-core/scrnaseq (MIT). See `docs/usage.md` for the protocol compatibility matrix across aligners and `docs/output.md` for the exact output directory layout (`results/{fastqc,simpleaf,star,kallisto,cellranger,cellrangerarc,cellrangermulti,reference_genome,multiqc}` plus `${aligner}/mtx_conversions/`).
