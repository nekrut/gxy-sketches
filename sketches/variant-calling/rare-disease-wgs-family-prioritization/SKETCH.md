---
name: rare-disease-wgs-family-prioritization
description: Use when you need to call, annotate, and rank germline variants (SNV,
  indel, SV, CNV, repeat expansions, mitochondrial, mobile elements) from Illumina
  paired-end WGS/WES of rare disease patients or family trios, producing clinically
  prioritized VCFs suitable for diagnostic review in tools like Scout.
domain: variant-calling
organism_class:
- vertebrate
- human
- diploid
input_data:
- short-reads-paired
- reference-fasta
- pedigree
- vep-cache
- vcfanno-resources
source:
  ecosystem: nf-core
  workflow: nf-core/raredisease
  url: https://github.com/nf-core/raredisease
  version: 2.6.0
  license: MIT
  slug: raredisease
tools:
- name: bwa-mem2
- name: deepvariant
- name: glnexus
  version: 1.4.1
- name: manta
- name: tiddit
- name: cnvnator
  version: 0.4.1
- name: gatk-germlinecnvcaller
- name: expansionhunter
  version: 5.0.0
- name: stranger
- name: retroseq
- name: svdb
  version: 3.6.1
- name: vcfanno
  version: 0.3.5
- name: vep
  version: '110.0'
- name: genmod
- name: bcftools
- name: gatk-mutect2
- name: haplogrep
- name: hmtnote
tags:
- rare-disease
- trio
- wgs
- wes
- mitochondrial
- sv
- cnv
- repeat-expansion
- mobile-element
- clinical-genomics
- pedigree
- scout
test_data: []
expected_output: []
---

# Rare disease WGS/WES family variant prioritization

## When to use this sketch
- Diagnostic-style rare disease analysis of Illumina paired-end WGS or WES from a proband (optionally with parents / siblings as a trio or quattro) against GRCh37 or GRCh38.
- Need a comprehensive callset across variant classes: SNV/indel, structural variants, copy number variants, short tandem repeat expansions, mitochondrial SNV+SV, and mobile element insertions.
- Need pedigree-aware inheritance modeling and rank-scoring of variants, split into a clinical (HGNC-gene-filtered) and research VCF set for downstream review (e.g. Scout).
- Samples are sequenced on Illumina; FASTQ, SPRING-compressed FASTQ, or duplicate-marked BAM input is acceptable.

## Do not use when
- You only need plain germline SNV/indel calling on a single sample without pedigree, ranking, or clinical annotation — use a simpler DeepVariant / GATK HaplotypeCaller sketch.
- Tumor or tumor/normal somatic analysis — use a somatic variant-calling sketch.
- Long-read (ONT / PacBio) data — this pipeline currently only supports Illumina short reads.
- Non-human organism, or non-vertebrate — references, VEP cache, gnomAD, CADD and rank models assume human.
- Pure structural-variant discovery without SNV workup — use a dedicated SV sketch.
- De novo genome assembly — use an assembly sketch instead.

## Analysis outline
1. Read QC and (optional) adapter/quality trimming with FastQC and fastp.
2. Align paired-end reads to the reference with bwa-mem2 (default; alternatives: bwa, BWA-MEME, Sentieon BWA) and coordinate-sort with samtools.
3. Mark duplicates with Picard MarkDuplicates (or Sentieon Dedup when using the Sentieon aligner).
4. Alignment QC with Mosdepth, Picard CollectMultipleMetrics / CollectWgsMetrics / CollectHsMetrics, Qualimap, TIDDIT cov, Chromograph, and VerifyBamID2 for contamination.
5. SNV/indel calling with DeepVariant (default) or Sentieon DNAscope; joint-genotype the family with GLnexus and normalize with bcftools norm.
6. Structural-variant calling with Manta and TIDDIT sv; CNV calling with GATK GermlineCNVCaller and CNVnator; merge all SV/CNV calls with SVDB merge.
7. Short tandem repeat expansion calling with ExpansionHunter using the Stranger-extended variant catalog, then pathogenicity annotation with Stranger.
8. Mobile element calling with RetroSeq, per-sample merging with SVDB.
9. Mitochondrial subworkflow: GATK Mutect2 MT short-variant discovery on shifted + unshifted references, eKLIPse for large mtDNA deletions, Haplocheck for MT contamination, HaploGrep2 for haplogroup, HmtNote for variant annotation.
10. SNV annotation: bcftools roh → vcfanno (gnomAD AF, CADD-SNV, custom resources) → CADD (on-the-fly for indels) → Ensembl VEP with pLI/LoFtool/SpliceAI/MaxEntScan plugins; UPD + Chromograph + rhocall viz for trios.
11. SV and mobile-element annotation: SVDB query against population SV databases → VEP; bcftools filter for PASS / population-AF.
12. Rank and split variants with GENMOD (inheritance models + rank score) using the provided score_config files; filter_vep against an HGNC gene list to emit `*_clinical.vcf.gz` plus the full `*_research.vcf.gz` for each of SNV, SV, MT, and mobile elements.
13. Optional benchmarking against truth VCFs with RTG Tools vcfeval; optional Gens CNV-visualization track generation.
14. Aggregate run-wide QC with MultiQC.

