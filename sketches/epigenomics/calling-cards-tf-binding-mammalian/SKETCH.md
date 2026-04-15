---
name: calling-cards-tf-binding-mammalian
description: Use when you need to process bulk Calling Cards sequencing data from
  mammalian samples (human or mouse) to map transcription factor binding sites via
  transposon insertion ('hop') counts. Handles single-TF libraries with UMI/barcode
  extraction, alignment to a reference genome, and qBed hop quantification. For yeast
  multiplexed Calling Cards libraries, see the sibling sketch.
domain: epigenomics
organism_class:
- mammalian
- vertebrate
- diploid
input_data:
- short-reads-single
- reference-fasta
- gtf-annotation
- barcode-details-json
source:
  ecosystem: nf-core
  workflow: nf-core/callingcards
  url: https://github.com/nf-core/callingcards
  version: 1.0.0
  license: MIT
  slug: callingcards
tools:
- name: callingCardsTools
- name: umi-tools
- name: seqkit
- name: trimmomatic
  version: '0.39'
- name: bwa-mem2
- name: bwa
- name: bowtie2
- name: bowtie
- name: samtools
- name: picard
- name: rseqc
- name: fastqc
  version: 0.12.1
- name: bedtools
- name: multiqc
  version: '1.21'
tags:
- calling-cards
- transcription-factor
- tf-binding
- transposon
- hops
- qbed
- mammalian
- mouse
- human
test_data: []
expected_output: []
---

# Mammalian bulk Calling Cards TF-binding mapping

## When to use this sketch
- You have Illumina short-read FASTQs from a mammalian (human or mouse) Calling Cards experiment where a piggyBac/SRT transposon is used to mark transcription factor (TF) binding sites.
- Each sequencing library represents a single TF (not multiplexed); reads are typically single-end R1 and carry a non-genomic barcode/UMI at the 5' end.
- You want per-sample transposition ('hop') quantification in qBed format plus alignment/library QC.
- You can supply either an iGenomes key (e.g. `GRCh38`, `GRCm38`) or an explicit `--fasta` + `--gtf`, and a `barcode_details.json` describing the expected barcode/SRT pattern.

## Do not use when
- Your Calling Cards library is a multiplexed yeast experiment where a single FASTQ encodes many TFs via R1/R2 barcodes — use the sibling `calling-cards-tf-binding-yeast` sketch instead (different demultiplexing logic via `callingCardsTools parse fastq`, paired-end reads required, no UMItools extract step).
- You are doing ChIP-seq, CUT&RUN, CUT&Tag, or ATAC-seq TF profiling — those are not Calling Cards and belong in dedicated peak-calling sketches.
- You only need variant calling, RNA quantification, or generic alignment — this pipeline is specialized for hop counting and will not produce those outputs.
- Your reads are long-read (ONT/PacBio) — this pipeline targets Illumina short reads only.

## Analysis outline
1. Prepare genome — optionally hard-mask regions with `bedtools maskfasta`, optionally append extra sequences, build the chosen aligner index, and index the FASTA with `samtools faidx`.
2. Raw-read QC — `FastQC` on the input FASTQs.
3. Split FASTQs for parallelism — `seqkit split2` by part count or by size.
4. Extract non-genomic barcode/UMI — `umi_tools extract` using `--r1_bc_pattern` (e.g. a 38 nt `N` pattern); barcode is appended to the read ID.
5. Crop and trim — optional `r1_crop` to keep only the genomic portion, then `Trimmomatic` for adapter/quality trimming.
6. Align to reference — one of `bwa-mem2` (default), `bwa aln`, `bowtie2`, or `bowtie`; sort and index with `samtools`.
7. Count hops — `callingCardsTools` partitions alignments into passing/failing by `min_mapq` and barcode concordance, emits `*_passing.bam`, `*_failing.bam`, a `.qbed` of per-coordinate hop counts, and `*_summary.tsv` / `*_barcode_qc.tsv` / `*_srt_count.tsv` tallies.
8. Alignment QC — `Picard CollectMultipleMetrics`, `samtools stats/flagstat/idxstats`, and `RSeQC` (`read_distribution` by default, with optional `bam_stat`, `infer_experiment`, etc.).
9. Aggregate QC — `MultiQC` report over the whole run.

## Key parameters
- `datatype: mammals` — selects the mammalian sub-workflow (required; alternative is `yeast`).
- `input` — CSV samplesheet with columns `sample,fastq_1,fastq_2,barcode_details`; leave `fastq_2` blank for mammals (R1 only).
- `genome` (iGenomes key, e.g. `GRCm38`, `GRCh38`) OR `fasta` + `gtf` — reference must be provided explicitly for mammals.
- `aligner: bwamem2` (default) — or `bwa`, `bowtie2`, `bowtie`.
- `r1_bc_pattern` — UMItools-style N-pattern describing the length/layout of the non-genomic 5' barcode (e.g. `NNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN` for a 38 nt barcode). Set in `default_mammals` profile; verify it matches your library design.
- `r1_crop` — integer length to which R1 is cropped after barcode extraction and trimming (e.g. `40`), controlling the genomic portion passed to the aligner.
- `min_mapq: 10` — alignments with MAPQ ≤ this are excluded from hop counts.
- `split_fastq_by_part: 10` (default) or `split_fastq_by_size` — controls parallel chunking; set exactly one, nullify the other.
- `regions_mask` (optional BED) and `additional_fasta` (optional FASTA) — for masking and adding spike-in/custom contigs before indexing.
- `rseqc_modules: read_distribution` — default RSeQC set; extend if you want `bam_stat`, `infer_experiment`, etc.
- Recommended profile: `-profile default_mammals,<docker|singularity>`.

## Test data
The mammalian test profiles (`test_mammals`, `test_full`) pull a samplesheet from the `cmatKhan/test-datasets` `callingcards/mammals` branch containing single-end FASTQs from downsampled mouse Calling Cards runs (e.g. `AY60-6` and `AY09-1` libraries at 50k/100k read depths, including a deliberately low-quality variant) together with a shared `barcode_details.json`. They target the iGenomes `GRCm38` reference, use `aligner: bwa` (full) or `bwamem2`, a 38 nt `r1_bc_pattern`, `r1_crop: 40`, and `min_mapq: 10`. A successful run produces, per sample, coordinate-sorted BAMs, `hops/*_passing.bam` + `.qbed` hop tracks, `*_summary.tsv` / `*_barcode_qc.tsv` / `*_srt_count.tsv` tallies, Picard/RSeQC/samtools QC, and a combined `multiqc/multiqc_report.html`.

## Reference workflow
nf-core/callingcards v1.0.0 (DSL2, Nextflow ≥23.04.0). Primary entry point invoked as `nextflow run nf-core/callingcards -profile default_mammals,<container> --input samplesheet.csv --genome GRCm38 --outdir results` (or with explicit `--fasta`/`--gtf`). Core hop-counting logic is delegated to `callingCardsTools` (https://github.com/cmatKhan/callingCardsTools).
