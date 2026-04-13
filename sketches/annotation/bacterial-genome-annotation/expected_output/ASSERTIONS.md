# Content assertions (no golden file checked in)
## integronfinder2_logfile_text
Content assertions for `integronfinder2_logfile_text`.

- has_text: Writing out results for replicon

## integronfinder2_summary
Content assertions for `integronfinder2_summary`.

- has_text: contig00001

## integronfinder2_results_tabular
Content assertions for `integronfinder2_results_tabular`.

- has_text: contig00009_42

## bakta_hypothetical_tabular
Content assertions for `bakta_hypothetical_tabular`.

- has_text: DHJLLP_04750

## bakta_annotation_json
Content assertions for `bakta_annotation_json`.

- has_text: aa_hexdigest

## bakta_annotation_tabular
Content assertions for `bakta_annotation_tabular`.

- has_text: Phosphotransferase system cellobiose-specific component IIC

## isescan_results_tabular
Content assertions for `isescan_results_tabular`.

- has_text: IS256_162

## isescan_summary_tabular
Content assertions for `isescan_summary_tabular`.

- has_text: nIS

## isescan_logfile_text
Content assertions for `isescan_logfile_text`.

- has_text: Both complete and partial IS elements are reported.

## plasmidfinder_result_json
Content assertions for `plasmidfinder_result_json`.

- has_text: positions_in_contig

## plasmidfinder_results_tabular
Content assertions for `plasmidfinder_results_tabular`.

- has_n_columns: {'n': 8}

## tooldistillator_summarize_annotation_without_bakta
Content assertions for `tooldistillator_summarize_annotation_without_bakta`.

- that: has_text
- text: contig00009
- that: has_text
- text: rep9b:WARNING

## tooldistillator_summarize_bakta
Content assertions for `tooldistillator_summarize_bakta`.

- that: has_text
- text: UniParc:UPI000005C018
- that: has_text
- text: GO:0050511

