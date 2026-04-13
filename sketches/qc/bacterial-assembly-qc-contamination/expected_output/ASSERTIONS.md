# Content assertions (no golden file checked in)
## quast_tabular_report_for_fasta_files
Content assertions for `Quast tabular report for FASTA files`.

- has_text: # contigs (>= 500 bp)
- has_n_columns: {'n': 2}

## bracken_tabular_report
Content assertions for `Bracken tabular report`.

- has_text: Escherichia coli
- has_n_columns: {'n': 7}

## bracken_kraken_tabular_report
Content assertions for `Bracken Kraken tabular report`.

- has_text: Escherichia coli
- has_n_columns: {'n': 6}

## kraken2_sequence_assignation
Content assertions for `Kraken2 sequence assignation`.

- has_text: contig00359

## kraken2_tabular_report
Content assertions for `Kraken2 tabular report`.

- has_text: Escherichia fergusonii
- has_n_columns: {'n': 6}

## checkm2_tabular_report
Content assertions for `Checkm2 tabular report`.

- has_text: Completeness_General
- has_n_columns: {'n': 15}

## checkm2_diamond_files
Content assertions for `Checkm2 diamond files`.

- DIAMOND_RESULTS: has_text: UniRef100_B1IY62~K00116
- DIAMOND_RESULTS: has_n_columns: {'n': 12}

## checkm2_protein_files
Content assertions for `Checkm2 protein files`.

- E-coli3_S194.fasta: has_text: >contig00358_1

## tooldistillator_summarize_control
Content assertions for `Tooldistillator summarize control`.

- that: has_text
- text: quast_report
- that: has_text
- text: ncbi_taxonomic_id
- that: has_text
- text: kraken2_report
- that: has_text
- text: checkm2_report

