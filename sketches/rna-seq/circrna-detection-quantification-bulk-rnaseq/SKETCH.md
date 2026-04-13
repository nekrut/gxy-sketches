---
name: circrna-detection-quantification-bulk-rnaseq
description: Use when you need to detect, annotate and quantify circular RNAs (circRNAs)
  from bulk total RNA-seq short reads against a reference genome with GTF annotation,
  optionally predicting miRNA binding sites and running differential expression on
  circRNAs. Targets organisms with a reference (human, mouse, C. elegans, etc.).
domain: rna-seq
organism_class:
- eukaryote
input_data:
- short-reads-paired
- short-reads-single
- reference-fasta
- reference-gtf
- mature-mirna-fasta-optional
- phenotype-csv-optional
source:
  ecosystem: nf-core
  workflow: nf-core/circrna
  url: https://github.com/nf-core/circrna
  version: dev
  license: MIT
tools:
- fastqc
- trim-galore
- star
- circexplorer2
- circrna_finder
- ciriquant
- dcc
- find_circ
- mapsplice
- segemehl
- psirc-quant
- miranda
- targetscan
- circtest
- multiqc
tags:
- circrna
- back-splice-junction
- bsj
- total-rna
- non-coding-rna
- mirna-target
- nf-core
test_data: []
expected_output: []
---

# circRNA detection and quantification from bulk RNA-seq

## When to use this sketch
- The user has total RNA-seq (rRNA-depleted, ideally not poly-A selected) FASTQ files and wants to identify circular RNAs via back-splice junctions (BSJs).
- The organism has a reference genome FASTA and a GTF annotation with `gene_id`, `transcript_id`, `gene_name` attributes.
- The question is about circRNA discovery, quantification of linear + circular transcripts jointly, circRNA annotation against a GTF (and optionally database BED files), or circRNA differential expression across conditions.
- The user wants consensus BSJ calls across multiple circRNA callers (CIRCexplorer2, CIRIquant, DCC, find_circ, circRNA_finder, MapSplice, Segemehl) with configurable `min_tools` voting.
- They optionally want miRNA binding-site prediction on detected circRNAs given a `mature.fa` (e.g. miRBase), and optionally miRNA-transcript correlation given a miRNA expression TSV.

## Do not use when
- The user only wants standard linear mRNA expression / DE analysis with no interest in circRNAs — use a conventional bulk RNA-seq sketch (nf-core/rnaseq).
- Input is single-cell RNA-seq (10x, Smart-seq) — circRNA callers here assume bulk libraries.
- Input is long-read (ONT/PacBio) cDNA — this pipeline's BSJ callers are short-read aligners; long-read circRNA detection is a separate class.
- The user needs small RNA / miRNA quantification itself from sRNA-seq — use nf-core/smrnaseq and feed its output here via `--mirna_expression`.
- Organism has no reference genome — circRNA calling here requires a FASTA + GTF.

## Analysis outline
1. Raw read QC with FastQC.
2. Adapter/quality trimming with Trim Galore! (skippable via `--skip_trimming`).
3. Reference prep: build indices (STAR, BWA, Bowtie/Bowtie2, HISAT2, Segemehl as needed), clean FASTA headers, filter GTF to chromosomes in FASTA.
4. BSJ detection — run one or more of: CIRCexplorer2 + circRNA_finder + DCC (all off a STAR 2-pass alignment), CIRIquant (HISAT2+BWA+CIRI2), find_circ (Bowtie2), MapSplice, Segemehl. Tools selected via `--tools`.
5. Unify each tool's output to BED6, filter by `bsj_reads`, then merge per-sample across tools and keep BSJs supported by at least `min_tools` callers.
6. Annotate BSJs against the GTF (intron/exon/EI-circRNA classification) and any user-supplied database BEDs via `--annotation`.
7. Build a combined circular + linear transcriptome FASTA/GTF, then jointly quantify with psirc-quant (kallisto-based) controlled by `--quantification_tools` and `--bootstrap_samples`; aggregate with tximeta/tximport into gene/tx count & TPM matrices and a merged SummarizedExperiment RDS.
8. (Optional, needs `--mature`) Predict miRNA binding sites on circRNA sequences with miRanda and TargetScan, majority-vote across tools via `--mirna_min_tools`.
9. (Optional, needs `--mirna_expression`) Normalize/filter miRNA counts and compute miRNA–transcript correlations (`--mirna_correlation` pearson|spearman).
10. (Optional, needs `--phenotype`) Run CircTest for differential circRNA expression, with `condition` as the response and other phenotype columns as covariates.
11. Aggregate QC and tool logs into a MultiQC report.

