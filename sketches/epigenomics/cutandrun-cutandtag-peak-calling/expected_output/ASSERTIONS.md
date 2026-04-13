# Content assertions (no golden file checked in)
## mapping_stats
Content assertions for `Mapping stats`.

- Rep1: has_text: 289103 reads; of these:
- Rep1: has_text_matching: {'expression': '99.39% overall alignment rate'}

## bam_filtered_rmdup
Content assertions for `BAM filtered rmDup`.

- Rep1: has_size: {'value': 8661584, 'delta': 800000}

## markduplicates_metrics
Content assertions for `MarkDuplicates metrics`.

- Rep1: has_text: 0.33

## macs2_summits
Content assertions for `MACS2 summits`.

- Rep1: has_n_lines: {'n': 5870}

## macs2_narrowpeak
Content assertions for `MACS2 narrowPeak`.

- Rep1: has_n_lines: {'n': 5870}

## macs2_peaks_xls
Content assertions for `MACS2 peaks xls`.

- Rep1: has_text: # tag size is determined as 40 bps
- Rep1: has_text_matching: {'expression': '# total tags in treatment: 238930'}

