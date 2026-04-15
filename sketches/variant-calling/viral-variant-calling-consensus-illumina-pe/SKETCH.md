---
name: viral-variant-calling-consensus-illumina-pe
description: Use when you need to call SNVs/indels and build per-sample consensus
  genomes for a batch of Illumina paired-end sequenced non-segmented viral isolates
  (e.g. Morbilliviruses, SARS-CoV-2, measles) against a known reference. Handles both
  shotgun and ampliconic (primer-scheme) data and annotates variant effects with SnpEff.
domain: variant-calling
organism_class:
- viral
input_data:
- short-reads-paired
- reference-fasta
- reference-gtf
- primer-bed-optional
source:
  ecosystem: iwc
  workflow: Variant calling and consensus construction from paired end short read
    data of non-segmented viral genomes
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/virology/generic-non-segmented-viral-variant-calling
  version: '0.2'
  license: AGPL-3.0-or-later
  slug: virology--generic-non-segmented-viral-variant-calling
tools:
- name: fastp
  version: 1.0.1+galaxy3
- name: bwa-mem
  version: 0.7.19
- name: samtools
  version: 2.0.8
- name: lofreq
  version: 2.1.5+galaxy0
- name: ivar
  version: 1.4.4+galaxy1
- name: snpeff
  version: 5.2+galaxy1
- name: snpsift
  version: 4.3+t.galaxy0
- name: qualimap
  version: 2.3+galaxy0
- name: multiqc
  version: 1.24.1+galaxy0
tags:
- virology
- consensus
- amplicon
- ARTIC
- ivar
- snpeff
- illumina
- non-segmented
test_data: []
expected_output: []
---

# Viral variant calling and consensus from Illumina PE reads (non-segmented genomes)

## When to use this sketch
- You have a batch of Illumina paired-end FASTQ files, one pair per viral isolate, and want per-sample variant calls plus consensus genomes.
- The virus has a simple, stable, non-segmented genome (e.g. Morbilliviruses, SARS-CoV-2, measles, mumps, RSV).
- A trusted reference FASTA and matching GTF annotation are available for the target virus.
- Data is either untargeted shotgun or tiled-amplicon (ARTIC-style) sequencing; if amplicon, a BED primer scheme is available.
- You want SnpEff functional annotation of variants and an aggregated MultiQC QC report across samples.

## Do not use when
- Reads are long-read ONT/PacBio — use a long-read viral variant/consensus sketch instead.
- The virus has a segmented genome (e.g. influenza, Lassa, rotavirus) — use a segmented-virus sketch that handles per-segment references.
- You need de novo assembly rather than reference-based consensus — use a viral assembly sketch.
- You are doing host/eukaryotic diploid or polyploid variant calling — use a germline variant-calling sketch (bcftools/GATK).
- Your virus uses ribosomal slippage / polymerase stuttering to produce multiple translation products that must all be annotated — SnpEff annotation in this workflow will be incomplete.
- Single-end reads only — the workflow requires paired-end input and enforces proper-pair filtering.

## Analysis outline
1. Read QC and adapter/quality trimming with **fastp** on the paired collection.
2. Map trimmed reads to the reference FASTA with **bwa mem** (coordinate-sorted BAM, auto read groups).
3. Filter BAM with **samtools view** to keep only properly paired reads with MAPQ > 20.
4. Indel-aware realignment of filtered reads with **lofreq viterbi**.
5. If a primer BED is provided: trim primers and drop reads extending beyond amplicon boundaries with **ivar trim** (conditional step via map/pick-parameter helpers).
6. Call variants with **ivar variants** against the reference, emitting PASS-only VCF.
7. Build per-sample consensus with **ivar consensus** in parallel to variant calling.
8. Build a custom SnpEff database from the reference FASTA + GTF (**SnpEff build**) and annotate variant VCFs (**SnpEff eff**).
9. Clean suspicious `WARNING_TRANSCRIPT_INCOMPLETE` annotations with a regex replace step.
10. Flatten SnpEff VCFs to tabular with **SnpSift Extract Fields** and concatenate across samples into one combined variant report.
11. Rename consensus headers, then concatenate per-sample FASTAs into a combined multi-FASTA.
12. Aggregate fastp, samtools stats, and Qualimap BamQC metrics with **MultiQC** into a single QC report.

## Key parameters
- `Supporting read fraction to call variant` (ivar variants `min_freq`): float in [0.05, 0.25], default **0.25**. Lower = more sensitive, noisier; higher = cleaner.
- Consensus frequency threshold (ivar consensus `min_freq`): derived as **0.95 − min_freq** (e.g. 0.7 at default). Controls IUPAC ambiguity in consensus.
- `Minimum quality score to consider base for variant calling` (ivar `min_qual`): integer 0–93, default **20**; applied to both variant calling and consensus.
- `ivar consensus` `min_depth`: **20**; `min_indel_freq`: **0.8**; ambiguous-depth action: `-n N`.
- `samtools view` filter: keep flags `1,2` (paired + proper pair), MAPQ quality **20**.
- `ivar trim`: `min_qual=20`, `window_width=4`, `primer_pos_wiggle=0`, `min_len=5`, `inc_primers=true`; runs only when primer BED is supplied.
- `bwa mem`: paired-collection mode, Illumina analysis type, coordinate sort, auto read group ID/SM, PL=ILLUMINA.
- `SnpEff build`: input type `gtf`, `genome_version=viralDB`, codon table `Standard`; database built fresh from user-supplied reference + annotation.
- `SnpSift Extract Fields`: `CHROM POS REF ALT QUAL DP AF DP4 ANN[*].EFFECT ANN[*].IMPACT ANN[*].GENE ANN[*].TRID ANN[*].HGVS_C ANN[*].HGVS_P`.
- Primer BED must be format-tagged `bed` and primer names in column 4 must match the regex `.*_(\d+).*_(L(EFT)?|R(IGHT)?)` for ivar trim to parse amplicons and orientation.

## Test data
The workflow's test profile supplies a paired collection of Illumina PE FASTQs for a small batch of viral isolates together with a matching viral reference FASTA and a GTF annotation; an amplicon variant of the test additionally provides a BED primer scheme. A successful run is expected to produce a SnpEff-annotated VCF collection, a concatenated combined variant report (tabular), per-sample consensus FASTAs, a combined multi-FASTA of all consensus genomes, processed/realigned (and primer-trimmed, when applicable) BAMs, and a MultiQC HTML QC report. See the parsed test manifest in the caller for exact input files and golden output assertions.

## Reference workflow
Galaxy IWC — `workflows/virology/generic-non-segmented-viral-variant-calling/pe-illumina-simple-virus-calling-and-consensus.ga`, release **0.2** (2025-12-04), AGPL-3.0-or-later. Authors: Peter van Heusden, Wolfgang Maier. Tagged `ARTIC`, `virology`.
