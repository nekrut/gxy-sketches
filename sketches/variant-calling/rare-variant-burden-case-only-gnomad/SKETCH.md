---
name: rare-variant-burden-case-only-gnomad
description: Use when you have joint-called case-only germline exome/genome VCFs (no
  matched controls) and want to identify disease-predisposition genes via a consistent
  summary-count rare variant burden test against public gnomAD control counts, with
  ancestry stratification and FDR control.
domain: variant-calling
organism_class:
- human
- diploid
input_data:
- joint-called-vcf
- sample-list
- gnomad-control-summary-counts
source:
  ecosystem: nf-core
  workflow: nf-core/rarevariantburden
  url: https://github.com/nf-core/rarevariantburden
  version: dev
  license: MIT
  slug: rarevariantburden
tools:
- name: bcftools
- name: annovar
- name: vep
- name: cocorv
- name: seqarray
- name: hail
- name: gnomad-rf-classifier
tags:
- rare-variant
- burden-test
- case-only
- gnomad
- gene-based
- fdr
- ancestry-stratified
- cocorv
test_data: []
expected_output: []
---

# Case-only rare variant burden testing against gnomAD (CoCoRV)

## When to use this sketch
- You have sequenced human cases/patients (exome or genome) jointly called and VQSR-filtered, but no matched in-house controls.
- You want a gene-level rare variant burden test to nominate disease-predisposition genes, comparing allele counts in cases against precomputed gnomAD summary counts.
- Cases are from mixed or unknown ancestries and you need ancestry-stratified analysis using the gnomAD PCA + random-forest classifier.
- You want dominant, recessive, and compound-heterozygous models with discrete-count FDR control and QQ/lambda diagnostics.
- Reference build is GRCh37 (use gnomAD v2 exome) or GRCh38 (use gnomAD v4.1 exome or v4.1 genome).

## Do not use when
- You have matched case/control cohorts of your own — use a standard case/control association pipeline (e.g. SAIGE-GENE+, REGENIE burden) instead.
- You are doing common variant GWAS, single-variant association, or polygenic scoring — this is a rare-variant (AF ≤ ~5e-4), gene-collapsing test.
- You need per-sample diagnostic variant calling or clinical reporting — use a germline pipeline like nf-core/sarek with ClinVar/ACMG annotation.
- You are working in a non-human organism or a species without gnomAD-equivalent control summaries.
- You only have unfiltered per-sample gVCFs; joint calling + VQSR must be done upstream (e.g. via nf-core/sarek's GATK joint-calling module).

## Analysis outline
1. Split the joint-called, VQSR-applied case VCF per chromosome (bcftools).
2. Normalize and left-align indels, split multi-allelics, and apply per-genotype QC: DP≥10, GQ≥20, heterozygous allele balance 0.2–0.8 (bcftools).
3. Annotate each per-chromosome VCF with ANNOVAR (default: refGene, gnomad211_exome, REVEL) and optionally VEP with AlphaMissense/SpliceAI/LOFTEE/CADD plugins.
4. Convert normalized genotype VCFs and annotation VCFs to GDS format for fast R access (SeqArray).
5. Predict case-sample ancestry by projecting onto gnomAD PCA loadings and applying the gnomAD random-forest ONNX classifier (Hail).
6. Run CoCoRV per chromosome: consistent filtering of case and gnomAD control counts, AF cap, variant-group definition (e.g. pathogenic missense + LoF), and burden test under dominant / recessive / double-het models, stratified by predicted ancestry.
7. Merge per-chromosome association tables; optionally re-run with sex as covariate for sex-stratified analysis on chrX.
8. Compute discrete-count FDRs (DBH, ADBH.sd, resampling-based RBH), lambda inflation factor, and QQ plots with null-distribution boxplots.
9. For the top K genes, emit per-gene variant-sample tables with full annotations for manual QC and confounder inspection.

## Key parameters
- `reference`: `GRCh37` or `GRCh38` — must match your VCF build.
- `gnomADVersion`: `v2exome` (GRCh37), `v4exome` or `v4genome` (GRCh38).
- `AFMax`: alternate-allele frequency cap; `1e-4` for gnomAD v2 exome, `5e-4` (default) for v4.1 exome/genome.
- `variantGroup`: named variant set, default `annovar_pathogenic`; use `vep_lof_nosplicing` when running with VEP.
- `groupColumn`: gene-symbol column from the annotator — `Gene.refGene` for ANNOVAR, `SYMBOL` for VEP.
- `REVELThreshold`: minimum REVEL score for pathogenic missense, default `0.65`.
- `variantMissing`: max per-variant missingness, default `0.1`.
- `pLDControl`: p-value threshold for high-LD variant detection in controls (for 2HET model), default `0.05`.
- `ACANConfig`: file declaring ancestry groups to stratify on (e.g. NFE, AFR, EAS, SAS, AMR, ASJ).
- `chrSet`: chromosomes to analyze, default autosomes `1..22`; add `X` with `addSexToCaseGroup: true` and a `covariate` file containing a `Sex` column for sex-stratified chrX analysis.
- `annotationTool`: `ANNOVAR` (default), `VEP`, or `ANNOVAR_VEP`.
- `topK`: number of top-ranked genes to export variant-sample tables for, default `1000`.
- `batchSize`: CoCoRV processing batch size, default `10000`.

## Test data
The `test` profile uses a small two-chromosome case cohort (`samples.1KG.chr21-22.vcf.gz` with `samples.txt`) drawn from 1000 Genomes-style data, paired with a trimmed gnomAD v2 exome control folder staged from the nf-core test-datasets `rarevariantburden` branch. It runs on GRCh37 with `gnomADVersion: v2exome`, `AFMax: 1e-4`, and `chrSet: "21 22"`, and supplies pre-annotated case VCFs, pre-built genotype/annotation GDS files, an `ACANConfig` (`stratified_config_gnomad.txt`), a `variantExclude` list, and a precomputed `casePopulation.txt` so the ancestry classifier and ANNOVAR/VEP annotation steps are skipped. Expected outputs include per-chromosome normalized+QCed VCFs and GDS files, a merged `association.tsv`, the dominant-model FDR table `association.tsv.dominant.nRep1000.fdr.tsv`, a QQ plot PDF with lambda, kept-variant tables for cases and controls, and top-K per-gene variant-sample annotation tables.

## Reference workflow
nf-core/rarevariantburden (CoCoRV-nf), version `dev` — https://github.com/nf-core/rarevariantburden. Underlying method: Chen et al., "CoCoRV: a consistent summary-count-based rare variant burden test", *Nature Communications* 2022 (PMID 35545612); CoCoRV R package at https://bitbucket.org/Wenan/cocorv/.
