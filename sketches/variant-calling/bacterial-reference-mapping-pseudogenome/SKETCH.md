---
name: bacterial-reference-mapping-pseudogenome
description: Use when you need to map bacterial WGS reads (Illumina short-read or
  Oxford Nanopore long-read) to a reference genome, call haploid variants, and build
  per-sample pseudogenomes plus a multi-sample SNP alignment suitable for downstream
  phylogenetics or outbreak analysis.
domain: variant-calling
organism_class:
- bacterial
- haploid
input_data:
- short-reads-paired
- short-reads-single
- long-reads-ont
- reference-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/bactmap
  url: https://github.com/nf-core/bactmap
  version: 1.0.0
  license: MIT
tools:
- fastp
- adapterremoval
- porechop
- filtlong
- nanoq
- rasusa
- bowtie2
- bwa-mem2
- minimap2
- samtools
- freebayes
- clair3
- bcftools
- bedtools
- seqtk
- snp-sites
- multiqc
tags:
- bacteria
- wgs
- mapping
- pseudogenome
- snp-alignment
- haploid
- illumina
- nanopore
- outbreak
- phylogenetics
test_data: []
expected_output: []
---

# Bacterial reference mapping to pseudogenome and SNP alignment

## When to use this sketch
- You have bacterial WGS data (Illumina paired/single-end or ONT long reads) and a single closely related reference FASTA.
- You want per-sample filtered VCFs **and** a multi-sample pseudogenome alignment (one base per reference position) for downstream phylogenetics, SNP distance, or outbreak clustering.
- You need a haploid (ploidy=1) mapping-based SNP workflow, not de novo assembly.
- Mixed cohorts of samples sequenced on the same platform; run short-read and long-read cohorts as separate invocations for cleaner MultiQC reports.

## Do not use when
- You need a de novo assembly or annotation of each isolate — use an assembly sketch (e.g. nf-core/bacass-style `bacterial-short-read-assembly`).
- You need structural variants, large indels, or copy-number calls — mapping-to-consensus masks these.
- Your organism is eukaryotic/diploid/polyploid — this pipeline hard-codes haploid assumptions and masks low-coverage sites. Use a diploid variant-calling sketch instead.
- You need metagenomic profiling or strain deconvolution from mixed communities.
- You only have a single isolate and do not need the cross-sample pseudogenome alignment — a lighter single-sample variant sketch is cheaper.

## Analysis outline
1. Index the reference FASTA (`bwa-mem2 index` / `bowtie2-build` for short reads, `minimap2 -d` for long reads; `samtools faidx`).
2. Raw-read QC with `FastQC` (or `falco`) and FASTQ summary stats with `fastq-scan`.
3. Short-read preprocessing with `fastp` (default) or `AdapterRemoval2`: adapter clip, quality trim, optional pair merge, length filter.
4. Long-read preprocessing with `Porechop`/`Porechop_ABI` for adapters and `Nanoq` (default) or `Filtlong` for length/quality filtering.
5. Optional per-sample run merging via `cat` when a sample has multiple runs/lanes.
6. Downsample with `Rasusa` to a target coverage (default 100×) to bound runtime.
7. Map reads to the reference: `Bowtie2` (default) or `BWA-MEM2` for short reads; `minimap2` for ONT.
8. Sort/index alignments with `samtools sort`/`index` and summarise with `samtools stats`/`flagstat`/`idxstats`.
9. Call variants: `FreeBayes` (haploid) for short reads; `Clair3` (with a user-supplied model) for ONT, followed by `bcftools norm`.
10. Filter variants with `bcftools filter` and summarise with `bcftools stats`.
11. Build per-sample pseudogenome: `bcftools consensus` combined with `bedtools genomecov` to mask positions below a coverage threshold with `N`.
12. Assess per-sample quality with `seqtk` (non-ACGT fraction); drop samples exceeding `non_GATC_threshold` into `low_quality_pseudogenomes.tsv`.
13. Concatenate passing pseudogenomes into `aligned_pseudogenomes.fas` and extract informative sites with `SNP-sites`.
14. Aggregate all QC/variant reports with `MultiQC`.

## Key parameters
- `--input` — CSV samplesheet with columns `sample,run_accession,instrument_platform,fastq_1,fastq_2`; `instrument_platform` must be `ILLUMINA` or `OXFORD_NANOPORE`.
- `--fasta` — reference genome (single or multi-FASTA, optionally gzipped).
- `--clair3_model` — **required** for ONT data; path to a Clair3 model matching the basecaller/chemistry (`--clair3_platform ont` is fixed).
- `--shortread_mapping_tool` — `bowtie2` (default) or `bwa`.
- `--perform_shortread_qc` / `--perform_longread_qc` — on by default; toggle with `shortread_qc_tool` (`fastp`|`adapterremoval`) and `longread_filter_tool` (`nanoq`|`filtlong`).
- `--shortread_qc_minlength` (default 50), `--longread_qc_qualityfilter_minlength` (default 1000), `--longread_qc_qualityfilter_minquality` (default Q7).
- `--perform_subsampling` (on) and `--subsampling_depth_cutoff` (default 100×) — disable for very small genomes or already-downsampled input.
- `--perform_runmerging` (on) — concatenates same-`sample` runs after preprocessing.
- `--genomecov_threshold` (default 9) — per-base depth below which pseudogenome positions are masked as `N`.
- `--non_GATC_threshold` (default 0.5) — maximum allowed fraction of non-ACGT bases per pseudogenome before the sample is dropped from the alignment.
- Ploidy is implicitly 1 (FreeBayes haploid mode and single-consensus extraction); do not attempt diploid calling.

## Test data
The pipeline's `test` profile pulls a small mixed-platform samplesheet from `nf-core/test-datasets` (bactmap branch) and maps it against the *Bacteroides fragilis* reference `genome.fna.gz` from the nf-core modules test data. Running `nextflow run nf-core/bactmap -profile test,docker --outdir results` exercises read QC, preprocessing, subsampling, mapping, variant calling and pseudogenome alignment, and should produce per-sample filtered VCFs under `filtered_variants/`, per-sample pseudogenomes under `pseudogenomes/`, a concatenated `pseudogenomes/aligned_pseudogenomes.fas`, an `snpsites/filtered_alignment.fas` of informative sites, and a `multiqc/multiqc_report.html`. The `test_full` profile uses the same samplesheet/reference layout at full scale.

## Reference workflow
nf-core/bactmap v1.0.0 (template version 2.0.0) — https://github.com/nf-core/bactmap, MIT licensed. Pipeline summary and parameter semantics taken from the repository README, `docs/usage.md`, `docs/output.md`, and `nextflow_schema.json`.
