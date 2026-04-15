---
name: germline-exome-variant-calling-human
description: Use when you need to call germline SNVs and small indels from human whole-exome
  sequencing (WES) short-read Illumina data against a diploid reference (GRCh37/GRCh38),
  following GATK Best Practices with BQSR, HaplotypeCaller GVCF mode, VQSR, and SnpEff
  annotation.
domain: variant-calling
organism_class:
- vertebrate
- diploid
- human
input_data:
- short-reads-paired
- reference-fasta
- exome-capture-kit-bed
source:
  ecosystem: nf-core
  workflow: nf-core/exoseq
  url: https://github.com/nf-core/exoseq
  version: dev
  license: MIT
  slug: exoseq
tools:
- name: fastqc
- name: trim-galore
- name: bwa-mem
- name: picard
- name: qualimap
- name: gatk
- name: snpeff
- name: multiqc
tags:
- exome
- wes
- germline
- snv
- indel
- gatk
- best-practices
- human
- vqsr
test_data: []
expected_output: []
---

# Germline human exome variant calling (GATK Best Practices)

## When to use this sketch
- Input is human whole-exome sequencing (WES) from a capture kit, short-read paired-end Illumina FASTQ.
- You want germline SNVs and small indels against a diploid human reference (GRCh37, GRCh38, or another iGenomes human build).
- You want a GATK Best Practices-style pipeline: BWA-MEM alignment, MarkDuplicates, BQSR, indel realignment, HaplotypeCaller in GVCF mode, joint genotyping, VQSR for SNPs and indels, and functional annotation with SnpEff.
- You need standard QC reporting (FastQC, Qualimap, MultiQC) alongside variant calls.
- You have access to GATK resource bundles (dbSNP, 1000G, Omni, HapMap, Mills) required by BQSR and VQSR.

## Do not use when
- Sample is whole-genome sequencing rather than targeted/exome capture — prefer a WGS germline sketch.
- Organism is bacterial or otherwise haploid — see `haploid-variant-calling-bacterial`.
- You need somatic / tumor-normal variant calling — prefer a Mutect2-based somatic sketch.
- Input is long-read (ONT/PacBio) — prefer a long-read variant-calling sketch.
- You need structural variants or CNVs — prefer dedicated SV sketches.
- You want RNA variant calling from RNA-seq BAMs — prefer an RNA-variant sketch.

## Analysis outline
1. Raw read QC with FastQC.
2. Adapter and quality trimming with Trim Galore (Cutadapt).
3. Align trimmed reads to the reference with BWA-MEM; sort with samtools/Picard.
4. Mark PCR duplicates with Picard MarkDuplicates.
5. Collect alignment/coverage QC over the capture target with Qualimap 2.
6. Base Quality Score Recalibration with GATK BaseRecalibrator + ApplyBQSR using dbSNP and known-indel resources.
7. Local indel realignment with GATK RealignerTargetCreator + IndelRealigner (legacy GATK3 step retained by this pipeline).
8. Per-sample variant calling with GATK HaplotypeCaller in GVCF mode, restricted to the capture target intervals.
9. Joint genotyping of GVCFs with GATK GenotypeGVCFs.
10. Split SNPs and indels with GATK SelectVariants.
11. SNP VQSR with GATK VariantRecalibrator using HapMap, Omni, 1000G, and dbSNP truth/training sets, then ApplyRecalibration.
12. Indel VQSR with GATK VariantRecalibrator using the Mills gold-standard indels, then ApplyRecalibration.
13. Merge recalibrated SNP and indel VCFs with GATK CombineVariants.
14. Annotate variant context with GATK VariantAnnotator and evaluate callset quality with GATK VariantEval (Ti/Tv, dbSNP %, etc.).
15. Functional annotation with SnpEff.
16. Aggregate all QC and tool logs into a MultiQC report.

## Key parameters
- `--reads`: glob for paired FASTQs, e.g. `'data/*_R{1,2}.fastq.gz'` (must be quoted and use `{1,2}`).
- `--singleEnd`: only set for single-end libraries; mixed runs are not supported.
- `--genome`: iGenomes key selecting the reference bundle, typically `GRCh37` for human.
- `--bwa_index`, `--fasta`, `--gtf`: override iGenomes by pointing at custom reference files; FASTA + GTF is the minimum and other indices will be built.
- Capture kit (`kitfiles` / kit selection): supplies the target BED used to restrict BQSR, HaplotypeCaller, and coverage QC to exome regions.
- Trim Galore clipping: `--clip_r1`, `--clip_r2`, `--three_prime_clip_r1`, `--three_prime_clip_r2` for kit-specific adapter/UMI trimming.
- `--saveReference`, `--saveTrimmed`, `--saveAlignedIntermediates`: persist generated indices, trimmed FASTQs, and pre-MarkDuplicates BAMs when you need them.
- GATK ploidy is diploid (2); VQSR is the filtering method (not hard filters) and requires the standard GATK human resource bundle.
- Resource caps: `--max_cpus`, `--max_memory`, `--max_time` bound per-process requests; `-profile docker`/`singularity`/cluster profile selects execution environment.
- `--outdir` for results location, `--email` for completion notification.

## Test data
The bundled `test` profile points `readPaths` at a single tiny paired-end sample (`Testdata_R1.tiny.fastq.gz` and `Testdata_R2.tiny.fastq.gz`) hosted under the `nf-core/test-datasets` `exoseq` branch, with `singleEnd = false`, a local `./kits` capture-kit directory, and tight resource caps (`max_cpus = 2`, `max_memory = 6.GB`). Running `nextflow run nf-core/exoseq -profile test,docker` should execute the full alignment → MarkDuplicates → BQSR → HaplotypeCaller → joint genotyping → VQSR → SnpEff → MultiQC chain on this miniature sample. Expected artifacts include per-sample FastQC and Trim Galore reports, a duplicate-marked BAM with Picard metrics, Qualimap coverage output, GATK GVCF and joint-genotyped VCFs, VQSR-recalibrated SNP and indel VCFs merged via CombineVariants, a SnpEff-annotated VCF, and a consolidated MultiQC HTML report.

## Reference workflow
nf-core/exoseq (branch `dev`, GATK Best Practices exome pipeline), https://github.com/nf-core/exoseq — steps and parameters taken from `docs/usage.md`, `docs/output.md`, and `conf/test.config`.
