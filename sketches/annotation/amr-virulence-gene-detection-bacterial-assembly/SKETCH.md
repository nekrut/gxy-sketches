---
name: amr-virulence-gene-detection-bacterial-assembly
description: Use when you need to screen an assembled bacterial genome (contigs or
  complete chromosome FASTA) for antimicrobial resistance genes, resistance-conferring
  point mutations, plasmid replicons, MLST type, and virulence factors. Combines StarAMR
  (ResFinder/PointFinder/PlasmidFinder), NCBI AMRFinderPlus, and ABRicate (VFDB) into
  a single report.
domain: annotation
organism_class:
- bacterial
- haploid
input_data:
- assembly-fasta
source:
  ecosystem: iwc
  workflow: AMR Gene Detection
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/bacterial_genomics/amr_gene_detection
  version: 1.1.8
  license: GPL-3.0-or-later
tools:
- staramr
- amrfinderplus
- abricate
- tooldistillator
- multiqc
tags:
- amr
- antimicrobial-resistance
- virulence
- resfinder
- pointfinder
- plasmidfinder
- vfdb
- mlst
- bacterial-genomics
test_data: []
expected_output:
- role: staramr_detailed_summary
  description: Content assertions for `staramr_detailed_summary`.
  assertions:
  - 'has_text: Resistance'
  - 'has_n_columns: {''n'': 12}'
- role: staramr_resfinder_report
  description: Content assertions for `staramr_resfinder_report`.
  assertions:
  - 'has_text: Chloramphenicol'
  - 'has_n_columns: {''n'': 13}'
- role: staramr_mlst_report
  description: Content assertions for `staramr_mlst_report`.
  assertions:
  - 'has_text: Scheme'
- role: staramr_pointfinder_report
  description: Content assertions for `staramr_pointfinder_report`.
  assertions:
  - 'has_text: Pointfinder Position'
  - 'has_n_columns: {''n'': 18}'
- role: staramr_plasmidfinder_report
  description: Content assertions for `staramr_plasmidfinder_report`.
  assertions:
  - 'has_text: rep7a'
  - 'has_n_columns: {''n'': 9}'
- role: staramr_summary
  description: Content assertions for `staramr_summary`.
  assertions:
  - 'has_text: erythromycin'
  - 'has_n_columns: {''n'': 12}'
- role: amrfinderplus_report
  description: Content assertions for `amrfinderplus_report`.
  assertions:
  - 'has_text: catA'
  - 'has_n_columns: {''n'': 23}'
- role: amrfinderplus_mutation
  description: Content assertions for `amrfinderplus_mutation`.
  assertions:
  - 'has_text: Element subtype'
  - 'has_n_columns: {''n'': 23}'
- role: abricate_virulence_report
  description: Content assertions for `abricate_virulence_report`.
  assertions:
  - 'has_text: RESISTANCE'
- role: tooldistillator_summarize_amr
  description: Content assertions for `tooldistillator_summarize_amr`.
  assertions:
  - 'that: has_text'
  - 'text: % Identity to reference sequence'
  - 'that: has_text'
  - 'text: pointfinder_file'
  - 'that: has_text'
  - 'text: LINCOSAMIDE'
- role: multiqc_html_report
  description: Content assertions for `multiqc_html_report`.
  assertions:
  - 'that: has_text'
  - 'text: ABRicate virulence'
  - 'that: has_text'
  - 'text: Staramr detailed summary'
---

# AMR and virulence gene detection from bacterial assemblies

