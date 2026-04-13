# Content assertions (no golden file checked in)
## hicup_report_html
Content assertions for `HiCUP report (html)`.

- test_dataset: has_size: {'value': 4602173, 'delta': 4000000}

## hicup_report_txt
Content assertions for `HiCUP report (txt)`.

- test_dataset: has_text: 	99742	99742	92512	92628	7230	7114	22.45	22.63	2658	2476	73431	72142	17767	18475	5886	6649	57671	57671	39966	1652	17997	20317	17705	481	2432	13452	1340	0	0	39962	1652	17996	20314	57.82	69.30	99.99	50.83	40.07

## valid_pairs_in_juicebox_format
Content assertions for `valid pairs in juicebox format`.

- test_dataset: that: has_line
- test_dataset: line: 1	1	chr10	100023987	28055	1	chr10	101500419	28474	42	42
- test_dataset: that: has_line
- test_dataset: line: 2	1	chr10	100091500	28079	1	chr10	122245984	34516	38	42
- test_dataset: that: has_line
- test_dataset: line: 3	0	chr10	100127492	28094	1	chr10	50864290	13489	0	42

## valid_pairs_in_juicebox_format_mapq_filtered
Content assertions for `valid pairs in juicebox format MAPQ filtered`.

- test_dataset: that: has_line
- test_dataset: line: 1	1	chr10	100023987	28055	1	chr10	101500419	28474	42	42
- test_dataset: that: has_line
- test_dataset: line: 2	1	chr10	100091500	28079	1	chr10	122245984	34516	38	42
- test_dataset: that: not_has_text
- test_dataset: text: 3	0	chr10	100127492	28094	1	chr10	50864290	13489	0	42

## valid_pairs_filtered_and_sorted
Content assertions for `valid pairs filtered and sorted`.

- test_dataset: has_size: {'value': 807, 'delta': 80}

## matrix_with_raw_values
Content assertions for `matrix with raw values`.

- test_dataset: has_size: {'value': 42118, 'delta': 4000}

## matrix_with_iced_values
Content assertions for `matrix with iced values`.

- test_dataset: has_size: {'value': 47830, 'delta': 4000}

