---
name: sars-cov-2-wgs-illumina-pe-variant-calling
description: Use when you need sensitive low-frequency variant calling (including
  intra-host minor variants across a wide range of allele frequencies) from paired-end
  Illumina whole-genome sequencing of SARS-CoV-2 against the NC_045512.2 Wuhan-Hu-1
  reference, with SnpEff annotation using the covid19 database.
domain: variant-calling
organism_class:
- viral
- haploid
input_data:
- short-reads-paired
- reference-fasta
source:
  ecosystem: iwc
  workflow: 'COVID-19: variation analysis on WGS PE data'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/sars-cov-2-variant-calling/sars-cov-2-pe-illumina-wgs-variant-calling
  version: 0.2.4
  license: MIT
tools:
- fastp
- bwa-mem
- samtools
- picard-markduplicates
- lofreq
- snpeff
- multiqc
tags:
- sars-cov-2
- covid-19
- viral
- wgs
- illumina
- paired-end
- low-frequency-variants
- lofreq
- snpeff
- intra-host
test_data:
- role: nc_045512_2_fasta_sequence_of_sars_cov_2
  url: https://zenodo.org/record/4555735/files/NC_045512.2_reference.fasta?download=1
  sha1: db3759c2e1d9ce8827ba4aa1749e759313591240
- role: paired_collection__srr11578257__forward
  url: https://zenodo.org/records/10174466/files/SRR11578257_R1.fastq.gz?download=1
  sha1: db2f908fbbb6c4920ee0de73265acdeb92c9895f
- role: paired_collection__srr11578257__reverse
  url: https://zenodo.org/records/10174466/files/SRR11578257_R2.fastq.gz?download=1
  sha1: 4f754a7023bcc3cb1a240d3fb03532338c5c1107
expected_output: []
---

# SARS-CoV-2 WGS paired-end Illumina variant calling

## When to use this sketch
- Input is paired-end Illumina WGS (not amplicon/ARTIC) of SARS-CoV-2 isolates.
- You need sensitive detection of SNVs and indels across a wide range of allele frequencies, including sub-consensus / intra-host minor variants (LoFreq with permissive AF filtering).
- Reference is the Wuhan-Hu-1 NC_045512.2 genome and you want functional annotation via the covid19-specific SnpEff database.
- You want QC (fastp, samtools stats, MarkDuplicates metrics) aggregated into a MultiQC report alongside variants.

## Do not use when
- Reads come from an amplicon protocol (ARTIC, midnight) — use an ARTIC/amplicon-specific SARS-CoV-2 sketch that performs primer trimming with ivar/cutadapt before calling.
- Reads are single-end Illumina — use the SE Illumina SARS-CoV-2 sketch.
- Reads are Oxford Nanopore long reads — use the ONT SARS-CoV-2 variant-calling sketch (medaka/minimap2-based).
- You only need a consensus FASTA or Pangolin lineage assignment — use a consensus/lineage-calling sketch.
- Organism is a bacterium or eukaryote — use the appropriate haploid or diploid variant-calling sketch instead.

## Analysis outline
1. Read QC and adapter/quality trimming with **fastp** (paired collection input, HTML+JSON reports).
2. Map trimmed reads to the NC_045512.2 reference with **BWA-MEM** (coordinate-sorted BAM).
3. Filter alignments with **samtools view**: keep properly paired reads (flags 1+2 required) at MAPQ ≥ 20.
4. Collect alignment metrics with **samtools stats**.
5. Remove PCR/optical duplicates with **Picard MarkDuplicates** (`REMOVE_DUPLICATES=true`).
6. Realign reads around indels with **lofreq viterbi** to improve indel representation.
7. Insert indel base qualities with **lofreq indelqual** using the Dindel model.
8. Call SNVs and indels with **lofreq call** (`--call-indels`) across the whole genome.
9. Apply strand-bias filtering with **lofreq filter** (FDR-controlled, compound SB filter, reports all variants with flags).
10. Annotate variants with **SnpEff** using the dedicated `NC_045512.2` / covid19 database.
11. Aggregate fastp, samtools stats, and MarkDuplicates metrics into a single **MultiQC** report.

## Key parameters
- Reference: SARS-CoV-2 Wuhan-Hu-1 `NC_045512.2` FASTA (must match the SnpEff `genome_version: NC_045512.2`, tool version `4.5covid19`).
- samtools view filter: `-q 20`, inclusive flags `1,2` (paired + properly paired), output BAM.
- MarkDuplicates: `REMOVE_DUPLICATES=true`, `DUPLICATE_SCORING_STRATEGY=SUM_OF_BASE_QUALITIES`, `VALIDATION_STRINGENCY=LENIENT`.
- lofreq viterbi: default BQ2 handling (`keep`, defqual=2), `keepflags=false`.
- lofreq indelqual: strategy `dindel` with the reference FASTA.
- lofreq call: `min_cov=5`, `max_depth=1000000`, `min_bq=30`, `min_alt_bq=30`, `min_mq=20`, extended BAQ enabled, significance `sig=0.0005`, `--call-indels`, whole-genome region.
- lofreq filter: no hard AF or coverage cutoff (`af_min=0.0`, `cov_min=0`), strand-bias filter `mtc=fdr` with `sb_alpha=0.001`, compound SB on, `--print-all` (soft flag rather than drop).
- SnpEff: `genome_version=NC_045512.2`, annotations `-formatEff -classic`, filter out `-no-downstream -no-intergenic -no-upstream -no-utr`, `udLength=0`, stats HTML on.

## Test data
The source workflow ships a planemo test that runs one paired-end sample, `SRR11578257`, as a `list:paired` collection (`SRR11578257_R1.fastq.gz` / `SRR11578257_R2.fastq.gz` hosted on Zenodo record 10174466), together with the `NC_045512.2_reference.fasta` (Zenodo record 4555735). Running the workflow on this input is expected to produce a SnpEff-annotated VCF for `SRR11578257` that matches the bundled golden file `test-data/final_snpeff_annotated_variants.vcf` via a line-diff comparison tolerating up to 6 differing lines (to absorb SnpEff header/date noise). Ancillary outputs include the fastp HTML report, filtered and realigned BAMs, the unfiltered and strand-bias-filtered LoFreq VCFs, the SnpEff stats HTML, and a combined MultiQC preprocessing-and-mapping report.

## Reference workflow
Galaxy IWC — `workflows/sars-cov-2-variant-calling/sars-cov-2-pe-illumina-wgs-variant-calling`, workflow `COVID-19: variation analysis on WGS PE data`, release 0.2.4 (MIT). Uses LoFreq 2.1.5, BWA 0.7.17, fastp 0.23.2, Picard MarkDuplicates 2.18.2, samtools 1.13 / stats 2.0.3, MultiQC 1.11, SnpEff 4.5covid19.
