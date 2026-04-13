---
name: short-read-qc-and-taxonomic-screen
description: Use when you need to QC, trim, and taxonomically screen paired-end Illumina
  raw reads prior to bacterial genome assembly, to verify expected organism identity
  and flag contamination before running an assembler. Produces cleaned FASTQs plus
  Kraken2/Bracken species profiles.
domain: qc
organism_class:
- bacterial
input_data:
- short-reads-paired
- kraken2-database
source:
  ecosystem: iwc
  workflow: Raw Read Quality and Contamination Control For Genome Assembly
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/genome-assembly/quality-and-contamination-control-raw-reads
  version: 1.1.11
  license: GPL-3.0-or-later
tools:
- fastp
- kraken2
- bracken
- tooldistillator
tags:
- qc
- trimming
- contamination
- kraken2
- bracken
- fastp
- bacterial-genomics
- paired-end
- pre-assembly
test_data: []
expected_output:
- role: fastp_report_json
  description: Content assertions for `fastp_report_json`.
  assertions:
  - 'has_text: read2_before_filtering'
- role: kraken_report_tabular
  description: Content assertions for `kraken_report_tabular`.
  assertions:
  - 'has_text: Enterococcus avium'
  - 'has_n_columns: {''n'': 6}'
- role: kraken_report
  description: Content assertions for `kraken_report`.
  assertions:
  - 'has_text: M07044:90:000000000-JRJWP:1:1119:23974:4461'
  - 'has_n_columns: {''n'': 5}'
- role: bracken_kraken_report
  description: Content assertions for `bracken_kraken_report`.
  assertions:
  - 'has_text: Enterococcus gallinarum'
  - 'has_n_columns: {''n'': 6}'
- role: bracken_report_tsv
  description: Content assertions for `bracken_report_tsv`.
  assertions:
  - 'has_text: Escherichia coli'
  - 'has_n_columns: {''n'': 7}'
- role: tooldistillator_summarize_control
  description: Content assertions for `tooldistillator_summarize_control`.
  assertions:
  - 'that: has_text'
  - 'text: fastp_report'
---

# Short-read QC and taxonomic contamination screen

## When to use this sketch
- Paired-end Illumina FASTQ(.gz) reads from a bacterial isolate that you intend to assemble, and you want a pre-assembly sanity check on quality and species identity.
- You need a single pass that performs adapter/quality trimming and produces a Kraken2 + Bracken species-level profile to detect contamination or mislabelled samples.
- You want machine-parsable QC reports (fastp JSON, Kraken2/Bracken tabular, aggregated ToolDistillator JSON) to feed into a downstream LIMS or batch QC gate.
- The user already has (or can select) a Kraken2/Bracken database appropriate for bacteria (e.g. a Standard or MinusB build).

## Do not use when
- Reads are long-read ONT or PacBio — use a long-read QC sketch (NanoPlot / chopper / Centrifuge-style) instead.
- You need to actually assemble and annotate the genome — this sketch stops at cleaned reads and a taxonomic profile; chain it into a bacterial assembly sketch (e.g. unicycler/shovill-based) afterwards.
- You are profiling a metagenomic community for ecology/abundance rather than screening an isolate for contamination — use a dedicated metagenomics taxonomic profiling sketch.
- Input is single-end data — this workflow strictly expects a paired collection.
- You need host-read removal against a vertebrate reference before taxonomic assignment — that requires an added decontamination step not covered here.

## Analysis outline
1. Zip the forward and reverse FASTQ inputs into a paired collection (Galaxy `__ZIP_COLLECTION__`).
2. Trim adapters and low-quality bases with **fastp** on the paired collection, emitting cleaned R1/R2 plus HTML and JSON reports.
3. Unzip the trimmed paired collection back into separate forward/reverse datasets (Galaxy `__UNZIP_COLLECTION__`) for downstream tools.
4. Run **Kraken2** on the trimmed paired reads against the user-selected Kraken2 database to produce a per-read classification and a tabular report.
5. Re-estimate species-level abundances with **Bracken** at level `S` using the Kraken2 report and the same database's k-mer distribution.
6. Aggregate fastp outputs into a structured JSON via **ToolDistillator**, then consolidate with **ToolDistillator Summarize** into a single summary JSON.

## Key parameters
- fastp: `single_paired_selector: paired_collection`; adapter trimming enabled (default auto-detect); quality and length filtering enabled with tool defaults; `report_html: true`, `report_json: true`; polyG/polyX trimming and base correction left off.
- Kraken2: `confidence: 0.0`, `min_base_quality: 10`, `minimum_hit_groups: 2`, `report.create_report: true`, `use_mpa_style: false`, paired mode on.
- Bracken: `level: S` (species), `threshold: 10` reads, `out_report: true` to emit the re-estimated Kraken-style report alongside the Bracken TSV.
- ToolDistillator: `tool_list: fastp` (fastp JSON + HTML are the inputs being distilled in this release; Recentrifuge was removed in 1.1.11).
- Database choice: a Kraken2/Bracken database matching your expected organisms; the test profile uses `k2_minusb_20210517`.

## Test data
The test profile runs two paired-end bacterial Illumina FASTQ files (`paired_r1.fastq.gz` and `paired_r2.fastq.gz` from Zenodo record 11484215) together with the `k2_minusb_20210517` Kraken2/Bracken database. Successful execution is asserted by checking that the fastp JSON report contains `fastp_version` and `read2_before_filtering`; that the Kraken2 tabular report is 6 columns wide and mentions `Enterococcus avium`; that the per-read Kraken2 output is 5 columns wide and contains a specific read ID (`M07044:90:000000000-JRJWP:1:1119:23974:4461`); that the Bracken-adjusted Kraken-style report is 6 columns wide and lists `Enterococcus gallinarum`; that the Bracken TSV is 7 columns wide and lists `Escherichia coli`; and that the ToolDistillator summary JSON contains `fastp_report`.

## Reference workflow
Galaxy IWC `workflows/genome-assembly/quality-and-contamination-control-raw-reads` — "Raw Read Quality and Contamination Control For Genome Assembly", release 1.1.11 (ABRomics; GPL-3.0-or-later).
