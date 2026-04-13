# Content assertions (no golden file checked in)
## rooted_tree
Content assertions for `Rooted tree`.

- has_size: {'min': '2M', 'max': '3M'}
- has_archive_member: {'path': '^[^/]*/data/tree.nwk', 'n': 1, 'asserts': [{'has_text_matching': {'expression': 'k__Bacteria'}}]}
- has_archive_member: {'path': '^[^/]*/metadata.yaml', 'n': 1, 'asserts': [{'has_line': {'line': 'type: Phylogeny[Rooted]'}}, {'has_line': {'line': 'format: NewickDirectoryFormat'}}]}

## rarefaction_curve
Content assertions for `Rarefaction curve`.

- has_size: {'min': '400k', 'max': '500k'}
- has_archive_member: {'path': '^[^/]*/data/index.html', 'n': 1}
- has_archive_member: {'path': '^[^/]*/data/.*\\.csv', 'n': 3}
- has_archive_member: {'path': '^[^/]*/data/.*\\.jsonp', 'n': 21}

## taxonomy_classification
Content assertions for `Taxonomy classification`.

- has_size: {'min': '40k', 'max': '80k'}
- has_archive_member: {'path': '^[^/]*/metadata.yaml', 'n': 1, 'asserts': [{'has_line': {'line': 'type: FeatureData[Taxonomy]'}}, {'has_line': {'line': 'format: TSVTaxonomyDirectoryFormat'}}]}
- has_archive_member: {'path': '^[^/]*/data/taxonomy.tsv', 'n': 1, 'asserts': [{'has_n_lines': {'n': 288}}]}

## taxa_barplot
Content assertions for `Taxa barplot`.

- has_size: {'min': '400k', 'max': '500k'}
- has_archive_member: {'path': '^[^/]*/data/.*\\.csv', 'n': 7}
- has_archive_member: {'path': '^[^/]*/data/.*\\.jsonp', 'n': 7}

## taxonomy_classification_table
Content assertions for `Taxonomy classification table`.

- has_size: {'min': '1M', 'max': '2M'}
- has_archive_member: {'path': '^[^/]*/data/metadata.tsv', 'n': 1, 'asserts': [{'has_n_lines': {'n': 289}}]}

