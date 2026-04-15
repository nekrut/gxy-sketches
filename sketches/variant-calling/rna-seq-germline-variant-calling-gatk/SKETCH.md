---
name: rna-seq-germline-variant-calling-gatk
description: Use when you need to call SNVs and small indels from bulk RNA-seq (Illumina
  short reads) following the GATK4 RNA-seq best practices workflow, including STAR
  2-pass alignment, SplitNCigarReads, BQSR and HaplotypeCaller soft-filtering. Intended
  for human/vertebrate samples where you want variants from expressed transcripts
  rather than whole-genome DNA.
domain: variant-calling
organism_class:
- vertebrate
- diploid
- eukaryote
input_data:
- short-reads-paired
- reference-fasta
- gtf-annotation
source:
  ecosystem: nf-core
  workflow: nf-core/rnavar
  url: https://github.com/nf-core/rnavar
  version: 1.2.3
  license: MIT
  slug: rnavar
tools:
- name: star
- name: samtools
- name: picard-markduplicates
- name: gatk4
- name: bcftools
- name: snpeff
- name: ensembl-vep
- name: fastqc
  version: 0.12.1
- name: multiqc
tags:
- rna-seq
- variant-calling
- gatk4
- haplotypecaller
- splitncigarreads
- bqsr
- snv
- indel
- annotation
test_data: []
expected_output: []
---

# RNA-seq germline variant calling (GATK4 best practices)

## When to use this sketch
- You have bulk Illumina RNA-seq FASTQ files (single- or paired-end) and want to call SNVs and small indels from expressed transcripts.
- Samples are from a species with a reference genome FASTA + GTF (human GRCh38 is the default, but any vertebrate/eukaryote works).
- You want the canonical GATK4 RNA-seq variant pipeline: STAR 2-pass → MarkDuplicates → SplitNCigarReads → (BQSR) → HaplotypeCaller → VariantFiltration → annotation (snpEff / VEP / bcftools annotate).
- You optionally want HLA typing from the same RNA-seq reads via Seq2HLA, or UMI extraction via UMI-tools.
- You want soft-filtered VCFs (FILTER column flagged, records retained) rather than hard filtering.

## Do not use when
- You have DNA-seq (WGS/WES) input — use a DNA germline variant-calling sketch (e.g. nf-core/sarek) instead.
- You are calling somatic tumor variants from RNA — this pipeline targets germline HaplotypeCaller, not Mutect2 tumor-only/tumor-normal.
- You need transcript quantification, differential expression, or splicing analysis — use an rna-seq expression sketch (e.g. nf-core/rnaseq) instead.
- You are working with a haploid organism where `ploidy=1` matters — use a haploid variant-calling sketch.
- You want structural variants or fusion calls from RNA — use an SV/fusion sketch.
- You need allele-specific expression or RNA editing detection as primary output — this pipeline does not compute those.

## Analysis outline
1. Concatenate re-sequenced FASTQs per sample (`cat`).
2. Raw-read QC (`FastQC`).
3. Optional: extract UMIs from reads (`UMI-tools extract`) when `--extract_umi` is set.
4. Optional: HLA typing from FASTQ (`Seq2HLA`) when `--tools seq2hla` is set.
5. Splice-aware alignment to the reference in 2-pass mode (`STAR`), using `sjdbOverhang = read_length - 1`.
6. Sort/index BAM and collect alignment stats (`samtools sort/index/stats/flagstat`).
7. Mark (or optionally remove) duplicates (`Picard MarkDuplicates`).
8. Build an interval list from the GTF/BED and scatter it into N chunks (`GATK4 BedToIntervalList` + `IntervalListTools`, default 25 scatters).
9. Split reads spanning introns per scatter (`GATK4 SplitNCigarReads`).
10. Base quality score recalibration (`GATK4 BaseRecalibrator` + `ApplyBQSR`) using `dbsnp` and `known_indels`; skipped with `--skip_baserecalibration`.
11. Germline variant calling per scatter (`GATK4 HaplotypeCaller`, optional GVCF mode).
12. Merge per-scatter VCFs (`GATK4 MergeVcfs`) and index (`Tabix`).
13. Soft-filter variants (`GATK4 VariantFiltration`) with RNA-seq-appropriate thresholds (QD, FS, SNP clusters).
14. Annotate variants with one or more of `snpEff`, `Ensembl VEP`, `bcftools annotate` (selected via `--tools`).
15. Aggregate QC across FastQC / STAR / samtools / MarkDuplicates / snpEff / VEP into a `MultiQC` report.

