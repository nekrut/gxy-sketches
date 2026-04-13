---
name: cgmlst-bacterial-strain-typing
description: Use when you need to genotype a single assembled bacterial genome by
  core genome MLST (cgMLST) against a curated allele scheme (pubMLST, BIGSdb, Enterobase,
  or cgMLST.org) to characterize or compare strains. Input is contigs; output is a
  per-locus allele profile plus any novel alleles.
domain: annotation
organism_class:
- bacterial
- haploid
input_data:
- bacterial-contigs-fasta
- cgmlst-reference-scheme
source:
  ecosystem: iwc
  workflow: core genome Multilocus Sequence Typing (cgMLST) of bacterial genome
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/bacterial_genomics/cgmlst-bacterial-genome
  version: '1.1'
  license: GPL-3.0-or-later
tools:
- coreprofiler
- tooldistillator
- tooldistillator_summarize
tags:
- bacteria
- cgmlst
- mlst
- allele-calling
- typing
- genotyping
- strain-typing
- surveillance
test_data:
- role: bacterial_genome_contigs
  url: https://zenodo.org/records/16779020/files/E-coli3_S194.fasta
  filetype: fasta
expected_output:
- role: coreprofiler_allele_calling_report
  description: Content assertions for `CoreProfiler allele calling report`.
  assertions:
  - 'has_text: AEJV01_03887'
  - 'has_n_columns: {''n'': 2514}'
- role: newly_detected_alleles_by_coreprofiler
  description: Content assertions for `Newly detected alleles by CoreProfiler`.
  assertions:
  - 'has_text: >'
- role: information_about_temporary_alleles_found_by_coreprofiler
  description: Content assertions for `Information about temporary alleles found by
    CoreProfiler`.
  assertions:
  - 'has_text: tmp_loci'
- role: summarized_cgmlst_tooldistillator_results
  description: Content assertions for `Summarized cgMLST ToolDistillator results`.
  assertions:
  - 'that: has_text'
  - 'text: coreprofiler_report'
  - 'that: has_text'
  - 'text: profiles_w_tmp_alleles'
  - 'that: has_text'
  - 'text: new_alleles_fna'
---

# Core genome MLST (cgMLST) of a bacterial genome

## When to use this sketch
- You already have an assembled bacterial genome (contigs FASTA) and want a cgMLST allele profile for strain typing, outbreak investigation, or surveillance.
- A curated reference allele scheme is available for your species on pubMLST, BIGSdb, Enterobase, or cgMLST.org (e.g. Escherichia coli Enterobase cgMLST 2513-locus scheme, Listeria monocytogenes, Salmonella enterica, Klebsiella pneumoniae).
- You need both exact allele matches and detection of potentially novel alleles with their FASTA sequences.
- You want a machine-readable JSON summary (via ToolDistillator) that can be merged into a larger typing/surveillance report.

## Do not use when
- You only have raw reads and no assembly yet — run a bacterial assembly sketch first (e.g. a short-read or hybrid bacterial-assembly workflow) to produce contigs.
- You want classical 7-gene MLST sequence types rather than core-genome MLST — use a traditional MLST sketch instead.
- You want SNP-based phylogeny / outbreak clustering from reads against a reference — use a haploid bacterial variant-calling / SNP-phylogeny sketch.
- You want whole-genome taxonomic identification or AMR gene detection — use dedicated taxonomy (Kraken2, sourmash) or AMR (AMRFinderPlus, abricate) sketches.
- You need to type many isolates and build a minimum spanning tree across them — this sketch runs on one genome at a time; iterate it per sample and cluster downstream.

## Analysis outline
1. Provide contigs of one assembled bacterial genome as a FASTA input.
2. Select a curated reference allele scheme (pubMLST / BIGSdb / Enterobase / cgMLST.org) matching the species.
3. Run `CoreProfiler allele_calling` to perform a two-step BLAST-based comparison of contigs against the scheme, reporting exact-match alleles and candidate novel alleles.
4. Run `ToolDistillator` to parse CoreProfiler's report, novel-allele FASTA and temporary-allele JSON into a normalized per-tool JSON.
5. Run `ToolDistillator Summarize` to aggregate the distilled JSON into a single summary JSON suitable for downstream reporting.

## Key parameters
- `input_file`: contigs FASTA of a single bacterial genome.
- `input_scheme`: name/version of the curated cgMLST scheme (must match the organism, e.g. `coreprofiler_downloaded_2026-01-15-escherichia_v1-cgMLST-2513-enterobase-no_token`).
- CoreProfiler autotag: `autotag_word_size: 31` (BLAST word size for exact allele matching).
- CoreProfiler scannew (novel-allele detection):
  - `min_id_new_allele: 90` (% identity threshold for a candidate new allele)
  - `min_cov_new_allele: 90` (% coverage threshold for a candidate new allele)
  - `min_cov_incomplete: 70` (% coverage to flag incomplete loci)
  - `detailed: true` (emit detailed per-locus info)
  - `cds: true` (require coding-sequence consistency)
  - `output_selection: [profiles_w_tmp_alleles_output, outfa_output]` (emit tmp-allele JSON + novel-allele FASTA).
- ToolDistillator `tool_list: coreprofiler`; pass the scheme name as `reference_database_version` so provenance is preserved in the JSON.

## Test data
A single contigs FASTA for an Escherichia coli isolate (`E-coli3_S194.fasta`, hosted on Zenodo record 16779020) is typed against the Enterobase E. coli cgMLST scheme `coreprofiler_downloaded_2026-01-15-escherichia_v1-cgMLST-2513-enterobase-no_token` (2513 loci). A successful run produces: a CoreProfiler allele-calling report with 2514 columns (one per locus plus a sample-id column) that contains the locus `AEJV01_03887`; a FASTA of newly detected alleles (non-empty, header line starts with `>`); a JSON of temporary/tentative alleles containing the `tmp_loci` key; and a ToolDistillator summary JSON that mentions `coreprofiler_report`, `profiles_w_tmp_alleles`, and `new_alleles_fna`.

## Reference workflow
Galaxy IWC — `workflows/bacterial_genomics/cgmlst-bacterial-genome` ("core genome Multilocus Sequence Typing (cgMLST) of bacterial genome"), release 1.1, GPL-3.0-or-later, maintained by ABRomics. Core tools: `coreprofiler_allele_calling 2.0.0+galaxy2`, `tooldistillator 1.0.5+galaxy1`, `tooldistillator_summarize 1.0.5+galaxy1`.
