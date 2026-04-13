---
name: linked-read-denovo-assembly-10x
description: Use when you need to perform de novo genome assembly from 10x Genomics
  Chromium linked-read (barcoded) sequencing data for a eukaryotic genome, and want
  both pseudohaploid and phased (megabubbles) FASTA outputs plus assembly QC (QUAST,
  BUSCO). Not for short-read-only, long-read, or metagenome assemblies.
domain: assembly
organism_class:
- eukaryote
- diploid
input_data:
- 10x-chromium-linked-reads-fastq
source:
  ecosystem: nf-core
  workflow: nf-core/neutronstar
  url: https://github.com/nf-core/neutronstar
  version: 1.0.0
  license: MIT
tools:
- supernova
- quast
- busco
- multiqc
tags:
- 10x-genomics
- linked-reads
- chromium
- de-novo
- phased-assembly
- supernova
- archived-pipeline
test_data: []
expected_output: []
---

# Linked-read de novo assembly (10x Chromium)

## When to use this sketch
- Input is 10x Genomics Chromium linked-read FASTQs produced by `mkfastq` / `bcl2fastq` (barcoded short reads with GEM partitioning).
- Goal is a de novo whole-genome assembly of a eukaryote with a known approximate genome size.
- You want both a pseudohaploid assembly and a haplotype-phased (megabubbles) FASTA, alongside contiguity metrics and ortholog completeness.
- You are assembling one or a small number of samples where Supernova's memory/time requirements are acceptable.
- Note: the upstream pipeline is archived (10x Chromium discontinued). Use only when you already have legacy Chromium data.

## Do not use when
- Reads are standard Illumina paired-end without 10x barcodes — use a short-read de novo assembly sketch (e.g. SPAdes/Unicycler) instead.
- Reads are PacBio HiFi or ONT long reads — use a long-read assembly sketch (hifiasm, Flye, Canu).
- Target is a bacterial isolate — use a bacterial assembly sketch (Unicycler/SPAdes/Shovill).
- The sample is a microbial community — use a metagenome assembly sketch (metaSPAdes, MEGAHIT).
- You only need variant calls against a reference — use a variant-calling sketch, not assembly.

## Analysis outline
1. Stage 10x Chromium FASTQ directory (output of `cellranger mkfastq` / `bcl2fastq`) for each sample id.
2. Run `supernova run` with `--id`, `--fastqs`, and optional read/barcode subsetting (`--maxreads`, `--bcfrac`, `--sample`, `--lanes`, `--indices`) to build the linked-read assembly graph.
3. Emit FASTA assemblies with `supernova mkoutput` in two styles: `pseudohap` (`sample_id.fasta`) and `megabubbles` (`sample_id.phased.fasta`).
4. Compute contiguity stats with QUAST, using `--genomesize` to bound NGxx statistics.
5. Score gene-space completeness with BUSCO against a lineage dataset (e.g. `eukaryota_odb9`, `aves_odb9`).
6. Aggregate Supernova, QUAST and BUSCO metrics into a MultiQC HTML report.

## Key parameters
- `--id` (required): unique run id, `[a-zA-Z0-9_-]+`, used as sample/output prefix.
- `--fastqs` (required): path to the directory produced by `mkfastq`/`bcl2fastq`.
- `--genomesize` (required): estimated haploid genome size in bp, drives QUAST NGxx bounds.
- `--busco_data`: BUSCO lineage dataset name (e.g. `eukaryota_odb9`); `--busco_folder` points at the downloaded lineage directory.
- `--maxreads`: downsample to NUM reads or `all` (default `all`); use to control Supernova's recommended ~56x raw coverage window.
- `--bcfrac`: fraction of barcodes to keep (barcode-level downsampling).
- `--sample`, `--lanes`, `--indices`: restrict which FASTQs/lanes/index sets are consumed.
- `--minsize`: drop scaffolds shorter than NUM bp from the FASTA (default 1000).
- `--no_accept_extreme_coverage`: disable Supernova's `--accept_extreme_coverage` escape hatch.
- `--nopreflight`: skip Supernova preflight checks.
- `--full_output`: keep the entire Supernova assembly directory instead of the minimal subset required for `supernova mkoutput`.
- Multi-sample runs: supply a YAML `-params-file` with a top-level `genomesize` and a `samples:` list of `{id, fastqs, [maxreads, bcfrac, ...]}` entries.

## Test data
The bundled `test` profile runs a single fake assembly (`name: testrun`, `busco_data: busco_example`, `full_output: true`) using a stubbed Supernova binary on the `$baseDir/tests` PATH and the `nfcore/supernova:2.1.1` container only for `supernova_mkoutput`. It exercises the Supernova → mkoutput → QUAST → BUSCO → MultiQC graph end-to-end without performing a real assembly. Expected outputs are a `results/supernova/testrun/` working directory, `results/assemblies/testrun.fasta` and `results/assemblies/testrun.phased.fasta`, plus QUAST, BUSCO and MultiQC reports under `results/`.

## Reference workflow
nf-core/neutronstar v1.0.0 (https://github.com/nf-core/neutronstar) — archived community pipeline wrapping 10x Genomics Supernova, QUAST, BUSCO and MultiQC for de novo assembly of Chromium linked-read data.
