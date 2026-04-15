---
name: differential-tf-activity-from-chromatin-and-rnaseq
description: Use when you need to rank transcription factors by differential regulatory
  activity between two or more conditions by integrating bulk RNA-seq counts with
  open-chromatin data (ATAC-seq, DNase-seq, or histone-modification ChIP-seq peaks
  and/or BAMs). Produces a prioritized TF list per contrast using STARE affinities,
  DESeq2 differential expression, and DYNAMITE elastic-net regression.
domain: epigenomics
organism_class:
- vertebrate
- eukaryote
input_data:
- chipseq-peaks-bed
- atacseq-peaks-bed
- chipseq-bam
- rnaseq-counts-matrix
- design-matrix
- reference-fasta
- gtf-annotation
source:
  ecosystem: nf-core
  workflow: nf-core/tfactivity
  url: https://github.com/nf-core/tfactivity
  version: dev
  license: MIT
  slug: tfactivity
tools:
- name: STARE
- name: DESeq2
- name: ChromHMM
- name: ROSE
- name: DYNAMITE
- name: FIMO
- name: SNEEP
- name: bedtools
- name: universalmotif
- name: JASPAR
- name: GTFtools
- name: samtools
- name: TFLink
tags:
- transcription-factor
- tf-activity
- regulatory-genomics
- chromatin
- atac-seq
- chip-seq
- histone-modification
- differential-expression
- enhancer
- motif-scanning
- tf-prioritizer
test_data: []
expected_output: []
---

# Differential transcription factor activity from chromatin accessibility and RNA-seq

## When to use this sketch
- You have two or more biological conditions and want a ranked list of transcription factors whose activity differs between them.
- You already have called peaks (broadPeak/BED) from ATAC-seq, DNase-seq, or histone-modification ChIP-seq, and/or BAM files for histone ChIP-seq (plus controls) from which enhancers should be predicted.
- You also have a bulk RNA-seq raw count matrix (e.g. from nf-core/rnaseq) with a matching condition/batch design matrix; samples in the design must share condition labels with the chromatin samplesheet.
- You are working with a well-annotated vertebrate genome available via iGenomes (e.g. GRCh38, GRCh37, mm10) or for which you can supply FASTA + GTF + motifs (or a JASPAR taxon_id).
- You want outputs that integrate TF-gene binding affinity, differential expression, and a regression-based attribution of expression changes to TFs, not just a motif enrichment table.

## Do not use when
- You only have RNA-seq and no chromatin data — this pipeline requires open-chromatin input; use a pure DE + TF enrichment workflow instead.
- You only have chromatin data and no matched RNA-seq counts — pipeline is hard-gated on `--counts` and `--counts_design`.
- You need per-cell TF activity from scATAC or scRNA — use a single-cell regulon workflow (e.g. SCENIC/chromVAR), not this bulk pipeline.
- You want raw peak calling from FASTQ — run nf-core/atacseq or nf-core/chipseq first, then feed peaks/BAMs here.
- You want to call or annotate non-coding variants on their own — for pure variant effect on TF binding, SNEEP standalone is more appropriate; this pipeline only runs SNEEP as an optional add-on.
- Your organism has no usable motif collection and no JASPAR taxon entry.

## Analysis outline
1. Prepare genome: decompress FASTA/GTF, extract gene ID↔symbol map and gene lengths (GTFtools), index FASTA (samtools faidx).
2. Process expression: combine count tables, compute TPM, filter genes and TFs by min count/TPM, build DESeq2 design, run DESeq2 per pairwise contrast.
3. Prepare motifs: load user motifs or fetch JASPAR by `--taxon_id`, normalize with universalmotif, deduplicate, export to MEME/TRANSFAC/PSEM.
4. Process peaks: clean BEDs; optionally footprint (merge close peaks, subtract overlaps) for histone ChIP; optionally merge replicates by `--merge_samples`/`--min_peak_occurrence`.
5. (Optional) Predict enhancers from BAMs: ChromHMM binarize + learn states, select enhancer/promoter states by histone marks, refine with ROSE (TSS filtering + stitching).
6. Compute TF-gene affinities with STARE (Activity-By-Contact) over a `--window_size` window with optional distance decay; aggregate across replicates and synonyms; compute per-contrast affinity ratios/sums.
7. Run DYNAMITE elastic-net regression linking TF affinities to DE log2FCs with nested cross-validation; filter by minimum regression coefficient.
8. Compute composite TF-TG scores integrating DE, affinity, and DYNAMITE coefficients; run Mann-Whitney U test at `--alpha`; rank TFs and target genes per assay and across assays.
9. (Optional) FIMO motif scanning within candidate regulatory regions for site-level binding predictions.
10. (Optional) SNEEP variant-effect analysis using `--snps` against filtered motifs to flag SNPs that disrupt TF binding in the candidate regions.
11. (Optional) Annotate rankings with TFLink literature-supported TF→target edges when `--tflink_file` (or an iGenomes default) is provided.
12. Emit the interactive HTML `report.zip` with per-TF pages, rankings, expression plots, and parameter record.

