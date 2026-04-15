---
name: ribosome-profiling-orf-translation
description: Use when you need to analyze ribosome profiling (Ribo-seq) data to identify
  translated ORFs, determine P-site offsets, and assess translational efficiency in
  eukaryotes. Supports paired Ribo-seq + RNA-seq designs for translational efficiency
  analysis with anota2seq. Handles short-read Illumina Ribo-seq libraries against
  a reference genome + GTF.
domain: rna-seq
organism_class:
- eukaryote
input_data:
- short-reads-single
- reference-fasta
- gtf-annotation
source:
  ecosystem: nf-core
  workflow: nf-core/riboseq
  url: https://github.com/nf-core/riboseq
  version: 1.2.0
  license: MIT
  slug: riboseq
tools:
- name: fastqc
  version: 0.12.1
- name: trimgalore
- name: fastp
- name: umi-tools
- name: sortmerna
  version: '1.21'
- name: star
- name: salmon
- name: samtools
- name: ribotish
- name: ribotricer
- name: ribowaltz
  version: '2.0'
- name: anota2seq
  version: 1.24.0
- name: multiqc
tags:
- riboseq
- ribosome-profiling
- translation
- orf-prediction
- p-site
- translational-efficiency
- tiseq
test_data: []
expected_output: []
---

# Ribosome profiling: ORF detection, P-site QC, and translational efficiency

## When to use this sketch
- Input is Ribo-seq (ribosome footprinting) data, typically single-end short Illumina reads from RNase-digested, monosome-purified RNA.
- You want to QC footprint periodicity, determine P-site offsets per read length, and identify translated ORFs or translation initiation sites (TIS).
- Your reference is a eukaryotic genome with a GTF annotation (Ensembl or GENCODE); human/mouse are typical but any annotated transcriptome works.
- You optionally have matched RNA-seq and Ribo-seq libraries from two treatment groups and want a translational efficiency (TE) analysis distinguishing transcriptional, translational, and buffering regulation.
- Samples may use UMIs (e.g., McGlincy/Ingolia-style Ribo-seq kits) — the pipeline handles UMI extraction and post-alignment deduplication.
- TI-seq (harringtonine/LTM) libraries can be marked `type: tiseq` and fed to Ribo-TISH predict for initiation-site calling.

## Do not use when
- You have plain bulk RNA-seq with no ribosome footprinting — use a standard `rna-seq-bulk-quantification` sketch (nf-core/rnaseq) instead.
- You want differential gene expression on Ribo-seq counts alone without P-site / ORF analysis — a generic RNA-seq DE sketch is simpler.
- You are doing single-cell ribosome profiling or long-read native RNA translation assays — out of scope.
- You need CLIP-seq / RIP-seq style peak calling — different analysis class.
- Your organism is a prokaryote without spliced transcript annotation — Ribo-TISH and riboWaltz assume eukaryotic transcript models.

## Analysis outline
1. Concatenate re-sequenced FASTQs per sample (`cat`) and lint with `fq lint`.
2. Sub-sample and auto-infer strandedness via `Salmon` quant (when `strandedness: auto`).
3. Raw read QC with `FastQC`.
4. Optional UMI extraction with `UMI-tools extract` (or skip if UMIs already in read name).
5. Adapter/quality trimming with `Trim Galore!` (default) or `fastp`.
6. Optional contaminant binning with `BBSplit` and rRNA removal with `SortMeRNA` (on by default).
7. Spliced genome + transcriptome alignment with `STAR` (outputs `Aligned.toTranscriptome.out.bam`).
8. Sort/index BAMs and compute stats with `SAMtools`; optional UMI dedup via `umi_tools dedup` or `UMICollapse`.
9. Ribo-seq QC and P-site offset estimation with `Ribo-TISH quality` and `riboWaltz` (transcriptome BAMs).
10. Translated-ORF prediction with `Ribo-TISH predict` (per-sample and all-samples) and candidate-ORF detection with `Ribotricer prepare-orfs` + `detect-orfs`.
11. Transcript/gene quantification with `Salmon` from transcriptome BAMs; tximport-style merged count/TPM matrices.
12. Optional translational efficiency analysis with `anota2seq` on matched Ribo-seq/RNA-seq contrasts.
13. Aggregate all logs into a single `MultiQC` report.

## Key parameters
- `input`: samplesheet CSV with columns `sample,fastq_1,fastq_2,strandedness,type` where `type` is `riboseq`, `tiseq`, or `rnaseq`.
- `fasta`, `gtf`: mandatory reference genome + annotation (prefer Ensembl/GENCODE over iGenomes); set `--gencode` for GENCODE GTFs.
- `contrasts`: CSV with `id,variable,reference,target,batch,pair` — required to trigger anota2seq TE analysis.
- `trimmer`: `trimgalore` (default) or `fastp`; extra flags via `extra_trimgalore_args` / `extra_fastp_args`.
- `with_umi`: enable UMI dedup; pair with `umitools_bc_pattern` (e.g., `NNNNNN`) and optionally `skip_umi_extract` if UMIs are already in the read name.
- `remove_ribo_rna`: `true` by default; uses `ribo_database_manifest` (SortMeRNA SILVA defaults).
- `aligner`: `star` (only option); tune with `extra_star_align_args` (e.g., `--alignEndsType EndToEnd --outFilterMismatchNmax 2` for short footprints).
- `extra_ribowaltz_args`: e.g., `"--length_range 27:31 --periodicity_threshold 40 --extremity 5end --start_nts 45 --stop_nts 24"` for classic 28–30 nt footprints.
- `extra_ribotish_quality_args`, `extra_ribotish_predict_args`, `extra_ribotricer_prepareorfs_args`, `extra_ribotricer_detectorfs_args`, `extra_anota2seq_run_args`: pass-throughs for fine-tuning each downstream tool.
- `min_trimmed_reads` (default 10000) and `min_mapped_reads` (default 5%): sample-drop thresholds — lower for sparse Ribo-seq test data.
- `skip_ribotish` / `skip_ribotricer` / `skip_ribowaltz`: toggle individual downstream modules.
- `stranded_threshold` (0.8) / `unstranded_threshold` (0.1): strandedness inference cutoffs.

## Test data
The `test` profile runs a minimal human chr20 subset: a samplesheet of paired Ribo-seq and RNA-seq FASTQs from SRA accessions SRX11780879–SRX11780890 (PM2.5 control vs. treated study), restricted to chr20, plus a chr20-only GRCh38 FASTA and Ensembl 111 chr20 GTF from `nf-core/test-datasets`. A `contrasts.csv` with a single `treated_vs_control` row (variable `treatment`, pairing column `pair`) drives an anota2seq TE run. `min_trimmed_reads` is dropped to 1000 and Ribotricer is skipped. Expected outputs include per-sample STAR genome/transcriptome BAMs, Ribo-TISH `*_qual.pdf`/`*_pred.txt`, riboWaltz P-site TSVs and QC PDFs, Salmon merged gene/transcript count and TPM matrices, anota2seq `*.translation.anota2seq.results.tsv` plus fold-change plot, and a consolidated `multiqc_report.html`. The `test_full` profile swaps in the full primary-assembly GRCh38 FASTA and Ensembl 111 GTF for the same sample set.

## Reference workflow
nf-core/riboseq v1.2.0 (https://github.com/nf-core/riboseq), MIT license. Downstream Ribo-seq logic adapted from Ribo-TISH, Ribotricer, riboWaltz, and anota2seq; preprocessing borrows from nf-core/rnaseq.
