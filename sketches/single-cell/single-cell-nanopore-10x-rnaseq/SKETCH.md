---
name: single-cell-nanopore-10x-rnaseq
description: Use when you have 10X Genomics single-cell or single-nuclei RNA-seq libraries
  sequenced on Oxford Nanopore (ideally R10.4 Q20+ chemistry, though older chemistries
  work) and need cell-barcode demultiplexing, UMI deduplication, and gene/transcript
  feature-barcode matrices from long reads. Not for Illumina paired-end scRNA-seq.
domain: single-cell
organism_class:
- eukaryote
input_data:
- long-reads-ont
- reference-fasta
- transcriptome-fasta
- gtf-annotation
source:
  ecosystem: nf-core
  workflow: nf-core/scnanoseq
  url: https://github.com/nf-core/scnanoseq
  version: 1.2.2
  license: MIT
tools:
- nanofilt
- blaze
- minimap2
- samtools
- umi-tools
- picard
- isoquant
- oarfish
- seurat
- multiqc
- nanoplot
- nanocomp
- toulligqc
- fastqc
tags:
- single-cell
- scrna-seq
- snrna-seq
- nanopore
- long-read
- 10x-genomics
- isoquant
- oarfish
- blaze
- umi
test_data: []
expected_output: []
---

# Single-cell 10X RNA-seq from Oxford Nanopore long reads

## When to use this sketch
- Input is 10X Genomics single-cell or single-nuclei cDNA libraries sequenced on Oxford Nanopore (GridION / PromethION), preferably R10.4 Q20+ chemistry but older ONT chemistries are also supported.
- Per-sample FASTQ(s) only — no paired Illumina short reads required; each row is one ONT FASTQ with an expected `cell_count`.
- You need BLAZE-based cell-barcode calling + correction, UMI deduplication, and a feature-barcode matrix (gene and/or transcript level) suitable for downstream Seurat analysis.
- Chemistry is one of `10X_3v3`, `10X_3v4`, `10X_5v2`, or `10X_5v3`.
- Works for any eukaryote where a genome FASTA, transcriptome FASTA, and GTF annotation are available.

## Do not use when
- Reads are Illumina short reads → use a short-read scRNA-seq pipeline (e.g. nf-core/scrnaseq with Cell Ranger / STARsolo / Alevin-fry), not this sketch.
- Bulk long-read RNA-seq without single-cell barcodes → use nf-core/nanoseq or nf-core/rnaseq-style long-read quantification instead.
- Non-10X single-cell chemistries (Drop-seq, BD Rhapsody, Parse, Smart-seq) — the BLAZE barcode caller and `barcode_format` enum only cover 10X 3'/5' v2/v3/v4.
- You only need basecalling / raw pod5 → ONT basecalling is upstream of this pipeline; input must already be FASTQ.

## Analysis outline
1. Raw-read QC on FASTQ with FastQC, NanoPlot, NanoComp, and ToulligQC.
2. Optionally split each FASTQ into chunks of `split_amount` lines for parallelism; unzip/re-zip with pigz.
3. Quality/length trim reads with Nanofilt (`min_length`, `min_q_score`).
4. Post-trim QC (FastQC / NanoPlot / NanoComp / ToulligQC).
5. Call cell barcodes with BLAZE using the `barcode_format` whitelist (or a user `--whitelist`) and the per-sample expected `cell_count`.
6. Pre-extract barcodes/UMIs into synthetic R1, cDNA into R2 (`pre_extract_barcodes.py`), then correct barcodes against the BLAZE whitelist (`correct_barcodes.py`).
7. Post-extraction QC and read-count tracking across stages.
8. Align long reads with minimap2 to the genome (for IsoQuant) and/or transcriptome (for oarfish).
9. Sort, index, and filter BAMs with samtools; collect flagstat/idxstats/stats and RSeQC read-distribution metrics.
10. Tag BAM records with `CR/CY/CB/UR/UY` barcode/UMI tags via `tag_barcodes.py`.
11. Deduplicate reads with UMI-tools (default) or Picard MarkDuplicates — always run for oarfish, optional (`skip_dedup`) for IsoQuant.
12. Quantify feature-barcode matrices: IsoQuant on the genome BAM (gene + transcript counts) and/or oarfish on the transcriptome BAM (transcript counts, MatrixMarket format).
13. Run Seurat-based preliminary matrix QC (nFeature / nCount distributions, plots).
14. Aggregate all QC with MultiQC.

## Key parameters
- `input`: samplesheet CSV with `sample,fastq,cell_count`; rows sharing a sample name are merged.
- `outdir`: results directory (absolute path on cloud).
- `gtf`: **required** gene annotation.
- `genome_fasta`: required if `quantifier` includes `isoquant`.
- `transcript_fasta`: required if `quantifier` includes `oarfish`.
- `quantifier`: `isoquant`, `oarfish`, or `isoquant,oarfish` (comma-delimited).
- `barcode_format`: one of `10X_3v3` (default for tests), `10X_3v4`, `10X_5v2`, `10X_5v3`; sets the default BLAZE whitelist.
- `whitelist`: optional user barcode whitelist that overrides the built-in one.
- `dedup_tool`: `umitools` (default) or `picard`.
- `split_amount`: lines-per-chunk for FASTQ splitting; `500000` is a good starting point for large datasets, lower to `200000`/`100000` if `PREEXTRACT_FASTQ`/`CORRECT_BARCODES` are slow; `0` disables splitting.
- `min_length` (default 1) and `min_q_score` (default 10) control Nanofilt trimming; `skip_trimming` bypasses it.
- `stranded`: `None`, `forward`, or `reverse`.
- `kmer_size`: minimap2 minimizer k (default 14).
- `save_transcript_secondary_alignment`: true by default — recommended for accurate oarfish EM quantification.
- `retain_introns`: true by default, include intronic reads in counts (important for snRNA-seq).
- `fasta_delimiter`: override the transcript-id delimiter if the transcriptome FASTA is not GENCODE/Ensembl/NCBI-style.
- `skip_dedup`: only meaningful for IsoQuant; oarfish always deduplicates.

## Test data
The `test` profile uses the nf-core `scnanoseq` test-datasets samplesheet (`samplesheet_test.csv`) with ONT FASTQ(s) aligned against a chr21-only human reference (`chr21.fa` + `chr21.gtf`), `barcode_format=10X_3v3`, and `quantifier=isoquant`; resource limits are capped at 4 CPUs / 15 GB / 1 h. The `test_full` profile runs the same pipeline on a full-size samplesheet against the GENCODE v45 GRCh38 primary assembly, transcripts FASTA, and annotation GTF with `quantifier=isoquant,oarfish` and `split_amount=500000`. A successful run produces BLAZE barcode-calling outputs (knee plot, whitelist, putative barcodes), sorted/indexed genome and/or transcriptome BAMs with `CR/CB/UR` tags and deduplicated variants, IsoQuant `*.gene_counts.tsv` / `*.transcript_counts.tsv` and/or an oarfish `barcodes.tsv.gz` + `features.tsv.gz` + `matrix.mtx.gz` triple, Seurat QC CSVs/PNGs, and a combined MultiQC report under `<outdir>/multiqc/`.

## Reference workflow
nf-core/scnanoseq v1.2.2 — https://github.com/nf-core/scnanoseq (Trull A, Worthey EA, Ianov L. *Bioinformatics* 41(9):btaf487, 2025; DOI 10.1093/bioinformatics/btaf487; Zenodo 10.5281/zenodo.13899279).
