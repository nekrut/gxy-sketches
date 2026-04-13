---
name: gene-based-pathogen-identification-nanopore
description: Use when you need to identify pathogenic bacteria in nanopore metagenomic
  sequencing data by assembling reads into contigs and screening them for virulence
  factors (VFs) and antimicrobial resistance (AMR) genes. Designed for preprocessed
  ONT long reads from foodborne/microbiome samples.
domain: metagenomics
organism_class:
- bacterial
- microbial-community
input_data:
- long-reads-ont
- preprocessed-fastq-collection
source:
  ecosystem: iwc
  workflow: Gene-based Pathogen Identification
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/microbiome/pathogen-identification/gene-based-pathogen-identification
  version: '0.1'
  license: MIT
tools:
- flye
- medaka
- bandage
- abricate
- vfdb
- ncbi-amr
tags:
- nanopore
- pathogen
- virulence
- amr
- metagenomics
- assembly
- foodborne
- pathogfair
test_data:
- role: collection_of_preprocessed_samples__nanopore_preprocessed_collection_of_all_samples_spike3bbarcode10
  url: https://zenodo.org/record/12190648/files/nanopore_preprocessed_collection_of_all_samples_Spike3bBarcode10.fastq.gz
  sha1: bd6e7a3eb3c8e8fbb2e0f0508fab39dd09f289e9
  filetype: fastqsanger.gz
- role: collection_of_preprocessed_samples__nanopore_preprocessed_collection_of_all_samples_spike3bbarcode12
  url: https://zenodo.org/record/12190648/files/nanopore_preprocessed_collection_of_all_samples_Spike3bBarcode12.fastq.gz
  sha1: 225b4650e7358c2b76cef6067884742d1bec374e
  filetype: fastqsanger.gz
expected_output:
- role: extracted_samples_ids
  path: expected_output/extracted_samples_IDs.txt
  description: Expected output `extracted_samples_IDs` from the source workflow test.
  assertions: []
---

# Gene-based Pathogen Identification (Nanopore)

## When to use this sketch
- You have a collection of preprocessed Oxford Nanopore FASTQ samples (host-filtered, quality-trimmed) and want to decide whether each sample carries a bacterial pathogen.
- Your pathogenicity call should be driven by detection of virulence factor (VF) genes and antimicrobial resistance (AMR) genes on assembled contigs, not by taxonomic profiling alone.
- You need per-sample contig FASTAs plus tabular VF and AMR reports suitable for tracking pathogens across a microbiome study (e.g. foodborne surveillance, PathoGFAIR-style pipelines).
- The upstream data came from the Nanopore Preprocessing workflow, so reads are already QC'd and depleted of host.

## Do not use when
- You only have short-read Illumina data — use a short-read assembly + ABRicate workflow instead.
- You want taxonomic pathogen identification by read classification (Kraken2/Bracken/MetaPhlAn); see a `taxonomic-pathogen-identification` sketch.
- You need eukaryotic pathogen detection, SNP-based outbreak typing, or plasmid reconstruction — this sketch is scoped to bacterial VF/AMR gene screening.
- Your reads are raw/unfiltered; run a nanopore preprocessing sketch first.
- You want antibiotic resistance prediction with curated mutation catalogs (e.g. TB-Profiler, AMRFinderPlus point mutations) rather than acquired-gene screening.

## Analysis outline
1. Extract per-sample identifiers from the input collection (Galaxy `collection_element_identifiers`) and split them one-per-file so downstream steps can tag contigs with the originating sample.
2. Wrap the sample collection as a list-of-lists so Flye can run per sample (`Build list`).
3. Metagenomic de novo assembly of each sample's ONT reads with **Flye** in `--meta --nano-hq` mode to produce contigs and an assembly graph.
4. Polish the Flye consensus against the raw reads with the **medaka consensus pipeline** to yield the final per-sample contig FASTA.
5. Visualize the assembly graph with **Bandage Image** (JPG) for QC.
6. Rename contig headers to embed the sample ID: FASTA→tabular, regex replace header with `<sampleID>_<contigN>`, tabular→FASTA, emitting a merged `contigs` FASTA per sample.
7. Screen the polished contigs with **ABRicate** against the **VFDB** database to produce the `vfs` virulence-factor report.
8. Screen the same contigs with **ABRicate** against the **NCBI AMR** database to produce the `amrs` resistance-gene report.
9. Post-process both ABRicate reports: rename the `#FILE` column to `SampleID` and replace filename with the true sample identifier so results are joinable across samples.

## Key parameters
- Flye: `mode = --nano-hq`, `meta = true`, `iterations = 1`, `keep_haplotypes = false`, `scaffold = false`, `no_alt_contigs = false`.
- Medaka: basecaller model `m = r941_min_hac_g507`, batch `b = 100`; emit consensus, probs, calls, gaps, log.
- ABRicate (VF): `db = vfdb`, `min_dna_id = 50.0`, `min_cov = 50.0`.
- ABRicate (AMR): `db = ncbi`, `min_dna_id = 50.0`, `min_cov = 50.0`.
- Bandage Image: `output_format = jpg`, `height = 1000`.
- Header rewriting: regex `^(.+)$` replaced with composed `<sampleID>_$1` so every contig is prefixed with its source sample.

## Test data
Two preprocessed nanopore FASTQ samples from a foodborne spike-in experiment — `nanopore_preprocessed_collection_of_all_samples_Spike3bBarcode10.fastq.gz` and `...Spike3bBarcode12.fastq.gz`, hosted on Zenodo record 12190648 — are supplied as a Galaxy list collection named `collection_of_preprocessed_samples`. They correspond to barcodes 10 and 12 from the GTN "pathogen detection from nanopore foodborne data" tutorial. The minimal assertion in the test spec checks that `extracted_samples_IDs.txt` (the list of sample identifiers extracted from the input collection) matches the golden file; a full run additionally yields per-sample polished contigs FASTA, a Bandage assembly-graph image, and the ABRicate `vfs` (VFDB) and `amrs` (NCBI) tabular reports with sample-tagged rows.

## Reference workflow
Galaxy IWC — `workflows/microbiome/pathogen-identification/gene-based-pathogen-identification` (PathoGFAIR / microGalaxy), release 0.1 (2024-04-18), MIT. Companion tutorial: GTN `microbiome/pathogen-detection-from-nanopore-foodborne-data`.
