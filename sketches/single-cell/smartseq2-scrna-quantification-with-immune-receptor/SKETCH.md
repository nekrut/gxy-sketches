---
name: smartseq2-scrna-quantification-with-immune-receptor
description: Use when you need to preprocess plate-based Smart-seq2 single-cell RNA-seq
  data (one paired-end FASTQ pair per cell) into per-cell gene expression matrices,
  with optional reconstruction of T-cell and B-cell receptor sequences. Targets human
  or mouse full-length scRNA-seq, not droplet 10x data.
domain: single-cell
organism_class:
- vertebrate
- diploid
input_data:
- short-reads-paired
- reference-fasta
- gtf-annotation
source:
  ecosystem: nf-core
  workflow: nf-core/smartseq2
  url: https://github.com/nf-core/smartseq2
  version: dev
  license: MIT
tools:
- fastqc
- star
- rsem
- featurecounts
- tracer
- bracer
- multiqc
tags:
- single-cell
- scrna-seq
- smart-seq2
- full-length
- tcr
- bcr
- plate-based
test_data: []
expected_output: []
---

# Smart-seq2 scRNA-seq quantification with TCR/BCR reconstruction

## When to use this sketch
- Plate-based, full-length single-cell RNA-seq produced with the Smart-seq2 protocol (Picelli et al. 2014), where each well/cell is delivered as its own paired-end FASTQ pair.
- Goal is a per-cell gene expression matrix (TPM and/or raw counts) plus standard QC.
- Human (`Hsap`) or mouse (`Mmus`) samples where you also want to reconstruct T-cell receptor (TraCeR) and/or B-cell receptor (BraCeR) sequences from the same reads, e.g. immune repertoire studies on sorted T/B cells.
- You have, or can build, a STAR index and RSEM reference from a genome FASTA + GTF (iGenomes keys like `GRCh37`, `GRCm38` are supported).

## Do not use when
- Reads come from a droplet-based protocol (10x Genomics, Drop-seq, inDrops) — use a droplet scRNA-seq sketch (Cell Ranger / STARsolo / Alevin) instead.
- You need trajectory inference, clustering, or downstream Seurat/Scanpy analysis — this sketch stops at the expression matrix.
- The organism is not human or mouse *and* you need TCR/BCR reconstruction (TraCeR/BraCeR custom references are not wired through the pipeline; use `--skip_tracer --skip_bracer` or a different workflow).
- You need variant calling from RNA-seq — see an RNA-seq variant-calling sketch.
- Bulk RNA-seq — use a bulk RNA-seq quantification sketch (e.g. nf-core/rnaseq).

## Analysis outline
1. **Input staging**: one paired-end FASTQ pair per cell, provided via `--reads '*_R{1,2}.fastq.gz'` (glob expands to per-cell channels).
2. **Read QC**: FastQC per cell, aggregated by MultiQC at the end.
3. **Reference preparation**: build STAR index and RSEM reference from `--fasta` + `--gtf` (or reuse prebuilt `--star_index` / `--rsem_ref`; iGenomes via `--genome`).
4. **Alignment**: STAR aligns each cell to the genome, producing coordinate-sorted and transcriptome BAMs.
5. **Quantification**: RSEM computes TPM per gene per cell from the transcriptome BAM; featureCounts computes raw counts per gene per cell from the genome BAM. Both matrices are merged across cells into `resultTPM.txt` and `resultCOUNT.txt`.
6. **TCR reconstruction**: TraCeR assembles T-cell receptor chains per cell, producing `filtered_TCR_summary/cell_data.csv`.
7. **BCR reconstruction**: BraCeR assembles B-cell receptor chains per cell, producing `filtered_BCR_summary/IMGT_gapped_db.tab`.
8. **Reporting**: MultiQC aggregates FastQC, STAR, RSEM, and featureCounts statistics into a single HTML report.

## Key parameters
- `--reads`: glob with `{1,2}` notation, one pair per cell (e.g. `'data/*_R{1,2}.fastq.gz'`).
- `--species`: `Hsap` (default) or `Mmus` — controls the TraCeR/BraCeR reference.
- `--genome`: iGenomes key (e.g. `GRCh37`, `GRCm38`) — alternative to `--fasta`/`--gtf`.
- `--fasta`, `--gtf`: explicit genome FASTA and annotation when not using iGenomes.
- `--star_index`, `--rsem_ref`: reuse prebuilt indices to skip index construction.
- `--save_reference`: persist generated indices for future runs.
- `--skip_fastqc`, `--skip_transcriptomics`, `--skip_fc`, `--skip_rsem`, `--skip_tracer`, `--skip_bracer`: toggle individual stages (e.g. set `--skip_tracer --skip_bracer` for non-immune cells).
- `-profile`: `docker`, `singularity`, `conda`, or `test`; combine with an institutional profile as needed.

## Test data
The `test` profile supplies two paired-end FASTQ pairs from the nf-core test-datasets `smartseq2` branch: one labelled `Bcell` (`b-cell1_1.fastq.gz` / `b-cell1_2.fastq.gz`) and one labelled `Tcell` (`t-cell1_1.fastq` / `t-cell1_2.fastq`), together with a tiny `genome.fa` and matching `genes.gtf` from the test-datasets reference directory. The profile caps resources at 2 CPUs and 6 GB RAM and sets `skip_tracer = true` and `skip_bracer = true`, so running `nextflow run nf-core/smartseq2 -profile test,docker` exercises FastQC, STAR index build, STAR alignment, RSEM, featureCounts, and MultiQC end-to-end. Expected outputs are a merged `results/RSEM/resultTPM.txt`, `results/featureCounts/resultCOUNT.txt`, per-cell STAR BAMs and logs under `results/STAR/{Bcell,Tcell}/`, FastQC reports under `results/fastqc/`, and a `results/multiqc/multiqc_report.html`.

## Reference workflow
nf-core/smartseq2 (`dev` branch, https://github.com/nf-core/smartseq2), MIT-licensed. Method references: Picelli et al., *Nat. Protoc.* 2014 (Smart-seq2); Dobin et al. 2013 (STAR); Li & Dewey 2011 (RSEM); Liao et al. 2014 (featureCounts); Stubbington et al. 2016 (TraCeR); Lindeman et al. 2018 (BraCeR).
