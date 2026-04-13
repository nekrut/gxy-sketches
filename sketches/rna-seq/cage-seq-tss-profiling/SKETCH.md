---
name: cage-seq-tss-profiling
description: Use when you need to identify and quantify transcription start sites
  (TSS) from CAGE-seq (Cap Analysis of Gene Expression) single-end short-read data,
  producing CTSS BED files, paraclu tag clusters, and per-sample count tables against
  a reference genome.
domain: rna-seq
organism_class:
- eukaryote
input_data:
- short-reads-single
- reference-fasta
- gtf-annotation
source:
  ecosystem: nf-core
  workflow: nf-core/cageseq
  url: https://github.com/nf-core/cageseq
  version: 1.0.2
  license: MIT
tools:
- fastqc
- cutadapt
- sortmerna
- star
- bowtie1
- samtools
- paraclu
- bedtools
- ucsc-tools
- rseqc
- multiqc
tags:
- cage-seq
- tss
- transcription-start-site
- ctss
- paraclu
- ecop15
- 5-prime
- promoter
test_data: []
expected_output: []
---

# CAGE-seq transcription start site profiling

## When to use this sketch
- Input is CAGE-seq (Cap Analysis of Gene Expression) single-end FASTQ data, typically produced with an EcoP15I-based protocol.
- Goal is to map 5' cap sites to a reference genome and obtain CAGE tag start sites (CTSS), clustered tag clusters, and a per-sample count table for downstream promoter/TSS analysis.
- You need CAGE-specific preprocessing: EcoP15 binding site removal at 5', linker trimming at 3', leading-G correction, and optional sequencing artifact trimming.
- Eukaryotic reference genome with a GTF annotation is available (e.g. human GRCh38, mouse GRCm38).
- Optional rRNA depletion in silico via SortMeRNA is desired.

## Do not use when
- Data are standard bulk RNA-seq / mRNA-seq without CAGE cap trapping — use a conventional rna-seq quantification sketch instead.
- You are profiling 3' ends (e.g. QuantSeq, 3'-Tag-seq, PAS-seq) — needs a 3'-end sketch, not CAGE.
- Single-cell or spatial transcriptomics libraries — use a single-cell sketch.
- You only need differential expression on gene models; CAGE-seq here clusters at the CTSS level, not gene level.
- Long-read (ONT/PacBio) full-length cDNA data — use a long-read transcript sketch.

## Analysis outline
1. Raw read QC with FastQC (skippable via `--skip_initial_fastqc`).
2. 5' EcoP15 site + 3' linker trimming with cutadapt; optional 5' leading-G removal and 5'/3' artifact removal (also cutadapt).
3. Post-trim FastQC.
4. Optional rRNA filtering with SortMeRNA against the bundled rRNA database manifest.
5. Alignment to the reference genome with STAR (default) or bowtie1, selected via `--aligner`; index built on the fly from `--fasta` if not supplied.
6. samtools stats / flagstat on the alignments.
7. CTSS generation: `bin/make_ctss.sh` produces a per-sample BED6 of 1 bp summed CAGE tag starts, optionally a bigWig (`--bigwig`).
8. Tag clustering: paraclu run on the pooled CTSS with a minimum cluster size and TPM threshold, simplified into `ctss_all_clustered_simplified.bed`.
9. Count table generation: intersect per-sample CTSS with paraclu clusters into `count_table.tsv` (rows=clusters, columns=samples).
10. CTSS QC with RSeQC `read_distribution.py` across genomic features.
11. Aggregate QC with MultiQC.

## Key parameters
- `--input`: glob of single-end FASTQ files (e.g. `'*_R1.fastq.gz'`).
- `--aligner`: `star` (default) or `bowtie1`.
- `--fasta` + `--gtf`: reference genome and annotation, or `--genome <iGenomes_key>` (e.g. `GRCh38`). Precomputed `--star_index` / `--bowtie_index` are accepted.
- `--min_aln_length`: minimum aligned bp per read to retain (default 15).
- Trimming toggles: `--trim_ecop`, `--trim_linker`, `--trim_5g`, `--trim_artifacts` (all on by default).
- `--eco_site`: EcoP15 5' site, default `CAGCAG`.
- `--linker_seq`: 3' linker, default `TCGTATGCCGTCTTC`.
- `--artifacts_5end` / `--artifacts_3end`: FASTA files of artifact sequences (ship with the pipeline).
- `--remove_ribo_rna` + `--ribo_database_manifest`: enable SortMeRNA rRNA filtering.
- paraclu: `--min_cluster` (default 30) and `--tpm_cluster_threshold` (default 0.2).
- `--bigwig`: also emit CTSS bigWigs alongside BED files.
- Skip switches: `--skip_initial_fastqc`, `--skip_trimming`, `--skip_trimming_fastqc`, `--skip_alignment`, `--skip_samtools_stats`, `--skip_ctss_generation`, `--skip_ctss_qc`.

## Test data
The bundled `test` profile runs two single-end CAGE FASTQs (`cage1.fastq.gz`, `cage2.fastq.gz`) from the nf-core/test-datasets `cageseq` branch against a chromosome-subset reference (`chr_sub.fasta` + `chr_sub.gtf`). Running `-profile test,docker` is expected to produce, per sample, cutadapt-trimmed FASTQs, STAR alignments, a `<sample>.ctss.bed`, a pooled `ctss_all_clustered_simplified.bed` from paraclu, a combined `count_table.tsv`, RSeQC read-distribution reports, and a single MultiQC HTML summarising FastQC, cutadapt, STAR, samtools, SortMeRNA (if enabled) and RSeQC. The `test_full` profile uses the same inputs with unrestricted resources.

## Reference workflow
nf-core/cageseq v1.0.2 (https://github.com/nf-core/cageseq, DOI 10.5281/zenodo.4095105, MIT).
