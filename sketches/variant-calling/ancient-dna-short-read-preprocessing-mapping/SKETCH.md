---
name: ancient-dna-short-read-preprocessing-mapping
description: 'Use when you need to process ancient/degraded DNA short-read sequencing
  data: adapter trimming and read merging, mapping to a reference genome, PCR duplicate
  removal, and characteristic aDNA damage profiling (C>T at 5'' ends, G>A at 3'' ends).
  Handles UDG-treated, half-UDG, and non-UDG libraries, short fragments, and can optionally
  do damage-aware BAM trimming or rescaling before downstream genotyping.'
domain: variant-calling
organism_class:
- eukaryote
- ancient-dna
input_data:
- short-reads-paired
- short-reads-single
- bam
- reference-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/eager
  url: https://github.com/nf-core/eager
  version: 2.5.3
  license: MIT
  slug: eager
tools:
- name: fastqc
- name: adapterremoval
- name: fastp
- name: bwa-aln
- name: samtools
- name: picard-markduplicates
- name: dedup
- name: damageprofiler
- name: mapdamage2
- name: qualimap
- name: preseq
- name: bamutil
- name: pmdtools
- name: multiqc
tags:
- ancient-dna
- adna
- palaeogenomics
- damage
- bwa-aln
- udg
- deamination
- short-read
test_data: []
expected_output: []
---

# Ancient DNA short-read preprocessing, mapping and damage assessment

This sketch covers the core nf-core/eager recipe: take raw short-read sequencing data from an ancient or historical specimen, clean it, map it to a reference with parameters tuned for short damaged fragments, deduplicate, and quantify authenticity (damage patterns, fragment length, library complexity). The output BAMs and damage profiles are the standard input for downstream aDNA genotyping, consensus calling, sex determination, contamination estimation, or SNP-table building.

## When to use this sketch
- Input is short-read Illumina FASTQ (or pre-aligned BAM that needs re-preprocessing) from an ancient, historical, museum, or otherwise degraded sample (human, animal, plant, microbe).
- Reads are expected to be short (often 30–80 bp), collapsed from paired-end overlap, and to carry C>T deamination damage at fragment ends.
- You need a reproducible pipeline that does adapter/quality trimming + read merging, reference mapping with aDNA-friendly parameters, PCR duplicate removal that is aware of merged reads, and per-library damage profiles.
- Libraries may be a mix of non-UDG, half-UDG (Rohland-style) and full-UDG treatment; you want UDG-treatment-aware BAM trimming / rescaling before genotyping.
- You want a single MultiQC report summarising sequencing QC, endogenous DNA %, cluster factor / duplication, damage, coverage (Qualimap) and library complexity (Preseq).

## Do not use when
- You want metagenomic taxonomic screening of off-target reads (MALT/HOPS/Kraken2 on unmapped reads) — that is a sibling metagenomic-screening sketch, not this one. This sketch only covers the host-mapping side.
- You are doing ancient bacterial pathogen SNP phylogenetics with MultiVCFAnalyzer / GATK UnifiedGenotyper on a haploid reference — use a dedicated ancient-pathogen-snp-phylogenetics sketch built around the same pipeline.
- You are doing ancient human population genetics with pileupCaller / eigenstrat random-draw genotypes at a 1240K-like SNP panel — use a dedicated ancient-human-popgen-pileupcaller sketch.
- Your data is modern, high-quality, high-coverage short-read data with no damage — use a standard germline-variant-calling or WGS-preprocessing sketch instead; aDNA-tuned mismatch thresholds and merged-read deduplication are wasted there.
- Your data is long-read (ONT / PacBio) — aDNA long-read workflows need a different recipe.

