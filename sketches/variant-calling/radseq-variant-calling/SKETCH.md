---
name: radseq-variant-calling
description: Use when calling SNPs and small indels from Restriction site-Associated
  DNA sequencing (RAD-seq) / ddRAD Illumina short-read data for population genomics
  of model or non-model organisms, either against an existing reference genome or
  a de novo pseudo-reference assembled from the reads themselves. Supports optional
  UMI deduplication.
domain: variant-calling
organism_class:
- eukaryote
- non-model
- diploid
input_data:
- short-reads-paired
- short-reads-single
- reference-fasta-optional
source:
  ecosystem: nf-core
  workflow: nf-core/radseq
  url: https://github.com/nf-core/radseq
  version: dev
  license: MIT
tools:
- fastp
- fastqc
- cd-hit-est
- rainbow
- seqtk
- bwa
- bwa-mem2
- samtools
- umi_tools
- bedtools
- bedops
- freebayes
- bcftools
- tabix
- multiqc
tags:
- radseq
- ddrad
- population-genomics
- non-model
- freebayes
- denovo-reference
- umi
- reduced-representation
test_data: []
expected_output: []
---

# RAD-seq variant calling (reference or de novo)

## When to use this sketch
- Input is reduced-representation sequencing from restriction enzyme digestion (RAD-seq, ddRAD, ezRAD, 2bRAD) on Illumina, single- or paired-end.
- Goal is a joint multi-sample VCF of SNPs/indels for downstream population genomics (F_ST, PCA, structure, outlier detection).
- Either a reference genome is available (`method = 'reference'`) OR no reference exists and you need a dDocent-style de novo pseudo-reference built from the reads (`method = 'denovo'`).
- Samples may carry UMI barcodes that you want to use for PCR duplicate removal.
- Working on non-model eukaryotes where standard WGS pipelines over-filter or mis-model the locus structure.

## Do not use when
- You have whole-genome shotgun (WGS) short-read data from a diploid vertebrate — use a germline short-variant pipeline (e.g. nf-core/sarek) instead.
- You are calling variants on a haploid bacterial isolate — use `haploid-variant-calling-bacterial`.
- Your data is amplicon / 16S metabarcoding — use an amplicon sketch (DADA2/QIIME2).
- You need structural variant discovery — use a dedicated SV sketch.
- Your reads are long-read (PacBio/ONT) — RAD-seq assumes short reads and uses BWA/BWA-MEM2.
- You want stacks-style catalog loci with population summary stats baked in — this pipeline stops at a FreeBayes VCF.

## Analysis outline
1. Raw read QC with FastQC.
2. Adapter and quality trim with fastp (sliding-window cut-right, optional poly-G trim, paired-end correction).
3. Reference selection: either use the supplied reference FASTA, or build a de novo pseudo-reference by (a) collapsing unique reads per individual and across individuals above depth thresholds, (b) joining R1+R2 with an `NNNNNNNNNN` spacer, (c) clustering with CD-HIT-EST, (d) splitting putative haplotypes with `rainbow div`, (e) merging contigs with `rainbow merge`, (f) writing a FASTA.
4. Index the reference (samtools faidx + bwa/bwa-mem2 index).
5. Align trimmed reads per sample with BWA or BWA-MEM2, filter with `samtools view -q 1`, coordinate-sort and index.
6. Optional UMI-tools dedup when `umi_barcodes = true` in the samplesheet.
7. Merge per-sample BAMs by shared sample prefix with samtools merge.
8. Build FreeBayes parallelisation intervals via bedtools bamtobed → bedops merge → bedtools sort/coverage/merge → bedtools makewindows (splitting high-coverage regions above `splitByReadCoverage`) → bedtools intersect → per-interval BEDs.
9. Joint variant calling with FreeBayes across all merged BAMs per interval, with RAD-tuned thresholds (min map/base quality, min alt fraction, haplotype entropy).
10. Concatenate, sort, bgzip and tabix-index per-interval VCFs with bcftools + tabix into one project VCF.
11. Aggregate QC (FastQC, fastp, samtools stats, bcftools stats) with MultiQC.

## Key parameters
- `input`: CSV samplesheet with columns `sample,fastq_1,fastq_2,umi_barcodes`. Sample grouping/merging is by the shared prefix up to the first digit — name samples accordingly (e.g. `pop1_ind01`).
- `genome` / reference FASTA: required when `method = 'reference'`.
- `method`: `reference` (use supplied FASTA) or `denovo` (build pseudo-reference).
- `sequence_type`: one of `SE`, `PE`, `RPE`, `OL`, `ROL` — controls dDocent-style de novo handling.
- `aligner`: `bwa-mem2` (default, faster) or `bwamem`.
- `need_to_trim_fastq`: trim reads with fastp before de novo clustering.
- `minreaddepth_withinindividual` / `minreaddepth_betweenindividual`: minimum read support (e.g. `2` and `2,3`) for a unique sequence to enter the de novo reference.
- CD-HIT-EST: `-c 0.9 -g 1 -d 100` (identity threshold 0.9).
- `rainbow div`: `-f 0.5 -K 10`.
- `rainbow merge`: `-r 2 -N 10000 -R 10000 -l 20 -f 0.75`.
- BWA/BWA-MEM2: `-L 20,5 -a -M -T 30 -A 1 -B 4 -O 6`; then `samtools view -q 1`.
- FreeBayes: `-m 5 -q 5 -E 3 -n 1 -F 10 --min-repeat-entropy 1` (diploid default; min alt fraction 10%).
- `splitByReadCoverage` (default 500000): split high-coverage windows to ~½ read length for FreeBayes parallelism.
- `subset_intervals_channel`: randomly subsample individuals fed into the intervals subworkflow when sample counts are large to keep bedtools merge memory bounded.
- `umi_read_structure`: required when samples carry UMIs, to reposition barcodes into read headers before UMI-tools dedup.

## Test data
The bundled `test` profile pulls a small RAD-seq dataset derived from *Limulus polyphemus* (Atlantic horseshoe crab) ddRAD libraries digested with SbfI/MluCI, aligned against a gzipped chromosome-26 slice of the horseshoe crab reference (`hsc_Chr26.fasta.gz`). It exercises `method = 'reference'`, `sequence_type = 'PE'`, and `aligner = 'bwa-mem2'`, capped at 1 CPU / 2 GB / 10 min so it runs on GitHub Actions. A successful run should produce trimmed FASTQs, per-sample sorted/indexed BAMs under `reference/alignments/bwamem2/`, per-interval BEDs, a concatenated bgzipped `*.vcf.gz` with tabix index under `reference/variant_calling/`, and a MultiQC HTML report aggregating FastQC, fastp, samtools stats, and bcftools stats.

## Reference workflow
nf-core/radseq (`dev`), https://github.com/nf-core/radseq — a Nextflow DSL2 reimplementation of the dDocent RAD-seq variant-calling protocol (Puritz et al., PeerJ 2014), with FreeBayes as the genotyper and optional UMI-tools deduplication.
