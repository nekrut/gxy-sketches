# Content assertions (no golden file checked in)
## groot_report
Content assertions for `Groot Report`.

- raw_reads_metag_test: has_text: argannot~~~(Bla)cfxA2~~~AF504910:1-966
- raw_reads_metag_test: has_n_columns: {'n': 4}

## argnorm_groot_report
Content assertions for `argNorm Groot Report`.

- raw_reads_metag_test: has_text: ARO:3003002
- raw_reads_metag_test: has_n_columns: {'n': 1}

## tooldistillator_summarize
Content assertions for `Tooldistillator Summarize`.

- raw_reads_metag_test: that: has_text
- raw_reads_metag_test: text: groot_report
- raw_reads_metag_test: that: has_text
- raw_reads_metag_test: text: sylph_report
- raw_reads_metag_test: that: has_text
- raw_reads_metag_test: text: sylphtax_report
- raw_reads_metag_test: that: has_text
- raw_reads_metag_test: text: argnorm_report
- raw_reads_metag_test: that: has_text
- raw_reads_metag_test: text: deeparg_report
- raw_reads_metag_test: that: has_text
- raw_reads_metag_test: text: sylph-tax.sylphmpa_file

## multiqc_report
Content assertions for `MultiQC report`.

- that: has_text
- text: multiqc
- that: has_text
- text: sylphtax
- that: has_text
- text: DeepARG
- that: has_text
- text: Groot

