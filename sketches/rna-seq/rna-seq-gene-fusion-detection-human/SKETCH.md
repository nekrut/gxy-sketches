---
name: rna-seq-gene-fusion-detection-human
description: 'Use when you need to detect and visualize gene fusions from human tumor
  bulk RNA-seq (Illumina paired-end, GRCh38) by running multiple fusion callers and
  aggregating them. Typical use: cancer samples screened for oncogenic fusions like
  BCR-ABL1, EML4-ALK, TMPRSS2-ERG, plus cancer splicing aberrations.'
domain: rna-seq
organism_class:
- vertebrate
- diploid
- human
input_data:
- short-reads-paired
- reference-fasta
- gtf-annotation
source:
  ecosystem: nf-core
  workflow: nf-core/rnafusion
  url: https://github.com/nf-core/rnafusion
  version: 4.1.0
  license: MIT
  slug: rnafusion
tools:
- name: star
- name: arriba
- name: star-fusion
- name: fusioncatcher
  version: 1.33b
- name: fusioninspector
- name: fusion-report
- name: ctat-splicing
- name: stringtie
  version: 2.2.3
- name: fastp
- name: fastqc
  version: 0.12.1
- name: picard
- name: salmon
- name: samtools
- name: multiqc
  version: '1.30'
tags:
- rna-seq
- gene-fusion
- cancer
- transcriptomics
- grch38
- chimeric-transcripts
- fusion-calling
- tumor
test_data: []
expected_output: []
---

# Human RNA-seq gene fusion detection

## When to use this sketch
- Human tumor or cell-line bulk RNA-seq (Illumina paired-end FASTQ) where the biological question is "what gene fusions are present?"
- You want consensus calls from multiple orthogonal fusion callers (Arriba + STAR-Fusion + FusionCatcher) rather than trusting a single tool.
- You need publication- or clinical-review-ready artifacts: per-sample fusion TSVs, an aggregated HTML index, a PDF visualization of each fusion, and a VCF-formatted fusion collection.
- GRCh38 reference; gencode-based annotation. GRCh38 is the only supported build.
- You also want cancer splicing aberrations (CTAT-SPLICING) and/or transcript assembly (StringTie) alongside fusion calls.
- Read length is roughly 75-150 bp; for reads >100 bp you plan to tail-trim before FusionCatcher.

## Do not use when
- The organism is not human or the assembly is not GRCh38 — this pipeline hardcodes GRCh38 + gencode references.
- You need differential expression, splicing quantification, or standard transcript quantification as the primary output — use a generic bulk RNA-seq quantification sketch instead.
- You need variant calling (SNV/indel) from RNA-seq — use an RNA variant-calling sketch.
- You have single-cell RNA-seq — use a 10x / scRNA sketch.
- You have only single-end reads shorter than 130 bp — FusionCatcher will not run; fall back to an Arriba- or STAR-Fusion-only configuration.
- You need de novo fusion discovery in a non-model organism without curated fusion references — the required Arriba/FusionCatcher/CTAT resource bundles do not exist.

## Analysis outline
1. Validate samplesheet (`sample,fastq_1,fastq_2,strandedness`) and, if references are absent, run the `--references_only` workflow to download/build gencode FASTA+GTF, STAR index, STAR-Fusion CTAT lib, FusionCatcher DB, Arriba resource bundle, HGNC, Salmon index, and fusion-report DBs (COSMIC/Mitelman/FusionGDB2).
2. Raw-read QC with FastQC; optional quality/adapter trimming with fastp (enable via `--tools fastp`). An extra fastp pass with `--trim_tail_fusioncatcher` tail-trims reads for FusionCatcher only.
3. Align reads to GRCh38 with STAR using chimeric-read settings (`--chimSegmentMin 10`, `--chimOutType Junctions WithinBAM`, `--outSAMstrandField intronMotif`) to produce a sorted BAM + `Chimeric.out.junction` + `SJ.out.tab`.
4. Run fusion callers in parallel on the STAR outputs / FASTQ: Arriba (from BAM), STAR-Fusion (from chimeric junctions), FusionCatcher (from tail-trimmed FASTQ).
5. Run CTAT-SPLICING on the STAR alignment to flag cancer-associated aberrant splicing introns; run StringTie for transcript assembly.
6. Aggregate per-caller fusion tables with fusion-report, scoring each fusion by a Fusion Indication Index that combines tool agreement (50%) and curated DB hits (COSMIC + Mitelman weighted 50 each; FusionGDB2 weight 0).
7. Re-score and validate the union of predicted fusions with FusionInspector, then render an Arriba PDF visualization of the FusionInspector-confirmed fusions and a per-sample VCF via vcf_collect.
8. Collect QC metrics with Picard (CollectRnaSeqMetrics, CollectInsertSizeMetrics, MarkDuplicates), optionally quantify with Salmon, compress BAM→CRAM via samtools if `--cram`, and summarize everything in MultiQC.

