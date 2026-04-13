---
name: bacterial-short-read-assembly-shovill
description: Use when you need to assemble a bacterial isolate genome de novo from
  adapter-trimmed paired-end Illumina short reads into contigs, with an assembly graph
  and basic graph statistics. Targets single-isolate bacterial WGS; not for metagenomes,
  long reads, or eukaryotes.
domain: assembly
organism_class:
- bacterial
- haploid
input_data:
- short-reads-paired
source:
  ecosystem: iwc
  workflow: Bacterial Genome Assembly using Shovill
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/genome-assembly/bacterial-genome-assembly
  version: 2.0.1
  license: GPL-3.0-or-later
tools:
- shovill
- spades
- bandage
- tooldistillator
tags:
- bacteria
- wgs
- de-novo-assembly
- illumina
- paired-end
- isolate
- abromics
test_data: []
expected_output:
- role: shovill_contigs_graph
  description: Content assertions for `shovill_contigs_graph`.
  assertions:
  - 'has_text: KC:i'
- role: shovill_logfile
  description: Content assertions for `shovill_logfile`.
  assertions:
  - 'has_text: [shovill] Done.'
- role: shovill_contigs_fasta
  description: Content assertions for `shovill_contigs_fasta`.
  assertions:
  - 'has_text: >contig00001'
- role: bandage_contig_graph_stats
  description: Content assertions for `bandage_contig_graph_stats`.
  assertions:
  - 'has_text: Total length orphaned nodes (bp):'
  - 'has_n_columns: {''n'': 2}'
- role: tooldistillator_summarize_assembly
  description: Content assertions for `tooldistillator_summarize_assembly`.
  assertions:
  - 'has_text: contig00146'
---

# Bacterial short-read de novo assembly with Shovill

## When to use this sketch
- You have a single bacterial isolate sequenced on Illumina as paired-end short reads (FASTQ / FASTQ.gz).
- Reads have already been adapter- and quality-trimmed (e.g. with fastp) upstream.
- You want a de novo draft assembly (contigs FASTA), the underlying assembly graph (GFA), read alignment to the assembly (BAM), and a quick graph plot/stats for sanity checking.
- You want a compact machine-readable JSON summary of the assembly step for downstream aggregation.

## Do not use when
- Input is a metagenomic / microbiome sample — use a dedicated metagenomic assembler sketch instead.
- Input is long reads (ONT or PacBio) or hybrid — use a long-read / hybrid bacterial assembly sketch.
- Raw, untrimmed FASTQs — run an adapter/quality trimming workflow first (fastp / trim-galore) before feeding this sketch.
- You need downstream QC of the assembly (QUAST, CheckM2, Kraken2 contamination check) — that was split into the sibling `quality-and-contamination-control-post-assembly` workflow.
- You need variant calling against a reference — use a haploid bacterial variant-calling sketch.
- You need gene / functional annotation (Prokka, Bakta) — chain an annotation sketch after this one.

## Analysis outline
1. Ingest paired-end trimmed FASTQs as forward (R1) and reverse (R2) inputs.
2. Assemble with **Shovill** (SPAdes backend) to produce contigs FASTA, contig graph, read-to-assembly BAM, and run log.
3. Compute assembly graph statistics with **Bandage Info** on the Shovill contig graph.
4. Render the assembly graph as an image with **Bandage Image**.
5. Extract structured metrics from Shovill outputs with **ToolDistillator** (per-tool JSON).
6. Aggregate the per-tool JSON into a single summary JSON with **ToolDistillator Summarize**.

## Key parameters
- Shovill `assembler`: `spades` (default backend; skip the built-in trim since reads are pre-trimmed).
- Shovill `trim`: `false` — inputs are already adapter-trimmed.
- Shovill `adv.depth`: `100` — subsample reads down to 100x target coverage before assembly.
- Shovill `adv.mincov`: `2` — minimum contig coverage to keep.
- Shovill `adv.minlen`: `0` — no minimum contig length filter at this stage.
- Shovill `adv.namefmt`: `contig%05d` — zero-padded contig names (contig00001, contig00002, …).
- Shovill `adv.keep_files.nocorr`: `yes_correction` and `keepfiles: true` — keep intermediate files and run the post-assembly correction step.
- Shovill `log`: `true` — emit the stdout log as an output.
- Bandage Image: `output_format: svg`, `width: 1000`, `height: 1000` — vector graph plot.
- Bandage Info: default (non-TSV) tabular output with graph-level stats.
- ToolDistillator: configured for the `shovill` tool section so it parses Shovill contigs, contig graph and BAM outputs.

## Test data
The workflow ships a test profile driven by two adapter-trimmed paired-end FASTQ files hosted on Zenodo record 11485346 (`fastp_trimmed_R1.fastqsanger.gz` and `fastp_trimmed_R2.fastqsanger.gz`). A successful run is expected to produce: a Shovill contigs FASTA whose first record is `>contig00001` (zero-padded naming confirms Shovill ran to completion), a Shovill assembly graph containing `KC:i` depth tags, a Shovill log ending with `[shovill] Done.`, Bandage graph statistics as a 2-column table including a `Total length orphaned nodes (bp):` row, and a ToolDistillator summary JSON referencing the `shovill_contigs_fasta` asset and containing at least `contig00146`, indicating the test sample assembles into ~150 contigs.

## Reference workflow
Galaxy IWC — `workflows/genome-assembly/bacterial-genome-assembly` ("Bacterial Genome Assembly using Shovill"), release 2.0.1, GPL-3.0-or-later, maintained by the ABRomics consortium. Key tool versions: shovill 1.1.0+galaxy2, bandage 2022.09+galaxy2/4, tooldistillator 1.0.4+galaxy0.
