# Content assertions (no golden file checked in)
## full_multiqc_report
Content assertions for `Full MultiQC Report`.

- that: has_text
- text: 50contig_reads_bin
- that: has_text
- text: QUAST
- that: has_text
- text: CheckM

## assembly_report
Content assertions for `Assembly Report`.

- 50contig_reads: that: has_text
- 50contig_reads: text: All statistics are based on contigs of size
- 50contig_reads: that: has_size
- 50contig_reads: value: 372000
- 50contig_reads: delta: 50000

