---
name: alternative-splicing-rnaseq
description: Use when you need to detect and quantify alternative splicing from bulk
  RNA-seq reads against an annotated reference genome (human, mouse, or other model
  organism). Covers differential exon usage (DEXSeq/edgeR), differential transcript
  usage (DRIMSeq+DEXSeq), and event-based splicing analysis (rMATS, SUPPA2) from paired
  or single-end Illumina FASTQ.
domain: rna-seq
organism_class:
- eukaryote
- vertebrate
input_data:
- short-reads-paired
- short-reads-single
- reference-fasta
- gtf-annotation
source:
  ecosystem: nf-core
  workflow: nf-core/rnasplice
  url: https://github.com/nf-core/rnasplice
  version: 1.0.4
  license: MIT
tools:
- fastqc
- trim-galore
- star
- salmon
- featurecounts
- htseq
- dexseq
- edger
- drimseq
- rmats
- suppa2
- tximport
- multiqc
tags:
- rna-seq
- splicing
- alternative-splicing
- dtu
- deu
- rmats
- suppa
- dexseq
test_data: []
expected_output: []
---

# Alternative splicing analysis from bulk RNA-seq

## When to use this sketch
- You have bulk RNA-seq short reads (FASTQ, BAM, or existing Salmon quants) from an organism with a reference genome + GTF annotation.
- The biological question is about **splicing**: differential exon usage (DEU), differential transcript usage (DTU), or specific local splicing events (SE, A5/A3, MXE, RI, AF/AL).
- You have at least two conditions with replicates and want contrast-wise statistics.
- You want a single pipeline that can combine multiple orthogonal splicing methods (rMATS + SUPPA2 + DEXSeq + edgeR) on the same samples.

## Do not use when
- You only need gene-level differential expression — use a standard bulk RNA-seq DGE sketch (e.g. nf-core/rnaseq) instead.
- Organism has no reference genome/annotation — use a de novo transcriptome assembly sketch.
- Long-read (Iso-Seq / ONT direct-RNA) isoform discovery — use a long-read isoform sketch instead.
- Single-cell RNA-seq splicing — use a dedicated scRNA splicing sketch.
- Prokaryotes / organisms without meaningful alternative splicing.

## Analysis outline
1. Merge re-sequenced FASTQ files per sample (`cat`).
2. Raw read QC (`FastQC`).
3. Adapter and quality trimming (`Trim Galore`).
4. Splice-aware alignment to the genome (`STAR`), producing genome and transcriptome BAMs.
5. Quantification — one or more of:
   - Transcript quantification via `STAR` → `Salmon` (required for DTU + SUPPA2).
   - Exon counts via `featureCounts` (required for edgeR DEU).
   - Exon counts via `HTSeq`/DEXSeq-count script (required for DEXSeq DEU).
   - Optional pseudo-alignment directly with `Salmon` (skips STAR).
6. BAM sort/index (`samtools`) and optional bigWig coverage (`bedtools` + `bedGraphToBigWig`).
7. Differential Exon Usage: `DEXSeq` (from HTSeq counts) and/or `edgeR::diffSpliceDGE` (from featureCounts).
8. Differential Transcript Usage: `tximport` → `DRIMSeq::dmFilter` → `DEXSeq` → `stageR` stage-wise adjustment.
9. Event-based splicing: `rMATS` on genome BAMs (per contrast) and `SUPPA2` generateEvents → psiPerEvent → diffSplice → clusterEvents on Salmon TPMs.
10. Aggregate QC with `MultiQC`.

## Key parameters
- `--input samplesheet.csv` — columns: `sample,fastq_1,fastq_2,strandedness,condition`. Rows sharing `sample` are merged as technical replicates. `strandedness` ∈ {`unstranded`,`forward`,`reverse`}.
- `--contrasts contrastsheet.csv` — columns: `contrast,treatment,control`; drives all pairwise DEU/DTU/rMATS/SUPPA comparisons.
- `--source {fastq|genome_bam|transcriptome_bam|salmon_results}` — entry point; `genome_bam` unlocks DEU + rMATS, `transcriptome_bam`/`salmon_results` unlock DTU + SUPPA.
- `--genome GRCh37` (iGenomes) **or** `--fasta` + `--gtf` (mandatory pair). Use `--gencode` if annotation is GENCODE. `--gff_dexseq` to supply a pre-flattened DEXSeq GFF.
- `--aligner {star|star_salmon}` (default `star`) and optional `--pseudo_aligner salmon`; `--skip_alignment` to run Salmon alone.
- Analysis toggles (all off by default except SUPPA): `--dexseq_exon`, `--edger_exon`, `--dexseq_dtu`, `--rmats`, `--suppa`, `--sashimi_plot`.
- DEXSeq DEU: `--alignment_quality 10`, `--aggregation true`, `--n_dexseq_plot 10`.
- DEXSeq DTU: `--dtu_txi {dtuScaledTPM|scaledTPM}`, DRIMSeq filters `--min_samps_gene_expr`, `--min_samps_feature_expr`, `--min_gene_expr 10`, `--min_feature_expr 10`, `--min_feature_prop 0.1`.
- rMATS: `--rmats_read_len` (must match library), `--rmats_paired_stats true` (2 conditions only), `--rmats_splice_diff_cutoff 0.0001`, `--rmats_novel_splice_site`, `--rmats_min_intron_len 50`, `--rmats_max_exon_len 500`. All samples must share strandedness and read type.
- SUPPA2: `--generateevents_event_type "SE SS MX RI FL"`, `--generateevents_pool_genes true`, `--diffsplice_method {empirical|classical}`, `--diffsplice_alpha 0.05`, `--clusterevents_dpsithreshold 0.05`, `--clusterevents_method {DBSCAN|OPTICS}`.

## Test data
The bundled `test` profile uses a tiny human chrX subset from `nf-core/test-datasets` (branch `rnasplice`): a few paired-end FASTQ samples declared in `samplesheet.csv` with a matching `contrastsheet.csv`, plus `reference/X.fa.gz` and `reference/genes_chrX.gtf` as the reference FASTA and GTF. Running `-profile test` with capped resources (2 CPUs, 6 GB, 6 h) exercises FASTQ → STAR → Salmon → SUPPA2 end-to-end, produces a MultiQC report, Salmon quant tables, and SUPPA event/PSI/dpsi outputs for the declared contrast; enabling `--dexseq_exon`, `--edger_exon`, `--dexseq_dtu`, or `--rmats` additionally yields per-contrast DEXSeq/edgeR/rMATS result tables. A `test_full` profile runs the same workflow on GRCh37 iGenomes with the full samplesheet.

## Reference workflow
nf-core/rnasplice v1.0.4 — https://github.com/nf-core/rnasplice (DOI 10.5281/zenodo.8424632).
