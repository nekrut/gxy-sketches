# Content assertions (no golden file checked in)
## taxonomic_rank_summary_table
Content assertions for `Taxonomic rank summary table`.

- that: has_size
- size: 11263
- that: has_text
- text: superkingdom	kingdom	phylum	class	order	family	ERR3046414	ERR3046440	ERR4319664	ERR4319712
- that: has_text
- text: Bacteria	unassigned	Actinobacteria	Acidimicrobiia	unassigned	unassigned	0	0	1	3
- that: has_text
- text: Bacteria	unassigned	Actinobacteria	Actinobacteria	Actinomycetales	Actinomycetaceae	4	1	0	0
- that: has_n_lines
- n: 129
- that: has_n_columns
- n: 10

