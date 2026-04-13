---
name: host-decontamination-long-reads
description: Use when you need to remove host or contaminant sequences (e.g. human,
  bee, mouse) from long-read metagenomic/microbiome sequencing data (Nanopore or PacBio)
  by mapping reads to a host reference and keeping only the unmapped reads as clean
  FASTQ for downstream microbiome analysis.
domain: metagenomics
organism_class:
- microbiome
- host-associated
input_data:
- long-reads-ont
- long-reads-pacbio
- reference-fasta
source:
  ecosystem: iwc
  workflow: Host or Contamination Removal on Long-Reads
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/microbiome/host-contamination-removal/host-contamination-removal-long-reads
  version: '0.3'
  license: MIT
tools:
- minimap2
- bamtools
- samtools
- qualimap
- multiqc
tags:
- decontamination
- host-removal
- nanopore
- pacbio
- long-reads
- microbiome
- preprocessing
test_data:
- role: long_reads__spike3bbarcode10
  url: https://zenodo.org/record/12190648/files/collection_of_all_samples_Spike3bBarcode10.fastq.gz
  filetype: fastqsanger.gz
- role: long_reads__spike3bbarcode12
  url: https://zenodo.org/record/12190648/files/collection_of_all_samples_Spike3bBarcode12.fastq.gz
  filetype: fastqsanger.gz
expected_output:
- role: multiqc_html_report
  description: Content assertions for `MultiQC HTML Report`.
  assertions:
  - 'has_text: Spike3bBarcode12'
- role: reads_without_host_or_contamination
  description: Content assertions for `Reads without Host or Contamination`.
  assertions:
  - 'Spike3bBarcode10: has_text: @0a0c4d2c-291f-46a4-87d5-625efbfed6a0'
  - 'Spike3bBarcode12: has_text: @0a0c4e88-893a-4284-9119-ab4274e05445'
---

# Host or contamination removal on long reads

## When to use this sketch
- Raw Nanopore or PacBio FASTQ from a microbiome/metagenomic experiment where reads are suspected to contain host DNA/RNA (human, animal, plant, etc.) or other contaminant sequences.
- You want a clean, decontaminated FASTQ collection to feed into downstream long-read metagenomic classification, assembly, or binning steps.
- You also need per-sample mapping QC (fraction of reads aligning to host) aggregated into a single MultiQC report.
- Host reference is available as a FASTA (or a Galaxy cached genome such as `hg38`, `apiMel3`, etc.).

## Do not use when
- Reads are short-read Illumina paired-end — use the `host-decontamination-short-reads` sketch (sibling IWC workflow uses BWA-MEM2/Bowtie2 instead of Minimap2).
- You want to *keep* the host reads and discard microbial reads (invert the logic; this sketch outputs unmapped reads only).
- You need taxonomic classification of the contaminant — use a Kraken2/Centrifuge-based sketch instead; this workflow only does reference-based host depletion.
- Your contaminant is unknown and you have no reference genome — use a de novo contamination screening sketch.

## Analysis outline
1. **Map long reads to host reference** with `minimap2` using a long-read preset (`map-ont` for Nanopore, `map-pb` for PacBio, `map-hifi` for HiFi), output BAM.
2. **Split BAM by mapping status** with `bamtools split_mapped` into `mapped` and `unmapped` BAM streams.
3. **Extract unmapped reads to FASTQ** with `samtools fastx`, excluding secondary (256) and supplementary (2048) alignments, producing the decontaminated read set.
4. **Compute mapping statistics** per sample with `QualiMap BamQC` on the full alignment BAM.
5. **Flatten** the per-sample QualiMap raw_data collection so MultiQC can consume it.
6. **Aggregate QC** with `MultiQC` (qualimap module) into a single HTML report titled "Host/Contamination Removal".

## Key parameters
- `minimap2 analysis_type_selector` (profile): **must be a long-read preset** — typically `map-ont` (Nanopore), `map-pb` (PacBio CLR), or `map-hifi` (PacBio HiFi). The test uses `map-pb`.
- `minimap2 reference_source`: `cached` genome build or a history FASTA of the host/contaminant.
- `minimap2 output_format`: `BAM` (required for downstream BAMtools/QualiMap).
- `minimap2 alignment_options.no_end_flt`: `true` (disables end-filtering, recommended for long reads).
- `samtools fastx exclusive_filter`: `[256, 2048]` to drop secondary and supplementary alignments so each read is emitted once.
- `samtools fastx output_fmt`: `fastqsanger`.
- `qualimap_bamqc stats_regions.region_select`: `all` (whole-reference QC).
- `multiqc results[0].software`: `qualimap`.
- Post-job: `alignment_output`, `mapped`, `unmapped`, and raw QualiMap BAM reports are hidden; only the cleaned FASTQ collection, flattened QualiMap stats, and MultiQC HTML are surfaced.

## Test data
Two Nanopore FASTQ samples from a Zenodo mock spike-in dataset (`Spike3bBarcode10` and `Spike3bBarcode12`, record 12190648) are provided as a `fastqsanger.gz` collection and mapped against the cached honeybee reference `apiMel3` using the `map-pb` long-read preset. The run is expected to produce a cleaned FASTQ collection `Reads without Host or Contamination` containing the unmapped reads (asserted by the presence of specific read IDs `@0a0c4d2c-291f-46a4-87d5-625efbfed6a0` in sample 10 and `@0a0c4e88-893a-4284-9119-ab4274e05445` in sample 12), per-sample QualiMap raw_data elements (genome_results referencing a 586,300,787 bp reference, coverage_across_reference with 416 lines, mapping_quality_histogram, homopolymer_indels, etc.), and a MultiQC HTML report mentioning both sample names.

## Reference workflow
Galaxy IWC `microbiome/host-contamination-removal/host-contamination-removal-long-reads`, release **0.3** (MIT). Tool versions: minimap2 2.28+galaxy2, bamtools_split_mapped 2.5.2+galaxy2, samtools_fastx 1.22+galaxy1, qualimap_bamqc 2.3+galaxy0, multiqc 1.33+galaxy0. Sibling workflow: `host-contamination-removal-short-reads` for Illumina paired-end data.
