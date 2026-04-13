# Content assertions (no golden file checked in)
## baredsc_numpy
Content assertions for `baredsc_numpy`.

- split_file_000000.tabular: has_size: {'value': 1257919, 'delta': 100000}
- split_file_000001.tabular: has_size: {'value': 1601519, 'delta': 100000}
- split_file_000002.tabular: has_size: {'value': 2180423, 'delta': 200000}
- split_file_000003.tabular: has_size: {'value': 28234812, 'delta': 2000000}

## baredsc_neff
Content assertions for `baredsc_neff`.

- split_file_000000.tabular: has_n_lines: {'n': 1}
- split_file_000000.tabular: has_line_matching: {'expression': '80[0-9][0-9].[0-9]*'}
- split_file_000001.tabular: has_n_lines: {'n': 1}
- split_file_000001.tabular: has_line_matching: {'expression': '13[0-9][0-9].[0-9]*'}
- split_file_000002.tabular: has_n_lines: {'n': 1}
- split_file_000002.tabular: has_line_matching: {'expression': '2[0-9][0-9].[0-9]*'}
- split_file_000003.tabular: has_n_lines: {'n': 1}
- split_file_000003.tabular: has_line_matching: {'expression': '[7-9][0-9][0-9].[0-9]*'}

## combined_other_outputs
Content assertions for `combined_other_outputs`.

- individuals: has_size: {'value': 108407, 'delta': 10000}
- means: has_n_lines: {'n': 99998, 'delta': 4000}
- means: has_line_matching: {'expression': '6.[0-9]*e-01'}
- posterior_andco: has_size: {'value': 197980, 'delta': 10000}
- posterior_individuals: has_size: {'value': 105262, 'delta': 10000}
- posterior_per_cell: has_n_lines: {'n': 2362}
- posterior_per_cell: has_line_matching: {'expression': 'mu\tsd'}
- with_posterior: has_size: {'value': 234303, 'delta': 20000}

## combined_pdf
Content assertions for `combined_pdf`.

- has_line: x	low	mean	high	median
- has_text: 0.0125	