## Key parameters
- `--input` (peak samplesheet: `sample,condition,assay,peak_file` with optional `footprinting,include_original,max_peak_gap`) and/or `--input_bam` (`sample,condition,assay,signal,control`).
- `--counts` and `--counts_design` (`sample,condition[,batch][,counts_file]`) — condition labels must match the chromatin samplesheets.
- Reference: `--genome` (iGenomes id, e.g. `GRCh38`, `mm10`) OR the explicit quartet `--fasta --gtf --blacklist --motifs` plus optional `--snps` and `--taxon_id` for JASPAR fallback.
- Expression filtering: `--min_count 50`, `--min_tpm 1`, `--min_count_tf 50`, `--min_tpm_tf 1`, `--expression_aggregation mean`.
- Peak merging: `--merge_samples`, `--min_peak_occurrence 1`.
- STARE: `--window_size 50000`, `--decay true`, `--affinity_aggregation max`.
- ChromHMM (for BAM input): `--chromhmm_states 10`, `--chromhmm_threshold 0.75`, `--chromhmm_enhancer_marks H3K27ac,H3K4me1`, `--chromhmm_promoter_marks H3K4me3`.
- ROSE: `--rose_tss_window 2500`, `--rose_stitching_window 12500`.
- DYNAMITE: `--dynamite_ofolds 3`, `--dynamite_ifolds 6`, `--dynamite_alpha 0.1`, `--dynamite_min_regression 0.1`, `--dynamite_randomize false`.
- Motifs: `--duplicate_motifs remove|merge|keep`, optional `--taxon_id` for JASPAR.
- Ranking: `--alpha 0.05` (Mann-Whitney U significance threshold).
- Optional steps: `--skip_chromhmm`, `--skip_rose`, `--skip_fimo`, `--skip_sneep`; FIMO uses `--fimo_qvalue_threshold 0.05`; SNEEP needs `--sneep_scale_file`, `--sneep_motif_file`, and `--snps`.
- Optional annotation: `--tflink_file` for TFLink-based edge support columns in the final rankings.

## Test data
The bundled `test` profile runs on mouse `mm10` restricted to chromosome 1. Inputs are a peaks samplesheet and a BAM samplesheet from the `nf-core/test-datasets` `tfactivity` branch covering several conditions with histone marks (H3K27ac, H3K4me3, etc.), a gene-id list plus a per-sample RNA-seq counts design, chr1 FASTA and GTF (gzipped), and a chr1 SNPs BED for SNEEP. Running `-profile test,docker` exercises genome prep, DESeq2, motif preparation, peak cleaning + ChromHMM + ROSE, STARE, DYNAMITE, ranking, FIMO, and SNEEP, and is expected to produce the `05_ranking/` tables (per-contrast TF/TG rankings and cross-assay `all.tsv`) and an `08_report/report.zip` interactive HTML report. The `test_full` profile reuses the same config and only swaps in the full BAM samplesheet.

## Reference workflow
nf-core/tfactivity (dev, nf-core template 3.5.1; https://github.com/nf-core/tfactivity). Based on the TF-Prioritizer methodology — Hoffmann et al., *GigaScience* 12, giad026 (2023), https://doi.org/10.1093/gigascience/giad026 — re-implemented as a Nextflow DSL2 pipeline integrating STARE, DESeq2, ChromHMM, ROSE, DYNAMITE, FIMO, and SNEEP.
