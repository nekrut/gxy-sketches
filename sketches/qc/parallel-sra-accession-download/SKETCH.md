---
name: parallel-sra-accession-download
description: Use when you need to download raw sequencing reads as FASTQ from SRA/ENA/DDBJ
  run accessions (SRR/ERR/DRR) in parallel, given a text file with one accession per
  line. Produces separate single-end and paired-end read collections. Use before any
  downstream QC, mapping, or assembly sketch when the user only has accession IDs.
domain: qc
organism_class:
- any
input_data:
- sra-accession-list
source:
  ecosystem: iwc
  workflow: Parallel Accession Download
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/data-fetching/parallel-accession-download
  version: 0.1.14
  license: MIT
  slug: data-fetching--parallel-accession-download
tools:
- name: fasterq-dump
  version: 3.1.1+galaxy0
- name: sra-tools
- name: split_file_to_collection
  version: 0.5.2
tags:
- sra
- ena
- fastq
- download
- data-fetching
- fasterq-dump
- accessions
- parallel
test_data: []
expected_output: []
---

# Parallel SRA accession download

## When to use this sketch
- User supplies a list of run accessions (SRR*, ERR*, DRR*) and needs the underlying FASTQ files before any analysis.
- The accession list is non-trivial (tens to hundreds of runs) and you want per-accession parallelism so one bad run does not block the rest.
- You need the result split cleanly into paired-end and single-end collections, ready to feed into a downstream workflow (QC, mapping, assembly, variant calling, etc.).
- Mixed single-end / paired-end accessions in the same input list are fine — they are routed to separate output collections.

## Do not use when
- You already have local FASTQ files — skip fetching entirely.
- You need to fetch assemblies, annotations, or reference genomes rather than raw reads — use a genome/reference fetching sketch instead.
- You want reads from ENA via direct FTP/Aspera URLs rather than SRA prefetch/fasterq-dump — use an ENA-fetch sketch.
- You need 10x Genomics-style per-cell barcoded FASTQs with technical reads preserved — this sketch sets `skip_technical=true` and `--split-3`, which is wrong for 10x; use a scRNA-specific fetch sketch.
- The user wants downstream analysis (alignment, variant calling, assembly) — use this only as a preparatory step, then hand off to the appropriate analysis sketch.

## Analysis outline
1. Accept a plain-text file of run accessions, one per line (`Input dataset`, datatype `txt`).
2. Split the file into a collection of single-accession files using `split_file_to_collection` with `chunksize=1`, so each accession becomes its own element — this is what creates the parallel fan-out.
3. For each element, run `fasterq-dump` (sra-tools) in list mode, which downloads and extracts FASTQ for that accession as its own Galaxy job.
4. Flatten the paired-end output via `Apply rules` into a list:paired collection tagged `name:PE`, keyed on the run accession with `forward`/`reverse` identifiers.
5. Flatten the single-end output via `Apply rules` into a flat list collection tagged `name:SE`, keyed on the run accession.

## Key parameters
- `split_file_to_collection.select_mode.mode`: `chunk`
- `split_file_to_collection.select_mode.chunksize`: `1`  (one accession per job — required for parallelism)
- `split_file_to_collection.select_ftype`: `txt`
- `fasterq_dump.input.input_select`: `file_list`  (reads accessions from the split file directly)
- `fasterq_dump.adv.split`: `--split-3`  (separates paired vs. unpaired reads)
- `fasterq_dump.adv.skip_technical`: `true`  (drops technical reads — do NOT use for 10x)
- `fasterq_dump.adv.seq_defline`: `@$sn/$ri`
- `Apply rules` (PE): map column 1 → `list_identifiers`, column 2 → `paired_identifier`; output tagged `name:PE`.
- `Apply rules` (SE): map column 1 → `list_identifiers`; output tagged `name:SE`.
- Workflow outputs exposed: `Paired End Reads`, `Single End Reads`. All intermediate datasets are hidden.

## Test data
The source workflow ships two Planemo tests. The first uses `input_accession_single_end.txt` (a single accession, `SRR044777`) and asserts that the `Single End Reads` collection contains an element `SRR044777` whose FASTQ contains the bytes in `SRR044777_head.fastq`. The second uses `input_accession_paired_end.txt` and asserts that the `Paired End Reads` collection contains an element `SRR11953971` with `forward` and `reverse` sub-elements matching `SRR11953971_1_head.fastq` and `SRR11953971_2_head.fastq` respectively (compared with `contains` after decompression). Both inputs are tiny text files validated by SHA-1 hash; the expected FASTQ fixtures are head-truncated reference slices, not full runs.

## Reference workflow
IWC `workflows/data-fetching/parallel-accession-download`, release `0.1.14` (Galaxy `.ga`, MIT). Key tool versions: `sra_tools/fasterq_dump 3.1.1+galaxy0`, `split_file_to_collection 0.5.2`.
