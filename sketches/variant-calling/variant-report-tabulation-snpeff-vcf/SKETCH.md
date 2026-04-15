---
name: variant-report-tabulation-snpeff-vcf
description: "Use when you have annotated VCFs (e.g. SnpEff-annotated output from\
  \ a SARS-CoV-2 or other variant-calling workflow) and need to turn them into filtered,\
  \ tabular per-sample and per-variant reports with allele-frequency, depth, and effect\
  \ columns. Not a variant caller \u2014 strictly a post-calling reporting/aggregation\
  \ step."
domain: variant-calling
organism_class:
- viral
- bacterial
- eukaryote
input_data:
- annotated-vcf-collection
source:
  ecosystem: iwc
  workflow: Generic variation analysis reporting
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/variant-calling/variation-reporting
  version: 0.1.1
  license: MIT
  slug: variant-calling--variation-reporting
tools:
- name: snpsift
  version: 4.3+t.galaxy1
- name: datamash
  version: 1.1.0
- name: column_maker
- name: text_processing
- name: split_file_to_collection
  version: 0.5.0
tags:
- vcf
- reporting
- snpeff
- allele-frequency
- aggregation
- tabular
- post-variant-calling
test_data: []
expected_output:
- role: all_variants_all_samples
  path: expected_output/all_variants_all_samples.tabular
  description: Expected output `all_variants_all_samples` from the source workflow
    test.
  assertions: []
- role: by_variant_report
  path: expected_output/by_variant_report.tabular
  description: Expected output `by_variant_report` from the source workflow test.
  assertions: []
- role: combined_variant_report
  path: expected_output/combined_variant_report.tabular
  description: Expected output `combined_variant_report` from the source workflow
    test.
  assertions: []
---

# Variant report tabulation from annotated VCFs

## When to use this sketch
- You already have a collection of SnpEff-annotated VCFs (one per sample) from an upstream variant-calling pipeline and need human-readable tables.
- You want filtered per-sample and cross-sample reports keyed by allele frequency, total depth, and alt-supporting depth.
- You need an "all variants of all samples" long-format table plus by-variant and by-sample summaries suitable for downstream plotting.
- You want recalculated allele frequencies derived from DP4 fields rather than trusting the caller's AF tag alone.

## Do not use when
- You still need to call variants from FASTQ/BAM — run an upstream caller workflow first (e.g. the SARS-CoV-2 Illumina/ONT variation workflows, or a haploid bacterial calling workflow).
- Your VCFs are not SnpEff-annotated — the SnpSift Extract Fields step depends on `EFF[*]` annotations and DP4/AF fields.
- You need germline joint-genotyped cohort VCFs processed as a single multi-sample VCF — this sketch assumes a list collection of per-sample VCFs.
- You want structural-variant, CNV, or phased-haplotype reporting — none are handled.

## Analysis outline
1. Pre-filter each input VCF with **SnpSift Filter** on `DP >= 1` to drop zero-depth records.
2. Compose a combined filter expression from the AF/DP/DP_ALT parameters using the Compose text parameter tool, and apply it with a second **SnpSift Filter** run (adding a FILTER tag rather than dropping records).
3. Extract fixed columns (CHROM, POS, FILTER, REF, ALT, DP, AF, DP4, SB and per-effect EFF fields) with **SnpSift Extract Fields**, one effect per line.
4. Recalculate allele frequency as `(DP4[2]+DP4[3])/DP` with the **Compute** (column_maker) tool, adding an `AFrecalc` column.
5. Collapse multi-effect rows per variant with **Datamash** (grouping on variant identity, collapsing EFF columns) and use **text_processing** find/replace steps to keep the highest-impact effect and tidy the header.
6. **Collapse Collection** merges per-sample tables into one flat table, adding sample name columns; further Compute steps add `change` and `change_with_pos` keys.
7. Compute cross-sample per-position statistics with **Datamash** (countunique samples, min/max AF, collapsed sample/AF lists) on both the full and PASS-only variant tables.
8. Join the per-variant stats back with the long-format variants using **Join** (easyjoin), then **Cut** and **Sort** to emit `Combined Variant Report by Variant` and `Combined Variant Report by Sample`.
9. **Split file to collection** the per-sample table by sample ID to produce a `Per-sample variants for plotting` collection.

## Key parameters
- `AF Filter` (float, default **0.05**) — minimum allele frequency retained; used in both the cutoff expression and the FILTER-tag name (`min_af_<value>`).
- `DP Filter` (int, default **1**) — minimum site depth; becomes `min_dp_<value>` in the filter tag.
- `DP_ALT Filter` (int, default **10**) — minimum reads supporting the alt allele; becomes `min_dp_alt_<value>`.
- Effective SnpSift expression: `( ( DP4[2] + DP4[3] ) < ( AF * DP ) ) | ( DP < DP_min ) | ( ( AF * DP ) < ( DP_ALT - 0.5 ) )` — variants matching any clause get tagged, not removed.
- SnpSift Extract Fields list is fixed: `CHROM POS FILTER REF ALT DP AF DP4 SB EFF[*].IMPACT EFF[*].FUNCLASS EFF[*].EFFECT EFF[*].GENE EFF[*].CODON EFF[*].AA EFF[*].TRID DP4[2] DP4[3]` with `one_effect_per_line=true`.
- PASS filter for cross-sample stats: `c4=='PASS' or c4=='.'`.

## Test data
The workflow test ships a single-element list collection containing one SnpEff-annotated VCF (`filtered variants ERR3485802.vcf`, derived from a SARS-CoV-2 ERR3485802 run) and runs with the default parameters `AF Filter=0.05`, `DP Filter=1`, `DP_ALT Filter=10`. Expected outputs are three golden tabular files — `all_variants_all_samples.tabular`, `by_variant_report.tabular`, and `combined_variant_report.tabular` — each compared with `diff` allowing up to 6 differing lines (to tolerate tool-version whitespace/ordering drift). A per-element `af_recalculated.tabular` golden is also checked against the intermediate `af_recalculated` output for the `ERR3485802` element.

## Reference workflow
Galaxy IWC workflow `variant-calling/variation-reporting` — *Generic variation analysis reporting*, release 0.1.1 (MIT). Source: https://github.com/galaxyproject/iwc/tree/main/workflows/variant-calling/variation-reporting
