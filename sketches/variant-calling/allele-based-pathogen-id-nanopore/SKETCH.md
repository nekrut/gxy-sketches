---
name: allele-based-pathogen-id-nanopore
description: Use when you need to identify and track pathogen strains from long-read
  Nanopore metagenomic samples by mapping preprocessed reads against a known pathogen
  reference genome and calling haploid SNPs/variants with Clair3, producing per-sample
  VCFs, a consensus sequence, and mapping coverage/depth summaries.
domain: variant-calling
organism_class:
- bacterial
- haploid
- viral
input_data:
- long-reads-ont
- reference-fasta
source:
  ecosystem: iwc
  workflow: Allele-based Pathogen Identification
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/microbiome/pathogen-identification/allele-based-pathogen-identification
  version: 0.1.4
  license: MIT
  slug: microbiome--pathogen-identification--allele-based-pathogen-identification
tools:
- name: minimap2
  version: 2.28+galaxy1
- name: clair3
  version: 1.0.10+galaxy1
- name: bcftools
  version: 1.15.1+galaxy4
- name: snpsift
  version: 4.3+t.galaxy1
- name: samtools
  version: 1.15.1+galaxy2
- name: bcftools-consensus
  version: 1.15.1+galaxy4
tags:
- nanopore
- pathogen
- snp
- allele
- microbiome
- foodborne
- pathogfair
- consensus
- haploid
test_data:
- role: reference_genome_of_tested_strain
  url: https://zenodo.org/record/12190648/files/reference_genome_of_tested_strain.fasta.gz
  sha1: aeb6264c50f216061cac85426da2b7e1af20fec4
  filetype: fasta.gz
- role: collection_of_preprocessed_samples__nanopore_preprocessed_collection_of_all_samples_spike3bbarcode10
  url: https://zenodo.org/record/12190648/files/nanopore_preprocessed_collection_of_all_samples_Spike3bBarcode10.fastq.gz
  sha1: bd6e7a3eb3c8e8fbb2e0f0508fab39dd09f289e9
  filetype: fastqsanger.gz
- role: collection_of_preprocessed_samples__nanopore_preprocessed_collection_of_all_samples_spike3bbarcode12
  url: https://zenodo.org/record/12190648/files/nanopore_preprocessed_collection_of_all_samples_Spike3bBarcode12.fastq.gz
  sha1: 225b4650e7358c2b76cef6067884742d1bec374e
  filetype: fastqsanger.gz
expected_output:
- role: mapping_mean_depth_per_sample
  path: expected_output/mapping_mean_depth_per_sample.tabular
  description: Expected output `mapping_mean_depth_per_sample` from the source workflow
    test.
  assertions: []
---

# Allele-based pathogen identification from Nanopore reads

## When to use this sketch
- You have a collection of already-preprocessed Oxford Nanopore (or PacBio) long-read samples (host-filtered, quality-trimmed FASTQ) and a single reference genome for a suspected pathogen strain.
- You want to identify the pathogen at the allele/strain level by calling SNPs and small variants against that reference, not by taxonomic classification.
- You need per-sample VCFs, variant counts, a consensus FASTA per sample, and mapping coverage/depth QC to track emerging variants across samples (e.g. foodborne outbreak investigation, PathoGFAIR-style surveillance).
- Organism is effectively haploid (bacterial, viral, single-chromosome prokaryote) — Clair3 is run with `--haploid_precise`.

## Do not use when
- You still need to identify *which* pathogen is present from an unknown metagenome — run a taxonomic/gene-based pathogen identification sketch first, then come back here with the chosen reference.
- Your reads are short Illumina reads — use a short-read bacterial variant-calling sketch (bwa/bowtie2 + bcftools/GATK) instead; minimap2 presets and Clair3 models here are tuned for long reads.
- Your organism is diploid or polyploid (human, plant) — use a diploid variant-calling sketch; the haploid Clair3 model will under-call heterozygous sites.
- You need structural variants or large indels — use a dedicated SV sketch (sniffles/cuteSV).
- Raw reads still contain host contamination or adapters — run the Nanopore preprocessing sketch first; this workflow assumes its output as input.

## Analysis outline
1. Decompress the gzipped reference FASTA (CONVERTER_gz_to_uncompressed) so downstream tools can index it.
2. Map each preprocessed long-read sample to the reference with **minimap2** using a long-read preset chosen via the `samples_profile` parameter (e.g. `map-ont`, `map-pb`).
3. Call variants per sample with **Clair3** using a built-in ONT model and haploid-precise mode, emitting pileup, full-alignment, and merged VCFs.
4. Normalize the merged Clair3 VCF with **bcftools norm** against the reference (warn on REF mismatch).
5. Quality-filter the normalized VCF with **SnpSift Filter** (`QUAL > 2`).
6. Extract tabular variant fields (CHROM, POS, ID, REF, ALT, FILTER) with **SnpSift Extract Fields** and count variants per sample.
7. Build a per-sample consensus FASTA from the filtered VCF with **bcftools consensus**.
8. Compute mapping mean depth per sample with **samtools depth** + Table Compute (mean across positions).
9. Compute breadth of coverage percentage per sample with **samtools coverage** (column 6) and collapse across the sample collection into one summary table.

## Key parameters
- `samples_profile` (minimap2 `analysis_type_selector`): long-read preset, typically `map-ont` for Nanopore or `map-pb` for PacBio. Required — drives mapping sensitivity.
- minimap2 `no_end_flt: true` (disables end filtering for long reads).
- Clair3 `model_source`: built-in `r941_prom_hac_g360+g422` ONT model.
- Clair3 `ploidity_model: --haploid_precise` (hard requirement for bacterial/viral targets).
- Clair3 `snp_min_af: 0.08`, `indel_min_af: 0.15`, `qual: 0`, `include_all_ctgs: true`, `chunk_size: 5000000`.
- bcftools norm `check_ref: w` (warn), `output_type: v`.
- SnpSift Filter expression: `(QUAL > 2)`.
- SnpSift Extract Fields: `CHROM POS ID REF ALT FILTER`.
- samtools depth/coverage: skip flags `4,256,512,1024` (unmapped, secondary, QC-fail, duplicate).

## Test data
The source test profile provides a gzipped reference FASTA (`reference_genome_of_tested_strain.fasta.gz`) and a two-element Nanopore read collection (`Spike3bBarcode10` and `Spike3bBarcode12`, both `fastqsanger.gz`), all hosted on Zenodo record 12190648 and originating from the Galaxy foodborne-pathogen-detection training tutorial. The `samples_profile` parameter is left empty in the test job. The asserted output is `mapping_mean_depth_per_sample.tabular`, a two-column table of sample name and mean mapping depth; a full run additionally produces `extracted_fields_from_the_vcf_output`, `number_of_variants_per_sample`, `mapping_coverage_percentage_per_sample`, per-sample normalized/quality-filtered VCFs, and `bcftools_consensus` FASTAs.

## Reference workflow
Galaxy IWC — `workflows/microbiome/pathogen-identification/allele-based-pathogen-identification`, release 0.1.4 (MIT). Part of the PathoGFAIR / microGalaxy foodborne pathogen detection suite; see the GTN tutorial `topics/microbiome/tutorials/pathogen-detection-from-nanopore-foodborne-data` for context and intended upstream Nanopore preprocessing workflow.
