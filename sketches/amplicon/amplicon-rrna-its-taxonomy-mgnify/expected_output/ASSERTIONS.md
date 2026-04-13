# Content assertions (no golden file checked in)
## single_end_multiqc_report
Content assertions for `Single-end MultiQC report`.

- that: has_text
- text: DRR010481_ambiguous_base_filtering
- that: has_text
- text: 84.0
- that: has_text
- text: DRR010481_initial_reads
- that: has_text
- text: 84.8
- that: has_text
- text: DRR010481_length_filtering
- that: has_text
- text: DRR010481_trimming

## single_end_multiqc_statistics
Content assertions for `Single-end MultiQC statistics`.

- that: has_text
- text: DRR010481_ambiguous_base_filtering	84.0	47.0	242.02	244	40.0	2.4999999999999998e-05
- that: has_text
- text: DRR010481_initial_reads	84.84848484848484	47.0	545.0454545454545	550	40.0	3.2999999999999996e-05
- that: has_text
- text: DRR010481_length_filtering	84.0	47.0	242.02	244	40.0	2.4999999999999998e-05
- that: has_text
- text: DRR010481_trimming	84.0	47.0	242.02	244	40.0	2.4999999999999998e-05

## paired_end_multiqc_report
Content assertions for `Paired-end MultiQC report`.

- that: has_text
- text: ERR2715528_ambiguous_base_filtering
- that: has_text
- text: ERR2715528_initial_reads
- that: has_text
- text: ERR2715528_length_filtering
- that: has_text
- text: ERR2715528_trimming
- that: has_text
- text: 92.2

## ssu_taxonomic_classifications_using_silva_db
Content assertions for `SSU taxonomic classifications using SILVA DB`.

- ERR2715528: that: has_text
- ERR2715528: text: # mapseq v1.2.6 (Jan 20 2023)
- ERR2715528: that: has_text
- ERR2715528: text: SILVA
- ERR2715528: that: has_n_columns
- ERR2715528: comment: #
- ERR2715528: n: 15

## ssu_otu_tables_silva_db
Content assertions for `SSU OTU tables (SILVA DB)`.

- ERR2715528: that: has_text
- ERR2715528: text: # Constructed from biom file
- ERR2715528: that: has_text
- ERR2715528: text: # OTU ID
- ERR2715528: that: has_text
- ERR2715528: text: Unspecified
- ERR2715528: that: has_text
- ERR2715528: text: taxonomy
- ERR2715528: that: has_text
- ERR2715528: text: taxid
- ERR2715528: that: has_n_columns
- ERR2715528: comment: #
- ERR2715528: n: 4

## lsu_otu_tables_silva_db
Content assertions for `LSU OTU tables (SILVA DB)`.

- DRR010481: that: has_text
- DRR010481: text: # Constructed from biom file
- DRR010481: that: has_text
- DRR010481: text: # OTU ID
- DRR010481: that: has_text
- DRR010481: text: Unspecified
- DRR010481: that: has_text
- DRR010481: text: taxonomy
- DRR010481: that: has_text
- DRR010481: text: taxid
- DRR010481: that: has_n_columns
- DRR010481: comment: #
- DRR010481: n: 4

## ssu_otu_tables_in_hdf5_format_silva_db
Content assertions for `SSU OTU tables in HDF5 format (SILVA DB)`.

- ERR2715528: that: has_size
- ERR2715528: value: 37000
- ERR2715528: delta: 10000

## ssu_otu_tables_in_json_format_silva_db
Content assertions for `SSU OTU tables in JSON format (SILVA DB)`.

- ERR2715528: that: has_text
- ERR2715528: text: "type": "OTU table"

## ssu_taxonomic_abundance_pie_charts_silva_db
Content assertions for `SSU taxonomic abundance pie charts (SILVA DB)`.

- that: has_text
- text: ERR2715528

## lsu_otu_tables_in_hdf5_format_silva_db
Content assertions for `LSU OTU tables in HDF5 format (SILVA DB)`.

- DRR010481: that: has_size
- DRR010481: value: 37000
- DRR010481: delta: 10000

## lsu_otu_tables_in_json_format_silva_db
Content assertions for `LSU OTU tables in JSON format (SILVA DB)`.

