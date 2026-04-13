# Content assertions (no golden file checked in)
## multiqc_stats
Content assertions for `MultiQC stats`.

- has_text_matching: {'expression': 'SRR5085167\t0.11[0-9]*\t18.3[0-9]*\t69.6[0-9]*\t0.3[0-9]*\t0.3[0-9]*\t94.62\t0.12[0-9]*\t34.43\t0.2[0-9]*\t36.[0-9]*\t46.0\t75.0\t75\t27.27[0-9]*\t0.39[0-9]*'}

## counts_table
Content assertions for `Counts Table`.

- SRR5085167: has_line: YAL038W	1775

## mapped_reads
Content assertions for `Mapped Reads`.

- SRR5085167: has_size: {'value': 31570787, 'delta': 3000000}

## gene_abundance_estimates_from_stringtie
Content assertions for `Gene Abundance Estimates from StringTie`.

- SRR5085167: has_text_matching: {'expression': 'YAL038W\tCDC19\tchrI\t\\+\t71786\t73288\t57.[0-9]*\t3575.[0-9]*\t3084.[0-9]*'}

## genes_expression_from_cufflinks
Content assertions for `Genes Expression from Cufflinks`.

- SRR5085167: has_text_matching: {'expression': 'YAL038W\t-\t-\tYAL038W\tCDC19\t-\tchrI:71785-73288\t-\t-\t3375.8[0-9]*\t3161.3[0-9]*\t3590.3[0-9]*\tOK'}

## transcripts_expression_from_cufflinks
Content assertions for `Transcripts Expression from Cufflinks`.

- SRR5085167: has_text_matching: {'expression': 'YAL038W_mRNA\t-\t-\tYAL038W\tCDC19\t-\tchrI:71785-73288\t1503\t57.56[0-9]*\t3375.8[0-9]*\t3161.3[0-9]*\t3590.3[0-9]*\tOK'}

## stranded_coverage
Content assertions for `Stranded Coverage`.

- SRR5085167_forward: has_size: {'value': 555489, 'delta': 50000}
- SRR5085167_reverse: has_size: {'value': 526952, 'delta': 50000}

## unstranded_coverage
Content assertions for `Unstranded Coverage`.

- SRR5085167: has_size: {'value': 978542, 'delta': 90000}

