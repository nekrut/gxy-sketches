# Content assertions (no golden file checked in)
## demultiplexed_single_end_data
Content assertions for `Demultiplexed single-end data`.

- has_size: {'value': '20M', 'delta': '1M'}
- has_archive_member: {'path': '.*data/L[0-9]S[0-9]{1,3}_[0-9]{1,2}_L001_R1_001\\.fastq\\.gz', 'n': 34}
- has_archive_member: {'path': '.*/data/metadata.yml', 'asserts': [{'has_text': {'text': 'phred-offset: 33'}}]}
- has_archive_member: {'path': '^[^/]*/metadata.yaml', 'n': 1, 'asserts': [{'has_text': {'text': 'uuid:'}}, {'has_text': {'text': 'type: SampleData[SequencesWithQuality]'}}, {'has_text': {'text': 'format: SingleLanePerSampleSingleEndFastqDirFmt'}}]}

