# Content assertions (no golden file checked in)
## multiqc_starsolo
Content assertions for `MultiQC_STARsolo`.

- has_text_matching: {'expression': '<span class="val">33.[0-9]<span class=[\'"]mqc_small_space[\'"]>'}

## cite_seq_count_report
Content assertions for `CITE-seq-Count report`.

- subsample: that: has_line
- subsample: line: CITE-seq-Count Version: 1.4.4
- subsample: that: has_line
- subsample: line: Reads processed: 116993
- subsample: that: has_line
- subsample: line: Percentage mapped: 99
- subsample: that: has_line
- subsample: line: Percentage unmapped: 1

