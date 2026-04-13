---
name: lcwgs-relatedness-estimation
description: Use when you need to estimate pairwise genetic relatedness between individuals
  from low-coverage whole-genome sequencing (lcWGS) data, especially for non-model
  organisms lacking a high-confidence known variant set. Handles FASTQ/BAM/CRAM inputs,
  builds a bootstrapped variant panel if needed, and produces genotype-likelihood-based
  relatedness estimates via NgsRelate.
domain: variant-calling
organism_class:
- eukaryote
- diploid
- non-model
input_data:
- short-reads-paired
- reference-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/genomicrelatedness
  url: https://github.com/nf-core/genomicrelatedness
  version: dev
  license: MIT
tools:
- fastp
- bwa-mem2
- samtools
- gatk4
- bcftools
- vcftools
- mosdepth
- preseq
- ngsrelate
- multiqc
tags:
- lcwgs
- relatedness
- kinship
- genotype-likelihoods
- bqsr
- bootstrapping
- non-model
- ngsrelate
- ibd
- pedigree
test_data: []
expected_output: []
---

# Low-coverage WGS relatedness estimation

## When to use this sketch
- User has low-coverage whole-genome sequencing (lcWGS) data from multiple individuals and wants to infer pairwise relatedness / kinship / IBD.
- Organism is a non-model species with no curated dbSNP-style known variant set, so a variant panel must be bootstrapped from the data itself.
- Inputs are short-read Illumina paired FASTQ (optionally SPRING-compressed) or already-aligned BAM/CRAM, together with a reference FASTA.
- Need genotype-likelihood-based estimates that are robust at very low coverage, not hard genotype calls.
- Cohort size is at least a handful of individuals (joint calling with GATK HaplotypeCaller + GenomicsDBImport + GenotypeGVCFs is used).

## Do not use when
- You are calling germline or somatic variants for their own sake rather than for relatedness — use a general short-read variant-calling sketch (e.g. `germline-variant-calling-short-read`) instead.
- Haploid bacterial data — use `haploid-variant-calling-bacterial`.
- You already have a dense, validated genotype matrix and just want kinship — go directly to KING / PLINK / NgsRelate without this pipeline.
- Ancient DNA / damage-aware kinship on pseudo-haploid pileups — use an aDNA-specific kinship sketch (READv2/BREADR-centric).
- Long-read (ONT/PacBio) data — this pipeline is BWA-MEM2 short-read only.
- Single-sample analysis — relatedness needs ≥2 individuals.

## Analysis outline
1. **Prepare reference**: BWA-MEM2 index, `samtools faidx`, GATK4 `CreateSequenceDictionary`.
2. **Build intervals**: split the reference into BED intervals (gawk + split_intervals) for parallel calling.
3. **Preprocess reads**: `fastp` (trim/filter/merge pairs) → `bwa-mem2 mem` → `samtools sort` → GATK4 `AddOrReplaceReadGroups` using samplesheet RG fields.
4. **Merge & dedup**: `samtools merge` per sample, GATK4 `MarkDuplicates`, `samtools index` → per-individual CRAM.
5. **Preprocessing QC**: `preseq c_curve`/`lc_extrap`, `mosdepth`, `samtools stats` — aggregated by MultiQC.
6. **Bootstrap known variant set (optional, 1–3 rounds)**: joint call with GATK4 `HaplotypeCaller` (GVCF) → `GenomicsDBImport` → `GenotypeGVCFs` → `MergeVcfs`; hard-filter with `VariantFiltration` + `SelectVariants` to produce a high-confidence VCF.
7. **BQSR**: GATK4 `BaseRecalibrator` → `GatherBQSRReports` → `ApplyBQSR` → re-merge/index; `AnalyzeCovariates` for diagnostics. Iterated (default 2 rounds).
8. **Joint variant calling, two callers in parallel**: GATK4 HaplotypeCaller pathway AND `bcftools mpileup`+`bcftools call` per scaffold, concatenated with `bcftools concat`.
9. **Intersect & thin**: `bcftools isec` to keep sites called by both callers; `vcftools` to include/exclude scaffolds and thin (remove indels, MAF, max-missing) → final variant set.
10. **Relatedness estimation**: ANGSD `NgsRelate v2` on genotype likelihoods → pairwise relatedness matrix.
11. **Report**: MultiQC aggregates QC across preprocessing, BQSR rounds, and variant stats.

## Key parameters
- `--input`: CSV samplesheet. Required columns: `sample`, one of `fastq_1`/`fastq_2`, `spring_1`/`spring_2`, `bam`, or `cram`, plus read-group fields `RGID`, `RGLB`, `RGPL`, `RGPU`, `RGSM`.
- `--fasta`: reference genome FASTA (indices auto-built if absent; optional `--fasta_fai`, `--dict`, `--bwamem2_index`).
- `--known_variants_vcf` (+ `--known_variants_tbi`): skip bootstrapping if a trusted variant set already exists. Mutually exclusive with `--bootstrapping_rounds`.
- `--bootstrapping_rounds`: integer 1–3. Controls how many rounds of call→filter→BQSR are used to build the variant panel from scratch.
- `--target_number_of_interval_files` / `--max_number_of_intervals_per_file`: parallelism knobs for scatter-gather.
- `--include_scaffolds` / `--exclude_scaffolds`: restrict to autosomes or drop mitochondrial/sex scaffolds before relatedness (mutually exclusive).
- Hard-filter thresholds (fixed): `QUAL≥100, QD<2.0, MQ<35.0, FS>60, HaplotypeScore>13.0, MQRankSum<-12.5, ReadPosRankSum<-8.0`.
- vcftools thinning defaults: `--remove-filtered-all --remove-indels --maf 0.025 --max-missing 0.75 --recode --recode-INFO-all`.
- bcftools calling: `mpileup --output-type z -d 100`; `call --output-type z -m -v`.
- Stage skip flags: `--skip_bqsr`, `--skip_variant_calling`, `--skip_intersection_thinning`, `--skip_relatedness_estimation`, `--hard_filter_variants`. Skipping variant calling forces skipping of the downstream stages.

## Test data
The bundled `-profile test` uses a small multi-sample samplesheet of paired-end short reads with a reference FASTA, constrained to 4 CPUs / 15 GB / 1 h so it can run on a laptop or CI. Running it exercises the full metro map: preprocessing (fastp, bwa-mem2, MarkDuplicates, mosdepth, preseq), at least one bootstrapping round producing a filtered VCF, BQSR with AnalyzeCovariates plots, parallel GATK + bcftools variant calling, `bcftools isec` intersection, vcftools thinning, and a final NgsRelate pairwise relatedness TSV under `relatedness_estimation/angsd_ngsrelate/`, plus an aggregated `multiqc/multiqc_report.html`. The full-size `-profile test_full` points at the nf-core/test-datasets viralrecon reference to smoke-test scaling behaviour end-to-end.

## Reference workflow
nf-core/genomicrelatedness (dev, nf-core template 3.5.1), MIT-licensed. Upstream method: Snyder-Mackler et al., *Genetics* 2016, doi:10.1534/genetics.116.187492. Key tools: fastp, BWA-MEM2, samtools, GATK4, bcftools, vcftools, mosdepth, preseq, ANGSD NgsRelate v2, MultiQC.
