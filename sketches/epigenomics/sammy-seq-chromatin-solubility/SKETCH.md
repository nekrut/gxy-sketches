---
name: sammy-seq-chromatin-solubility
description: Use when analyzing SAMMY-seq data (Sequential Analysis of MacroMolecules
  accessibilitY sequencing) to profile chromatin solubility/accessibility fractions
  (S2/S2S/S2L/S3/S4) from Illumina short reads, generate per-fraction bigWig tracks,
  compute pairwise fraction comparisons, and optionally call differentially soluble
  regions between sample groups.
domain: epigenomics
organism_class:
- eukaryote
- vertebrate
input_data:
- short-reads-single-or-paired
- reference-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/sammyseq
  url: https://github.com/nf-core/sammyseq
  version: dev
  license: MIT
  slug: sammyseq
tools:
- name: fastqc
  version: 0.12.1
- name: trim-galore
- name: trimmomatic
  version: '0.39'
- name: bwa
- name: bowtie2
- name: samtools
- name: picard
- name: deeptools
- name: spp
- name: multiqc
tags:
- sammy-seq
- chromatin
- accessibility
- solubility
- bigwig
- fractionation
- heterochromatin
test_data: []
expected_output: []
---

# SAMMY-seq chromatin solubility profiling

## When to use this sketch
- Input is SAMMY-seq data: Illumina short reads (single- or paired-end) from biochemically fractionated chromatin, where each library corresponds to a solubility fraction (S2, S2S, S2L, S3, S4) from a given biological specimen.
- Goal is to produce normalized per-fraction coverage bigWig tracks and QC (PCA, correlation heatmap, optional fingerprint, optional TSS meta-profile) across fractions and replicates.
- Need pairwise fraction comparison tracks (e.g. S2SvsS3, S4vsS3) within the same `experimentalID`, either via the SPP Gaussian-smoothed difference method (single-end) or deepTools `bigwigCompare` log2 ratio (required for paired-end).
- Want differential solubility analysis: binning the genome, quantile-normalizing, thresholding, and computing Cohen's d between `sample_group`s to find regions whose solubility pattern differs between conditions (e.g. disease vs control), optionally annotating overlapping protein-coding gene promoters via a GTF.
- Studying chromatin compartmentalization, heterochromatin alteration, or bivalent gene deregulation in mammalian/eukaryotic systems (e.g. the progeria / HGPS and cancer contexts the method was published in).

## Do not use when
- You have ChIP-seq for a specific factor/histone mark — use a ChIP-seq sketch (e.g. nf-core/chipseq), not SAMMY-seq.
- You have ATAC-seq or DNase-seq accessibility data — use an accessibility sketch (nf-core/atacseq). SAMMY-seq measures solubility fractionation, not transposase/DNase cleavage.
- You need cut&run / cut&tag analysis — use nf-core/cutandrun.
- You are calling SNVs/indels, doing RNA-seq, Hi-C, or bisulfite methylation — pick the matching domain sketch.
- Your samplesheet has no `fraction` / `experimentalID` structure; this pipeline is built around SAMMY fraction semantics and comparisons only make sense across fractions of the same specimen.

## Analysis outline
1. Parse samplesheet (`sample,fastq_1,fastq_2,experimentalID,fraction,sample_group`); concatenate multi-lane FASTQs for the same `sample`; optionally concatenate all fractions of an `experimentalID` with `--combine_fractions`.
2. Raw read QC with **FastQC**.
3. Adapter/quality trimming with **Trim Galore!** (default) or **Trimmomatic** (`--trimmer`).
4. Post-trim FastQC.
5. Prepare reference: index FASTA (`samtools faidx`), build aligner index (BWA or Bowtie2) unless `--bwa_index` / `--bowtie2_index` / `--fai` / `--chrom_sizes` supplied; optionally `--save_reference`.
6. Align to reference with **BWA-MEM** (default), **BWA-ALN**, or **Bowtie2** (`--aligner`), sort with **samtools**.
7. Mark duplicates with **Picard MarkDuplicates** (not removed).
8. Filter reads with **samtools view** using `--flag` (default 1540) and `--q_score` (default 1), optionally restricted to `--keep_regions_bed`; emit filtered BAM + `flagstat`/`idxstats`/`stats`.
9. Per-fraction signal tracks with **deepTools bamCoverage** → bigWig, using `--normalizeUsing` (RPKM default; CPM/BPM/RPGC), `--binsize`/`--bw_resolution`, `--effectiveGenomeSize`, `--ignoreForNormalization`, `--blacklist`, `--extendReads`/`--fragment_size` for SE.
10. Cross-sample QC with **deepTools**: `multiBigwigSummary` → `plotPCA` and `plotCorrelation` (`--corr_method` spearman/pearson); optional `plotFingerprint` global and region-specific; optional `computeMatrix reference-point` + `plotProfile` around TSS when `--tss_bed` is supplied.
11. Pairwise fraction comparisons within each `experimentalID` via `--comparison` (e.g. `S2SvsS3,S2LvsS3,S4vsS3`) or free-form `--comparison_file`; engine selected by `--comparison_maker`: **SPP** MLE Gaussian-smoothed difference (default, single-end only) or **deepTools bigwigCompare** log2 ratio (required for paired-end).
12. Optional differential solubility: enable `--differential_solubility`, set `--compare_groups` (e.g. `HGPSvsCTRL`) and at least one `--comparison`; bin the genome inside `--keep_regions_bed` at `--binsize` (default 50000), quantile-normalize, drop bins below `--solubility_threshold` (default 0.1), compute Cohen's d, emit selected bins / BED regions / R rds / summary; if `--gtf` provided, intersect significant bins with protein-coding promoters (−2500/+500 of TSS) and emit overlapping gene lists.
13. Aggregate everything with **MultiQC** (skippable via `--skip_multiqc`).

