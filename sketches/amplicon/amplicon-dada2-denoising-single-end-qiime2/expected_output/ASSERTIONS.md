# Content assertions (no golden file checked in)
## denoising_output_table
Content assertions for `Denoising output table`.

- has_size: {'min': '20k'}
- has_archive_member: {'path': '^[^/]*/data/feature-table.biom', 'n': 1}

## representative_denoised_sequences
Content assertions for `Representative denoised sequences`.

- has_size: {'min': '20k'}
- has_archive_member: {'path': '^[^/]*/metadata.yaml', 'n': 1}
- has_archive_member: {'path': '^[^/]*/data/dna-sequences.fasta', 'n': 1, 'asserts': [{'has_text_matching': {'expression': '>.*', 'n': 770}}]}

## denoising_statistics
Content assertions for `Denoising statistics`.

- has_size: {'min': 0}
- has_size: {'min': '10k'}
- has_archive_member: {'path': '^[^/]*/data/stats.tsv', 'n': 1, 'asserts': [{'has_n_columns': {'n': 7}}, {'has_n_lines': {'n': 36}}]}

