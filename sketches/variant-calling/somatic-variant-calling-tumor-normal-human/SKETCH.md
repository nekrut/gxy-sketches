---
name: somatic-variant-calling-tumor-normal-human
description: Use when calling somatic SNVs, small indels, CNVs and structural variants
  from matched tumor/normal human short-read WGS or WES data (e.g. HCC1395, clinical
  oncology cohorts). Handles GATK best-practices preprocessing plus Mutect2/Strelka/Manta/ASCAT
  and optional VEP/snpEff annotation.
domain: variant-calling
organism_class:
- vertebrate
- diploid
- human
input_data:
- short-reads-paired
- reference-fasta
- tumor-normal-pair
source:
  ecosystem: nf-core
  workflow: nf-core/sarek
  url: https://github.com/nf-core/sarek
  version: 3.8.1
  license: MIT
  slug: sarek
tools:
- name: fastp
- name: bwa-mem2
- name: gatk4
- name: mutect2
- name: strelka
- name: manta
- name: ascat
- name: cnvkit
- name: controlfreec
- name: msisensorpro
  version: '0.1'
- name: snpeff
- name: vep
- name: multiqc
tags:
- human
- cancer
- somatic
- tumor-normal
- wgs
- wes
- snv
- indel
- cnv
- sv
- msi
- gatk-best-practices
test_data: []
expected_output: []
---

# Somatic variant calling for human tumor/normal pairs

## When to use this sketch
- Matched tumor and normal samples from the same patient (optionally with additional relapse samples) sequenced on Illumina short reads.
- Human whole-genome, whole-exome, or targeted panel data where GATK best-practices preprocessing (BWA-MEM2 → MarkDuplicates → BQSR) is appropriate.
- You need a comprehensive somatic call set: SNVs/indels (Mutect2, Strelka2), structural variants (Manta, TIDDIT), allele-specific copy number and purity/ploidy (ASCAT), plus microsatellite instability (MSIsensorPro).
- You also want downstream filtering, normalisation and functional annotation with VEP and/or snpEff against GRCh38/GRCh37.
- You are happy to rely on AWS iGenomes bundles (`--genome GATK.GRCh38`) or to supply equivalent custom references including dbSNP, known_indels, germline_resource and (strongly recommended) a panel-of-normals.

## Do not use when
- You only have a single germline sample with no matched tumor → prefer a germline-only HaplotypeCaller/DeepVariant sketch (same pipeline, `--tools haplotypecaller,deepvariant,strelka` without tumor/normal pairing).
- You are calling variants on a haploid bacterial genome → use `haploid-variant-calling-bacterial`.
- Your data is long-read ONT/PacBio → use a long-read-specific sketch; sarek's aligners and callers here assume Illumina short reads.
- Your input is RNA-seq and you want RNA variants → use an RNA-seq variant-calling sketch built on STAR + GATK RNA best practices.
- You need UMI duplex consensus from paired index UMIs → prefer nf-core/fastquorum.
- You need joint genotyping across a large cohort of healthy individuals → use the joint-germline sketch (`--joint_germline` with HaplotypeCaller gVCFs).

## Analysis outline
1. Build/stage references (fasta, BWA-MEM2 index, dict, dbSNP, known_indels, germline_resource, intervals) via the `PREPARE_GENOME` subworkflow or `--genome GATK.GRCh38`.
2. QC and optional trimming/splitting of FASTQ with `fastp` (and `FastQC`).
3. Align per-lane reads with `bwa-mem2` (default) or `bwa-mem`/`dragmap`/`sentieon-bwamem`; merge lanes per sample.
4. Mark duplicates with `GATK MarkDuplicates` (or `MarkDuplicatesSpark`) producing CRAM.
5. Base quality score recalibration with `GATK BaseRecalibrator` + `ApplyBQSR` against dbSNP and known_indels.
6. Coverage and alignment QC with `mosdepth`, `samtools stats`, and sample-swap check via `NGSCheckMate`.
7. Somatic SNV/indel calling on tumor vs. matched normal with `GATK Mutect2` (with PON + germline resource, then `FilterMutectCalls`) and `Strelka2` (seeded by `Manta` candidate indels).
8. Structural variant calling with `Manta` (diploid + somatic) and `TIDDIT`; allele-specific CNV and purity/ploidy with `ASCAT`; additional CNV with `CNVkit` and `Control-FREEC`.
9. Microsatellite instability with `MSIsensorPro` (tumor/normal) and/or `MSIsensor2` (tumor-only fallback).
10. Post-processing: `bcftools view` PASS filtering, `bcftools norm` normalisation, optional `bcftools isec` consensus across callers.
11. Annotation with `Ensembl VEP` and/or `snpEff` (optionally merged), with plugins such as dbNSFP, LOFTEE, SpliceAI when configured.
12. Aggregate QC with `MultiQC`.

