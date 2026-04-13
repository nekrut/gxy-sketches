---
name: protein-sequence-annotation
description: 'Use when you have one or more protein FASTA files (e.g. predicted proteomes
  from different species) and need sequence-level annotations: conserved domains (Pfam/FunFam),
  functional signatures (InterProScan member databases), and predicted secondary structure,
  together with input QC stats.'
domain: annotation
organism_class:
- eukaryote
- bacterial
- viral
input_data:
- protein-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/proteinannotator
  url: https://github.com/nf-core/proteinannotator
  version: 1.0.0
  license: MIT
tools:
- seqfu
- seqkit
- hmmer
- pfam
- funfam
- interproscan
- s4pred
- multiqc
- aria2
tags:
- protein
- annotation
- domains
- interproscan
- pfam
- funfam
- secondary-structure
- proteome
test_data: []
expected_output: []
---

# Protein sequence annotation (domains, function, secondary structure)

## When to use this sketch
- You already have amino-acid FASTA files (one per species/sample) and want a unified per-protein annotation report.
- You need conserved-domain hits against Pfam and/or FunFam HMM libraries via `hmmsearch`.
- You need functional annotation via InterProScan member databases (Hamap, PANTHER, PIRSF, TIGRFAM, SFLD, etc.) producing GFF3/JSON/TSV/XML.
- You want predicted secondary structure (α-helix / β-strand / coil) from single-sequence input with s4pred.
- You want before/after QC stats on your input proteomes (length distributions, duplicate removal, gap/stop-codon cleanup).
- Multi-sample comparative annotation: several species or assembly versions submitted together via a samplesheet.

## Do not use when
- You have nucleotide contigs or raw reads and still need gene prediction — run a gene-calling / structural annotation pipeline (e.g. a prokka- or funannotate-style sketch) first, then feed its protein FASTA here.
- You only need protein-level QC without annotation — a lighter `seqkit stats` sketch suffices.
- You want orthology / gene family inference across species (use an OrthoFinder-based sketch instead).
- You want structure prediction from 3D folding (AlphaFold / ESMFold sketches), not just per-residue secondary-structure probabilities.
- You want to annotate variants, transcripts, or metagenomic reads — use the corresponding variant-calling, RNA-seq, or metagenomics sketches.

## Analysis outline
1. Parse samplesheet (`id,fasta`) — one row per protein FASTA (may be gzipped).
2. Input QC stats with **SeqFu** (per-sample `_before.tsv`, MultiQC-ready).
3. Preprocess sequences with **SeqKit**: remove gaps, upper-case, validate, filter by length, replace special characters (e.g. `/`), optionally remove duplicates; re-run SeqFu for `_after.tsv` stats.
4. Optionally download reference databases with **aria2** (Pfam HMM, FunFam HMM, InterProScan tarball) if local copies are not supplied.
5. Domain annotation with **HMMER `hmmsearch`** against Pfam-A and/or FunFam → per-sample `.domtbl.gz`.
6. Functional annotation with **InterProScan** against the selected member applications → per-sample `gff / json / tsv / xml`.
7. Secondary-structure prediction with **s4pred** (`run_model`) → per-sample `ss2` / `fas` / `horiz` per-residue probabilities.
8. Aggregate QC and tool outputs into a **MultiQC** HTML report plus `pipeline_info/` run reports.

## Key parameters
- `input`: CSV samplesheet with columns `id,fasta` (fasta may be `.fa[.gz]` or `.fasta[.gz]`).
- `outdir`: absolute path for results (required).
- QC / preprocessing:
  - `skip_preprocessing` (default `false`)
  - `min_seq_length: 30`, `max_seq_length: 5000` (passed to `seqkit seq --min-len/--max-len`)
  - `remove_duplicates_on_sequence: false` — set `true` to dedupe by sequence, not just ID.
- Domain annotation:
  - `skip_pfam`, `skip_funfam` (default `false`)
  - `pfam_db`, `funfam_db` — pre-downloaded HMM libraries; otherwise auto-downloaded from `pfam_latest_link` (Pfam-A current release) and `funfam_latest_link` (FunFam v4_3_0).
  - `hmmsearch_evalue_cutoff: 0.001` (passed as `-E`).
- Functional annotation:
  - `skip_interproscan: false`
  - `interproscan_db` — path to a pre-extracted InterProScan `data/` tree (strongly recommended; the default download is ~5.5 GB).
  - `interproscan_db_url` — default points at InterProScan 5.72-103.0.
  - `interproscan_applications: "Hamap,PANTHER,PIRSF,TIGRFAM,sfld"` — comma-separated member DBs.
  - `interproscan_enableprecalc: false` — enable to use UniProtKB precalculated matches for speed.
- Secondary structure:
  - `skip_s4pred: false`
  - `s4pred_outfmt: ss2` (one of `ss2`, `fas`, `horiz`).
- Execution: always pick a container profile (`-profile docker` / `singularity` / `conda`).

## Test data
The pipeline's `test` profile uses a tiny samplesheet of protein FASTA files hosted under `nf-core/test-datasets/proteinannotator/`, together with drastically downsized reference databases: a `Pfam-A_test.hmm.gz`, a `funfam-hmm3-v4_3_0_test.lib.gz`, and an `interproscan_test.tar.gz`, with `interproscan_applications` narrowed to `Hamap,TIGRFAM,sfld` so a full run completes inside 4 CPU / 15 GB / 1 h. Running it is expected to produce per-sample SeqFu before/after stats, a SeqKit-preprocessed FASTA, `domain_annotation/pfam/<id>.domtbl.gz` and `domain_annotation/funfam/<id>.domtbl.gz`, InterProScan `functional_annotation/interproscan/<id>/<id>.{gff,json,tsv,xml}`, s4pred per-residue predictions under `s4pred/<id>/ss2/<id>.ss2`, and a consolidated `multiqc/multiqc_report.html`. The `test_full` profile exercises the same wiring against a larger public samplesheet.

## Reference workflow
nf-core/proteinannotator v1.0.0 — <https://github.com/nf-core/proteinannotator> (DOI [10.5281/zenodo.18547735](https://doi.org/10.5281/zenodo.18547735)). Invoke with `nextflow run nf-core/proteinannotator -r 1.0.0 -profile <container> --input samplesheet.csv --outdir <OUTDIR>`.
