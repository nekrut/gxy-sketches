---
name: population-variant-catalogue-human-wgs
description: Use when you need to build a population-level variant catalogue (variant
  list with allele frequencies) from a cohort of human short-read whole-genome sequences,
  jointly calling SNVs/indels and mitochondrial variants across samples for downstream
  population-frequency and background-variant reference use.
domain: variant-calling
organism_class:
- vertebrate
- diploid
- human
input_data:
- short-reads-paired
- reference-fasta
- mitochondrial-reference-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/variantcatalogue
  url: https://github.com/nf-core/variantcatalogue
  version: dev
  license: MIT
  slug: variantcatalogue
tools:
- name: bwa
- name: trimmomatic
  version: '0.39'
- name: samtools
- name: fastqc
  version: 0.11.9
- name: mosdepth
  version: 0.3.3
- name: picard
- name: deepvariant
- name: glnexus
  version: 1.4.1
- name: bcftools
- name: bedtools
- name: hail
- name: gatk
- name: mutect2
  version: 4.4.0.0
- name: vep
  version: '108.2'
tags:
- population-genomics
- variant-catalogue
- allele-frequency
- wgs
- human
- snv
- indel
- mitochondrial
- joint-calling
- cohort
test_data: []
expected_output: []
---

# Population variant catalogue from human WGS cohorts

## When to use this sketch
- You have a cohort of human whole-genome short-read samples (Illumina paired-end FASTQ) and want a population-level variant catalogue with per-variant allele frequencies, similar in spirit to gnomAD.
- You need joint-called SNVs/indels across many samples plus a parallel mitochondrial variant track from the same BAMs.
- You want VEP-annotated, QC-filtered, sex-aware output usable as a background-variant reference for downstream rare-disease or population studies.
- Your reference is GRCh37 or GRCh38 and you are comfortable running DeepVariant + GLnexus joint calling and Hail for cohort QC.

## Do not use when
- You only have a single sample or a trio and want per-sample clinical variant calling — use a standard germline short-variant sketch instead.
- Your organism is non-human, bacterial, or haploid — see `haploid-variant-calling-bacterial` or a species-appropriate sketch.
- You need structural variants as the primary output — the SV subworkflow is not yet included here; use a dedicated SV sketch.
- You only need tumor/normal somatic calling — use a somatic variant-calling sketch.
- Your data is long-read (ONT/PacBio) — this pipeline assumes Illumina short reads.

## Analysis outline
1. Read trimming of paired-end FASTQ with Trimmomatic.
2. Reference indexing with BWA index and alignment with BWA-MEM; index BAMs with samtools.
3. Raw-read QC with FastQC; coverage with Mosdepth; alignment QC with Picard CollectWgsMetrics, CollectAlignmentSummaryMetrics, and QualityScoreDistribution; aggregate with MultiQC.
4. Per-sample SNV/indel calling with DeepVariant producing gVCFs.
5. Cohort joint calling with GLnexus to produce a multi-sample VCF.
6. Normalize and split multi-allelic sites with bcftools/bedtools norm; re-assign variant IDs with bedtools annotate.
7. Sample QC and genetic sex inference with Hail; variant QC and allele-frequency computation with Hail.
8. Functional annotation of the cohort VCF with Ensembl VEP.
9. Mitochondrial subworkflow: extract MT reads with GATK, realign to both canonical and shifted chrM references with BWA-MEM, mark duplicates, collect Picard HS metrics, call variants with GATK Mutect2 in mitochondrial mode, liftover shifted calls, merge VCFs, and run Hail-based MT variant QC and frequency calculation.

## Key parameters
- `--input`: CSV samplesheet with columns `sample,fastq_1,fastq_2`; rows sharing a `sample` ID are concatenated across lanes before mapping.
- `--outdir`: absolute output directory.
- `--genome`: iGenomes key, typically `GRCh38` (test profile) or `GRCh37`.
- `--fasta`: explicit reference FASTA when not using iGenomes; BWA index is auto-built if absent.
- `Mitochondrial_chromosome`: MT contig name, e.g. `chrM` for GRCh38.
- Mitochondrial references (canonical + shifted-by-8000): `reference_MT`, `reference_MT_shifted`, plus matching `.fai`/`.dict`, `ShiftBack.chain`, `blacklist_sites_hg38_MT`, `control_region_shifted_reference_interval_list`, `non_control_region_interval_list`, `artifact_prone_sites_bed`, `mitotip_predictions_table`, `pon_predictions_table`.
- VEP cache: `species` (e.g. `Homo_sapiens`), `cache_version` (e.g. `105`), `cache_path`, `vep_extra_files`.
- DeepVariant is run per sample in WGS mode; GLnexus joint-calling uses the DeepVariant preset; Mutect2 is run in `--mitochondria-mode` against both canonical and shifted chrM.
- Cohort-level filtering thresholds and sex inference are applied inside Hail scripts rather than via top-level params.
- Resource caps via `--max_cpus`, `--max_memory`, `--max_time`.

## Test data
The `test` profile uses a small samplesheet of human paired-end FASTQs aligned against a GRCh38 subset reference containing only chr20, chrX, chrY, and chrM (`hg38_full_analysis_set_plus_decoy_hla_chr20_X_Y_MT.fa`) hosted in the upstream `scorreard/Variant_catalogue_pipeline` test data repo, together with the matching canonical and shifted chrM references and MT auxiliary files (blacklist BED, interval lists, ShiftBack chain, MitoTIP and PoN prediction tables, artifact-prone sites BED). Running `nextflow run nf-core/variantcatalogue -profile test,docker --outdir results` is expected to produce: per-sample trimmed/aligned BAMs with indices, FastQC/Mosdepth/Picard/MultiQC reports, a DeepVariant gVCF per sample, a GLnexus-joint-called and normalized cohort VCF with per-variant allele frequencies and VEP annotations, and a Mutect2-based mitochondrial VCF merged from canonical and shifted alignments with Hail-derived MT allele frequencies. Exact variant contents are not asserted by golden files; QC-report generation and non-empty annotated VCFs are the practical success signals.

## Reference workflow
nf-core/variantcatalogue (dev), https://github.com/nf-core/variantcatalogue, MIT. Method described in Correard et al., bioRxiv 2022.10.03.508010, "The variant catalogue pipeline: A workflow to generate a background variant library from Whole Genome Sequences."