## Key parameters
- `--input` samplesheet CSV with columns `sample,fastq_1,fastq_2,experimentalID,fraction,sample_group` (required).
- `--fasta` reference genome FASTA (required unless `--genome`/`--bwa_index`/`--bowtie2_index` fully supplied); `--fai`, `--chrom_sizes`, `--save_reference` optional.
- `--aligner` `bwamem` (default) | `bwaaln` | `bowtie2`; `--trimmer` `trimgalore` (default) | `trimmomatic`.
- `--q_score` MAPQ filter (default 1); `--flag` samtools flag filter (default 1540); `--keep_regions_bed`, `--blacklist` for region restriction.
- `--binsize` (multiBamSummary / differential solubility bin size, default 50000); `--bw_resolution` bamCoverage/bigWig bin size (default 1); `--normalizeUsing` `RPKM` (default) | `CPM` | `BPM` | `RPGC`; `--effectiveGenomeSize`, `--ignoreForNormalization`, `--extendReads`, `--fragment_size` (SE only, default 100).
- `--corr_method` `spearman` (default) | `pearson`; `--plotfingerprint`, `--region`, `--numberOfSamples` (500000 default); `--tss_bed` to enable TSS profile plots.
- `--comparison` restricted to `{S2SvsS3,S2LvsS3,S2SvsS4,S2LvsS4,S2vsS3,S2vsS4,S4vsS3}` (comma-separated); or `--comparison_file` for arbitrary sample-pair CSV; `--comparison_maker` `spp` (default, single-end) | `bigwigcompare` (paired-end).
- `--bigwigcompare_operation` (default `log2`), `--bigwigcompare_pseudocount` (1e-14), `--bigwigcompare_skip_non_covered_regions` (true), `--bigwigcompare_fixed_step`.
- `--differential_solubility` (boolean), `--compare_groups` `GroupBvsGroupA[,…]` matching `sample_group`, `--solubility_threshold` (default 0.1), `--gtf` for gene-level annotation.
- `--combine_fractions` to concatenate fractions per `experimentalID`; `--skip_multiqc`; `--stopAt` to stop after a given stage for debugging.

## Test data
The pipeline's built-in `test` profile points at a tiny SAMMY-seq dataset hosted on the ISASI-CNR mirror: a human chr22-only reference FASTA (`chr22.fa`) and a samplesheet (`samplesheet_test_github_chr22_tinier.csv`) of down-sampled SAMMY-seq fraction libraries confined to chr22, suitable for CPU-/memory-limited CI runs (4 CPUs, 2 GB, 1 h). Running `-profile test,docker --outdir results` is expected to complete end-to-end and produce per-sample filtered BAMs, per-fraction normalized bigWig tracks under `single_tracks/deeptools/`, deepTools PCA and correlation QC, and a final `multiqc/multiqc_report.html`; no comparison or differential-solubility outputs are produced unless `--comparison` / `--differential_solubility` are added on top of the test profile.

## Reference workflow
nf-core/sammyseq (dev, nf-core template 3.4.1) — https://github.com/nf-core/sammyseq. Method references: Lucini et al., *Nucleic Acids Research* 2024 (doi:10.1093/nar/gkae454) and Sebestyén et al., *Nature Communications* 2020 (doi:10.1038/s41467-020-20048-9). Differential solubility follows Wang et al., 2024 (doi:10.1038/s41594-025-01622-5).
