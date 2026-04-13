# Content assertions (no golden file checked in)
## coreprofiler_allele_calling_report
Content assertions for `CoreProfiler allele calling report`.

- has_text: AEJV01_03887
- has_n_columns: {'n': 2514}

## newly_detected_alleles_by_coreprofiler
Content assertions for `Newly detected alleles by CoreProfiler`.

- has_text: >

## information_about_temporary_alleles_found_by_coreprofiler
Content assertions for `Information about temporary alleles found by CoreProfiler`.

- has_text: tmp_loci

## summarized_cgmlst_tooldistillator_results
Content assertions for `Summarized cgMLST ToolDistillator results`.

- that: has_text
- text: coreprofiler_report
- that: has_text
- text: profiles_w_tmp_alleles
- that: has_text
- text: new_alleles_fna

