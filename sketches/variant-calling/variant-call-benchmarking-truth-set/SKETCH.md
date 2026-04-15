---
name: variant-call-benchmarking-truth-set
description: "Use when you need to benchmark one or more variant-caller VCFs (SNV/INDEL/SV/CNV,\
  \ germline or somatic) against a gold-standard truth set such as Genome in a Bottle\
  \ (HG002) or SEQC2, computing precision/recall/F1 with tools like hap.py, rtg vcfeval,\
  \ Truvari, SVanalyzer or witty.er. Not for calling variants from reads \u2014 assumes\
  \ VCFs already exist."
domain: variant-calling
organism_class:
- vertebrate
- diploid
- human
input_data:
- test-vcf
- truth-vcf
- reference-fasta
- high-confidence-bed
source:
  ecosystem: nf-core
  workflow: nf-core/variantbenchmarking
  url: https://github.com/nf-core/variantbenchmarking
  version: 1.4.0
  license: MIT
  slug: variantbenchmarking
tools:
- name: happy
  version: 0.3.14
- name: rtg-vcfeval
- name: truvari
- name: svanalyzer
- name: wittyer
- name: sompy
  version: 0.3.14
- name: bcftools
- name: survivor
- name: bedtools
tags:
- benchmarking
- giab
- seqc2
- precision-recall
- f1
- truth-set
- germline
- somatic
- sv
- snv
- indel
- cnv
test_data: []
expected_output: []
---

# Variant caller benchmarking against a truth set

## When to use this sketch
- You already have one or more test VCFs from variant callers and want to measure their accuracy against a gold-standard truth VCF (e.g. GIAB HG002/HG001/HG003, SEQC2).
- You need per-caller precision, recall, and F1 reports, plus TP/FP/FN VCFs for downstream inspection.
- You are benchmarking germline *or* somatic calls, and the variant class is one of: small (SNV+INDEL), SNV-only, INDEL-only, structural variants (SV), or copy-number variants (CNV).
- You want to compare multiple callers side-by-side with consolidated plots and a MultiQC / datavzrd report.
- You may need VCF preprocessing (normalization, multi-allelic splitting, decomposition, liftover hg19↔hg38) before comparison.
- You want concordance comparisons between test VCFs even when no truth set exists (GATK4 Concordance).

## Do not use when
- You need to *call* variants from FASTQ/BAM/CRAM — use an upstream variant-calling sketch (e.g. nf-core/sarek for germline/somatic short-read calling, nf-core/bacass for bacterial, nf-core/raredisease).
- You want bacterial haploid variant calling — use `haploid-variant-calling-bacterial` instead.
- You need structural variant *discovery* rather than evaluation — use a dedicated SV-calling workflow (Manta, Delly, etc.).
- You only want raw variant statistics with no truth comparison — `bcftools stats` alone is sufficient.
- You are benchmarking non-human organisms without an established truth set.

## Analysis outline
1. Parse a samplesheet of test VCFs (`id,test_vcf,caller[,subsample,liftover,test_regions,...]`) and load the truth VCF + reference FASTA/FAI.
2. Optional liftover of truth or test VCFs between hg19/hg38 via `picard LiftoverVcf` and `UCSC liftOver` for BED.
3. Standardize SVs: `variant-extractor` homogenize, `svync` reheader, `svtk standardize`, `rtg svdecompose` (to BND).
4. Preprocess VCFs: `bcftools norm` (split multi-allelic, left-align, deduplicate), contig filtering, optional `prepy` for hap.py germline.
5. Filter variants: `bcftools filter` include/exclude expressions; `SURVIVOR filter` for SV size/AF/read-support bounds.
6. Collect input statistics with `bcftools stats` (small variants) and `SURVIVOR stats` (SVs).
7. Run the selected benchmarking method(s) per caller:
   - Germline small: `hap.py` and/or `rtg vcfeval`.
   - Somatic small: `som.py` and/or `rtg vcfeval --squash-ploidy` (run SNV and INDEL separately).
   - SV: `truvari bench`, `svanalyzer benchmark`, `witty.er`; BND-only with `rtg bndeval`.
   - CNV: `truvari bench --pctseq 0`, `witty.er`, or BED `bedtools intersect`.
8. Optionally run `GATK4 Concordance` to compare test VCFs to each other.
9. Merge TP/FP/FN across callers (`bcftools merge` for small variants, `SURVIVOR merge` for SVs) to find shared vs unique calls.
10. Summarize with Python/R scripts, emit per-tool tables and plots (metrics, upset, SV length), a `datavzrd` HTML report, and a MultiQC report.

## Key parameters
- `--analysis`: `germline` | `somatic` (required).
- `--variant_type`: `small` | `snv` | `indel` | `structural` | `copynumber` (required; drives which methods are valid).
- `--method`: comma-separated from `happy,rtgtools,sompy,truvari,svanalyzer,wittyer,bndeval,intersect,concordance`.
- `--truth_id` and `--truth_vcf`: truth sample label (e.g. `HG002`, `SEQC2`) and path to gold-standard VCF.
- `--fasta` + `--fai` (required); `--sdf` optional for rtg vcfeval, auto-generated if absent.
- `--regions_bed`: high-confidence BED (GIAB Tier1, CMRG, etc.); `--targets_bed`, `--falsepositive_bed`, `--ambiguous_beds` for hap.py/sompy stratification.
- `--preprocess`: any of `split_multiallelic,normalize,deduplicate,prepy,filter_contigs`.
- `--sv_standardization`: any of `homogenize,svync,svdecompose,svtk` — `svdecompose` is required when using `bndeval`.
- SV filters: `min_sv_size` (default 30 in example configs, 0 disables), `max_sv_size` (-1 disables), `min_allele_freq`, `min_num_reads`.
- `--include_expression` / `--exclude_expression`: bcftools filter expressions.
- `--liftover`: `test` or `truth`, combined with `--chain`, `--rename_chr`, and `--dictionary`.
- Tool-specific per-row overrides in the samplesheet: Truvari (`pctsize`, `pctseq`, `pctovl`, `refdist`, `chunksize`, `dup_to_ins`, `typeignore`), SVanalyzer (`normshift`, `normdist`, `normsizediff`, `maxdist`), witty.er (`bpDistance`, `percentThreshold`, `absoluteThreshold`, `maxMatches`, `evaluationmode`).
- `--skip_plots`: `metrics`, `upset`, `svlength` to trim reporting.

## Test data
The default `test` profile benchmarks a germline HG002 structural-variant call set against the GIAB Tier1 chr21 truth VCF and high-confidence BED on GRCh37, running only `svanalyzer` with `preprocess=normalize,deduplicate,filter_contigs`. The `test_full` profile benchmarks GIAB HG002 small variants (CMRG v1.00 GRCh37) with `happy,rtgtools`, while sibling profiles (`germline_small`, `germline_sv`, `somatic_snv`, `somatic_indel`, `somatic_sv`, `somatic_cnv`, `test_happy`, `test_ga4gh`, `liftover_test`, `liftover_truth`) exercise each analysis mode. Expected outputs are per-caller TP/FP/FN VCFs, tool-specific summary JSON/CSV (e.g. `truvari summary.json`, `happy *.summary.csv`, `rtgtools *.summary.txt`, `sompy *.stats.csv`, `wittyer *.json`), merged `summary/tables/*.summary.csv`, precision/recall/F1 plots under `summary/plots/`, a `datavzrd` HTML report, and an aggregated MultiQC report.

## Reference workflow
nf-core/variantbenchmarking v1.4.0 — https://github.com/nf-core/variantbenchmarking (DOI: 10.5281/zenodo.14916661).
