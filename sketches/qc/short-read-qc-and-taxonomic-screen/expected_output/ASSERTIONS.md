# Content assertions (no golden file checked in)
## fastp_report_json
Content assertions for `fastp_report_json`.

- has_text: read2_before_filtering

## kraken_report_tabular
Content assertions for `kraken_report_tabular`.

- has_text: Enterococcus avium
- has_n_columns: {'n': 6}

## kraken_report
Content assertions for `kraken_report`.

- has_text: M07044:90:000000000-JRJWP:1:1119:23974:4461
- has_n_columns: {'n': 5}

## bracken_kraken_report
Content assertions for `bracken_kraken_report`.

- has_text: Enterococcus gallinarum
- has_n_columns: {'n': 6}

## bracken_report_tsv
Content assertions for `bracken_report_tsv`.

- has_text: Escherichia coli
- has_n_columns: {'n': 7}

## tooldistillator_summarize_control
Content assertions for `tooldistillator_summarize_control`.

- that: has_text
- text: fastp_report

