---
name: sars-cov-2-variant-reporting
description: Use when you already have per-sample VCFs of SARS-CoV-2 variants (from
  Illumina WGS, ARTIC amplicon, or ONT ARTIC calling workflows) and need to produce
  filtered, annotated tabular variant reports by-sample and by-variant plus an allele-frequency
  overview plot across samples. Not for calling variants from FASTQ/BAM.
domain: variant-calling
organism_class:
- viral
- haploid
input_data:
- vcf-collection
- snpeff-annotated-vcf
source:
  ecosystem: iwc
  workflow: 'COVID-19: variation analysis reporting'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/sars-cov-2-variant-calling/sars-cov-2-variation-reporting
  version: 0.3.4
  license: MIT
tools:
- snpsift
- datamash
- column_maker
- snpfreqplot
- text_processing
tags:
- sars-cov-2
- covid-19
- reporting
- variant-summary
- allele-frequency
- viral-surveillance
test_data:
- role: gene_products_translations
  url: https://zenodo.org/record/4555735/files/NC_045512.2_feature_mapping.tsv?download=1
  sha1: 5ae9f8f1b7bc969827ad4c5ce357ef45a904e132
expected_output: []
---

# SARS-CoV-2 variation analysis reporting

## When to use this sketch
- You have a collection of per-sample VCF files of SARS-CoV-2 variants already called and snpEff-annotated by one of the galaxyproject/iwc `sars-cov-2-*-variant-calling` workflows (Illumina PE/SE WGS, ARTIC Illumina, ARTIC ONT).
- You need downstream summary tables: one row per (sample, variant) and one row per (variant) aggregated across samples, with consistent AF/DP filtering and effect annotation cleaned up to human-readable gene-product names.
- You want a single overview SVG/PDF plot of variant allele frequencies across all samples, optionally with hierarchical clustering of samples.
- You are doing SARS-CoV-2 surveillance / outbreak reporting and need consistent thresholds (e.g. AF ≥ 0.05, DP ≥ 1, DP_ALT ≥ 10) applied to a heterogeneous batch of VCFs from different sequencing modalities.

## Do not use when
- You are starting from FASTQ or BAM and still need to call variants — use the upstream `sars-cov-2-{pe,se,ont,pe-artic,ont-artic}-variant-calling` workflows first, then feed their VCF outputs here.
- You need lineage assignment or consensus sequence generation (Pangolin, Nextclade, consensus FASTA) — use a lineage/consensus workflow instead.
- You are reporting variants for a non-viral organism or a diploid/polyploid organism — this sketch assumes haploid viral calls with snpEff `4.5covid19` annotations and a NC_045512.2-specific gene product translation table.
- You want phylogenetic or transmission analysis — use a phylogenetics sketch.

## Analysis outline
1. Pre-filter the input VCF collection with SnpSift Filter to drop records with DP < 1 (avoids division-by-zero in unbiased AF recomputation).
2. Compose a SnpSift filter expression from user AF / DP / DP_ALT thresholds and re-filter each VCF, tagging (not dropping) failing records so `FILTER` reflects threshold pass/fail.
3. Extract flat tabular fields with SnpSift Extract Fields: `CHROM POS FILTER REF ALT DP AF DP4 SB EFF[*].IMPACT EFF[*].FUNCLASS EFF[*].EFFECT EFF[*].GENE EFF[*].CODON EFF[*].AA EFF[*].TRID DP4[2] DP4[3]`, one effect per line.
4. Replace snpEff NCBI RefSeq protein IDs in the `TRID` column with human-readable gene-product names via a Zenodo-hosted mapping table (doi:10.5281/zenodo.4555734).
5. Recompute an unbiased allele frequency `AF = (DP4[2] + DP4[3]) / DP` and preserve the caller-reported AF as `AFcaller` (Compute tool).
6. Collapse multiple snpEff effects per variant with Datamash, keep the highest-impact effect via a regex Replace step, and merge the per-sample tabular files into one.
7. Add `change` (REF>ALT) and `change_with_pos` columns; normalize `EFF[*].` prefixes away.
8. Use Datamash + Join to compute cross-sample statistics (min/max AF, number of samples with variant above/below threshold, collapsed sample and AF lists) and merge them back onto per-variant and per-sample rows.
9. Sort and rename into two final reports: **Combined Variant Report by Variant** and **Combined Variant Report by Sample**.
10. Split the per-sample table by sample ID and feed the collection to `snpfreqplot` (Variant Frequency Plot) with Ward.D2 hierarchical clustering to produce the overview AF heatmap.

## Key parameters
- `AF Filter` (float, default `0.05`): minimum unbiased allele frequency `(DP4[2]+DP4[3])/DP` required for a variant to be flagged as above-threshold.
- `DP Filter` (int, default `1`): minimum total site depth `DP`.
- `DP_ALT Filter` (int, default `10`): minimum variant-supporting depth, compared against `DP * AF(caller)`.
- `Number of Clusters` (int, default `1`): number of clusters for `snpfreqplot` Ward.D2 hierarchical clustering of samples.
- `gene products translations`: tabular mapping of NCBI RefSeq protein IDs (as emitted by `snpEff 4.5covid19`) to gene-product names; obtain from https://doi.org/10.5281/zenodo.4555734 (file `NC_045512.2_feature_mapping.tsv`).
- snpfreqplot advanced settings are fixed in the workflow: `output_type=svg`, `ratio=0.67`, `color=Set3`, `method=ward.D2`, `varfreq=0.0`.
- SnpSift Extract Fields field list and the Compute expression for unbiased AF are hard-coded and should not be altered.

## Test data
The test job supplies a `list` collection `Variation data to report` with four SARS-CoV-2 VCF files representing the main upstream calling modalities: `ont-artic.vcf`, `se-illumina-wgs.vcf`, `pe-illumina-wgs.vcf`, and `pe-artic.vcf` (all bundled under `test-data/`). The `gene products translations` input is fetched from Zenodo record 4555735 (`NC_045512.2_feature_mapping.tsv`, SHA-1 `5ae9f8f1b7bc969827ad4c5ce357ef45a904e132`). Default filter thresholds are used (AF=0.05, DP=1, DP_ALT=10, clusters=1). Running the workflow is expected to produce a `by_variant_report` tabular matching `test-data/by_variant_report.tsv` and a `combined_variant_report` tabular matching `test-data/combined_variant_report.tsv`; intermediate outputs (`prefiltered_variants`, `filtered_variants`, `variant_frequency_plot`, etc.) are produced but not asserted against golden files.

## Reference workflow
Galaxy IWC: `galaxyproject/iwc` — `workflows/sars-cov-2-variant-calling/sars-cov-2-variation-reporting` (`COVID-19: variation analysis reporting`), release 0.3.4, MIT-licensed. Upstream calling workflows producing compatible VCF input live as siblings under `workflows/sars-cov-2-variant-calling/` in the same repository.
