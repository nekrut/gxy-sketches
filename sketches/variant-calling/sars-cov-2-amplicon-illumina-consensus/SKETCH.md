---
name: sars-cov-2-amplicon-illumina-consensus
description: Use when you have Illumina paired-end amplicon sequencing of SARS-CoV-2
  (or related viral) samples and need a full intra-host variant-calling and consensus-genome
  workflow including primer trimming, lineage assignment (Pangolin), clade assignment
  (Nextclade) and optional mixed-lineage deconvolution (Freyja). Assumes an ARTIC-like
  tiled-amplicon protocol against a single-segment viral reference such as MN908947.3.
domain: variant-calling
organism_class:
- viral
- haploid
input_data:
- short-reads-paired
- reference-fasta
- primer-bed
source:
  ecosystem: nf-core
  workflow: nf-core/viralrecon
  url: https://github.com/nf-core/viralrecon
  version: 3.0.0
  license: MIT
  slug: viralrecon
tools:
- name: fastp
- name: bowtie2
- name: samtools
- name: ivar
- name: bcftools
- name: bedtools
- name: mosdepth
- name: snpeff
- name: snpsift
- name: pangolin
- name: nextclade
- name: freyja
- name: kraken2
- name: multiqc
tags:
- sars-cov-2
- covid
- viral
- amplicon
- artic
- consensus
- lineage
- pangolin
- nextclade
- ivar
test_data: []
expected_output: []
---

# SARS-CoV-2 Illumina amplicon variant calling and consensus

## When to use this sketch
- Illumina paired-end (or single-end) short reads from a tiled-amplicon viral enrichment protocol (ARTIC v1/v3/v4/v4.1/v5, Midnight, SWIFT, etc.).
- Target is SARS-CoV-2 or another small single-segment RNA virus that can be mapped to a single reference FASTA (default `MN908947.3`).
- You need per-sample SNVs/indels with functional annotation, a masked consensus FASTA, and lineage/clade calls (Pangolin + Nextclade).
- You optionally want mixed-lineage / wastewater deconvolution via Freyja.
- You want primer-aware trimming so primer-binding sites don't contaminate variant calls.

## Do not use when
- Reads are Oxford Nanopore — use the nanopore-artic sibling sketch (nf-core/viralrecon `--platform nanopore` runs `artic minion` with clair3 instead of Bowtie2 + iVar).
- Library is shotgun metagenomic rather than amplicon — drop the primer-trim step and switch `--protocol metagenomic` (default variant caller becomes `bcftools` and the `de novo` assembly branch with SPAdes/Unicycler/minia becomes relevant); use a metagenomic-viral sibling sketch.
- You need de novo viral assembly without a reference (use an assembly-focused sketch: SPAdes rnaviral / Unicycler / minia branch of viralrecon).
- Organism is bacterial, eukaryotic, or diploid — see haploid-variant-calling-bacterial or a germline variant sketch.
- You only want taxonomic profiling of a clinical swab — use a Kraken2/metagenomics sketch.

## Analysis outline
1. Concatenate re-sequenced FASTQs per `sample` id (`cat`).
2. Raw-read QC with `FastQC`.
3. Adapter and quality trimming with `fastp`.
4. Optional host-read screening / filtering with `Kraken2` against a human (or host) database.
5. Reference alignment with `Bowtie2` against the viral FASTA; sort/index with `SAMtools`.
6. Amplicon primer soft-clipping with `ivar trim` using the primer BED (coordinates relative to reference).
7. Optional duplicate marking with Picard `MarkDuplicates` (off by default for viral data).
8. Alignment QC with Picard `CollectMultipleMetrics`, `SAMtools stats`, and genome-wide + per-amplicon coverage with `mosdepth`.
9. Variant calling with `ivar variants` (default for `--protocol amplicon`) from an `samtools mpileup`; convert to VCF via the bundled `ivar_variants_to_vcf.py`.
10. Variant annotation with `SnpEff` + `SnpSift` against the viral SnpEff database.
11. Consensus calling by masking low-coverage positions (`bedtools maskfasta`) and projecting high-AF variants with `bcftools consensus` (default), or alternatively `ivar consensus`.
12. Consensus QC with `QUAST`; lineage assignment with `Pangolin`; clade/mutation/QC calls with `Nextclade`.
13. Optional mixed-lineage abundance recovery with `Freyja` (demix + bootstrap) using UShER barcodes.
14. Per-sample long-format variants table joining BCFTools stats, SnpSift effects and Pangolin lineage.
15. Aggregate reporting with `MultiQC` including `summary_variants_metrics_mqc.csv`.

