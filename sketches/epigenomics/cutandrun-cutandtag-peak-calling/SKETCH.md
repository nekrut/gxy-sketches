---
name: cutandrun-cutandtag-peak-calling
description: "Use when you need to map protein\u2013DNA interactions from paired-end\
  \ CUT&RUN or CUT&TAG Illumina sequencing and call punctate peaks against a reference\
  \ genome. Covers adapter trimming, Bowtie2 alignment with dovetail, MAPQ30/concordant-pair\
  \ filtering, duplicate removal, and MACS2 peak calling tuned for the low-background,\
  \ punctate signal profile typical of CUT&RUN/CUT&TAG."
domain: epigenomics
organism_class:
- eukaryote
input_data:
- short-reads-paired
- bowtie2-index
source:
  ecosystem: iwc
  workflow: 'CUT&amp;RUN/CUT&amp;TAG Analysis: Protein-DNA Interaction Mapping'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/epigenetics/cutandrun
  version: '0.18'
  license: MIT
  slug: epigenetics--cutandrun
tools:
- name: cutadapt
  version: 5.2+galaxy2
- name: bowtie2
  version: 2.5.5+galaxy0
- name: samtools
- name: picard-markduplicates
  version: 3.1.1.0
- name: bedtools
  version: 2.31.1+galaxy0
- name: macs2
  version: 2.2.9.1+galaxy0
- name: ucsc-wigtobigwig
- name: multiqc
  version: 1.33+galaxy2
tags:
- cutandrun
- cutandtag
- chromatin
- peak-calling
- macs2
- bowtie2
- punctate
- protein-dna
test_data:
- role: pe_fastq_input__rep1__forward
  url: https://zenodo.org/record/6823059/files/Rep1_R1.fastq
  sha1: f60788cf7767330c960afb7ae6ba8f4009a11770
  filetype: fastqsanger
- role: pe_fastq_input__rep1__reverse
  url: https://zenodo.org/record/6823059/files/Rep1_R2.fastq
  sha1: a0af1b73fa1b24d2abe5d816091f544133149b25
  filetype: fastqsanger
expected_output:
- role: mapping_stats
  description: Content assertions for `Mapping stats`.
  assertions:
  - 'Rep1: has_text: 289103 reads; of these:'
  - 'Rep1: has_text_matching: {''expression'': ''99.39% overall alignment rate''}'
- role: bam_filtered_rmdup
  description: Content assertions for `BAM filtered rmDup`.
  assertions:
  - 'Rep1: has_size: {''value'': 8661584, ''delta'': 800000}'
- role: markduplicates_metrics
  description: Content assertions for `MarkDuplicates metrics`.
  assertions:
  - 'Rep1: has_text: 0.33'
- role: macs2_summits
  description: Content assertions for `MACS2 summits`.
  assertions:
  - 'Rep1: has_n_lines: {''n'': 5870}'
- role: macs2_narrowpeak
  description: Content assertions for `MACS2 narrowPeak`.
  assertions:
  - 'Rep1: has_n_lines: {''n'': 5870}'
- role: macs2_peaks_xls
  description: Content assertions for `MACS2 peaks xls`.
  assertions:
  - 'Rep1: has_text: # tag size is determined as 40 bps'
  - 'Rep1: has_text_matching: {''expression'': ''# total tags in treatment: 238930''}'
---

# CUT&RUN / CUT&TAG peak calling

## When to use this sketch
- Paired-end Illumina FASTQ data from a CUT&RUN or CUT&TAG experiment targeting a transcription factor or histone mark with a punctate (narrow) signal profile.
- A Bowtie2 index is already available (or selectable) for the target eukaryotic reference genome (e.g. hg38, mm10, dm6, ce11).
- You want narrow peaks, summits, a coverage bigWig, and a MultiQC report in one pass, without a matched IgG/input control.
- Library prep is known (TruSeq for CUT&RUN, Nextera for CUT&TAG) so adapter sequences can be supplied explicitly.