## Key parameters
- `--input` samplesheet CSV with columns `sample,fastq_1,fastq_2[,strandedness]`; rows with identical `sample` are concatenated across lanes.
- `--fasta`, `--gtf` reference genome and annotation; set `--genome null --igenomes_ignore` when not using iGenomes.
- `--tools` comma list of BSJ callers from {ciri, circexplorer2, find_circ, circrna_finder, mapsplice, circtools, segemehl, psirc}. Default `circexplorer2`.
- `--bsj_reads` minimum reads spanning a BSJ for it to be kept (default 1; use ≥2 for real data).
- `--min_tools` minimum number of callers that must agree on a BSJ (default 1 = union; raise for stricter consensus).
- `--min_samples` minimum samples a BSJ must appear in.
- `--max_shift` / `--consider_strand` control when two BSJs are collapsed as equivalent.
- `--exons_only` (default true) restrict circRNA sequence extraction to exons — important for single-end data.
- `--quantification_tools` default `ciriquant,psirc,sum,max`; `--bootstrap_samples` (psirc) default 30.
- `--mature` FASTA of mature miRNAs — presence gates the whole miRNA sub-workflow.
- `--mirna_expression` TSV of miRNA counts; `--mirna_min_sample_percentage` (0.2), `--mirna_min_reads` (5), `--mirna_tools` (miranda,targetscan), `--mirna_min_tools` (1), `--mirna_correlation` (pearson|spearman).
- `--phenotype` CSV with a `sample` column matching the samplesheet and a `condition` column — required to trigger CircTest.
- `--annotation` CSV of BED database files (`name,file,min_overlap`) for extra annotation sources.
- STAR knobs that matter for circRNA sensitivity: `--chimSegmentMin` (default 10, must be >0), `--chimJunctionOverhangMin`, `--sjdboverhang`, `--limitSjdbInsertNsj`.
- `--skip_trimming`, `--save_reference`, `--save_intermediates` for common operational tweaks.
- `-profile docker|singularity|conda|...` plus `--outdir`; parameters must come via CLI or `-params-file`, never `-c`.

## Test data
The pipeline ships a minimal `test` profile (`conf/test.config`) that pulls a down-sampled *C. elegans* chromosome I reference (`reference/chrI.fa` + `reference/chrI.gtf`) and a tiny samplesheet (`samples.csv`) from the nf-core test-datasets `circrna` branch, together with a `phenotype.csv` and a mature miRNA FASTA (`reference/mature.fa`). It runs with `--tools circexplorer2`, `--bsj_reads 2`, trimming enabled, and caps resources at 4 CPUs / 6 GB / 1 h. A successful run should produce FastQC/TrimGalore reports, STAR 2-pass alignments, CIRCexplorer2 BSJ calls with per-sample annotated BED/GTF/FASTA under `bsj_detection/`, psirc-quant linear+circular count matrices and a merged SummarizedExperiment under `quantification/combined/`, miRanda/TargetScan binding-site tables under `mirna_prediction/` (gated by `--mature`), CircTest output under `statistical_tests/circtest/` (gated by `--phenotype`), and a MultiQC HTML report.

## Reference workflow
nf-core/circrna (dev, nf-core template 3.5.1; requires Nextflow ≥25.04.0). Originally by Barry Digby; see Digby et al., *BMC Bioinformatics* 24, 27 (2023), doi:10.1186/s12859-022-05125-8. Source: https://github.com/nf-core/circrna.
