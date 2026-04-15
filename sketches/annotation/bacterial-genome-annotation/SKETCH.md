---
name: bacterial-genome-annotation
description: 'Use when you have an assembled bacterial genome FASTA and need comprehensive
  functional and mobile-element annotation: CDS/sORF prediction, AMR gene calls, plasmid
  replicon typing, integron detection, and insertion sequence (IS) element discovery,
  aggregated into structured JSON.'
domain: annotation
organism_class:
- bacterial
- haploid
input_data:
- assembly-fasta
source:
  ecosystem: iwc
  workflow: Bacterial Genome Annotation
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/bacterial_genomics/bacterial_genome_annotation
  version: 1.2.0
  license: GPL-3.0-or-later
  slug: bacterial_genomics--bacterial_genome_annotation
tools:
- name: bakta
  version: 1.9.4+galaxy1
- name: plasmidfinder
  version: 2.1.6+galaxy1
- name: integron_finder
  version: 2.0.5+galaxy0
- name: isescan
  version: 1.7.3+galaxy0
- name: tooldistillator
  version: 1.0.4+galaxy0
- name: amrfinderplus
tags:
- bacteria
- annotation
- plasmid
- integron
- insertion-sequence
- amr
- mobile-genetic-elements
- bakta
- abromics
test_data: []
expected_output:
- role: integronfinder2_logfile_text
  description: Content assertions for `integronfinder2_logfile_text`.
  assertions:
  - 'has_text: Writing out results for replicon'
- role: integronfinder2_summary
  description: Content assertions for `integronfinder2_summary`.
  assertions:
  - 'has_text: contig00001'
- role: integronfinder2_results_tabular
  description: Content assertions for `integronfinder2_results_tabular`.
  assertions:
  - 'has_text: contig00009_42'
- role: bakta_hypothetical_tabular
  description: Content assertions for `bakta_hypothetical_tabular`.
  assertions:
  - 'has_text: DHJLLP_04750'
- role: bakta_annotation_json
  description: Content assertions for `bakta_annotation_json`.
  assertions:
  - 'has_text: aa_hexdigest'
- role: bakta_annotation_tabular
  description: Content assertions for `bakta_annotation_tabular`.
  assertions:
  - 'has_text: Phosphotransferase system cellobiose-specific component IIC'
- role: isescan_results_tabular
  description: Content assertions for `isescan_results_tabular`.
  assertions:
  - 'has_text: IS256_162'
- role: isescan_summary_tabular
  description: Content assertions for `isescan_summary_tabular`.
  assertions:
  - 'has_text: nIS'
- role: isescan_logfile_text
  description: Content assertions for `isescan_logfile_text`.
  assertions:
  - 'has_text: Both complete and partial IS elements are reported.'
- role: plasmidfinder_result_json
  description: Content assertions for `plasmidfinder_result_json`.
  assertions:
  - 'has_text: positions_in_contig'
- role: plasmidfinder_results_tabular
  description: Content assertions for `plasmidfinder_results_tabular`.
  assertions:
  - 'has_n_columns: {''n'': 8}'
- role: tooldistillator_summarize_annotation_without_bakta
  description: Content assertions for `tooldistillator_summarize_annotation_without_bakta`.
  assertions:
  - 'that: has_text'
  - 'text: contig00009'
  - 'that: has_text'
  - 'text: rep9b:WARNING'
- role: tooldistillator_summarize_bakta
  description: Content assertions for `tooldistillator_summarize_bakta`.
  assertions:
  - 'that: has_text'
  - 'text: UniParc:UPI000005C018'
  - 'that: has_text'
  - 'text: GO:0050511'
---

# Bacterial genome annotation (CDS, plasmids, integrons, IS elements)

## When to use this sketch
- You already have an assembled bacterial genome (contigs or a closed chromosome) in FASTA form and need to annotate it.
- You want a one-shot workflow that produces CDS/sORF calls plus AMR annotations (Bakta + AMRFinderPlus), plasmid replicon typing (PlasmidFinder), integron/CALIN/In0 detection (IntegronFinder2), and insertion sequence elements (ISEScan).
- You want per-tool results aggregated into a single structured JSON via ToolDistillator so downstream agents or dashboards can parse everything uniformly.
- You are working on any bacterial taxon (MRSA, E. coli, Klebsiella, M. tuberculosis, etc.) — the workflow is taxon-agnostic and uses translation table 11 by default.

