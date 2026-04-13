# Content assertions (no golden file checked in)
## staramr_detailed_summary
Content assertions for `staramr_detailed_summary`.

- has_text: Resistance
- has_n_columns: {'n': 12}

## staramr_resfinder_report
Content assertions for `staramr_resfinder_report`.

- has_text: Chloramphenicol
- has_n_columns: {'n': 13}

## staramr_mlst_report
Content assertions for `staramr_mlst_report`.

- has_text: Scheme

## staramr_pointfinder_report
Content assertions for `staramr_pointfinder_report`.

- has_text: Pointfinder Position
- has_n_columns: {'n': 18}

## staramr_plasmidfinder_report
Content assertions for `staramr_plasmidfinder_report`.

- has_text: rep7a
- has_n_columns: {'n': 9}

## staramr_summary
Content assertions for `staramr_summary`.

- has_text: erythromycin
- has_n_columns: {'n': 12}

## amrfinderplus_report
Content assertions for `amrfinderplus_report`.

- has_text: catA
- has_n_columns: {'n': 23}

## amrfinderplus_mutation
Content assertions for `amrfinderplus_mutation`.

- has_text: Element subtype
- has_n_columns: {'n': 23}

## abricate_virulence_report
Content assertions for `abricate_virulence_report`.

- has_text: RESISTANCE

## tooldistillator_summarize_amr
Content assertions for `tooldistillator_summarize_amr`.

- that: has_text
- text: % Identity to reference sequence
- that: has_text
- text: pointfinder_file
- that: has_text
- text: LINCOSAMIDE

## multiqc_html_report
Content assertions for `multiqc_html_report`.

- that: has_text
- text: ABRicate virulence
- that: has_text
- text: Staramr detailed summary