## Key parameters
- `input`: samplesheet CSV with columns `sample,lane,fastq_1,fastq_2,sex,phenotype,paternal_id,maternal_id,case_id` (sex 1=male/2=female, phenotype 1=unaffected/2=affected, PED-style).
- `genome`: `GRCh37` or `GRCh38` (default GRCh38).
- `analysis_type`: `wgs` (default), `wes`, or `mito`.
- `aligner`: `bwamem2` (default), `bwa`, `bwameme`, or `sentieon`.
- `variant_caller`: `deepvariant` (default) or `sentieon` (DNAscope, requires `ml_model` and a Sentieon license).
- `mt_aligner` and `mito_name` (default `chrM`): control MT subworkflow; `run_mt_for_wes` to enable MT analysis on WES.
- `skip_subworkflows`: comma list selected from `me_calling,me_annotation,mt_annotation,mt_subsample,repeat_annotation,repeat_calling,snv_annotation,snv_calling,sv_annotation,sv_calling,generate_clinical_set` to turn off whole branches.
- `skip_tools`: comma list from `fastp,gens,germlinecnvcaller,haplogrep3,peddy,smncopynumbercaller,vcf2cytosure,fastqc,qualimap,ngsbits,eklipse`.
- Mandatory references: `fasta`, `intervals_wgs`, `intervals_y`; plus (depending on enabled branches) `vep_cache`, `vep_cache_version`, `vep_plugin_files`, `vcfanno_toml`, `vcfanno_resources`, `gnomad_af`, `variant_catalog`, `score_config_snv`, `score_config_sv`, `score_config_mt`, `svdb_query_dbs`, `mobile_element_references`, `ploidy_model`, `gcnvcaller_model`, `readcount_intervals`, `reduced_penetrance`, `variant_consequences_snv`, `variant_consequences_sv`, `vep_filters` (HGNC list for the clinical set).
- `scatter_count` (default 20) controls annotation parallelism; `mt_subsample_rd` (default 150) controls MT coverage downsampling for IGV.
- `cnvnator_binsize` (default 1000), `sentieon_dnascope_pcr_indel_model` (default `CONSERVATIVE`), `min_trimmed_length` (default 40), `bait_padding` (default 100) tune individual tools.

## Test data
The pipeline's `test` profile runs a tiny three-sample family case with FASTQ/SPRING input taken from `nf-core/test-datasets` (branch `raredisease`): samplesheet `testdata/samplesheet_fq_spring.csv` plus a downsampled human GRCh37 `reference.fasta`, a gnomAD AF tab, WGS and chrY interval lists, a dbSNP VCF, a target BED, a Stranger variant catalog, vcfanno TOML/resources, VEP cache (v107), SVDB query DB list, mobile-element references, rank-model INIs for SNV/SV/MT, and an HGNC filter list. The profile disables `fastp,gens,haplogrep3,peddy,germlinecnvcaller,qualimap,eklipse,ngsbits` and the `mt_annotation,mt_subsample,me_calling,me_annotation,sv_annotation` subworkflows. Running `-profile test` should produce a normalized family SNV VCF under `call_snv/genome/<case_id>_snv.vcf.gz`, an SVDB-merged SV VCF under `call_sv/genome/<case_id>_sv_merge.vcf.gz`, Stranger-annotated repeat-expansion VCFs under `repeat_expansions/`, GENMOD-ranked `*_snv_ranked_clinical.vcf.gz` / `*_snv_ranked_research.vcf.gz` (and SV equivalents) under `rank_and_filter/`, and a MultiQC report under `multiqc/`. A `test_singleton` profile exercises the same graph on a single sample, and `test_full` uses `samplesheet_trio.csv` for a full trio.

## Reference workflow
nf-core/raredisease v2.6.0 (https://github.com/nf-core/raredisease), DOI 10.5281/zenodo.7995798, inspired by Clinical Genomics Stockholm's MIP pipeline. Requires Nextflow ≥ 24.04.2 with Docker/Singularity/Podman (Conda not fully supported).