## Do not use when
- The data are single-end, long-read, or not from a CUT&RUN/CUT&TAG-style protocol — use a ChIP-seq sketch instead.
- You need broad-domain peaks (e.g. H3K27me3, H3K9me3 over large blocks) — switch MACS2 to `--broad`, which this sketch does not do.
- You have a matched IgG/input control you want to use for background correction — this workflow runs treatment-only; a ChIP-seq-with-control sketch is more appropriate.
- You need ATAC-seq-style Tn5 shift correction or fragment-size partitioning (nucleosome vs. sub-nucleosome) — use an ATAC-seq sketch.
- You need differential binding across conditions — this sketch stops at per-sample peak calls.

## Analysis outline
1. Adapter and quality trimming of paired reads with **cutadapt** (TruSeq or Nextera adapters on R1/R2, quality cutoff 30, minimum length 15 bp).
2. Alignment to the reference with **Bowtie2** using `--very-sensitive`, `--dovetail`, and fragment length `-I 0 -X 1000`.
3. Filter the BAM with **samtools filter** to keep only properly paired reads (flag 0x2) with MAPQ ≥ 30.
4. Remove PCR duplicates with **Picard MarkDuplicates** (`REMOVE_DUPLICATES=true`).
5. Convert the cleaned BAM to BED with **bedtools bamtobed** so MACS2 sees both mates of each fragment.
6. Call peaks with **MACS2 callpeak** in BED mode, no control, `--nomodel --extsize 200 --shift -100`, q-value 0.05, `--call-summits`, optionally `--SPMR` for normalized pileup.
7. Convert the MACS2 treatment pileup bedGraph to bigWig with **wigToBigWig**.
8. Extract a one-line MACS2 summary (grep `^#` from peaks.xls) and aggregate cutadapt, Bowtie2, Picard, and MACS2 logs with **MultiQC**.

## Key parameters
- `adapter_forward` / `adapter_reverse`: TruSeq (`GATCGGAAGAGCACACGTCTGAACTCCAGTCAC` / `GATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT`) for CUT&RUN, Nextera (`CTGTCTCTTATACACATCTCCGAGCCCACGAGAC` / `CTGTCTCTTATACACATCTGACGCTGCCGACGA`) for CUT&TAG.
- cutadapt: `quality_cutoff=30`, `minimum_length=15`, `error_rate=0.1`.
- Bowtie2: preset `--very-sensitive`, `dovetail=true`, `I=0`, `X=1000`, orientation `--fr`.
- samtools filter: require `0x0002` (properly paired), `mapq≥30`, output BAM.
- Picard MarkDuplicates: `remove_duplicates=true`, `duplicate_scoring_strategy=SUM_OF_BASE_QUALITIES`.
- MACS2 callpeak: `format=BED`, `nomodel`, `extsize=200`, `shift=-100`, `qvalue=0.05`, `call_summits=true`, `keep_dup=all` (duplicates already removed upstream), no control, `gsize` = effective genome size (e.g. 2.7e9 human, 1.87e9 mouse, 1.2e8 D. melanogaster, 9e7 C. elegans), optional `--SPMR` via `normalize_profile`.

## Test data
A single paired-end sample `Rep1` (`Rep1_R1.fastq` / `Rep1_R2.fastq` from Zenodo record 6823059) is run against the `hg38canon` Bowtie2 index with TruSeq adapters, effective genome size 2.7e9, and `normalize_profile=false`. Expected results include a Bowtie2 mapping-stats report containing `289103 reads; of these:` and a `99.39% overall alignment rate`, a duplicate-removed BAM of ~8.66 MB, a Picard metrics file showing a duplication fraction around `0.33`, and MACS2 outputs with 5870 lines in both the narrowPeak and summits BED files plus a peaks.xls whose header reports a 40 bp tag size and `# total tags in treatment: 238930`. A second bundled test on a D. melanogaster subset (`SRR15904259`, `dm6`, `normalize_profile=true`) exercises the SPMR-normalized bigWig path.

## Reference workflow
Galaxy IWC `workflows/epigenetics/cutandrun` (`CUT&RUN/CUT&TAG Analysis: Protein-DNA Interaction Mapping`), release 0.18, MIT-licensed, authored by Lucille Delisle. Note: versions prior to 0.6 had a bug where PCR duplicates were not actually removed; use ≥0.6.
