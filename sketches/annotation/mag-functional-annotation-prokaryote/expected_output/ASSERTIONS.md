# Content assertions (no golden file checked in)
## multiqc_html_report
Content assertions for `multiqc html report`.

- that: has_text
- text: 50contig_reads_bin

## isescan_merged_output
Content assertions for `ISEScan Merged Output`.

- that: has_n_lines
- n: 0

## integron_finder_merged_output
Content assertions for `Integron Finder Merged Output`.

- that: has_n_lines
- n: 0

## bakta_cut_annotation_summary
Content assertions for `bakta cut annotation summary`.

- that: has_n_lines
- n: 16
- that: has_n_columns
- n: 2

## plasmidfinder_merged_summary
Content assertions for `PlasmidFinder Merged Summary`.

- that: has_text
- text: Sample	Database	Plasmid	Identity	Query / Template length	Contig	Position in contig	Note	Accession number
- that: has_n_lines
- n: 1

