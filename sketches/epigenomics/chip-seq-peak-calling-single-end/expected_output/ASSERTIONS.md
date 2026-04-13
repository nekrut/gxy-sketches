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

- has_line: Sample	macs2-d	macs2-treatment_redundant_rate	macs2-peak_count	bowtie_2_hisat2-overall_alignment_rate	fastp-after_filtering_q30_rate	fastp-after_filtering_q30_bases	fastp-filtering_result_passed_filter_reads	fastp-after_filtering_gc_content	fastp-pct_surviving	fastp-pct_adapter	fastp-before_filtering_read1_mean_length
- has_text_matching: {'expression': 'wt_H3K4me3\t200.0\t0.0\t9\t98.[0-9]*\t93.[0-9]*\t2.3[0-9]*\t0.049[0-9]*\t57.[0-9]*\t99.[0-9]*\t0.12[0-9]*\t51.0'}

## filtered_bam
Content assertions for `filtered BAM`.

- wt_H3K4me3: has_size: {'value': 2587182, 'delta': 200000}

## macs2_summits
Content assertions for `MACS2 summits`.

- wt_H3K4me3: has_n_lines: {'n': 9}

## macs2_peaks
Content assertions for `MACS2 peaks`.

- wt_H3K4me3: that: has_text
- wt_H3K4me3: text: # effective genome size = 1.87e+09
- wt_H3K4me3: that: has_text
- wt_H3K4me3: text: # d = 200
- wt_H3K4me3: that: has_text
- wt_H3K4me3: text: # tags after filtering in treatment: 44528

## macs2_narrowpeak
Content assertions for `MACS2 narrowPeak`.

- wt_H3K4me3: has_n_lines: {'n': 9}

## macs2_report
Content assertions for `MACS2 report`.

- wt_H3K4me3: that: has_text
- wt_H3K4me3: text: # effective genome size = 1.87e+09
- wt_H3K4me3: that: has_text
- wt_H3K4me3: text: # d = 200
- wt_H3K4me3: that: has_text
- wt_H3K4me3: text: # tags after filtering in treatment: 44528

## coverage_from_macs2
Content assertions for `coverage from MACS2`.

- wt_H3K4me3: has_size: {'value': 563563, 'delta': 10000}

## mapping_stats
Content assertions for `mapping stats`.

- wt_H3K4me3: that: has_text
- wt_H3K4me3: text: 49813 reads; of these:
- wt_H3K4me3: that: has_text
- wt_H3K4me3: text: 44357 (89.05%) aligned exactly 1 time
- wt_H3K4me3: that: has_text
- wt_H3K4me3: text: 98.27% overall alignment rate