## Analysis outline
1. Raw-read QC per FASTQ (`FastQC`).
2. Optional poly-G tail trimming for 2-colour chemistry (NextSeq/NovaSeq) reads (`fastp --poly_g_min_len`).
3. Adapter trimming, paired-end collapsing/merging into single reads, quality trimming and minimum-length filtering (`AdapterRemoval` with `--minlength 30`, `--minquality 20`; optionally `--preserve5p` and `--mergedonly` when using DeDup downstream).
4. Post-trimming QC (`FastQC` on merged reads).
5. Optional post-AdapterRemoval internal-barcode/damage trimming (`fastp --trim_front/--trim_tail`).
6. Reference indexing if needed (`bwa index`, `samtools faidx`, `picard CreateSequenceDictionary`) or reuse precomputed indices.
7. Mapping to reference with aDNA-friendly parameters (`bwa aln` with relaxed `-n` and disabled seeding `-l 1024`; alternatives: `bwa mem`, `CircularMapper` for circular contigs like mtDNA, `Bowtie2`).
8. BAM post-processing: sort, flagstat, optional mapping-quality and read-length filtering, optional retention/extraction of unmapped reads as BAM or FASTQ (`samtools view`, `filter_bam_fragment_length.py`).
9. Endogenous DNA % calculation from pre/post-filter flagstat (`endorS.py`).
10. PCR duplicate removal per library — `DeDup` for fully-merged paired-end data (uses both ends), or `Picard MarkDuplicates` for single-end / mixed SE+PE data.
11. Library complexity estimation (`preseq c_curve`, optionally `lc_extrap`).
12. Mapping/coverage QC per sample (`Qualimap bamqc`, with optional SNP-capture BED for on-target stats).
13. aDNA damage profiling per library (`DamageProfiler` default, or `mapDamage2` with optional `--downsample` for speed or `--rescale` to probabilistically remove damage).
14. Optional PMD-based authentication / filtering (`PMDtools` with `--threshold`, `--UDGhalf`/`--CpG` depending on UDG treatment).
15. Optional UDG-treatment-aware BAM trimming of damaged ends before genotyping (`bamUtil trimBam`, applied only to non-UDG and half-UDG libraries).
16. Library merging: same-library lanes after adapter removal → same-treatment libraries per sample after deduplication → final per-sample BAM for downstream analysis.
17. Aggregated run report (`MultiQC`) with general stats (endogenous %, cluster factor, mean read length, 5' C>T, median coverage, etc.).

## Key parameters
- `--input`: either a glob (`'*_{R1,R2}*.fastq.gz'`) or a TSV with columns `Sample_Name, Library_ID, Lane, Colour_Chemistry, SeqType, Organism, Strandedness, UDG_Treatment, R1, R2, BAM` — TSV is required for lane/library merging and mixed UDG treatments.
- `--fasta` (+ optional `--bwa_index`, `--fasta_index`, `--seq_dict`, `--large_ref` for >3.5 Gb references).
- `--udg_type`: `none` | `half` | `full` — controls PMDtools model and which libraries get BAM-trimmed.
- `--single_stranded`: toggles single-stranded-specific handling in MaltExtract, pileupCaller, and mapDamage rescaling.
- `--colour_chemistry` (2 or 4) and `--complexity_filter_poly_g` (+ `--complexity_filter_poly_g_min`, default 10) for NextSeq/NovaSeq poly-G trimming.
- AdapterRemoval: `--clip_readlength` (default 30), `--clip_min_read_quality` (default 20), `--min_adap_overlap`, `--mergedonly`, `--preserve5p`.
- Mapper: `--mapper bwaaln` (default) with `--bwaalnn 0.01–0.04` (relaxed mismatches for aDNA; Schubert 2012 recommends 0.01 for older samples), `--bwaalnl 1024` (disable seeding), `--bwaalnk 2`, `--bwaalno 2`. CircularMapper uses `--circularextension 500` and `--circulartarget MT`. Bowtie2 uses `--bt2_alignmode local` / `--bt2_sensitivity sensitive`.
- BAM filtering: `--run_bam_filtering`, `--bam_mapping_quality_threshold` (e.g. 0, 25, or 37), `--bam_filter_minreadlength`, `--bam_unmapped_type discard|bam|fastq|both`.
- Deduplication: `--dedupper markduplicates` (default; safe for SE/mixed) or `dedup` (PE-merged only; requires `--mergedonly --preserve5p`).
- Damage: `--damage_calculation_tool damageprofiler|mapdamage`; `--damageprofiler_length 100`, `--damageprofiler_threshold 15`; `--mapdamage_downsample` for speed; `--run_mapdamage_rescaling` with `--rescale_length_5p/3p` for bayesian damage removal.
- PMDtools: `--run_pmdtools`, `--pmdtools_range 10`, `--pmdtools_threshold 3`, optional `--pmdtools_reference_mask` BED.
- BAM trimming: `--run_trim_bam` with `--bamutils_clip_double_stranded_{half,none}_udg_{left,right}` (typical half-UDG: 2 bp each side; typical non-UDG: 3–7 bp each side) — applied only to non-UDG / half-UDG libraries.
- Preseq: `--preseq_mode c_curve` (default) or `lc_extrap`.
- Skip flags: `--skip_fastqc`, `--skip_adapterremoval`, `--skip_preseq`, `--skip_deduplication`, `--skip_damage_calculation`, `--skip_qualimap`.

## Test data
The pipeline's bundled `test` profile uses two public mammoth test samples (`JK2782`, `JK2802`) from Fellows Yates et al. 2017 — paired-end and single-end Illumina FASTQs downsampled to ~10k reads per file (`*.tengrand.fq.gz`) from the nf-core test-datasets Mammoth folder — mapped against a small mammoth mitochondrial reference FASTA (`Mammoth_MT_Krause.fasta`). A typical run is driven by `mammoth_design_fastq.tsv`, which exercises lane merging, mixed SE/PE input, and double-stranded full-UDG libraries. Running the workflow end-to-end is expected to produce, per sample/library, adapter-trimmed merged FASTQs, sorted and deduplicated BAMs aligned to the mammoth mtDNA, DamageProfiler plots showing the characteristic 5' C>T / 3' G>A ancient DNA damage pattern, Qualimap coverage reports over the mitochondrial reference, Preseq complexity curves, and an aggregated MultiQC HTML report at `results/MultiQC/multiqc_report.html` with endogenous DNA %, cluster factor, and damage metrics in its general-stats table. The larger `test_full` profile instead exercises the same recipe on Viking-age Atlantic cod (*Gadus morhua*) shotgun data mapped to the `gadMor3.0` reference with `--bwaalnn 0.04 --bwaalnl 1024`, mapping-quality filter 25, and GATK HaplotypeCaller diploid genotyping turned on downstream.

## Reference workflow
nf-core/eager v2.5.3 (https://github.com/nf-core/eager), the community ancient-DNA NGS pipeline described in Fellows Yates et al. 2021, *PeerJ* 9:e10947 (doi:10.7717/peerj.10947). Requires Nextflow ≤ 22.10.6. Default profile test data and parameter schema are from that release's `conf/test.config`, `conf/test_full.config`, and `nextflow_schema.json`.
