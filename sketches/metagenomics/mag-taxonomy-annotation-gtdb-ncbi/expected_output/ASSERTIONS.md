# Content assertions (no golden file checked in)
## multiqc_html_report
Content assertions for `MultiQC HTML report`.

- that: has_text
- text: GTDB-Tk
- that: has_text
- text: Unclassified

## gtdb_tk_summary_files
Content assertions for `GTDB-Tk summary files`.

- gtdbtk.bac120.summary: that: has_text
- gtdbtk.bac120.summary: text: 50contig_reads_binette_bin1.fasta
- gtdbtk.bac120.summary: that: has_text
- gtdbtk.bac120.summary: text: Unclassified
- gtdbtk.bac120.summary: that: has_text
- gtdbtk.bac120.summary: text: 95.0

## gtdb_ncbi_mapping
Content assertions for `GTDB-NCBI mapping`.

- gtdbtk.bac120.summary: that: has_text
- gtdbtk.bac120.summary: text: gtdb_taxonomy
- gtdbtk.bac120.summary: that: has_text
- gtdbtk.bac120.summary: text: NA
- gtdbtk.bac120.summary: that: has_text
- gtdbtk.bac120.summary: text: species

## ncbi_names_to_taxids_mapping
Content assertions for `NCBI names to taxIDs mapping`.

- gtdbtk.bac120.summary: that: has_text
- gtdbtk.bac120.summary: text: ncbi_taxonomy
- gtdbtk.bac120.summary: that: has_text
- gtdbtk.bac120.summary: text: unclassified
- gtdbtk.bac120.summary: that: has_text
- gtdbtk.bac120.summary: text: 12908

## full_gtdb_to_ncbi_mapping
Content assertions for `full GTDB to NCBI mapping`.

- gtdbtk.bac120.summary: that: has_text
- gtdbtk.bac120.summary: text: GTDB_name
- gtdbtk.bac120.summary: that: has_text
- gtdbtk.bac120.summary: text: 1648
- gtdbtk.bac120.summary: that: has_text
- gtdbtk.bac120.summary: text: species

