---
name: allele-specific-expression-rnaseq-umi
description: Use when you need to quantify allele-specific expression (ASE) from paired-end,
  UMI-tagged bulk RNA-seq against a phased/phasable per-sample VCF of heterozygous
  variants, using STAR-WASP to avoid reference mapping bias and phaser for gene-level
  ASE. Designed for human samples on a chosen chromosome.
domain: rna-seq
organism_class:
- vertebrate
- diploid
- human
input_data:
- short-reads-paired
- per-sample-vcf
- reference-fasta
- gtf
- star-index
- gene-features-bed
source:
  ecosystem: nf-core
  workflow: nf-core/alleleexpression
  url: https://github.com/nf-core/alleleexpression
  version: dev
  license: MIT
  slug: alleleexpression
tools:
- name: fastqc
  version: 0.12.1
- name: star
- name: wasp
- name: umi-tools
- name: samtools
- name: bcftools
- name: beagle
  version: 5.2_21Apr21.304
- name: phaser
- name: phaser-gene-ae
- name: multiqc
  version: '1.29'
tags:
- ase
- allele-specific-expression
- rna-seq
- umi
- wasp
- phasing
- beagle
- phaser
- human
test_data: []
expected_output: []
---

# Allele-specific expression from UMI-tagged RNA-seq (STAR-WASP + phaser)

## When to use this sketch
- User has paired-end Illumina bulk RNA-seq with UMIs in the read IDs and wants per-gene allele-specific expression (ASE) calls.
- A per-sample VCF of heterozygous variants is available (e.g. from matched WGS/WES or genotyping) and can be phased.
- Analysis is focused on a human sample (GRCh38/GRCh37) or other diploid organism where Beagle reference panels and genetic maps are available.
- Goal is haplotype-resolved read counts and gene-level log2 allelic fold-change / p-values, not differential expression between conditions.
- It is acceptable (and often desirable) to restrict the analysis to one chromosome at a time via `--chromosome`.

## Do not use when
- You only need standard differential gene expression — use a conventional nf-core/rnaseq + DESeq2/edgeR sketch instead.
- Reads have no UMIs and the library is not deep/complex enough to skip deduplication — the UMI-tools dedup step expects UMIs embedded in read IDs.
- You are working with single-cell or spatial data — use a 10x/scRNA ASE sketch.
- You lack per-sample heterozygous variants (ASE needs het sites; calling variants from RNA-seq alone is a different workflow).
- The organism is haploid or polyploid, or lacks a Beagle reference panel / genetic map — phasing assumptions break.
- You want transcript-level or isoform-resolved ASE — phaser operates at the gene level here.

## Analysis outline
1. Validate the samplesheet (`sample,fastq_1,fastq_2,vcf`) and prepare each per-sample VCF for STAR and Beagle (BCFtools: restrict to target chromosome, keep PASS sites, bgzip + tabix).
2. Run FastQC on raw reads for QC.
3. Align reads with STAR in WASP mode against the prebuilt STAR index, passing the per-sample VCF via `--varVCFfile` so WASP vW tags are written into the BAM.
4. Filter the STAR BAM to keep only reads carrying `vW:i:1` (WASP-passed), discarding reads with reference-mapping bias.
5. Deduplicate the WASP-filtered BAM with UMI-tools `dedup` using the configured `umi_separator` on read IDs.
6. Coordinate-sort and index the deduplicated BAM with samtools.
7. Phase the per-sample, chromosome-restricted VCF with Beagle, using `beagle_ref` (population reference panel) and `beagle_map` (genetic map) when provided.
8. Run phaser on the phased VCF + dedup BAM to produce haplotypic read counts and allele configurations.
9. Run phaser_gene_ae against the `gene_features` BED to get gene-level ASE (aCount/bCount/log2FC/pValue).
10. Extract the subset of expressed ASE genes (totalCount > 0) into a final `*.ASE.tsv` per sample.
11. Aggregate FastQC, STAR, UMI-tools and samtools metrics with MultiQC.

## Key parameters
- `input`: CSV samplesheet with exactly the columns `sample,fastq_1,fastq_2,vcf` (one VCF per sample).
- `fasta`, `gtf`, `star_index`, `gene_features`: reference genome FASTA, GTF annotation, prebuilt STAR index directory, and gene-coordinate BED for phaser_gene_ae. `--genome GRCh38` can pull these from iGenomes.
- `chromosome`: target contig for ASE, e.g. `chr11` or `chr22`. Pipeline is designed to run one chromosome at a time; default in the shipped test is `chr11`/`chr22`.
- `beagle_ref`: population reference panel VCF for the chosen chromosome (improves phasing).
- `beagle_map`: Beagle PLINK-format genetic map for the chosen chromosome.
- `umi_separator`: character separating the UMI from the rest of the read ID; default `:` (matches UMI-tools `--umi-separator`).
- STAR is invoked with ASE-critical flags: `--waspOutputMode SAMtag`, `--varVCFfile <sample.vcf>`, `--outSAMattributes NH HI AS nM NM MD jM jI rB MC vA vG vW`, `--alignEndsType EndToEnd`, `--outFilterMultimapNmax 1`.
- BCFtools VCF prep: restrict to `--chromosome` and keep only PASS variants before phasing.
- Containerisation: run with `-profile test,docker` (or `singularity`) for reproducibility.

## Test data
The pipeline ships two test profiles. `conf/test.config` is a minimal smoke test that only sets a profile name and expects the user to provide `--input`; it does not pin a samplesheet URL. `conf/test_full.config` points `input` at `https://raw.githubusercontent.com/nf-core/test-datasets/alleleexpression/samplesheet/v1.0/samplesheet_full.csv`, uses `genome = 'GRCh38'`, and restricts analysis to `chromosome = 'chr22'`. Each samplesheet row carries paired FASTQs plus a per-sample VCF. A successful run produces, per sample, FastQC reports, a STAR `Aligned.sortedByCoord.out.bam` with WASP tags, a `*.wasp_filtered.bam`, a `*.dedup.bam` + index, a chr22 `*_beagle.vcf.gz`, phaser `haplotypic_counts.txt` / `allele_config.txt` / `variant_connections.txt` / `haplotypes.txt`, a `*_gene_ae.tsv` with `aCount`/`bCount`/`log2FC`/`pValue`, a filtered `*.ASE.tsv`, and a top-level `multiqc/multiqc_report.html`.

## Reference workflow
nf-core/alleleexpression (dev), https://github.com/nf-core/alleleexpression — STAR-WASP + UMI-tools + Beagle + phaser pipeline. Core tool citations: STAR (Dobin 2013), WASP (van de Geijn 2015), UMI-tools (Smith 2017), SAMtools/BCFtools (Li 2009; Danecek 2021), Beagle (Browning 2021), phaser (Castel 2015), MultiQC (Ewels 2016).
