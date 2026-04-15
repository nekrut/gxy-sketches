---
name: long-read-de-novo-assembly-flye
description: Use when you need to assemble a genome de novo from long sequencing reads
  (Oxford Nanopore or PacBio non-HiFi) using Flye, producing a polished contig FASTA
  plus assembly graph and QC reports. Suitable for small to medium genomes including
  bacteria and small eukaryotes.
domain: assembly
organism_class:
- bacterial
- eukaryote
- haploid
input_data:
- long-reads-ont
- long-reads-pacbio
source:
  ecosystem: iwc
  workflow: Genome assembly with Flye
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/genome-assembly/assembly-with-flye
  version: '0.4'
  license: MIT
  slug: genome-assembly--assembly-with-flye
tools:
- name: flye
  version: 2.9.6+galaxy0
- name: quast
  version: 5.3.0+galaxy1
- name: fasta-stats
  version: '2.0'
- name: bandage
  version: 2022.09+galaxy4
tags:
- long-read
- nanopore
- pacbio
- de-novo
- assembly
- ont
- genome-graph
test_data: []
expected_output:
- role: flye_assembly_consensus
  description: Content assertions for `Flye assembly (consensus)`.
  assertions:
  - 'has_text: >contig_1'
  - 'has_size: {''min'': ''80k'', ''max'': ''86k''}'
- role: flye_assembly_assembly_graph
  description: Content assertions for `Flye assembly (assembly_graph)`.
  assertions:
  - 'has_text: digraph {'
  - 'has_n_lines: {''min'': 20, ''max'': 24}'
- role: flye_assembly_graphical_fragment_assembly
  description: Content assertions for `Flye assembly (Graphical Fragment Assembly)`.
  assertions:
  - 'has_text: edge_1'
  - 'has_n_lines: {''min'': 6, ''max'': 8}'
- role: flye_assembly_assembly_info
  description: Content assertions for `Flye assembly (assembly_info)`.
  assertions:
  - 'has_text: seq_name'
- role: quast_html_report
  description: 'Content assertions for `Quast: HTML report`.'
  assertions:
  - 'has_size: {''min'': ''250k'', ''max'': ''400k''}'
- role: flye_assembly_statistics
  description: Content assertions for `Flye assembly statistics`.
  assertions:
  - 'has_text: Scaffold L50'
- role: bandage_image_assembly_graph_image
  description: 'Content assertions for `Bandage Image: Assembly Graph Image`.'
  assertions:
  - 'has_size: {''min'': ''30k'', ''max'': ''50k''}'
---

# Long-read de novo genome assembly with Flye

## When to use this sketch
- You have raw long reads from Oxford Nanopore (nano-raw, nano-corr, nano-hq) or PacBio (pb-raw, pb-corr) and want a de novo draft assembly.
- Target is a single isolate genome (bacterial, archaeal, small eukaryote, or organelle) rather than a community.
- You want a one-shot pipeline that produces contigs, an assembly graph (GFA) visualization, and basic assembly QC (Quast + fasta stats).
- No reference genome is available or desired as input; assembly is reference-free.

## Do not use when
- Reads are PacBio HiFi and you need the best possible contiguity — prefer a Hifiasm-based assembly sketch (e.g. VGP Hifiasm workflows).
- Input is a metagenomic sample — use a metagenome-assembly sketch with `--meta` mode or dedicated metaFlye/metaSPAdes workflow.
- You only have short Illumina reads — use a short-read assembler sketch (SPAdes/Unicycler).
- You need polishing with short reads, scaffolding, or annotation — chain this sketch with a downstream polishing/annotation sketch.
- You need haplotype-resolved diploid assembly — use a haplotype-aware assembler sketch.

## Analysis outline
1. Provide raw long reads as a single FASTA/FASTQ (optionally gzipped) dataset.
2. Run **Flye** in `--nano-raw` mode (change to match your read type) to produce `consensus` FASTA, `assembly_graph` (dot), `assembly_gfa` (GFA1), and `assembly_info` tabular.
3. Run **Quast** on the Flye consensus to generate an HTML assembly report.
4. Run **Fasta Statistics** on the consensus to produce a tabular summary (N50, scaffold L50, etc.).
5. Render the GFA graph as a JPEG with **Bandage Image** for visual inspection of assembly topology.

## Key parameters
- Flye `mode`: `--nano-raw` (default in workflow). Switch to `--nano-corr`, `--nano-hq`, `--pacbio-raw`, `--pacbio-corr`, or `--pacbio-hifi` to match input read chemistry.
- Flye `iterations`: `1` polishing iteration (default). Increase for noisier reads.
- Flye `meta`: `false` — single-isolate mode; set true only for metagenomes (prefer a different sketch).
- Flye `keep_haplotypes`: `false`; `scaffold`: `false`; `plasmids`: `false`.
- Quast `assembly.type`: `genome`; `large`: `true` (large-genome mode enabled); `min_contig`: `500`; no reference supplied (`use_ref: false`).
- Bandage Image `output_format`: `jpg`, `height`: `1000`.

## Test data
The workflow ships with a single gzipped FASTQ (`Input_reads.fastqsanger.gz`, SHA-1 `18f30f2a901e027bb3b8e9d99a102b15c2648477`) representing a tiny long-read dataset. Running end-to-end should yield: a Flye consensus FASTA of ~80–86 kb containing `>contig_1`; an assembly graph dot file (20–24 lines, starting with `digraph {`); a GFA file (6–8 lines) containing `edge_1`; an `assembly_info` tabular with the `seq_name` header; a Quast HTML report between 250 kB and 400 kB; a Fasta Statistics tabular containing `Scaffold L50`; and a Bandage JPEG image between 30 kB and 50 kB.

## Reference workflow
Galaxy IWC `workflows/genome-assembly/assembly-with-flye` — “Genome assembly with Flye”, release 0.4 (2025-10-06). Tools: Flye 2.9.6+galaxy0, Quast 5.3.0+galaxy1, Fasta Statistics 2.0, Bandage Image 2022.09+galaxy4.
