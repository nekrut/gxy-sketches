---
name: crispr-targeted-edit-quantification
description: "Use when you have amplicon NGS reads (Illumina or ONT) from a CRISPR-Cas9\
  \ edited locus and want to quantify editing outcomes \u2014 indels, knock-outs,\
  \ knock-ins, base-editing or prime-editing events \u2014 against a reference amplicon\
  \ and a known protospacer. Produces per-sample edit classification and, optionally,\
  \ clonality calls."
domain: amplicon
organism_class:
- eukaryote
input_data:
- short-reads-paired
- reference-fasta
- protospacer-sequence
source:
  ecosystem: nf-core
  workflow: nf-core/crisprseq
  url: https://github.com/nf-core/crisprseq
  version: 2.3.0
  license: MIT
  slug: crisprseq
tools:
- name: pear
  version: 0.9.6
- name: fastqc
  version: 0.12.1
- name: cutadapt
  version: '4.6'
- name: seqtk
  version: '1.4'
- name: minimap2
- name: bwa
- name: bowtie2
- name: samtools
- name: vsearch
- name: medaka
  version: 1.11.3
tags:
- crispr
- cas9
- editing
- indel
- knock-out
- knock-in
- base-editing
- prime-editing
- amplicon
- crispr-a
test_data: []
expected_output: []
---

# CRISPR targeted edit quantification

## When to use this sketch
- You ran targeted amplicon sequencing over a CRISPR-Cas9 edit site and need to measure what fraction of reads are WT, NHEJ indels, MMEJ, or precise HDR/base/prime-edit outcomes.
- You have, per sample, an amplicon reference sequence and the protospacer (guide) sequence, so edits can be localised around the predicted cut site.
- Your assay is one of: gene knock-out (KO), knock-in (KI), base editing (BE) or prime editing (PE).
- Inputs are paired-end Illumina reads, OR long reads (ONT) where UMI-based consensus clustering is desired.
- You want a ready-made CIGAR-parsing edit caller plus optional clonality classification (homologous WT / homologous NHEJ / heterologous NHME).

## Do not use when
- You are running a genome-scale pooled CRISPR screen (KO / CRISPRa / CRISPRi) with an sgRNA library and want gene-level hit calling via MAGeCK, BAGEL2 or DrugZ — use the sibling sketch `crispr-pooled-screen-mageck` (the `--analysis screening` branch of nf-core/crisprseq) instead.
- You need germline or somatic variant calling against a full genome — use a general variant-calling sketch.
- You only need generic FASTQ QC with no edit calling — use a QC-only sketch.
- Your data are whole-genome or exome sequencing rather than targeted amplicons around the edited locus.

## Analysis outline
1. Merge overlapping paired-end reads with `pear` (short-read mode).
2. Read QC with `FastQC`.
3. Adapter and (optionally) overrepresented-sequence trimming with `cutadapt`.
4. Quality filtering with `seqtk`.
5. Optional UMI workflow for long-read / UMI-tagged libraries: extract UMIs, cluster with `vsearch`, pick cluster centroids, build consensus with `minimap2` + `racon` (two rounds), then polish with `medaka`.
6. Align reads to the per-sample amplicon reference with `minimap2` (default), `bwa`, or `bowtie2`; index and sort with `samtools`.
7. Parse CIGAR strings around the protospacer cut site in R to classify each read as WT / insertion / deletion / substitution, tally editing efficiency, and emit edit plots.
8. Optional clonality classification of samples into homologous WT, homologous NHEJ, or heterologous NHME.

## Key parameters
- `--analysis targeted` — selects the targeted edit-calling branch (required).
- `--input samplesheet.csv` — CSV with columns `sample,fastq_1,fastq_2,reference,protospacer,template`; `reference` is the amplicon FASTA sequence, `protospacer` is the guide sequence, `template` is the HDR donor (for KI).
- `--aligner` — one of `minimap2` (default), `bwa`, `bowtie2`.
- `--protospacer` — override the per-sample protospacer with a single sequence for all samples (must be A/C/G/T only).
- `--reference_fasta` — override per-sample amplicon references with a single FASTA.
- `--overrepresented` — enable cutadapt trimming of overrepresented sequences reported by FastQC.
- `--umi_clustering` — enable the UMI extraction / vsearch clustering / racon+medaka consensus path (for UMI-tagged, typically ONT libraries).
- `--umi_bin_size` (default 1) — minimum reads per UMI cluster to keep it.
- `--vsearch_minseqlength` / `--vsearch_maxseqlength` / `--vsearch_id` (defaults 55 / 57 / 0.99) — UMI cluster length window and identity threshold.
- `--medaka_model` — medaka model matching the ONT basecaller used for UMI consensus polishing.
- `--skip_clonality` — disable the homologous WT / NHEJ / heterologous NHME classification step.

## Test data
The pipeline ships a `test` profile (`-profile test`) wiring in a small nf-core test-datasets samplesheet for the `--analysis targeted` branch: a handful of amplicon FASTQ samples, each paired with a short reference amplicon sequence and a protospacer in the samplesheet. Running `nextflow run nf-core/crisprseq -profile test,docker --analysis targeted --outdir results` is expected to complete end-to-end and emit FastQC reports, merged/trimmed FASTQs, per-sample alignments (BAM/BAI), CIGAR-parsed edit-calling tables and plots for each sample, optional clonality classifications, and a final MultiQC report under the chosen `--outdir`.

## Reference workflow
nf-core/crisprseq v2.3.0 (`--analysis targeted`), https://github.com/nf-core/crisprseq — targeted branch is a Nextflow DSL2 re-implementation of CRISPR-Analytics (CRISPR-A; Sanvicente-García et al., PLoS Comput Biol 2023, doi:10.1371/journal.pcbi.1011137).
