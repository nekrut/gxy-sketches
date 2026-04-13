---
name: deep-learning-germline-variant-calling-human
description: Use when you need to call germline SNVs and small indels from human short-read
  BAM files using Google's DeepVariant deep-learning caller, against standard human
  references (hg19, GRCh38, GRCh37, hs37d5). Supports whole-genome or whole-exome
  mode and multi-sample parallel calling.
domain: variant-calling
organism_class:
- vertebrate
- diploid
- human
input_data:
- aligned-bam
- reference-fasta
- target-bed
source:
  ecosystem: nf-core
  workflow: nf-core/deepvariant
  url: https://github.com/nf-core/deepvariant
  version: '1.0'
  license: MIT
tools:
- deepvariant
- samtools
- bgzip
- nextflow
tags:
- human
- germline
- snv
- indel
- deep-learning
- wgs
- wes
- vcf
test_data: []
expected_output: []
---

# Human germline variant calling with DeepVariant

## When to use this sketch
- Input is one or more aligned human short-read BAM files and you want germline SNV/indel calls.
- Reads were aligned against a standard human reference build (hg19, GRCh38/h38, GRCh37 primary, or hs37d5).
- You want a deep-learning caller (DeepVariant) rather than a classical Bayesian caller, typically for higher accuracy on Illumina data.
- Whole-genome or whole-exome experiments; a BED file restricting calling to target/interval regions is available.
- You want multiple BAM files processed in parallel with one VCF emitted per sample.

## Do not use when
- Calling variants on a haploid bacterial genome → use `haploid-variant-calling-bacterial`.
- Calling somatic/tumor variants or tumor-normal pairs → use a somatic variant-calling sketch.
- Calling structural variants or large CNVs → use a structural-variants sketch.
- Starting from raw FASTQ without alignment → run an alignment workflow first, or use a pipeline that includes BWA/bwa-mem2 alignment.
- Long-read (PacBio HiFi / ONT) data where a long-read-specific DeepVariant model or caller is preferable → use a long-read variant-calling sketch.
- Joint/cohort genotyping across many samples (GVCF merging) — this pipeline emits independent per-sample VCFs.

## Analysis outline
1. Resolve reference genome: either download a prepared bundle via `--genome` (hg19, hg19chr20, h38, grch37primary, hs37d5) or accept user-supplied `--fasta`.
2. Preprocess reference: generate `.fai`, bgzipped `.fasta.gz`, `.gz.fai`, and `.gzi` with samtools/bgzip if not provided.
3. Preprocess each BAM: ensure BAM index (`.bai`) and required read-group headers exist; generate if missing.
4. DeepVariant `make_examples`: convert BAM + reference into tensor example images over regions from the BED file.
5. DeepVariant `call_variants`: run the trained CNN model on the example tensors to produce a tfrecord of predictions.
6. DeepVariant `postprocess_variants`: convert predictions into a standard VCF v4.2 file per input sample.
7. Publish per-sample `{sample}.vcf` to the results directory alongside pipeline info.

## Key parameters
- `--bam` or `--bam_folder`: single BAM path or directory of BAMs for parallel multi-sample calling.
- `--bam_file_prefix`: optional filter to restrict which BAMs in `--bam_folder` are processed.
- `--bed`: **required** interval BED defining regions to call over.
- `--genome`: one of `hg19`, `hg19chr20`, `h38`, `grch37primary`, `hs37d5` — selects a prepared reference bundle from `--genomes_base` (default `s3://deepvariant-data/genomes`).
- `--fasta` / `--fai` / `--fastagz` / `--gzfai` / `--gzi`: user-supplied reference files; any missing ones are auto-generated in preprocessing.
- `--exome`: flag that switches DeepVariant to the WES-trained model — set this for capture/exome BAMs, leave off for WGS.
- `--outdir`: results directory (default `results`).
- Resource caps: `--max_cpus`, `--max_memory`, `--max_time`. Note `make_examples` memory should be ~10–15× the BAM file size (handled automatically in `base.config`).
- Profiles: combine `-profile <env>,docker` (or `singularity`/`conda`) for containerized execution.

## Test data
The bundled `test` profile runs on a downsampled human NA12878 BAM restricted to a 100 kbp window around chr20:10 Mb (`NA12878_S1.chr20.10_10p1mb.bam`) with an accompanying interval BED (`test_nist.b37_chr20_100kbp_at_10mb.bed`), using the prepared `hg19chr20` reference bundle. Resources are capped at 2 CPUs and 6 GB RAM. A successful run emits a single per-sample VCF v4.2 file named after the BAM sample (e.g. `NA12878_S1.chr20.10_10p1mb.vcf`) into `results/`, plus a `pipeline_info` directory with Nextflow execution reports.

## Reference workflow
nf-core/deepvariant v1.0 (MIT) — https://github.com/nf-core/deepvariant. Wraps Google DeepVariant (`make_examples` → `call_variants` → `postprocess_variants`) with samtools/bgzip-based reference and BAM preprocessing.
