---
name: amplicon-16s-asv-illumina-paired
description: Use when you need to profile bacterial/archaeal communities from paired-end
  Illumina 16S rRNA amplicon sequencing (e.g. V3-V4 or V4 region) by inferring exact
  amplicon sequence variants (ASVs), assigning taxonomy against SILVA/GTDB/Greengenes2,
  and running standard QIIME2 downstream analysis (alpha/beta diversity, barplots,
  optional differential abundance). Assumes one sequencing run (or runs tracked via
  a run column) and known PCR primer sequences.
domain: amplicon
organism_class:
- bacterial
- archaeal
- microbial-community
input_data:
- short-reads-paired
- primer-sequences
- sample-metadata-tsv
source:
  ecosystem: nf-core
  workflow: nf-core/ampliseq
  url: https://github.com/nf-core/ampliseq
  version: 2.16.1
  license: MIT
  slug: ampliseq
tools:
- name: fastqc
  version: 0.12.1
- name: cutadapt
  version: '5.2'
- name: dada2
- name: vsearch
- name: barrnap
- name: qiime2
- name: multiqc
tags:
- 16S
- amplicon
- ASV
- microbiome
- DADA2
- QIIME2
- SILVA
- illumina
- diversity
test_data: []
expected_output: []
---

# 16S rRNA amplicon ASV profiling (paired-end Illumina)

## When to use this sketch
- Paired-end Illumina (MiSeq/NovaSeq) amplicon reads targeting a 16S rRNA variable region (V3-V4, V4, etc.) of bacteria/archaea.
- You know the forward and reverse PCR primer sequences (biological primers, not adapters) and want them trimmed before denoising.
- You want exact ASVs from DADA2 (not OTUs), taxonomic assignment against SILVA (default) or an alternative 16S database (GTDB, SBDI-GTDB, Greengenes2, RDP), and standard community analysis (barplots, alpha/beta diversity, optional ANCOM/ANCOM-BC) through QIIME2.
- Single sequencing run, or multiple runs where each sample's origin run is recorded so DADA2 can learn per-run error profiles.
- Optional metadata TSV (QIIME2 format) is available to drive grouped analyses.

## Do not use when
- The amplicon is ITS or any region with strongly variable length — use an ITS-focused sketch that sets `--illumina_pe_its`, skips fixed-length truncation, and uses UNITE for taxonomy.
- The amplicon is 18S (protists), COI (metazoans/eDNA), or NifH — use a eukaryotic-marker sketch that selects PR2, MIDORI2/COIDB, or the Zehr NifH database respectively.
- Input is long-read PacBio/IonTorrent amplicon data — a long-read amplicon sketch should set `--pacbio` or `--iontorrent` and adjust truncation/merging.
- You already have ASV/OTU sequences and only want taxonomy — use a "taxonomy-only amplicon classification" sketch that takes `--input_fasta`.
- You are scaffolding multiple primer regions along one reference (SMURF/Sidle multi-region analysis) — use a dedicated Sidle multi-region sketch driven by `--multiregion` and `--sidle_ref_taxonomy`.
- You are doing shotgun metagenomics or whole-genome sequencing — this pipeline is amplicon-only.

## Analysis outline
1. Read QC on raw FASTQs (FastQC).
2. Trim the supplied forward/reverse PCR primers from reads (Cutadapt); drop read pairs without primers unless `--retain_untrimmed` is set.
3. Quality-filter and truncate reads, then infer ASVs per sequencing run with DADA2 (error model, denoise, merge pairs, remove chimeras) producing `ASV_seqs.fasta` and `ASV_table.tsv`.
4. Optional ASV post-processing: VSEARCH clustering, Barrnap SSU filtering, length filter, codon filter.
5. Taxonomic classification of ASVs with DADA2 `assignTaxonomy` + `addSpecies` against SILVA by default (alternatives: GTDB, Greengenes2, RDP via `--dada_ref_taxonomy`, or QIIME2/Kraken2/SINTAX classifiers).
6. Import into QIIME2; exclude unwanted taxa (mitochondria, chloroplast by default), apply min frequency/sample filters, build phylogenetic tree of ASVs.
7. Downstream QIIME2 analyses: absolute/relative abundance tables, interactive barplots, alpha-rarefaction curves, alpha/beta diversity indices (Shannon, Faith PD, Jaccard, Bray-Curtis, UniFrac), PCoA, optional ADONIS.
8. Optional differential abundance with ANCOM and/or ANCOM-BC against chosen metadata columns/formulas.
9. Export phyloseq and TreeSummarizedExperiment R objects; aggregate QC with MultiQC and render an R Markdown summary report.