## Key parameters
- `--input samplesheet.csv` with columns `patient,sex,status,sample,lane,fastq_1,fastq_2` where `status=0` is normal and `status=1` is tumor; the same `patient` links the pair.
- `--step mapping` (default) — can also restart at `markduplicates`, `prepare_recalibration`, `recalibrate`, `variant_calling`, or `annotate`.
- `--tools mutect2,strelka,manta,ascat,cnvkit,controlfreec,msisensorpro,tiddit,vep,snpeff` to enable the full somatic stack; prune to what you need.
- `--genome GATK.GRCh38` (or `GATK.GRCh37`) to auto-wire dbSNP, known_indels, germline_resource, PON, intervals, VEP/snpEff cache metadata.
- `--wes true --intervals targets.bed` for exome/panel data; leave unset for WGS.
- `--pon / --pon_tbi` bgzipped panel-of-normals VCF for Mutect2 (use the bundled GRCh38 PON only as a starting point).
- `--joint_mutect2 true` to call all tumor samples of one patient jointly.
- `--only_paired_variant_calling true` to skip germline calling on the normal when you only care about somatic calls.
- `--aligner bwa-mem2` (default) vs. `bwa-mem`, `dragmap`, `sentieon-bwamem`, or experimental `parabricks` (requires `-profile gpu`).
- `--trim_fastq`, `--split_fastq 50000000`, `--nucleotides_per_second 200000` to tune preprocessing and scatter granularity.
- `--filter_vcfs true`, `--bcftools_filter_criteria "-f PASS,."`, `--normalize_vcfs true`, `--snv_consensus_calling true --consensus_min_count 2` for post-calling harmonisation.
- `--vep_cache / --snpeff_cache` (or `--download_cache`) and `--vep_genome GRCh38 --vep_species homo_sapiens --vep_cache_version 110` for annotation.

## Test data
The bundled `-profile test` runs a single-sample germline smoke test: one paired-end FASTQ (`tests/csv/3.0/fastq_single.csv`) against a tiny `testdata.nf-core.sarek` reference from nf-core/test-datasets, invoking only preprocessing plus `Strelka` germline calling and MultiQC — it completes in a couple of minutes and is meant to prove the plumbing works, not to exercise the somatic stack. The canonical full-size test is `-profile test_full`, which runs the HCC1395 tumor/normal whole-exome pair from `HCC1395_WXS_somatic_full_test.csv` with the Agilent SureSelect XT v6+UTR target BED, `--wes`, `--split_fastq 20000000`, and `--tools ascat,cnvkit,controlfreec,freebayes,lofreq,manta,msisensor2,muse,mutect2,ngscheckmate,strelka,tiddit,snpeff,vep`; expected outputs are per-caller somatic VCFs under `variant_calling/<tool>/tumor_vs_normal/`, CNV/ploidy tables from ASCAT, MSI scores, VEP/snpEff-annotated VCFs, and a consolidated MultiQC report, all benchmarked on the nf-core [sarek results page](https://nf-co.re/sarek/results).

## Reference workflow
nf-core/sarek v3.8.1 (https://github.com/nf-core/sarek), MIT licensed. Cite Hanssen et al., *NAR Genomics and Bioinformatics* 6(2), lqae031 (2024) and Garcia et al., *F1000Research* 9:63 (2020). See `docs/usage.md` and `docs/output.md` for exhaustive parameter and output documentation.