## Key parameters
- `--input <samplesheet.csv>`: required; `sample`, `strandedness` mandatory columns plus one of `fastq_1`/`bam`/`cram`/`junctions`.
- `--genomes_base <path>`: path to the pre-downloaded reference bundle (recommended: `aws s3 sync s3://nf-core-awsmegatests/rnafusion/references/`). Building from scratch takes ~24 h on HPC.
- `--tools <list>`: comma-separated subset of `arriba,ctatsplicing,fusioncatcher,starfusion,stringtie,fusionreport,fastp,salmon,fusioninspector` or `all`. Required — no callers run without it.
- `--references_only`: run only the reference-building sub-workflow; combine with `--tools all` for a full reference bundle.
- `--cosmic_username` / `--cosmic_passwd` (+ optional `--qiagen`): needed to build fusion-report DB with COSMIC. Use `--no_cosmic` if not licensed.
- `--read_length` (default 100): sets STAR `--sjdbOverhang = read_length - 1`.
- `--trim_tail_fusioncatcher <int>`: extra 3' tail trim (in bp) feeding FusionCatcher; critical when reads are >100 bp (FusionCatcher expects ~100 bp).
- `--fusioncatcher_limitSjdbInsertNsj` (default 2,000,000) and `--fusioninspector_limitSjdbInsertNsj` (default 1,000,000): raise if STAR runs inside these tools fail on splice-junction overflow.
- `--tools_cutoff <int>` (default 1): discard fusions detected by fewer than N callers before fusion-report display and FusionInspector input.
- `--whitelist <file>`: TSV of `GENE1--GENE2` pairs forced into FusionInspector in addition to detected calls.
- `--cram`: emit CRAM instead of BAM in the `star/` output.
- `--skip_qc` / `--skip_vis` / `--skip_vcf`: skip Picard metrics, Arriba/fusion-report/FusionInspector visualization, and vcf_collect respectively.
- Profile: must be `docker`, `singularity`, or an institutional profile — conda is unsupported (CTAT-SPLICING has no conda recipe).

## Test data
The pipeline ships a `-profile test` configuration that points at `tests/csv/fastq.csv` plus Arriba reference stubs hosted on the nf-core test-datasets repo (`protein_domains_hg38_GRCh38_v2.5.0.gff3`, `known_fusions_hg38_GRCh38_v2.5.0.tsv.gz`, `blacklist_hg38_GRCh38_v2.5.0.tsv.gz`, `cytobands_hg38_GRCh38_v2.5.0.tsv`) and a placeholder FusionCatcher reference under `assets/`. Because the real fusion references are many GB and take ~24 h to build, the test profile MUST be run with `-stub` — it exercises the workflow DAG and channel wiring against dummy files rather than producing real fusion calls. The full-size AWS megatest (`test_full`) uses `samplesheet_valid.csv` from `nf-core/test-datasets` branch `rnafusion/testdata/human` and is the only configuration that produces biologically meaningful outputs: per-sample `arriba/<sample>.arriba.fusions.tsv`, `starfusion/<sample>.starfusion.fusion_predictions.tsv`, `fusioncatcher/<sample>.fusion-genes.txt`, an aggregated `fusionreport/<sample>/<sample>_fusionreport_index.html`, a FusionInspector `.fusion_inspector_web.html`, an Arriba PDF visualization, a `vcf/<sample>_fusion_data.vcf`, and a top-level `multiqc/multiqc_report.html`.

## Reference workflow
nf-core/rnafusion v4.1.0 (https://github.com/nf-core/rnafusion), MIT-licensed, Nextflow ≥24.10.5. Requires Docker or Singularity; conda is explicitly unsupported. Reference-building uses gencode (fusioncatcher is pinned to gencode 46 / ensembl 102).