## Key parameters
- `--input`: samplesheet TSV/CSV/YAML with `sampleID`, `forwardReads`, `reverseReads`, optional `run` column (alternative: `--input_folder` with `--extension`).
- `--FW_primer` / `--RV_primer`: biological PCR primer sequences, e.g. `GTGYCAGCMGCCGCGGTAA` / `GGACTACNVGGGTWTCTAAT` for 515f/806r V4.
- `--metadata`: QIIME2-format metadata TSV (first column `ID`); required for diversity/differential analyses.
- `--trunclenf` / `--trunclenr`: DADA2 truncation lengths. If unset, derived automatically from `--trunc_qmin` (default median Q 25) subject to `--trunc_rmin` (default retain 75% of reads).
- `--max_ee` (default 2), `--truncq` (default 2), `--min_len` (default 50): DADA2 filterAndTrim quality knobs.
- `--sample_inference`: `independent` (default), `pooled`, or `pseudo`.
- `--dada_ref_taxonomy`: taxonomy database, default `silva=138.2`; common alternatives `gtdb`, `sbdi-gtdb`, `greengenes2`, `rdp`. Use `--cut_dada_ref_taxonomy` to trim the reference to the amplicon via primers.
- `--exclude_taxa` (default `mitochondria,chloroplast`), `--min_frequency`, `--min_samples` for QIIME2 ASV filtering.
- `--diversity_rarefaction_depth` (default 500), `--tax_agglom_min`/`--tax_agglom_max` (default 2-6) for downstream analyses.
- `--ancom` / `--ancombc` / `--ancombc_formula` to turn on differential abundance; `--qiime_adonis_formula` for PERMANOVA-style ADONIS.
- `--multiple_sequencing_runs` (only with `--input_folder`) to keep per-run error models when the samplesheet `run` column is not used.
- `--illumina_novaseq` if quality scores are binned (NovaSeq), which enforces monotone error model correction.

## Test data
The pipeline's `test` profile runs a tiny paired-end Illumina 16S V4 dataset fetched from the nf-core test-datasets repository: a samplesheet (`ampliseq/samplesheets/Samplesheet.tsv`) pointing at gzipped paired FASTQs and a companion metadata sheet (`ampliseq/samplesheets/Metadata.tsv`) with categorical columns such as `treatment1`, `badpairwise10`, and `mix8`. Primers are the 515f/806r V4 pair (`GTGYCAGCMGCCGCGGTAA` / `GGACTACNVGGGTWTCTAAT`), taxonomy is assigned with DADA2 against `gtdb=R07-RS207` (primer-trimmed) and in parallel with QIIME2 against a tiny `greengenes85` database, and Barrnap SSU filtering (`--filter_ssu bac`) plus `--max_len_asv 255` and abundance/prevalence filters (`--min_samples 2`, `--min_frequency 10`) are applied. Expected outputs include a DADA2 ASV fasta and count table, taxonomy tables, QIIME2 filtered abundance/relative-abundance tables, alpha/beta diversity artifacts with ADONIS on `treatment1,mix8`, VSEARCH-clustered ASVs, ANCOM-BC differentials for `treatment1`, an SBDI export, a MultiQC report, and an `overall_summary.tsv` read-count tracking table. The full-size test (`test_full`) uses a larger habitat-based samplesheet with `dada_ref_taxonomy = rdp`, `trunc_qmin = 35`, PICRUSt2, ANCOM and ANCOM-BC enabled.

## Reference workflow
nf-core/ampliseq v2.16.1 (https://github.com/nf-core/ampliseq), a Nextflow community pipeline built around FastQC, Cutadapt, DADA2, VSEARCH, Barrnap, QIIME2, EPA-NG, and MultiQC. Cite Straub et al., Front. Microbiol. 2020, 11:550420 (doi:10.3389/fmicb.2020.550420) and the nf-core framework (Ewels et al., Nat Biotechnol 2020).
