---
name: cancer-variant-prioritization-pcgr-cpsr
description: "Use when you have somatic SNV/InDel VCFs (and optionally ASCAT-style\
  \ CNA segments) and/or germline VCFs from a human cancer case \u2014 typically produced\
  \ by nf-core/sarek \u2014 and need clinically interpretable, precision-oncology\
  \ reports (PCGR for somatic, CPSR for germline predisposition) with TMB/MSI/mutational-signature\
  \ estimation and tumor-only filtering support."
domain: annotation
organism_class:
- vertebrate
- diploid
- human
input_data:
- somatic-vcf
- germline-vcf
- cna-segments
- vep-cache
- pcgr-bundle
source:
  ecosystem: nf-core
  workflow: nf-core/variantprioritization
  url: https://github.com/nf-core/variantprioritization
  version: 1.0.0
  license: MIT
  slug: variantprioritization
tools:
- name: pcgr
- name: cpsr
- name: ensembl-vep
- name: bcftools
- name: tabix
- name: vcf2maf
- name: multiqc
tags:
- cancer
- precision-oncology
- somatic
- germline
- tmb
- msi
- mutational-signatures
- cna
- tumor-only
- tumor-normal
- nf-core
- sarek-downstream
test_data: []
expected_output: []
---

# Cancer variant prioritization with PCGR and CPSR

## When to use this sketch
- You already have called variants (not raw reads) for a human cancer case and need clinical interpretation / reporting.
- Somatic SNV/InDel VCFs from Mutect2, Strelka (somatic SNVs + indels), and/or FreeBayes — in tumor-normal or tumor-only mode — that should be annotated, tiered, and summarized by PCGR.
- Germline SNV/InDel VCFs from DeepVariant or HaplotypeCaller that should be screened for cancer predisposition by CPSR (ACMG classification, virtual gene panels, secondary findings).
- Optional ASCAT-like allele-specific CNA segments to fold into the somatic report.
- You want derived metrics alongside the report: tumor mutational burden (TMB), microsatellite instability (MSI) prediction, and mutational signature re-fitting (SBS).
- Downstream of nf-core/sarek is the primary supported entry point, but any VCF whose header identifies the caller will work.

## Do not use when
- You are starting from FASTQ/BAM and need alignment + variant calling — run nf-core/sarek first, then feed its outputs here.
- The organism is not human — PCGR/CPSR reference bundles are human-only (GRCh37/GRCh38).
- You only need generic VEP annotation without clinical tiering — use a plain VEP workflow instead.
- You need structural variant interpretation (SVs, fusions, large rearrangements) — PCGR handles CNAs but not SV breakends.
- You are doing hereditary (non-cancer) germline screening — CPSR is cancer-predisposition specific.
- You need MAF-level cohort analysis across many patients — this pipeline is per-sample reporting.

## Analysis outline
1. Parse samplesheet (`patient,status,sample,vcf,cna`) — status 0 routes to CPSR, status 1 to PCGR; multiple VCFs per sample (one per caller) are allowed.
2. Stage reference resources: download or extract the PCGR data bundle (`pcgr_bundleversion`) and the VEP cache (`vep_cache_version`, species).
3. bgzip+tabix any VCFs that arrive unindexed (`tabix/`).
4. Left-align and normalize each VCF with `bcftools norm` against the reference FASTA.
5. Apply caller-specific hard filters with `bcftools filter` (e.g. `FILTER="PASS"`, depth thresholds) using per-caller expressions.
6. Detect the variant caller from each VCF header and reformat records via `reformat_vcf.py`, injecting unified INFO tags `TDP`, `NDP`, `TAF`, `NAF`, `ADT`, `ADN`, `TAL`/`AL` and auto-detecting tumor/normal column order.
7. For somatic samples with multiple callers, intersect per-variant caller support into `{sample}_keys.txt` and merge into one PCGR-ready VCF per sample, taking max depth/AF across callers.
8. Reformat ASCAT/CNVkit CNA segments into the PCGR allele-specific schema (`Chromosome,Start,End,nMajor,nMinor`) when `--cna_analysis` is enabled.
9. Run PCGR per somatic sample: VEP annotation → tiering → optional TMB, MSI, signature re-fitting, CNA gene/segment reporting, tumor-only germline leakage filtering, and optional vcf2maf export.
10. Run CPSR per germline sample: VEP annotation → virtual panel screening → ACMG classification → HTML/Excel/TSV report.
11. Aggregate provenance and QC with MultiQC and emit pipeline_info (execution trace, params, software versions).

