---
name: viral-intrahost-low-frequency-variants
description: Use when you need to assemble a small viral genome (e.g. dengue, Zika,
  SARS-CoV-2-like) from short-read Illumina data and call intrahost / low-frequency
  (sub-consensus) SNVs with allele-frequency estimates using LoFreq. Assumes a close
  reference is available and the sample may contain host contamination.
domain: variant-calling
organism_class:
- viral
input_data:
- short-reads-paired
- reference-fasta
- decontamination-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/vipr
  url: https://github.com/nf-core/vipr
  version: dev
  license: MIT
  slug: vipr
tools:
- name: skewer
- name: fastqc
- name: decont
- name: kraken
- name: bbtools-tadpole
- name: bwa
- name: lofreq
- name: samtools
- name: bedtools
tags:
- virus
- intrahost
- low-frequency
- minor-variants
- allele-frequency
- quasispecies
- assembly
- lofreq
test_data: []
expected_output: []
---

# Viral intrahost low-frequency variant calling

## When to use this sketch
- Short-read Illumina paired-end sequencing of a viral sample (clinical isolate, culture, environmental) where a close reference genome exists.
- You want both a sample-specific polished assembly AND sub-consensus / intrahost variants with allele frequencies (minor-variant / quasispecies analysis).
- Reads may contain substantial host (e.g. human) contamination that must be removed before assembly and variant calling.
- Typical targets: dengue, Zika, chikungunya, influenza segments, coronaviruses, and similar small RNA/DNA viruses.
- You need per-position coverage and an interactive AF-vs-coverage plot for QC of called minor variants.

## Do not use when
- You only need a consensus sequence with no minor-variant analysis — use a simpler viral consensus workflow instead.
- The organism is bacterial or eukaryotic — see `haploid-variant-calling-bacterial` or a diploid germline sketch.
- Input is long-read (ONT/PacBio) — LoFreq's short-read error model is not appropriate; use a long-read viral variant caller.
- You are doing amplicon/primer-scheme-based sequencing (e.g. ARTIC nCoV) where primer trimming and scheme-aware consensus are required — use an ARTIC-style sketch.
- You do not have a close reference genome; this pipeline's assembly-polishing step depends on one.

## Analysis outline
1. Per-readunit adapter and quality trimming with Skewer, then combine read pairs per sample; QC with FastQC.
2. Host decontamination of trimmed reads with `decont` against a host reference FASTA (e.g. `human_g1k_v37`).
3. Optional metagenomic classification / sample-purity check with Kraken against a Kraken database (skippable via `--skip-kraken`).
4. De novo contig assembly of decontaminated reads with BBtools' Tadpole.
5. Contig orientation and gap-filling against the user-supplied close viral reference using ViPR Tools, producing a gap-filled assembly and a gap BED.
6. Iterative assembly polishing: BWA map → LoFreq call → consensus/variant integration, yielding a polished sample-specific assembly.
7. Mask zero-coverage positions in the polished assembly with `N` to produce a submission-ready FASTA.
8. Final BWA mapping of decontaminated reads against the polished assembly, indexing and stats with samtools.
9. Low-frequency variant calling with LoFreq on the final BAM, emitting a per-sample VCF with AF annotations.
10. Per-position coverage with bedtools and an interactive AF-vs-coverage HTML plot via ViPR Tools.

## Key parameters
- `samples.<name>.readunits.<ru>.fq1` / `fq2`: paired FASTQ inputs, grouped by sample and readunit (multiple readunits per sample are merged).
- `ref_fasta`: close viral reference FASTA used for contig orientation, gap filling and polishing (e.g. `DENV2-NC_001474.2.fa`).
- `cont_fasta`: host/contaminant FASTA for `decont` (e.g. `human_g1k_v37.fasta`).
- `kraken_db`: path to a Kraken database directory (e.g. `minikraken_20171019_8GB`); required unless skipping.
- `skip_kraken`: set `true` to bypass the Kraken classification step.
- `outdir`: results directory (default `results`), with one subdirectory per sample.
- Run with `-profile docker` (or `singularity`) and supply all inputs via `-params-file params.yaml`; command-line `--reads` is not supported — input must come from the params YAML.

## Test data
Inputs follow the `example_params.yaml` schema: one or more samples, each with one or more paired-end FASTQ readunits (`fq1`/`fq2`), plus a close viral reference FASTA, a host decontamination FASTA, and optionally a Kraken database directory. A successful run produces, per sample, trimmed and decontaminated FASTQs under `reads/`, Tadpole contigs (`{sample}_contigs.fa`), a gap-filled and then polished assembly (`{sample}-gap-filled-assembly.fa`, `{sample}_polished_assembly.fa`, `{sample}_0cov2N.fa`), a BWA BAM against the polished assembly with index and stats, a LoFreq VCF (`{sample}.vcf.gz`) with low-frequency variant calls, a per-position coverage file (`{sample}.cov.gz`), an interactive `{sample}_af-vs-cov.html` plot, and — unless skipped — a `{sample}_kraken.report.txt`.

## Reference workflow
nf-core/vipr (dev), https://github.com/nf-core/vipr — viral assembly and intrahost/low-frequency variant calling pipeline built around Skewer, decont, Kraken, BBtools Tadpole, BWA, LoFreq, bedtools and ViPR Tools.