## Key parameters
- `--input` — samplesheet CSV with columns `sample,fastq_1,fastq_2` (or `bam/bai`, `cram/crai`, `vcf/tbi` to enter the pipeline mid-way). Same `sample` across rows triggers FASTQ merging.
- `--genome GRCh38` (default) or explicit `--fasta`, `--gtf`/`--gff`, `--fasta_fai`, `--dict`, `--star_index`, `--exon_bed`.
- `--read_length 150` (default) — must match input reads; drives STAR `sjdbOverhang`.
- `--aligner star` (only supported aligner); `--star_twopass true` (default); `--star_ignore_sjdbgtf`, `--star_max_intron_size`, `--star_max_memory_bamsort`, `--star_bins_bamsort`, `--star_max_collapsed_junc 1000000`.
- `--seq_platform illumina` (default), `--seq_center` for BAM read-group PL/CN fields.
- `--remove_duplicates false` (default: mark only). `--bam_csi_index` for genomes with chromosomes >512 Mb (disables VariantFiltration).
- Known-sites for BQSR: `--dbsnp` + `--dbsnp_tbi`, `--known_indels` + `--known_indels_tbi`. Use `--skip_baserecalibration` for non-model organisms without known sites.
- `--gatk_interval_scatter_count 25` (default) — parallelism for SplitNCigarReads / HaplotypeCaller.
- `--gatk_hc_call_conf 20` — HaplotypeCaller min phred-scaled confidence. `--generate_gvcf` to also emit GVCFs. `--no_intervals` to call across the whole genome.
- VariantFiltration defaults (RNA-seq recommended): `--gatk_vf_qd_filter 2.0`, `--gatk_vf_fs_filter 30.0`, `--gatk_vf_window_size 35`, `--gatk_vf_cluster_size 3`. Skip with `--skip_variantfiltration`.
- `--tools` — comma-separated subset of `seq2hla,bcfann,snpeff,vep,merge` (`merge` runs both snpEff and VEP and combines their annotations). Skip annotation entirely with `--skip_variantannotation`.
- Annotation cache: `--snpeff_cache`, `--vep_cache` (default `s3://annotation-cache/...`), `--snpeff_db`, `--vep_genome`, `--vep_species`, `--vep_cache_version`, `--download_cache`, `--outdir_cache`.
- VEP plugins: `--vep_dbnsfp` (+ `--dbnsfp`, `--dbnsfp_tbi`, `--dbnsfp_fields`), `--vep_loftee`, `--vep_spliceai` (+ `spliceai_snv[_tbi]`, `spliceai_indel[_tbi]`), `--vep_spliceregion`, `--vep_custom_args` (default `--everything --filter_common --per_gene --total_length --offline --format vcf`).
- bcftools annotate custom sources: `--bcftools_annotations`, `--bcftools_annotations_tbi`, `--bcftools_header_lines`, optional `--bcftools_columns`.
- UMI extraction: `--extract_umi`, `--umitools_extract_method string|regex`, `--umitools_bc_pattern`, `--umitools_bc_pattern2`, `--umitools_umi_separator`.
- Stage skips: `--skip_intervallisttools`, `--skip_multiqc`, `--skip_exon_bed_check`.

## Test data
The bundled `-profile test` uses a tiny synthetic `testdata.nf-core.rnavar` genome served from the nf-core/test-datasets `rnavar` branch, driven by `tests/csv/1.0/fastq_single.csv` (a single-sample FASTQ samplesheet). It supplies small sarscov2 test VCFs for `bcftools_annotations` plus dbSNP and Mills/1000G known-indels VCFs from the `homo_sapiens` test-data area so the BQSR step exercises real known-sites handling. A successful run produces a per-sample HaplotypeCaller VCF (`variant_calling/<SAMPLE>/<SAMPLE>.haplotypecaller.vcf.gz` + `.tbi`), a soft-filtered VCF (`.haplotypecaller.filtered.vcf.gz`), STAR/samtools/FastQC/MarkDuplicates stats under `reports/stats/<SAMPLE>/`, and a `reports/multiqc/multiqc_report.html`. The full-size profile (`-profile test_full`) runs against GM12878 Illumina RNA-seq (SRA SRR5665260, ~38.6M PE 2×151 bp reads) on GRCh38 with `--tools merge --skip_baserecalibration` and `read_length 101`, producing annotated `*_snpEff_VEP.ann.vcf.gz` files per sample.

## Reference workflow
nf-core/rnavar v1.2.3 (https://github.com/nf-core/rnavar), a GATK4 RNA-seq variant-calling pipeline maintained by Praveen Raj, Maxime U. Garcia and Nicolas Vannieuwkerke. Implements GATK4 RNA-seq best practices with STAR 2-pass alignment, SplitNCigarReads, optional BQSR, HaplotypeCaller, VariantFiltration, and annotation via snpEff / Ensembl VEP / bcftools annotate. DOI: 10.5281/zenodo.6669636.
