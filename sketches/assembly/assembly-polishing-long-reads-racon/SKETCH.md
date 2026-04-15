---
name: assembly-polishing-long-reads-racon
description: Use when you have a draft long-read genome assembly (PacBio CLR, PacBio
  HiFi, or Oxford Nanopore) and want to improve base-level accuracy by polishing it
  with the same long reads via four iterative rounds of minimap2+Racon. Produces a
  polished consensus FASTA.
domain: assembly
organism_class:
- eukaryote
- bacterial
input_data:
- long-reads-ont
- long-reads-pacbio
- draft-assembly-fasta
source:
  ecosystem: iwc
  workflow: Assembly polishing with long reads
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/genome-assembly/polish-with-long-reads
  version: '0.1'
  license: MIT
  slug: genome-assembly--polish-with-long-reads
tools:
- name: minimap2
  version: 2.26+galaxy0
- name: racon
  version: 1.5.0+galaxy1
tags:
- polishing
- long-reads
- racon
- minimap2
- consensus
- nanopore
- pacbio
- hifi
test_data: []
expected_output:
- role: assembly_polished_by_long_reads_using_racon
  path: expected_output/assembly_polished_by_long_reads.fasta
  description: Expected output `Assembly polished by long reads using Racon` from
    the source workflow test.
  assertions: []
---

# Assembly polishing with long reads (Racon x4)

## When to use this sketch
- You already have a draft assembly (contigs) produced from long reads and want to improve base accuracy before annotation or downstream analysis.
- Your reads are Oxford Nanopore (`map-ont`), PacBio CLR (`map-pb`), or PacBio HiFi (`map-hifi`) and you can feed them back over the contigs for consensus correction.
- You want a simple, deterministic polishing step that runs four iterations of minimap2 + Racon without requiring short reads or a reference genome.
- Works on bacterial, eukaryotic, or viral de novo assemblies — ploidy-agnostic, since Racon operates on local consensus.

## Do not use when
- You only have short reads — use a short-read polishing sketch (Pilon/NextPolish with bwa-mem2) instead.
- You want hybrid polishing combining long + short reads — prefer a Medaka-then-Pilon or Polypolish-based sketch.
- You need methylation-aware or neural-network polishing for ONT data — use Medaka directly rather than Racon.
- You still need to *produce* the assembly — use a long-read assembler sketch (Flye, Canu, hifiasm) first; this sketch assumes contigs already exist.
- You need variant calls against a reference, not a polished consensus — use a long-read variant-calling sketch.

## Analysis outline
1. Map long reads to the draft assembly with **minimap2** using the preset matching the read type; output PAF overlaps.
2. Run **Racon** with the reads, PAF overlaps, and draft assembly to produce polished assembly 1.
3. Re-map the same long reads to polished assembly 1 with minimap2; run Racon again → polished assembly 2.
4. Repeat minimap2 + Racon on polished assembly 2 → polished assembly 3.
5. Repeat minimap2 + Racon on polished assembly 3 → polished assembly 4 (final output, renamed `Racon_long_reads_polished_assembly.fasta`).

## Key parameters
- `minimap2 preset` (`-x`): **`map-ont`** for Nanopore, **`map-pb`** for PacBio CLR, **`map-hifi`** for PacBio HiFi. This is the only per-run parameter the workflow exposes.
- `minimap2 output_format`: `paf` (required input format for Racon).
- `minimap2 no_end_flt`: `true` (disable end filtering, matches workflow default).
- `racon error_threshold` (`-e`): `0.3`.
- `racon quality_threshold` (`-q`): `10.0`.
- `racon window_length` (`-w`): `500`.
- `racon match / mismatch / gap`: `3 / -5 / -4`.
- `racon include_unpolished`: `false` (drop unpolished sequences from output).
- Iteration count: **4 rounds** of minimap2 + Racon (fixed in the workflow).

## Test data
The source workflow ships with two inputs under `test-data/`: a draft `assembly.fasta` and a gzipped long-read FASTQ (`long_reads.fastqsanger.gz`), with the `minimap setting (for long reads)` parameter set to `map-ont` (i.e. Oxford Nanopore). Running the workflow is expected to produce a single polished consensus FASTA (`assembly_polished_by_long_reads.fasta`), which the test compares against a golden file using a size-similarity check (`compare: sim_size`, `delta_frac: 0.2`) rather than exact content, because Racon's iterative polishing can yield small deterministic differences between environments.

## Reference workflow
Galaxy IWC — `workflows/genome-assembly/polish-with-long-reads/Assembly-polishing-with-long-reads.ga`, release 0.1 (2023-07-15). Tools: minimap2 `2.26+galaxy0`, Racon `1.5.0+galaxy1`. Author: Anna Syme. License: MIT.
