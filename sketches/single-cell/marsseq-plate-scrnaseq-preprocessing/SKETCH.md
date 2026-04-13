---
name: marsseq-plate-scrnaseq-preprocessing
description: Use when preprocessing MARS-seq v2.0 plate-based single-cell RNA-seq
  experiments (FACS-indexed sorted cells with amplification and sequencing batch metadata)
  to generate per-amplification-batch UMI count matrices, optionally with RNA velocity
  spliced/unspliced counts via StarSolo. Supports mouse (mm9/mm10) and human (GRCh38)
  references with ERCC spike-ins.
domain: single-cell
organism_class:
- mouse
- human
- eukaryote
input_data:
- short-reads-paired
- marsseq-batch-metadata-xlsx
source:
  ecosystem: nf-core
  workflow: nf-core/marsseq
  url: https://github.com/nf-core/marsseq
  version: 1.0.3
  license: MIT
tools:
- bowtie2
- star
- starsolo
- cutadapt
- fastp
- fastqc
- multiqc
- perl-marsseq2
tags:
- mars-seq
- plate-based
- scrna-seq
- facs
- rna-velocity
- ercc
- umi
- demultiplexing
test_data: []
expected_output: []
---

# MARS-seq v2.0 plate-based scRNA-seq preprocessing

## When to use this sketch
- Raw FASTQ data comes from a MARS-seq v2.0 experiment (plate-based, FACS-indexed single-cell RNA-seq with pool barcodes + cell barcodes + UMIs).
- You have the MARS-seq bookkeeping spreadsheets (`amp_batches.xlsx`, `seq_batches.xlsx`, `wells_cells.xlsx`) that map wells to amplification and sequencing batches.
- Reads follow the MARS-seq layout: R1 = LA(3bp)+PB(4bp)+cDNA(66bp)+RA(2bp), R2 = CB(7bp)+UMI(8bp).
- You want per-amplification-batch UMI count matrices (genes x wells/cells) and QC, against mouse (mm9/mm10) or human (GRCh38) with ERCC spike-ins appended.
- Optionally, you also want spliced/unspliced counts for RNA velocity by re-formatting reads into 10x v2 layout and aligning with StarSolo.

## Do not use when
- Data is droplet-based 10x Genomics, Drop-seq, inDrops, or Smart-seq2/3 — use a 10x/STARsolo or smart-seq preprocessing sketch instead.
- You only need bulk RNA quantification — use a bulk RNA-seq sketch.
- Organism is not mouse or human and you cannot supply a matching GENCODE FASTA+GTF — this pipeline's genome presets cover only `mm9`, `mm10`, `GRCh38_v43`.
- Downstream clustering, annotation, trajectory analysis, or differential expression is the goal — this sketch stops at count matrices; hand the UMI tables to a scanpy/Seurat sketch.
- You lack the MARS-seq metadata spreadsheets; they are mandatory for demultiplexing.

## Analysis outline
1. **Build references** (run once, with `--build_references`): download FASTA+GTF from GENCODE for the chosen genome, append ERCC spike-ins, build `bowtie2` index, and (if `--velocity`) a `STAR` index.
2. **Prepare pipeline**: validate the samplesheet and `amp_batches`/`seq_batches`/`wells_cells` xlsx files, convert them to the Tanay-lab `.txt` formats (`amp_batches.txt`, `seq_batches.txt`, `wells_cells.txt`, `gene_intervals.txt`), and split raw FASTQs into chunks of ~4,000,000 reads so bowtie2 does not OOM.
3. **Label reads**: transfer the cell barcode + UMI from R2 onto R1 headers so downstream demultiplexing can see them.
4. **Align reads** with `bowtie2` per chunk, then merge alignments into a single per-batch SAM.
5. **(Optional) RNA velocity branch**: trim with `cutadapt`, reformat reads into 10x v2 layout, generate a whitelist of pool+cell barcodes, and align with `STARsolo` using `--soloFeatures Gene GeneFull SJ Velocyto` to produce spliced/unspliced matrices.
6. **Demultiplex** with the MARS-seq2.0 Perl tooling to emit per-amplification-batch `umi.tab`, `offset.tab`, `singleton_offset.tab`, plus `amp_batches_stats.txt` and `amp_batches_summary.txt`.
7. **QC**: run `fastp`/`FastQC` on raw reads, generate the internal per-sequencing-batch MARS-seq QC PDF, and aggregate everything with `MultiQC`.

## Key parameters
- `--input`: CSV samplesheet with columns `batch,fastq_1,fastq_2,amp_batches,seq_batches,well_cells` — one row per sequencing batch.
- `--genome`: one of `mm9`, `mm10`, `GRCh38_v43` (default `mm10`). Selects the GENCODE reference to download and ERCC-augment.
- `--build_references`: run once up front to materialize the FASTA, GTF, bowtie2 index, and (if velocity) STAR index under `--genomes_base`.
- `--velocity`: enable the StarSolo RNA-velocity branch (off by default).
- `--read_length`: required when `--velocity` is set; used to compute STAR's `--sjdbOverhang`.
- `--skip_qc`: skip FastQC/MultiQC steps for faster iteration.
- `--outdir`: absolute path for results; each sequencing batch gets its own subdirectory alongside shared `multiqc/`, `references/`, and `pipeline_info/`.
- Custom references (bypass `--genome`): `--fasta`, `--gtf`, `--bowtie2_index`, and `--star_index` must all be supplied together.

## Test data
The pipeline's `test` profile points at the nf-core `marsseq` test-datasets repo and uses `SB26-AB339.csv`, a single MARS-seq sequencing batch (`SB26`, amplification batch `AB339`) with paired-end `Undetermined_S0_L001_R{1,2}_001.fastq.gz` plus the three accompanying xlsx metadata files, all against the `mm10` GENCODE+ERCC reference. Running it exercises the full flow end-to-end on constrained CI resources (2 CPU / 6 GB / 6 h). Expected deliverables are a per-batch merged bowtie2 SAM, the MARS-seq `output/` tree containing `umi.tab/AB339.txt` (genes x wells UMI matrix), `offset.tab`, `singleton_offset.tab`, `amp_batches_stats.txt`, `amp_batches_summary.txt`, a `QC_reports/SB26.pdf`, a FastQC report per FASTQ, and an aggregated `multiqc/multiqc_report.html`. The full-size `test_full` profile runs the same layout on the complete `SB26` sequencing batch.

## Reference workflow
nf-core/marsseq v1.0.3 (https://github.com/nf-core/marsseq), implementing Keren-Shaul et al., *Nat Protoc* 2019 (MARS-seq2.0) with an added StarSolo-based RNA-velocity branch.