- DRR010481: that: has_text
- DRR010481: text: "type": "OTU table"

## lsu_taxonomic_abundance_pie_charts_silva_db
Content assertions for `LSU taxonomic abundance pie charts (SILVA DB)`.

- that: has_text
- text: DRR010481

## lsu_taxonomic_classifications_using_silva_db
Content assertions for `LSU taxonomic classifications using SILVA DB`.

- DRR010481: that: has_text
- DRR010481: text: # mapseq v1.2.6 (Jan 20 2023)
- DRR010481: that: has_text
- DRR010481: text: SILVA
- DRR010481: that: has_n_columns
- DRR010481: comment: #
- DRR010481: n: 15

## its_taxonomic_classifications_using_itsonedb
Content assertions for `ITS taxonomic classifications using ITSoneDB`.

- DRR010481: that: has_text
- DRR010481: text: # mapseq v1.2.6 (Jan 20 2023)
- DRR010481: that: has_text
- DRR010481: text: ITSone
- DRR010481: that: has_n_columns
- DRR010481: comment: #
- DRR010481: n: 15
- ERR2715528: that: has_text
- ERR2715528: text: # mapseq v1.2.6 (Jan 20 2023)
- ERR2715528: that: has_text
- ERR2715528: text: ITSone
- ERR2715528: that: has_n_columns
- ERR2715528: comment: #
- ERR2715528: n: 15

## its_otu_tables_in_json_format_unite_db
Content assertions for `ITS OTU tables in JSON format (UNITE DB)`.

- DRR010481: that: has_text
- DRR010481: text: "type": "OTU table"
- ERR2715528: that: has_text
- ERR2715528: text: "type": "OTU table"

## its_taxonomic_abundance_pie_charts_unite_db
Content assertions for `ITS taxonomic abundance pie charts (UNITE DB)`.

- that: has_text
- text: DRR010481
- that: has_text
- text: ERR2715528

## its_otu_tables_in_hdf5_format_unite_db
Content assertions for `ITS OTU tables in HDF5 format (UNITE DB)`.

- DRR010481: that: has_size
- DRR010481: value: 37000
- DRR010481: delta: 10000
- ERR2715528: that: has_size
- ERR2715528: value: 72000
- ERR2715528: delta: 10000

## its_taxonomic_abundance_pie_charts_itsonedb
Content assertions for `ITS taxonomic abundance pie charts (ITSoneDB)`.

- that: has_text
- text: DRR010481
- that: has_text
- text: ERR2715528

## its_otu_tables_in_json_format_itsonedb
Content assertions for `ITS OTU tables in JSON format (ITSoneDB)`.

- DRR010481: that: has_text
- DRR010481: text: "type": "OTU table"
- ERR2715528: that: has_text
- ERR2715528: text: "type": "OTU table"

## its_otu_tables_in_hdf5_format_itsonedb
Content assertions for `ITS OTU tables in HDF5 format (ITSoneDB)`.

- DRR010481: that: has_size
- DRR010481: value: 37000
- DRR010481: delta: 10000
- ERR2715528: that: has_size
- ERR2715528: value: 72000
- ERR2715528: delta: 10000

## its_taxonomic_classifications_using_unite_db
Content assertions for `ITS taxonomic classifications using UNITE DB`.

- DRR010481: that: has_text
- DRR010481: text: # mapseq v1.2.6 (Jan 20 2023)
- DRR010481: that: has_text
- DRR010481: text: UNITE
- DRR010481: that: has_n_columns
- DRR010481: comment: #
- DRR010481: n: 15
- ERR2715528: that: has_text
- ERR2715528: text: # mapseq v1.2.6 (Jan 20 2023)
- ERR2715528: that: has_text
- ERR2715528: text: UNITE
- ERR2715528: that: has_n_columns
- ERR2715528: comment: #
- ERR2715528: n: 15

## its_otu_tables_unite_db
Content assertions for `ITS OTU tables (UNITE DB)`.

