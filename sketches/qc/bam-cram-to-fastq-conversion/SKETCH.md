---
name: bam-cram-to-fastq-conversion
description: Use when you need to convert one or more mapped or unmapped BAM/CRAM
  files back into gzipped FASTQ files for reuse in downstream pipelines, optionally
  restricted to specific chromosomes or regions. Auto-detects single- vs paired-end
  and handles both BAM and CRAM inputs.
domain: qc
organism_class:
- any
input_data:
- bam
- cram
- reference-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/bamtofastq
  url: https://github.com/nf-core/bamtofastq
  version: 2.2.0
  license: MIT
  slug: bamtofastq
tools:
- name: samtools
- name: fastqc
  version: 0.12.1
- name: fastq_utils
- name: multiqc
  version: '1.28'
tags:
- bam
- cram
- fastq
- conversion
- samtools
- reformat
- reverse-alignment
test_data: []
expected_output: []
---

# BAM/CRAM to FASTQ conversion

## When to use this sketch
- You have one or more `.bam` or `.cram` files (mapped or unmapped) and need valid gzipped FASTQ output to feed into another pipeline.
- Input may be single-end or paired-end; you do not know in advance and want auto-detection.
- You want reads only from a specific chromosome or region (e.g. `chrX`, `chr{1..22}`) rather than the whole file.
- You need QC (FastQC, samtools flagstat/idxstats/stats) on both input alignments and extracted reads, aggregated in a MultiQC report.
- CRAM inputs require the original reference FASTA for decoding.

## Do not use when
- You are starting from raw FASTQ — this sketch only reverses an alignment back to reads; there is no trimming, mapping, or variant calling here.
- You need to realign to a new reference — pair this sketch with a downstream alignment/variant-calling sketch instead.
- You want per-read-group splitting or 10x/linked-read-specific demultiplexing — use a tool like `bamtofastq` from 10x Genomics, not this generic samtools-based pipeline.
- You want to keep supplementary/secondary alignments — `--samtools_collate_fast` only emits primary alignments.

## Analysis outline
1. Validate the samplesheet (`sample_id,mapped,index,file_type`) and index any BAM/CRAM lacking a `.bai`/`.crai` with `samtools index`.
2. Run `FastQC` on the input BAM (pre-conversion QC; skipped for CRAM).
3. Compute `samtools flagstat`, `samtools idxstats`, and `samtools stats` on the input alignments.
4. Auto-detect single-end vs paired-end by inspecting flags with `samtools view`.
5. If `--chr` is given, subset reads with `samtools view` to the requested region(s); otherwise keep all reads and split mapped vs unmapped streams.
6. Sort reads by name with `samtools collate` (optionally `-f -r` fast mode when `--samtools_collate_fast` is set).
7. Extract FASTQ with `samtools fastq`, producing `*.merged.fastq.gz` (paired) or `*.other.fq.gz` (single-end/orphans).
8. Run `FastQC` on the extracted FASTQ (post-conversion QC).
9. Validate output FASTQ integrity with `fastq_utils fastq_info`.
10. Aggregate all QC into a `MultiQC` HTML report.

## Key parameters
- `input`: path to samplesheet CSV with columns `sample_id,mapped,index,file_type` (`file_type` ∈ `bam`, `cram`).
- `outdir`: output directory (absolute path on cloud storage).
- `fasta`: reference FASTA — **mandatory for CRAM input**, must match the `@SQ` lines in the CRAM header (check with `samtools view -H sample.cram | grep '@SQ'`).
- `fasta_fai`: optional pre-built `.fai` index; generated if absent.
- `chr`: region filter, e.g. `'chr1'`, `'chr{1..22}'`, `'X chrX'`. Must match the exact contig naming in the BAM/CRAM or the result will be silently empty.
- `no_read_QC`: skip FastQC on extracted FASTQ (use when the downstream pipeline does its own QC).
- `no_stats`: skip ALL QC (FastQC pre/post, flagstat, idxstats, stats) — useful for very large inputs but loses sanity checking.
- `samtools_collate_fast`: enable `samtools collate -f -r` fast mode; outputs primary alignments only.
- `reads_in_memory`: integer passed to fast-mode collate (default `100000`); raise (e.g. `1000000`) to speed up large files at the cost of memory.
- `genome` / `igenomes_ignore`: use iGenomes reference presets, or disable and supply `fasta` directly.

## Test data
The pipeline ships a minimal `-profile test` that points `input` at `bamtofastq/samplesheet/test_bam_samplesheet.csv` from `nf-core/test-datasets`, a small samplesheet of BAM files with their `.bai` indexes and no reference FASTA required. A full-size `-profile test_full` uses `test_full_samplesheet.csv` together with the GRCh38 `Homo_sapiens_assembly38.fasta` reference from iGenomes on S3. Expected outputs are gzipped FASTQ files under `reads/` (`*.merged.fastq.gz` for paired, `*.other.fq.gz` for single-end), per-sample FastQC HTML/zip in `fastqc/`, samtools stats files in `samtools/`, `fastq_utils` validation reports in `fastutils/`, and a consolidated `multiqc/multiqc_report.html`.

## Reference workflow
nf-core/bamtofastq v2.2.0 (https://github.com/nf-core/bamtofastq), MIT license. Steps follow the pipeline's standard FastQC → samtools collate/fastq → fastq_utils → MultiQC chain as documented in `docs/output.md` and `nextflow_schema.json`.
