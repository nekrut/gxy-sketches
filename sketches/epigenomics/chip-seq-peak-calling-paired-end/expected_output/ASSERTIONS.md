# Content assertions (no golden file checked in)
## multiqc_webpage
Content assertions for `MultiQC webpage`.

- that: has_text
- text: wt_H3K4me3
- that: has_text
- text: <a href="#fastp" class="nav-l1">fastp</a>
- that: has_text
- text: <a href="#bowtie2" class="nav-l1">Bowtie 2 / HiSAT2</a>

## multiqc_on_input_dataset_s_stats
Content assertions for `MultiQC on input dataset(s): Stats`.

- has_line: Sample	macs2-d	macs2-treatment_redundant_rate	macs2-peak_count	bowtie_2_hisat2-overall_alignment_rate	fastp-after_filtering_q30_rate	fastp-after_filtering_q30_bases	fastp-filtering_result_passed_filter_reads	fastp-after_filtering_gc_content	fastp-pct_surviving	fastp-pct_adapter	fastp-before_filtering_read1_mean_length	fastp-before_filtering_read2_mean_length
- has_text_matching: {'expression': 'wt_H3K4me3\t20[12].0\t0.0\t13\t98.[0-9]*\t93.[0-9]*\t4.5[0-9]*\t0.095[0-9]*\t57.[0-9]*\t95.[0-9]*\t0.19[0-9]*\t51.0\t51.0'}

## filtered_bam
Content assertions for `filtered BAM`.

- wt_H3K4me3: has_size: {'value': 5311841, 'delta': 500000}

## macs2_summits
Content assertions for `MACS2 summits`.

- wt_H3K4me3: has_n_lines: {'n': 13}

## macs2_peaks
Content assertions for `MACS2 peaks`.

- wt_H3K4me3: that: has_text
- wt_H3K4me3: text: # effective genome size = 1.87e+09
- wt_H3K4me3: that: has_text_matching
- wt_H3K4me3: expression: # fragment size is determined as 20[12] bps
- wt_H3K4me3: that: has_text
- wt_H3K4me3: text: # fragments after filtering in treatment: 42745

## macs2_narrowpeak
Content assertions for `MACS2 narrowPeak`.

- wt_H3K4me3: has_n_lines: {'n': 13}

## macs2_report
Content assertions for `MACS2 report`.

- wt_H3K4me3: that: has_text
- wt_H3K4me3: text: # effective genome size = 1.87e+09
- wt_H3K4me3: that: has_text_matching
- wt_H3K4me3: expression: # fragment size is determined as 20[12] bps
- wt_H3K4me3: that: has_text
- wt_H3K4me3: text: # fragments after filtering in treatment: 42745

## coverage_from_macs2
Content assertions for `coverage from MACS2`.

- wt_H3K4me3: has_size: {'value': 568174, 'delta': 50000}

## mapping_stats
Content assertions for `mapping stats`.

- wt_H3K4me3: that: has_text
- wt_H3K4me3: text: 1344 (2.82%) aligned concordantly 0 times
- wt_H3K4me3: that: has_text
- wt_H3K4me3: text: 42961 (90.29%) aligned concordantly exactly 1 time
- wt_H3K4me3: that: has_text
- wt_H3K4me3: text: 3276 (6.89%) aligned concordantly >1 times

