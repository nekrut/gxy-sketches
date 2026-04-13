---
name: sra-manifest-to-concatenated-fastqs
description: Use when you need to bulk-download raw sequencing reads from NCBI SRA
  given a run selector manifest (or any tabular with run IDs and sample names) and
  produce per-sample FASTQ collections, automatically concatenating multiple runs
  that belong to the same biosample/experiment. Produces separate paired-end and single-read
  output collections relabelled by sample name.
domain: other
organism_class:
- any
input_data:
- sra-run-manifest-tabular
source:
  ecosystem: iwc
  workflow: sra_manifest_to_concatenated_fastqs_parallel
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/data-fetching/sra-manifest-to-concatenated-fastqs
  version: '0.9'
  license: MIT
tools:
- fasterq-dump
- sra-tools
- split_file_to_collection
- concatenate_multiple_datasets
- map_param_value
- compose_text_param
tags:
- sra
- data-fetching
- fastq
- download
- ncbi
- run-selector
- galaxy
- iwc
test_data: []
expected_output:
- role: single_output
  description: Content assertions for `single_output`.
  assertions:
  - 'GSM461176.-: has_size: {''value'': 139000000, ''delta'': 10000000}'
  - 'GSM461179-ID: has_size: {''value'': 298000000, ''delta'': 30000000}'
---

# SRA manifest to concatenated per-sample FASTQs

## When to use this sketch
- You have a list of SRA run accessions (e.g. SRR/ERR/DRR) from NCBI SRA Run Selector and need the raw FASTQ data in Galaxy.
- Multiple sequencing runs belong to the same biological sample and you want them merged into a single per-sample FASTQ (or R1/R2 pair) before downstream analysis.
- You want the output collection elements labelled with a human-readable column from the manifest (BioSample, Experiment, Sample Name, GSM, etc.) rather than raw run IDs.
- You need both paired-end and single-read outputs handled in one pass, since the manifest may mix layouts.
- You are staging data for a downstream pipeline (RNA-seq, variant calling, ChIP-seq, scRNA, etc.) and this sketch is the data-ingest prelude.

## Do not use when
- You already have local FASTQ files — skip straight to the relevant analysis sketch.
- You only need a handful of runs and no concatenation — use the simpler `fasterq-dump` tool directly instead of this workflow.
- You need to download from ENA/DDBJ by URL rather than from SRA via the toolkit — use a generic URL/FTP fetcher.
- You need 10x/long-read specific extraction modes (e.g. `--include-technical`, barcode handling) — the single-cell and long-read ingest sketches are better fits.
- Your input is not a tabular with a header line listing run IDs and sample IDs in columns.

## Analysis outline
1. Accept a tabular SRA manifest (with header) plus two integer parameters: the column number holding the SRA run ID and the column number holding the desired sample identifier.
2. Normalise the run-ID column parameter (Map parameter value: map `0` → `1`, the SRA Run Selector default).
3. Build a column selector string (`c<run>,c<sample>`) with Compose text parameter.
4. `Cut` those two columns out of the manifest to obtain a two-column run→sample mapping.
5. `Find and replace` (regex) to sanitise sample names — any char outside `[a-zA-Z0-9_\- .,]` becomes `-` — and to build a `run\trun___sample` relabel table.
6. `Cut` again to get a single run-ID column, then `Split file to collection` to emit one one-line file per run (keeping the header), producing a list collection keyed by run ID.
7. `Faster Download and Extract Reads in FASTQ` (fasterq-dump, `--split-3`, `skip_technical=true`, defline `@$sn/$ri`) runs one job per run ID in parallel, emitting a paired collection and a single-read collection.
8. `Relabel identifiers` on both the paired and single collections using the `run\trun___sample` table (non-strict) so each element becomes `run___sample`.
9. `Apply rules` to restructure: split the identifier on `___` to build a nested paired list keyed by sample (outer) and run (inner), then repeat for the single-read collection.
10. `Concatenate multiple datasets` on each restructured collection — by strand for the paired collection, plain concat for the singles — producing two final per-sample output collections named `Concatenated paired-end` and `Concatenated Single-read`.

## Key parameters
- `SRA_manifest`: tabular file with a header line; SRA Run Selector export is the canonical source.
- `Column number with SRA ID`: integer, `1` for SRA Run Selector manifests. `0` is auto-remapped to `1`.
- `Column number with final identifier`: integer; typical SRA Run Selector choices are `6` (BioSample), `16` (Experiment), `36` (Sample Name); arbitrary user manifests may use any column (the bundled test uses `22`).
- fasterq-dump: `split=--split-3`, `skip_technical=true`, `seq_defline=@$sn/$ri` — do not change unless you know you need technical reads.
- Sample-name sanitisation regex: `[^\w\- .,\t]` → `-` (English alphanumerics, underscore, dash, space, dot, comma only).
- Concatenate multiple datasets: `paired_cat_type=by_strand` for the paired branch, `input_type=singles` for the single branch, `headers=0`.

## Test data
The IWC test drives the workflow with a tabular manifest `SRA.txt` (SHA-1 `9b267d141fe2b577d6096ac5573a72b86abc33ba`) containing runs from GEO series that map to samples GSM461176–GSM461179 (the classic *Drosophila* pasilla RNA-seq dataset). It sets `Column number with SRA ID = 1` and `Column number with final identifier = 22`. The expected `paired_output` collection has elements `GSM461177-` (forward ≈294 MB, reverse ≈307 MB) and `GSM461178___a` (forward ≈178 MB, reverse ≈205 MB); the expected `single_output` collection has elements `GSM461176.-` (≈139 MB) and `GSM461179-ID` (≈298 MB). Assertions are on byte sizes with ±10–30 MB deltas — they verify that per-run FASTQs were fetched, relabelled, and correctly concatenated per sample, and that paired vs single layouts were routed to the right output collection.

## Reference workflow
Galaxy IWC `workflows/data-fetching/sra-manifest-to-concatenated-fastqs`, workflow `sra_manifest_to_concatenated_fastqs_parallel`, release 0.9 (2026-04-09), MIT. Upstream: https://github.com/galaxyproject/iwc/tree/main/workflows/data-fetching/sra-manifest-to-concatenated-fastqs