## Key parameters
- `input` — samplesheet CSV with columns `patient,status,sample,vcf,cna`.
- `genome` — `GRCh38` (or `GRCh37`); must match the VEP cache and PCGR bundle.
- `pcgr_download` / `pcgr_database_dir` / `pcgr_bundleversion` — fetch the PCGR reference bundle or point to a local/archived copy; bundle version must match the PCGR container.
- `vep_cache`, `vep_cache_version`, `vep_species` — VEP cache location (default `s3://annotation-cache/vep_cache/`, version `113`, `homo_sapiens`).
- `assay` — `WGS` | `WES` | `TARGETED`; drives TMB denominator and filter defaults.
- `cna_analysis` + `cna_overlap_pct` (default 50) — enable CNA reporting and gene-overlap threshold.
- `tumor_site` (0–30, default 0 = any), `tumor_purity`, `tumor_ploidy`, `effective_target_size_mb` (default 34).
- `estimate_tmb`, `estimate_msi`, `estimate_signatures` — toggle the three derived metrics; `tmb_display` = `coding_and_silent|coding_non_silent|missense_only`; `min_mutations_signatures` default 200.
- Tumor/normal VCF INFO tag mapping: `tumor_dp_tag`, `tumor_af_tag`, `control_dp_tag`, `control_af_tag`, `call_conf_tag` — point PCGR at the unified `TDP/NDP/TAF/NAF` tags produced by the reformat step (test profile uses `control_dp_tag=NDP`, `control_af_tag=NAF`).
- `tumor_only` + `pon_vcf` + `exclude_pon` + `exclude_likely_{hom,het}_germline` + `exclude_dbsnp_nonsomatic` + `maf_gnomad_*` (default 0.002 per population) — tumor-only germline leakage filtering.
- CPSR virtual panel: `panel_id` (default `0` = exploratory; comma-separated PanelApp IDs 1–44), `custom_list`, `diagnostic_grade_only`, `secondary_findings`, `pgx_findings`, `gwas_findings`, `pop_gnomad` (default `nfe`), `maf_upper_threshold` (default 0.9), `classify_all`, `ignore_noncoding`.
- Per-caller filter expressions (`filter_mutect2`, `filter_strelka_snvs`, `filter_strelka_indels`, `filter_haplotypecaller`, `filter_deepvariant`, `filter_freebayes_*`) — default `-i 'FORMAT/DP>10'`; test profile tightens Mutect2/Strelka to `FILTER="PASS"`.
- VEP runtime: `vep_n_forks` (4), `vep_buffer_size` (500), `vep_pick_order` (MANE-first), `vep_gencode_basic`, `vep_no_intergenic`.
- `vcf2maf` — also emit a MAF file for the somatic input; `no_html` — skip HTML if using a downsampled cache.

## Test data
The `test` profile points at the nf-core/test-datasets `variantprioritization` branch samplesheet (`samplesheets/default.csv`) together with a chr22-downsampled VEP cache (`vep_cache_113_GRCh38_chr22.tar.gz`) and a chr22-downsampled PCGR bundle (`pcgr_ref_grch38_chr22.tar.gz`), both hosted on GitHub. Inputs exercise tumor-normal somatic calling (Mutect2 + Strelka SNVs/indels with `FILTER="PASS"`) plus germline VCFs, with `cna_analysis`, `vcf2maf`, and the TMB/MSI/signature estimators all enabled; `no_html=true` is set because the downsampled cache cannot render the full HTML report. Running the test profile is expected to produce per-sample PCGR outputs under `pcgr/{sample}/` (`.xlsx`, `.maf`, `.pass.tsv.gz`, `.pass.vcf.gz`, `.snv_indel_ann.tsv.gz`, `.msigs.tsv.gz`, `.tmb.tsv`, `.cna_gene*.tsv.gz`, `.cna_segment.tsv.gz`, `.conf.yaml`), CPSR outputs under `cpsr/{sample}/`, consolidated somatic VCFs under `custom/pcgr_ready_vcf/`, and a MultiQC summary under `multiqc/`. The `test_full` profile runs the same configuration against the full-size samplesheet and the production VEP cache (`s3://annotation-cache/vep_cache/`) with `pcgr_download=true`.

## Reference workflow
nf-core/variantprioritization v1.0.0 (https://github.com/nf-core/variantprioritization, DOI 10.5281/zenodo.19480994), built around PCGR (Nakken et al., Bioinformatics 2018) and CPSR (Nakken et al., Int J Cancer 2021), designed to consume nf-core/sarek outputs.
