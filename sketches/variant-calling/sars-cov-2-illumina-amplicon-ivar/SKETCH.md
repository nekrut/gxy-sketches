---
name: sars-cov-2-illumina-amplicon-ivar
description: Use when you need to call consensus variants, build consensus genomes,
  and assign Pango lineage / Nextclade clade from paired-end Illumina ARTIC amplicon
  sequencing of SARS-CoV-2. Assumes a tiled-amplicon protocol with a known primer
  BED and the MN908947.3/NC_045512.2 reference.
domain: variant-calling
organism_class:
- viral
- haploid
input_data:
- short-reads-paired
- reference-fasta
- primer-bed
source:
  ecosystem: iwc
  workflow: SARS-CoV-2 Illumina Amplicon pipeline - iVar based
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/sars-cov-2-variant-calling/sars-cov-2-pe-illumina-artic-ivar-analysis
  version: '0.4'
  license: MIT
  slug: sars-cov-2-variant-calling--sars-cov-2-pe-illumina-artic-ivar-analysis
tools:
- name: fastp
  version: 1.1.0+galaxy0
- name: bwa-mem
  version: 0.7.19
- name: samtools
  version: 2.0.8
- name: ivar
  version: 1.4.4+galaxy1
- name: snpeff
  version: 4.5covid19
- name: pangolin
  version: 4.3.4+galaxy3
- name: nextclade
  version: 2.7.0+galaxy0
- name: qualimap
  version: 2.3+galaxy0
- name: multiqc
  version: 1.33+galaxy0
tags:
- sars-cov-2
- covid-19
- artic
- amplicon
- ivar
- consensus
- lineage
- pangolin
- nextclade
test_data: []
expected_output: []
---

# SARS-CoV-2 Illumina ARTIC amplicon analysis (iVar)

## When to use this sketch
- Paired-end Illumina sequencing of SARS-CoV-2 produced with a tiled-amplicon scheme (ARTIC v3/v4/v4.1 or compatible) and a matching primer BED file.
- You need per-sample majority-frequency variants (SNVs + small indels), a depth-masked consensus genome, SnpEff functional annotation, and Pango lineage + Nextclade clade assignments in one pass.
- Rapid public-health style surveillance similar to ncov2019-artic-nf, covid-19-signal, or Theiagen Titan, but run in Galaxy.
- Reference is MN908947.3 / NC_045512.2 (the workflow renames MN908947.3 to NC_045512.2 so SnpEff's covid19 database resolves).

## Do not use when
- Reads are Oxford Nanopore ARTIC data — use an ONT/medaka ARTIC sketch instead.
- You need low-frequency / intra-host minor variant calling — use the sibling `sars-cov-2-pe-illumina-artic-variant-calling` (lofreq-based) workflow.
- Data are metagenomic / non-amplicon WGS with no primer scheme — skip the `ivar trim` step and use a generic viral variant-calling sketch.
- Organism is not SARS-CoV-2 (SnpEff db, pangolin, and nextclade are SARS-CoV-2 specific).
- You need the latest Nextclade dataset with high fidelity — the bundled Nextclade is outdated; re-run the combined consensus multi-FASTA through clades.nextstrain.org.

## Analysis outline
1. Adapter/quality trim paired reads with `fastp` (per-sample HTML+JSON reports).
2. Rename the reference FASTA header from `MN908947.3` to `NC_045512.2` with sed so downstream SnpEff uses the covid19 database.
3. Map trimmed reads to the renamed reference with `bwa mem` (Illumina preset, coordinate-sorted BAM).
4. Filter alignments with `samtools view` keeping properly paired reads (flags 1+2) at MAPQ ≥ 20.
5. Compute `samtools stats` and `Qualimap BamQC` on the filtered BAM for coverage/insert-size QC.
6. Soft-clip primers from the BAM using `ivar trim` with the supplied primer BED (auto length filter, min-qual 20, sliding window 4).
7. Call majority variants with `ivar variants` against the reference (tabular + VCF), using the user-supplied min allele frequency and base quality thresholds.
8. Build a depth-masked consensus FASTA with `ivar consensus` (min depth 50, N-mask below, min indel freq 0.8).
9. Rename consensus FASTA headers with sed, then concatenate all per-sample consensuses into a combined multi-FASTA.
10. Annotate the per-sample variant VCFs with `SnpEff` (genome_version NC_045512.2) to produce annotated variants.
11. Run `Nextclade` (organism sars-cov-2) on the combined multi-FASTA for clade/QC assignments.
12. Run `pangolin` (usher mode, min_length 10000, max_ambig 0.5) on the combined multi-FASTA to assign Pango lineages; the workflow branches on whether the user selected a cached `pangolin-data` release or falls back to the bundled default.
13. Aggregate fastp, samtools stats, and Qualimap reports into a single `MultiQC` HTML quality-control report.

## Key parameters
- Reference: SARS-CoV-2 MN908947.3 (auto-renamed to NC_045512.2).
- Primer scheme: user-supplied ARTIC-style BED (must match amplicon kit/version).
- `Read fraction to call variant` (ivar variants/consensus `-t`): float 0–1, default **0.7** (majority-consensus threshold).
- `Minimum quality score to call base` (ivar `-q`): integer, default **20**.
- `ivar trim`: min_qual 20, window_width 4, primer_pos_wiggle 0, include primers, auto trimmed-length filter.
- `ivar consensus`: min_depth **50**, min_indel_freq **0.8**, depth_action `-n N` (mask low-coverage bases as N).
- `samtools view` filter: require flags 1,2 (paired + properly paired), MAPQ ≥ **20**.
- `pangolin`: analysis_mode **usher**, min_length **10000**, max_ambig **0.5**; `pangolin-data` version optionally selected from cached releases (else bundled default, currently v1.37).
- `Nextclade`: organism `sars-cov-2`, dataset downloaded at runtime.
- `SnpEff`: genome_version **NC_045512.2** (covid19 database, udLength 0).

## Test data
The test profile supplies a paired-read collection of one or more downsampled SARS-CoV-2 ARTIC Illumina samples, the MN908947.3 reference FASTA, and an ARTIC primer BED, plus the numeric parameters (min allele fraction ~0.7, min base quality 20). Running the workflow is expected to yield, per sample, a primer-trimmed BAM, an `ivar variants` tabular table, a SnpEff-annotated VCF, and a masked consensus FASTA; across all samples it produces a combined multi-FASTA, a Pangolin lineage TSV, a Nextclade clade TSV, and a MultiQC HTML QC report. The caller's parsed test manifest is the authoritative list of inputs and golden outputs.

## Reference workflow
Galaxy IWC `sars-cov-2-variant-calling/sars-cov-2-pe-illumina-artic-ivar-analysis` — workflow `SARS-CoV-2 Illumina Amplicon pipeline - iVar based`, release **0.4** (MIT). Modeled after ncov2019-artic-nf, covid-19-signal, and Theiagen Titan pipelines.
