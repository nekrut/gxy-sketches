---
name: kraken2-krona-taxonomy-profiling-nanopore
description: Use when you need to taxonomically profile preprocessed microbiome sequencing
  reads (typically Nanopore long reads) against a Kraken2 database and produce an
  interactive Krona pie chart for pathogen identification or community overview. Suitable
  for foodborne pathogen detection workflows where reads have already been QC-filtered
  and host-depleted.
domain: metagenomics
organism_class:
- bacterial
- viral
- eukaryote
input_data:
- long-reads-ont
- kraken2-database
source:
  ecosystem: iwc
  workflow: Taxonomy Profiling and Visualization with Krona
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/microbiome/pathogen-identification/taxonomy-profiling-and-visualization-with-krona
  version: '0.1'
  license: MIT
  slug: microbiome--pathogen-identification--taxonomy-profiling-and-visualization-with-krona
tools:
- name: kraken2
  version: 2.1.1+galaxy1
- name: krakentools-kreport2krona
  version: 1.2+galaxy1
- name: krona
tags:
- metagenomics
- taxonomy
- kraken2
- krona
- nanopore
- pathogen-detection
- microbiome
- shotgun
test_data:
- role: collection_of_preprocessed_samples__nanopore_preprocessed_collection_of_all_samples_spike3bbarcode10
  url: https://zenodo.org/record/12190648/files/nanopore_preprocessed_collection_of_all_samples_Spike3bBarcode10.fastq.gz
  sha1: bd6e7a3eb3c8e8fbb2e0f0508fab39dd09f289e9
  filetype: fastqsanger.gz
- role: collection_of_preprocessed_samples__nanopore_preprocessed_collection_of_all_samples_spike3bbarcode12
  url: https://zenodo.org/record/12190648/files/nanopore_preprocessed_collection_of_all_samples_Spike3bBarcode12.fastq.gz
  sha1: 225b4650e7358c2b76cef6067884742d1bec374e
  filetype: fastqsanger.gz
expected_output: []
---

# Kraken2 + Krona taxonomy profiling (Nanopore microbiome)

## When to use this sketch
- You have a collection of preprocessed (QC-trimmed, host-depleted) shotgun sequencing reads — typically Nanopore long reads in `fastqsanger`/`fastqsanger.gz` — and want per-sample taxonomic profiles from kingdom down to species.
- Your goal is pathogen identification or a quick community overview, and you want an interactive Krona pie chart plus a tabular abundance report.
- You are comfortable selecting an existing Kraken2 database (e.g. StandardPF, MinusB, PlusPF, Viral) hosted in Galaxy.
- The samples have already been run through a preprocessing step such as the Nanopore Preprocessing workflow; this sketch does not do QC, adapter trimming, or host removal.

## Do not use when
- You need marker-gene / 16S amplicon profiling — use an amplicon (DADA2/QIIME2) sketch instead.
- You need strain-level resolution, MAG recovery, or functional profiling — use a metagenome assembly / binning sketch or a HUMAnN-style functional profiling sketch.
- Reads are raw and unfiltered — run a preprocessing / host-depletion sketch first, then feed its output here.
- You need quantitative abundance re-estimation correcting for genome size and ambiguous assignments — use a Bracken-based sketch.
- You only have assembled contigs and want taxonomic annotation of bins/contigs — use a CAT/BAT or GTDB-Tk sketch.

## Analysis outline
1. Ingest a Galaxy dataset collection of preprocessed per-sample FASTQ files (single-end Nanopore reads).
2. Run **Kraken2** on each sample against the user-selected prebuilt Kraken2 database, producing a classification file and a standard Kraken2 report.
3. Convert each Kraken2 report to Krona-compatible text with **KrakenTools `kreport2krona`**.
4. Render an interactive HTML **Krona pie chart** from the converted report for visual exploration.

## Key parameters
- Kraken2 `single_paired_selector`: `no` (single-end; Nanopore reads are not paired).
- Kraken2 `kraken2_database`: user-selected prebuilt index (e.g. `k2_standard`, `k2_pluspf`, `k2_minusb`); choose based on expected taxa and RAM budget.
- Kraken2 `confidence`: `0.1` — minimum confidence score for a classification.
- Kraken2 `min_base_quality`: `0`.
- Kraken2 `minimum_hit_groups`: `2`.
- Kraken2 `report.create_report`: `true`; `use_mpa_style`: `false`; `report_zero_counts`: `false`; `report_minimizer_data`: `false`.
- Kraken2 `quick`: `false`; `split_reads`: `false`; `use_names`: `false`.
- KrakenTools `kreport2krona` `intermediate_ranks`: `false` (only standard ranks in the Krona input).
- Krona `type_of_data_selector`: `text`; `root_name`: `Root`; `combine_inputs`: `false` (one chart per sample).

## Test data
The workflow test ships a Galaxy collection of two preprocessed Nanopore FASTQ samples downloaded from Zenodo record 12190648: `nanopore_preprocessed_collection_of_all_samples_Spike3bBarcode10.fastq.gz` and `..._Spike3bBarcode12.fastq.gz`, both `fastqsanger.gz`. The Kraken2 database parameter is set to `k2_minusb_20210517`. The test asserts that the converted Krona-format report for the `Spike3bBarcode12` element matches a local golden file (`converted_kraken_report_collection_of_all_samples_Spike3bBarcode12.tabular`); the Krona HTML pie chart is produced as a downstream visualization artifact.

## Reference workflow
Galaxy IWC — `workflows/microbiome/pathogen-identification/taxonomy-profiling-and-visualization-with-krona` ("Taxonomy Profiling and Visualization with Krona"), release 0.1. Tools: Kraken2 `2.1.1+galaxy1`, KrakenTools `kreport2krona` `1.2+galaxy1`, Krona pie chart `2.7.1+galaxy0`. Part of the PathoGFAIR / microGalaxy foodborne pathogen detection training track.
