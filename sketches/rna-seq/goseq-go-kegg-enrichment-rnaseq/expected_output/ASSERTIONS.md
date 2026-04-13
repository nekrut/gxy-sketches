# Content assertions (no golden file checked in)
## goseq_enrichment_table_cellular_component
Content assertions for `goseq Enrichment Table (Cellular Component)`.

- that: has_text_matching
- expression: category	over_represented_pvalue	under_represented_pvalue	numDEInCat	numInCat	term	ontology	p_adjust_over_represented	p_adjust_under_represented
- that: has_text_matching
- expression: GO:0005737	4.79[0-9]+e-08	1	4810	8312	cytoplasm	CC	9.31[0-9]+e-05	1
- that: has_text_matching
- expression: over_represented_pvalue
- that: has_text_matching
- expression: under_represented_pvalue

## goseq_top_categories_plot_cellular_component
Content assertions for `goseq Top Categories plot (Cellular Component)`.

- that: has_size
- size: 7078

## goseq_differential_genes_in_each_category_cellular_component
Content assertions for `goseq Differential Genes in each Category (Cellular Component)`.

- that: has_text_matching
- expression: category	de_genes
- that: has_text_matching
- expression: GO:0005737	ENSMUSG00000045545,ENSMUSG00000029802,ENSMUSG00000058056

## goseq_differential_genes_in_each_category_biological_process
Content assertions for `goseq Differential Genes in each Category (Biological Process)`.

- that: has_text_matching
- expression: category	de_genes
- that: has_text_matching
- expression: GO:0043254	ENSMUSG00000023951,ENSMUSG00000032060,ENSMUSG00000031284,

## goseq_top_categories_plot_biological_process
Content assertions for `goseq Top Categories plot (Biological Process)`.

- that: has_size
- size: 7092

## goseq_enrichment_table_biological_process
Content assertions for `goseq Enrichment Table (Biological Process)`.

- that: has_text_matching
- expression: category	over_represented_pvalue	under_represented_pvalue	numDEInCat	numInCat	term	ontology	p_adjust_over_represented	p_adjust_under_represented
- that: has_text_matching
- expression: GO:0043254	3.41[0-9]+e-07	1	239	345	regulation of protein-containing complex assembly	BP	0.0034[0-9]+	1
- that: has_text_matching
- expression: over_represented_pvalue
- that: has_text_matching
- expression: under_represented_pvalue

## goseq_differential_genes_in_each_category_kegg
Content assertions for `goseq Differential Genes in each Category (KEGG)`.

- that: has_text_matching
- expression: category	de_genes
- that: has_text_matching
- expression: 04540	ENSMUSG00000063358,ENSMUSG00000045136,ENSMUSG00000025856,ENSMUSG00000028019

## goseq_top_categories_plot_molecular_function
Content assertions for `goseq Top Categories plot (Molecular Function)`.

- that: has_size
- size: 7166

## goseq_enrichment_table_molecular_function
Content assertions for `goseq Enrichment Table (Molecular Function)`.

- that: has_text_matching
- expression: category	over_represented_pvalue	under_represented_pvalue	numDEInCat	numInCat	term	ontology	p_adjust_over_represented	p_adjust_under_represented
- that: has_text_matching
- expression: GO:0005515	1.4094[0-9]+e-07	1	3758	6415	protein binding	MF	0.0006[0-9]+	1
- that: has_text_matching
- expression: over_represented_pvalue
- that: has_text_matching
- expression: under_represented_pvalue

## goseq_differential_genes_in_each_category_molecular_function
Content assertions for `goseq Differential Genes in each Category (Molecular Function)`.

- that: has_text_matching
- expression: category	de_genes
- that: has_text_matching
- expression: GO:0005515	ENSMUSG00000045545,ENSMUSG00000029802,ENSMUSG00000058056,ENSMUSG00000004044,

## goseq_enrichment_table_kegg
Content assertions for `goseq Enrichment Table (KEGG)`.

- that: has_text_matching
- expression: category	over_represented_pvalue	under_represented_pvalue	numDEInCat	numInCat	p_adjust_over_represented	p_adjust_under_represented	ID	Name
- that: has_text_matching
- expression: 04540	0.0031[0-9]+	0.99[0-9]+	47	61	0.46[0-9]+	1	04540	Gap junction - mmus

