# Content assertions (no golden file checked in)
## multiqc_stats
Content assertions for `MultiQC stats`.

- that: has_text_matching
- expression: SRR5085167	0.10[0-9]*	16.45[0-9]*	43.38[0-9]*	0.32[0-9]*	0.30[0-9]*	93.75	0.11[0-9]*	34.29	0.19[0-9]*
- that: has_text_matching
- expression: SRR5085167_forward	*36.33[0-9]*	46.0	75.0	75	27.27[0-9]*	0.39[0-9]*
- that: has_text_matching
- expression: SRR5085167_reverse	*35.31[0-9]*	46.0	75.0	75	45.45[0-9]*	0.39[0-9]*

## stranded_coverage
Content assertions for `Stranded Coverage`.

- SRR5085167_forward: has_size: {'value': 635210, 'delta': 30000}
- SRR5085167_reverse: has_size: {'value': 618578, 'delta': 30000}

## gene_abundance_estimates_from_stringtie
Content assertions for `Gene Abundance Estimates from StringTie`.

- SRR5085167: has_text_matching: {'expression': 'YAL038W\tCDC19\tchrI\t\\+\t71786\t73288\t92.5[0-9]*\t3273.[0-9]*\t[0-9]*.[0-9]*'}

## unstranded_coverage
Content assertions for `Unstranded Coverage`.

- SRR5085167: has_size: {'value': 1140004, 'delta': 50000}

## mapped_reads
Content assertions for `Mapped Reads`.

- SRR5085167: has_size: {'value': 56913572, 'delta': 2500000}

## genes_expression_from_cufflinks
Content assertions for `Genes Expression from Cufflinks`.

- SRR5085167: has_text_matching: {'expression': 'YAL038W\t-\t-\tYAL038W\tCDC19\t-\tchrI:71785-73288\t-\t-\t3437.[0-9]*\t3211.[0-9]*\t3662.[0-9]*\tOK'}

## transcripts_expression_from_cufflinks
Content assertions for `Transcripts Expression from Cufflinks`.

- SRR5085167: has_text_matching: {'expression': 'YAL038W_mRNA\t-\t-\tYAL038W\tCDC19\t-\tchrI:71785-73288\t1503\t102.8[0-9]*\t3437.[0-9]*\t3211.[0-9]*\t3662.[0-9]*\tOK'}

## counts_table
Content assertions for `Counts Table`.

- SRR5085167: has_line: YAL038W	1591