## Do not use when
- You need to assemble reads first — run a bacterial assembly sketch (e.g. a SPAdes/Shovill/Unicycler assembly workflow) and feed its contigs into this one.
- You need variant calling against a reference instead of de novo annotation — use the `haploid-variant-calling-bacterial` style sketch.
- Your input is a eukaryote, archaeon with non-standard code, or a virus — Bakta and the mobile-element tools here target bacteria.
- You only want AMR gene detection in isolation — call AMRFinderPlus or abriTAMR directly instead of running this full workflow.
- You need phylogenetic placement or pangenome analysis — those are downstream of this sketch.

## Analysis outline
1. Supply the assembled genome FASTA as the primary input, and pick the PlasmidFinder, Bakta, and AMRFinderPlus database versions as separate parameter inputs.
2. Run **ISEScan** on the assembly to detect insertion sequence elements (IS family table, GFF annotation, IS/ORF FASTAs).
3. Run **IntegronFinder2** on the assembly with `local_max=true` and `promoter_attI=true` to call complete integrons, CALIN, and In0 elements.
4. Run **PlasmidFinder** with `min_cov=0.6`, `threshold=0.95` against the selected replicon database to type plasmid replicons and emit hit FASTAs plus a tabular/JSON report.
5. Optionally (controlled by the `Run Bakta` boolean) run **Bakta** with `translation_table=11` and the selected Bakta + AMRFinderPlus databases to produce TSV/GFF3/GBFF/EMBL/FFN/FAA/JSON/plot annotations and an AMR-aware summary.
6. Run **ToolDistillator** on the PlasmidFinder, ISEScan, and IntegronFinder2 outputs to normalize each tool's results into JSON, then **ToolDistillator Summarize** to merge them into a single annotation JSON.
7. If Bakta was run, a parallel ToolDistillator + Summarize branch wraps the Bakta outputs into its own JSON using a `Pick parameter value` step to select the main Bakta JSON.

## Key parameters
- `Run Bakta`: boolean gate — default `true`. Set `false` to skip the expensive Bakta step when only mobile-element and plasmid calls are needed.
- Bakta `translation_table`: `11` (standard bacterial). `meta=false`, `complete=false`, `compliant=false`, `keep_contig_headers=false`.
- Bakta database selectors: `bakta_db_select` (e.g. `V5.0_2023-02-20`) and `amrfinder_db_select` (e.g. `amrfinderplus_V3.12_2024-05-02.2`) must be chosen to match installed data-managed databases.
- PlasmidFinder: `min_cov=0.6`, `threshold=0.95`, database e.g. `plasmidfinder_81c11f4_2023_12_04`; emits hit FASTA, plasmid FASTA, result TSV/TXT, data JSON.
- IntegronFinder2: `local_max=true`, `promoter_attI=true`, `dist_thresh=4000`, `calin_threshold=2`, `min_attc_size=40`, `max_attc_size=200`, `keep_palindromes=false`, `no_proteins=false`, `union_integrases=false`, `func_annot=false`.
- ISEScan: `log_activate=true`, `remove_short_is=false` (reports both complete and partial IS elements).
- Input contract: a single FASTA dataset — any contig headers are accepted; one record or many.

## Test data
The source test profile uses a single assembled bacterial contigs FASTA downloaded from Zenodo (`shovill_contigs_fasta`, SHA-1 `b77e9cf8473eaba8a640a398a0b06b9c87249052`), together with the parameter picks `Plasmid detection database = plasmidfinder_81c11f4_2023_12_04`, `Bacterial genome annotation database = V5.0_2023-02-20`, `AMRFinderPlus database = amrfinderplus_V3.12_2024-05-02.2`, and `Run Bakta = true`. Successful execution is asserted by substring checks across the downstream outputs: IntegronFinder2 logs/summary/results must reference replicons and contigs such as `contig00001` and `contig00009_42`; ISEScan tabular/summary/log must mention IS families (e.g. `IS256_162`), the `nIS` column header, and the “Both complete and partial IS elements are reported.” line; PlasmidFinder must emit a JSON with `positions_in_contig` and an 8-column result table; Bakta must produce an annotation TSV containing a cellobiose PTS IIC entry, a hypothetical-protein table row `DHJLLP_04750`, and a JSON containing `aa_hexdigest`; and the two ToolDistillator summaries must contain cross-tool markers such as `contig00009`, `rep9b:WARNING`, `UniParc:UPI000005C018`, and `GO:0050511`.

## Reference workflow
Galaxy IWC `bacterial_genomics/bacterial_genome_annotation` v1.2.0 (ABRomics), GPL-3.0-or-later. Tool versions pinned in this release: Bakta 1.9.4+galaxy1, PlasmidFinder 2.1.6+galaxy1, IntegronFinder 2.0.5+galaxy0, ISEScan 1.7.3+galaxy0, ToolDistillator / ToolDistillator Summarize 1.0.4+galaxy0, pick_value 0.2.0.