- DRR010481: that: has_text
- DRR010481: text: # Constructed from biom file
- DRR010481: that: has_text
- DRR010481: text: # OTU ID
- DRR010481: that: has_text
- DRR010481: text: Unspecified
- DRR010481: that: has_text
- DRR010481: text: taxonomy
- DRR010481: that: has_text
- DRR010481: text: taxid
- DRR010481: that: has_n_columns
- DRR010481: comment: #
- DRR010481: n: 4
- ERR2715528: that: has_text
- ERR2715528: text: # Constructed from biom file
- ERR2715528: that: has_text
- ERR2715528: text: # OTU ID
- ERR2715528: that: has_text
- ERR2715528: text: Unspecified
- ERR2715528: that: has_text
- ERR2715528: text: taxonomy
- ERR2715528: that: has_text
- ERR2715528: text: taxid
- ERR2715528: that: has_n_columns
- ERR2715528: comment: #
- ERR2715528: n: 4

## its_otu_tables_itsonedb
Content assertions for `ITS OTU tables (ITSoneDB)`.

- DRR010481: that: has_text
- DRR010481: text: # Constructed from biom file
- DRR010481: that: has_text
- DRR010481: text: # OTU ID
- DRR010481: that: has_text
- DRR010481: text: Unspecified
- DRR010481: that: has_text
- DRR010481: text: taxonomy
- DRR010481: that: has_text
- DRR010481: text: taxid
- DRR010481: that: has_n_columns
- DRR010481: comment: #
- DRR010481: n: 4
- ERR2715528: that: has_text
- ERR2715528: text: # Constructed from biom file
- ERR2715528: that: has_text
- ERR2715528: text: # OTU ID
- ERR2715528: that: has_text
- ERR2715528: text: Unspecified
- ERR2715528: that: has_text
- ERR2715528: text: taxonomy
- ERR2715528: that: has_text
- ERR2715528: text: taxid
- ERR2715528: that: has_n_columns
- ERR2715528: comment: #
- ERR2715528: n: 4

## itsonedb_phylum_level_taxonomic_abundance_summary_table
Content assertions for `ITSoneDB phylum level taxonomic abundance summary table`.

- that: has_text
- text: superkingdom	kingdom	phylum	DRR010481	ERR2715528
- that: has_n_columns
- n: 5
- that: has_n_lines
- n: 10
- delta: 4

## itsonedb_taxonomic_abundance_summary_table
Content assertions for `ITSoneDB taxonomic abundance summary table`.

- that: has_text
- text: #SampleID	DRR010481	ERR2715528
- that: has_n_columns
- n: 3
- that: has_n_lines
- n: 117
- delta: 17

## lsu_phylum_level_taxonomic_abundance_summary_table
Content assertions for `LSU phylum level taxonomic abundance summary table`.

- that: has_text
- text: superkingdom	kingdom	phylum	DRR010481
- that: has_n_columns
- n: 4
- that: has_n_lines
- n: 6
- delta: 4

## lsu_taxonomic_abundance_summary_table
Content assertions for `LSU taxonomic abundance summary table`.

- that: has_text
- text: #SampleID	DRR010481
- that: has_n_columns
- n: 2
- that: has_n_lines
- n: 6
- delta: 4

## ssu_phylum_level_taxonomic_abundance_summary_table
Content assertions for `SSU phylum level taxonomic abundance summary table`.

- that: has_text
- text: superkingdom	kingdom	phylum	ERR2715528
- that: has_n_columns
- n: 4
- that: has_n_lines
- n: 12
- delta: 4

## ssu_taxonomic_abundance_summary_table
Content assertions for `SSU taxonomic abundance summary table`.

- that: has_text
- text: #SampleID	ERR2715528
- that: has_n_columns
- n: 2
- that: has_n_lines
- n: 13
- delta: 4

## its_unite_db_phylum_level_taxonomic_abundance_summary_table
Content assertions for `ITS UNITE DB phylum level taxonomic abundance summary table`.

- that: has_text
- text: superkingdom	kingdom	phylum	DRR010481	ERR2715528
- that: has_n_columns
- n: 5
- that: has_n_lines
- n: 13
- delta: 4

## its_unite_db_taxonomic_abundance_summary_table
Content assertions for `ITS UNITE DB taxonomic abundance summary table`.

- that: has_text
- text: #SampleID	DRR010481	ERR2715528
- that: has_n_columns
- n: 3
- that: has_n_lines
- n: 130
- delta: 19

