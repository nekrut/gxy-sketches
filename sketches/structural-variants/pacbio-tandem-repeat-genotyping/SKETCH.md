---
name: pacbio-tandem-repeat-genotyping
description: Use when you need to genotype and visualize tandem repeat expansions
  (e.g. C9ORF72, FMR1, HTT) from PacBio HiFi long reads, typically from a PureTarget
  repeat expansion panel or targeted HiFi sequencing. Produces per-locus repeat motif
  counts, spanning-read BAMs, and waterfall plots against a reference.
domain: structural-variants
organism_class:
- vertebrate
- diploid
- human
input_data:
- long-reads-pacbio-hifi-ubam
- reference-fasta
- repeat-bed
source:
  ecosystem: nf-core
  workflow: nf-core/pacvar
  url: https://github.com/nf-core/pacvar
  version: 1.0.1
  license: MIT
tools:
- lima
- pbmm2
- samtools
- trgt
- bcftools
tags:
- pacbio
- hifi
- tandem-repeat
- repeat-expansion
- trgt
- puretarget
- long-read
- c9orf72
- genotyping
test_data: []
expected_output: []
---

# PacBio HiFi tandem repeat genotyping

## When to use this sketch
- You have PacBio Revio/Sequel II HiFi unaligned BAM (`.bam` + optional `.pbi`) reads, optionally multiplexed with PacBio barcodes.
- The biological question is the length/motif composition of one or more known tandem repeat loci (e.g. C9ORF72 GGGGCC, HTT CAG, FMR1 CGG, RFC1 AAGGG), not genome-wide SNV/SV discovery.
- Input is typically from PacBio's PureTarget repeat expansion panel or a comparable targeted HiFi capture, where spanning reads fully cover each repeat.
- You need per-allele repeat counts, a spanning-read BAM for IGV inspection, and waterfall motif plots per sample/locus.
- A repeat-definition BED (TRGT catalog format, with `ID=...;MOTIFS=...;STRUC=...` tags) is available for the loci of interest.

## Do not use when
- You want whole-genome PacBio HiFi SNV + SV calling with DeepVariant/pbsv/HiPhase — use the sibling `pacbio-hifi-wgs-variant-calling` sketch instead.
- Reads are ONT or Illumina — TRGT expects PacBio HiFi; use an ONT repeat caller (e.g. Straglr, NanoRepeat) or Illumina tools (ExpansionHunter).
- You are doing de novo repeat discovery across the genome rather than genotyping a known catalog.
- You only have aligned CRAMs with no per-read HiFi context — convert back to HiFi uBAM first or use a different tool.

## Analysis outline
1. (Optional) Demultiplex multiplexed HiFi uBAM by barcode pairs with `lima` using the provided `--barcodes` FASTA; skip with `--skip_demultiplexing` when samples are already per-barcode.
2. Align HiFi reads to the reference FASTA with `pbmm2` in HiFi preset, producing a per-sample aligned BAM.
3. Sort and index the aligned BAM with `samtools sort` + `samtools index`.
4. Genotype tandem repeats with `trgt genotype` using the repeat-definition BED (`--intervals`), the indexed BAM, the reference, and the sample `--karyotype` (XX/XY). This emits a spanning-read BAM and a per-sample VCF of repeat alleles.
5. Sort and index the TRGT spanning BAM with `samtools` so it is browsable.
6. Sort the TRGT VCF with `bcftools sort` and index it.
7. Render per-locus waterfall motif plots with `trgt plot` for each `repeat_id` of interest.

## Key parameters
- `--workflow repeat` — selects the tandem-repeat branch (the alternative `wgs` runs DeepVariant/pbsv/HiPhase instead).
- `--input samplesheet.csv` — CSV with columns `sample,bam,pbi` where `bam` is a HiFi uBAM and `pbi` is optional.
- `--fasta` / `--fasta_fai` (or `--genome GATK.GRCh38` via iGenomes) — reference the repeat BED coordinates are defined against.
- `--intervals <repeats.bed>` — TRGT-format repeat catalog; this drives which loci are genotyped/plotted.
- `--repeat_id <ID>` — the repeat locus ID (must match an `ID=` field in the BED) to render waterfall plots for, e.g. `C9ORF72`.
- `--karyotype XX|XY` — diploidy assumption for TRGT genotyping; default `XX`.
- `--skip_demultiplexing true` — set when the input uBAM is already per-sample and `--barcodes` is not provided.
- `--barcodes <barcodes.fasta>` — only needed when demultiplexing with lima.

## Test data
The pipeline's `test` profile exercises exactly this repeat workflow on a minimal PacBio PureTarget-style dataset: a small C9ORF72 reference slice (`pacbio_data/C9ORF72-12.fa` plus `.fai`), a TRGT repeat BED (`pacbio_data/c9orf72-short.bed`), and a samplesheet (`pacbio_data/samplesheet_pb_puretarget.csv`) of already-demultiplexed HiFi uBAMs, with `workflow=repeat`, `repeat_id=C9ORF72`, and `skip_demultiplexing=true`. Running it should produce, per sample, a TRGT VCF of C9ORF72 repeat alleles (`<sample>.bam.vcf.gz`), a spanning-read BAM (`<sample>.bam.spanning.bam` + `.bai`), and a C9ORF72 waterfall PNG under `trgt/`, plus a MultiQC report and pipeline_info directory. No golden VCFs are asserted — success is defined by the workflow completing and the expected output files existing.

## Reference workflow
nf-core/pacvar v1.0.1 — https://github.com/nf-core/pacvar — `repeat` subworkflow (lima → pbmm2 → samtools → TRGT genotype/plot → bcftools sort/index). TRGT: https://github.com/PacificBiosciences/trgt. pbmm2: https://github.com/PacificBiosciences/pbmm2.
