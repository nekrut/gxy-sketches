# Content assertions (no golden file checked in)
## mapping_stats
Content assertions for `mapping stats`.

- SRR891268_chr22_enriched: that: has_text
- SRR891268_chr22_enriched: text: 7282 (2.59%) aligned concordantly 0 times
- SRR891268_chr22_enriched: that: has_text
- SRR891268_chr22_enriched: text: 121059 (43.09%) aligned concordantly exactly 1 time
- SRR891268_chr22_enriched: that: has_text
- SRR891268_chr22_enriched: text: 152623 (54.32%) aligned concordantly >1 times

## markduplicates_metrics
Content assertions for `MarkDuplicates metrics`.

- SRR891268_chr22_enriched: has_text: 0.02

## bam_filtered_rmdup
Content assertions for `BAM filtered rmDup`.

- SRR891268_chr22_enriched: has_size: {'value': 15810403, 'delta': 1000000}

## histogram_of_fragment_length
Content assertions for `histogram of fragment length`.

- SRR891268_chr22_enriched: has_size: {'value': 47718, 'delta': 4000}

## macs2_narrowpeak
Content assertions for `MACS2 narrowPeak`.

- SRR891268_chr22_enriched: has_n_lines: {'n': 236}

## macs2_report
Content assertions for `MACS2 report`.

- SRR891268_chr22_enriched: that: has_text
- SRR891268_chr22_enriched: text: # tag size is determined as 47 bps
- SRR891268_chr22_enriched: that: has_text
- SRR891268_chr22_enriched: text: # total tags in treatment: 262080

## coverage_from_macs2_bigwig
Content assertions for `Coverage from MACS2 (bigwig)`.

- SRR891268_chr22_enriched: has_size: {'value': 2892925, 'delta': 200000}

## 1kb_around_summits
Content assertions for `1kb around summits`.

- SRR891268_chr22_enriched: has_n_lines: {'n': 217}

## nb_of_reads_in_summits_500bp
Content assertions for `Nb of reads in summits +-500bp`.

- SRR891268_chr22_enriched: has_line: 9548

## bigwig_norm
Content assertions for `bigwig_norm`.

- SRR891268_chr22_enriched: has_size: {'value': 1253177, 'delta': 100000}

## bigwig_norm2
Content assertions for `bigwig_norm2`.

- SRR891268_chr22_enriched: has_size: {'value': 1248419, 'delta': 100000}

## multiqc_on_input_dataset_s_stats
Content assertions for `MultiQC on input dataset(s): Stats`.

- has_line: Sample	MACS2_mqc_generalstats_macs2_d	MACS2_mqc_generalstats_macs2_peak_count	Picard: Mark Duplicates_mqc_generalstats_picard_mark_duplicates_PERCENT_DUPLICATION	Bowtie 2 / HiSAT2_mqc_generalstats_bowtie_2_hisat2_overall_alignment_rate	Cutadapt_mqc_generalstats_cutadapt_percent_trimmed
- has_text_matching: {'expression': 'SRR891268_chr22_enriched\t200.0\t236\t2.7[0-9]*\t98.[0-9]*\t4.7[0-9]*'}

## multiqc_webpage
Content assertions for `MultiQC webpage`.

- that: has_text
- text: <a href="#cutadapt_filtered_reads" class="nav-l2">Filtered Reads</a>
- that: has_text
- text: <td>% Aligned</td>
- that: has_text
- text: <td>% BP Trimmed</td>