## When to use this sketch
- You already have an assembled bacterial genome (draft contigs or closed chromosome) in FASTA format and want a comprehensive resistome + virulome profile.
- You need multiple complementary AMR callers (StarAMR's ResFinder/PointFinder/PlasmidFinder BLAST search AND NCBI AMRFinderPlus) rather than a single tool.
- You want resistance-associated point mutations for a supported organism (e.g. *Escherichia coli*, *Salmonella*, *Enterococcus faecalis*, *Mycobacterium tuberculosis*, *Campylobacter*, *Neisseria gonorrhoeae*, etc.).
- You also want plasmid replicon typing, MLST, and virulence factor screening (VFDB via ABRicate) in the same run.
- You want a single aggregated JSON (ToolDistillator) and a MultiQC HTML report summarising all tables for downstream parsing / dashboards.

## Do not use when
- You only have raw reads and no assembly yet — assemble first (e.g. with a Shovill/Unicycler/SPAdes workflow) and then feed the contigs here.
- You want to call SNVs/indels against a reference genome — use a haploid bacterial variant-calling sketch instead.
- Your organism is a virus, eukaryote, or metagenome — this pipeline assumes a single bacterial isolate assembly and bacterial AMR databases.
- You need functional/structural genome annotation (CDS, rRNA, tRNA) — use a Prokka/Bakta annotation sketch.
- You need shotgun metagenomic AMR profiling from reads — use a metagenomic AMR sketch (e.g. read-based ARIBA/AMRPlusPlus).

## Analysis outline
1. **StarAMR** (`staramr search`) — BLAST the assembly against ResFinder (acquired AMR genes), PointFinder (species-specific chromosomal resistance mutations) and PlasmidFinder (replicons); also runs MLST and emits summary / detailed / per-database / Excel reports.
2. **AMRFinderPlus** — run in nucleotide mode against the NCBI AMRFinderPlus database with `--organism` set, producing an AMR gene report, an all-mutations report, and extracted nucleotide sequences of hits.
3. **ABRicate** — screen the same FASTA against a virulence database (VFDB) for virulence factors.
4. **Column Regex Find And Replace** — strip the leading `#` from the ABRicate `#FILE` header so MultiQC can parse it as a table.
5. **ToolDistillator** — normalise StarAMR, AMRFinderPlus and ABRicate outputs into per-tool JSON, recording the reference database versions supplied as workflow parameters.
6. **ToolDistillator Summarize** — merge the per-tool JSONs into a single `tooldistillator_summarize_amr` JSON suitable for downstream ABRomics / database ingestion.
7. **MultiQC** — build a single HTML report with custom-content tables for StarAMR detailed summary, ResFinder, PlasmidFinder, PointFinder, AMRFinderPlus report, AMRFinderPlus mutations, and ABRicate virulence.

## Key parameters
- **Input**: single FASTA (assembled bacterial genome; may be multi-contig).
- **StarAMR database**: versioned bundle of ResFinder + PointFinder + PlasmidFinder (e.g. `staramr_downloaded_07042025_resfinder_..._pointfinder_..._plasmidfinder_...`).
- **StarAMR PointFinder organism**: lowercase species key, e.g. `enterococcus_faecalis`, `escherichia_coli`, `salmonella`, `campylobacter`, `mycobacterium_tuberculosis`.
- **StarAMR thresholds**: `pid_threshold=90.0`, `percent_length_overlap_resfinder=60.0`, `percent_length_overlap_pointfinder=95.0`, `percent_length_overlap_plasmidfinder=60.0`.
- **StarAMR QC bounds**: `genome_size_lower_bound=4000000`, `genome_size_upper_bound=6000000`, `minimum_N50_value=10000`, `minimum_contig_length=300`, `unacceptable_number_contigs=1000`, `mlst_scheme=auto`, `plasmidfinder_type=include_all`.
- **AMRFinderPlus database**: a versioned NCBI bundle, e.g. `amrfinderplus_V3.12_2024-05-02.2`.
- **AMRFinderPlus organism** (`--organism`): taxonomy group used for point-mutation reporting, e.g. `Enterococcus_faecalis`. `mutation_all=true`, `report_common=true`, `report_all_equal=true`, `print_node=true`, `plus=true`, `translation_table=11`, `coverage_min=0.5`, `ident_min=-1.0` (i.e. use per-gene curated cutoffs).
- **ABRicate database**: `vfdb` for virulence (swap for `card`, `ncbi`, `resfinder`, `megares`, `argannot`, `ecoh`, `plasmidfinder` if you want that tool to screen a different class).
- **ABRicate thresholds**: `min_dna_id=80.0`, `min_cov=80.0`.
- **ToolDistillator**: records `reference_database_version` for each of StarAMR, AMRFinderPlus, and ABRicate so provenance is embedded in the summary JSON.

## Test data
The workflow ships with a single-sample test: one assembled contig FASTA (`shovill_contigs_fasta_contig00089.fasta` from Zenodo record 15696987), run against the StarAMR bundle `staramr_downloaded_07042025_...`, AMRFinderPlus database `amrfinderplus_V3.12_2024-05-02.2`, ABRicate database `vfdb`, with PointFinder organism `enterococcus_faecalis` and AMRFinderPlus organism `Enterococcus_faecalis`. Expected outputs include a StarAMR detailed summary (12 columns, mentioning "Resistance"), a ResFinder report (13 columns, containing "Chloramphenicol"), a PointFinder report (18 columns, header "Pointfinder Position"), a PlasmidFinder report (9 columns, containing replicon `rep7a`), an MLST report with a `Scheme` column, a StarAMR summary (12 columns, mentioning "erythromycin"), an AMRFinderPlus report (23 columns, containing `catA`), an AMRFinderPlus mutation report (23 columns, header "Element subtype"), an ABRicate virulence report containing "RESISTANCE", a merged ToolDistillator JSON mentioning `% Identity to reference sequence`, `pointfinder_file`, and `LINCOSAMIDE`, and a MultiQC HTML report containing the "ABRicate virulence" and "Staramr detailed summary" sections.

## Reference workflow
Galaxy IWC — `workflows/bacterial_genomics/amr_gene_detection`, release `1.1.8` (ABRomics consortium; StarAMR 0.11.0+galaxy3, AMRFinderPlus 3.12.8+galaxy0, ABRicate 1.0.1, ToolDistillator 1.0.4+galaxy0, MultiQC 1.33+galaxy0). License: GPL-3.0-or-later.
