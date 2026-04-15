---
name: hybrid-denovo-assembly-bacterial
description: Use when you need a high-quality de novo genome assembly of a small (bacterial/plasmid-scale)
  isolate using a combination of Oxford Nanopore long reads and Illumina paired-end
  short reads, aiming for closed circular contigs via Unicycler's hybrid SPAdes+long-read
  bridging approach.
domain: assembly
organism_class:
- bacterial
- haploid
input_data:
- short-reads-paired
- long-reads-ont
source:
  ecosystem: nf-core
  workflow: nf-core/denovohybrid
  url: https://github.com/nf-core/denovohybrid
  version: dev
  license: MIT
  slug: denovohybrid
tools:
- name: porechop
- name: filtlong
- name: nanoplot
- name: fastqc
- name: unicycler
- name: miniasm
- name: racon
- name: pilon
- name: wtdbg2
- name: bandage
- name: quast
- name: multiqc
tags:
- hybrid-assembly
- nanopore
- illumina
- bacteria
- unicycler
- de-novo
- closed-genome
test_data: []
expected_output: []
---

# Hybrid de novo bacterial assembly (ONT + Illumina)

## When to use this sketch
- User has both Oxford Nanopore long reads and Illumina paired-end short reads for the same bacterial isolate(s) and wants a single polished assembly.
- Goal is a closed or near-closed small prokaryotic genome (typical target size a few Mb, e.g. ~5.3 Mb default) where short-read polishing is needed to reach high per-base accuracy.
- Multiple samples are provided as a TSV sheet (sample id, short R1, short R2, long reads) and should be assembled in one run.
- User explicitly wants Unicycler-style hybrid assembly with SPAdes graph + long-read bridging + short-read polishing.
- Long-read-only fallback is acceptable when short reads are missing for a given row in the sheet.

## Do not use when
- Only short reads are available with no long reads — use a pure short-read bacterial assembly sketch instead.
- Target is a large eukaryotic genome (human, plant, etc.) — prefer a long-read eukaryotic assembly sketch built around `miniasm` or `wtdbg2` with racon/Pilon polishing, not Unicycler.
- Task is variant calling against a known reference rather than de novo assembly — use a haploid bacterial variant-calling sketch.
- Input is PacBio HiFi — this pipeline is tuned for ONT long reads; pick a HiFi-specific assembler sketch.
- User wants metagenomic assembly from a mixed community — use a metagenome assembly sketch.

## Analysis outline
1. Parse the tab-separated input sheet of `sample_id`, short R1, short R2, long reads; rows missing short reads are routed to a long-read-only branch.
2. QC raw long reads with NanoPlot (length/quality distributions).
3. Trim Nanopore adapters and chimeric internal adapters with Porechop.
4. Quality- and length-filter long reads with Filtlong, biased toward quality, capping at `genomeSize * targetLongReadCov` bases.
5. Re-run NanoPlot on the filtered long reads to record the effect of trimming/filtering.
6. QC short reads with FastQC and subsample them to `targetShortReadCov` of the expected genome size.
7. Assemble with the chosen `--mode`: `unicycler` (default, hybrid SPAdes+long-read bridging+internal Pilon polishing), `miniasm` (long-read overlap assembly followed by Racon consensus and Pilon short-read polishing), `wtdbg2` (fuzzy de Bruijn long-read assembly followed by Racon + Pilon), or `all` (run every mode on every sample for comparison).
8. Visualise assembly graphs with Bandage for assemblers that emit GFA (Unicycler, miniasm).
9. Filter final contigs by `minContigLength` and write a sample-level FASTA whose headers encode sample id, assembler, and contig length.
10. Evaluate assemblies with QUAST (contig count, N50, length distribution) without an external reference.
11. Aggregate QC and assembly stats across samples with MultiQC into a single HTML report.

## Key parameters
- `--input`: path to the tab-separated sample sheet (`sample_id\tshort_R1\tshort_R2\tlong_reads`); rows with empty short-read columns trigger long-read-only assembly.
- `--mode`: `unicycler` (default, recommended for bacteria), `miniasm`, `wtdbg2`, or `all` to run every assembler on every sample.
- `--genomeSize`: expected assembly size in bp (default `5300000`); drives coverage-based subsampling and is required by several assemblers.
- `--targetLongReadCov`: target coverage for long reads after Filtlong (default `100`); lower values (e.g. 60) speed up assembly.
- `--targetShortReadCov`: target coverage for Illumina reads after subsampling (default `100`).
- `--minContigLength`: drop contigs below this length from the final FASTA (default `1000`).
- `--saveIntermediate`: keep intermediate assembly graphs and unpolished contigs for debugging.
- `-profile`: `docker`, `singularity`, `conda`, or `test` for the bundled CI configuration.

## Test data
The bundled `test` profile points at the nf-core `test-datasets` branch `denovohybrid`, pulling a small TSV sample sheet (`testdata/test_files.tsv`) that references tiny Illumina paired-end FASTQs and a matching Nanopore FASTQ for one or more toy samples. The profile pins `genomeSize = 11500` and sets `mode = 'all'`, so every test run exercises the Unicycler, miniasm, and wtdbg2 branches against the same inputs. Expected outputs are a per-sample polished FASTA for each assembler under `results/<sample>/`, NanoPlot and FastQC reports under `results/<sample>/qc/`, Bandage SVGs for the GFA-producing assemblers, a QUAST report per assembly, and a top-level MultiQC HTML summarising all samples. Resources are capped at 2 CPUs / 6 GB / 48 h so the workflow completes on CI.

## Reference workflow
nf-core/denovohybrid (dev branch, https://github.com/nf-core/denovohybrid), originally authored by Caspar Groß. Unicycler mode is the documented default and the state-of-the-art hybrid bacterial assembly recipe this sketch encodes; see `docs/usage.md` and `docs/output.md` for parameter and output details.