## Key parameters
- `--platform illumina` and `--protocol amplicon` (selects Bowtie2 + iVar branch).
- `--genome 'MN908947.3'` — pulls reference FASTA, GFF, SnpEff DB, Nextclade dataset and ARTIC primer scheme from the nf-core viralrecon genomes config. Override with `--fasta` / `--gff` for a custom virus.
- `--primer_set artic` plus `--primer_set_version <1|3|4|4.1|5.3.2>` — or supply a custom `--primer_bed`. For SWIFT, also set `--primer_left_suffix _F --primer_right_suffix _R --ivar_trim_offset 5`.
- `--variant_caller ivar` (default for amplicon) vs `bcftools` (default for metagenomic).
- `--consensus_caller bcftools` (default; high-AF variants projected onto masked reference). iVar filter thresholds: AF ≥ 0.25 / Q ≥ 20 / DP ≥ 10 for reporting; AF ≥ 0.75 for inclusion in consensus.
- `--min_mapped_reads 1000` — samples below this are dropped from downstream steps.
- `--kraken2_db` + `--kraken2_variants_host_filter` to actually remove host reads before variant calling (off by default; Kraken2 still runs to report host contamination).
- `--skip_assembly` — strongly recommended for variant-only runs; otherwise the SPAdes/Unicycler/minia branch also runs.
- `--skip_freyja` / `--skip_freyja_boot` / `--freyja_repeats` / `--freyja_depthcutoff` to control mixed-lineage analysis.
- `--skip_pangolin` / `--skip_nextclade` to disable lineage-calling tools when their DBs are stale.

## Test data
The pipeline's `test` profile points at `samplesheet_test_amplicon_illumina.csv` from the `nf-core/test-datasets` viralrecon branch: a small set of paired-end Illumina ARTIC v1 amplicon FASTQs derived from SARS-CoV-2 samples, mapped to `MN908947.3`. Host screening uses the downsampled `kraken2_hs22.tar.gz` human-chr22 Kraken2 database. Freyja is run with `freyja_repeats = 10` to keep bootstrapping fast, and `variant_caller = 'ivar'`, `assemblers = 'spades,unicycler'`. A successful run produces per-sample primer-trimmed BAMs, iVar TSV + converted VCFs, SnpEff-annotated VCFs, BCFTools-masked consensus FASTAs, Pangolin lineage CSVs, Nextclade clade CSVs, QUAST reports, mosdepth amplicon/genome coverage plots, a `variants_long_table.csv`, and a unified `multiqc_report.html` with `summary_variants_metrics_mqc.csv`. The full-size `test_full` profile runs the same workflow against ARTIC v3 primers.

## Reference workflow
nf-core/viralrecon v3.0.0 (https://github.com/nf-core/viralrecon), Illumina amplicon branch. Built on the ARTIC Network primer schemes and inspired by `connor-lab/ncov2019-artic-nf`. Canonical invocation: `nextflow run nf-core/viralrecon --input samplesheet.csv --outdir <OUTDIR> --platform illumina --protocol amplicon --genome 'MN908947.3' --primer_set artic --primer_set_version 3 --skip_assembly -profile docker`.
