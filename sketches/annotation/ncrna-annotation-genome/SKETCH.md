---
name: ncrna-annotation-genome
description: "Use when you need to annotate non-coding RNA (ncRNA) loci \u2014 snRNA,\
  \ snoRNA, rRNA, tRNA, miRNA precursors, lncRNA, SRP RNA, Y RNA, RNase P, vault RNA,\
  \ ribozymes \u2014 on a genome assembly using Rfam covariance models and Infernal\
  \ cmsearch. Supports vertebrate, invertebrate, metagenomic, and generic eukaryotic\
  \ modes; produces GTF, GFF3, and BED outputs."
domain: annotation
organism_class:
- vertebrate
- invertebrate
- eukaryote
- metagenome
input_data:
- genome-fasta
- rfam-cm
- rfam-seed
source:
  ecosystem: nf-core
  workflow: nf-core/ncrnannotator
  url: https://github.com/nf-core/ncrnannotator
  version: dev
  license: MIT
  slug: ncrnannotator
tools:
- name: infernal
- name: cmsearch
- name: rfam
- name: multiqc
tags:
- ncrna
- rfam
- infernal
- cmsearch
- annotation
- gtf
- gff3
- bed
- snrna
- snorna
- rrna
- trna
test_data: []
expected_output: []
---

# Genome-level non-coding RNA annotation with Rfam/Infernal

## When to use this sketch
- User has a finished or draft genome assembly (FASTA) and wants a catalogue of ncRNA loci (snRNA, snoRNA, scaRNA, rRNA, tRNA, pre-miRNA, lncRNA, SRP RNA, Y RNA, RNase P, vault RNA, ribozymes).
- User wants Ensembl-style output in GTF/GFF3/BED ready for genome browsers or downstream pipelines.
- Target is a vertebrate, invertebrate, generic eukaryote, or a metagenomic assembly (including prokaryotic rRNA).
- User asks explicitly for Rfam/Infernal `cmsearch`-based ncRNA annotation.

## Do not use when
- You need to call variants, assemble reads, or quantify expression — this sketch only emits coordinates of ncRNA features, not sequence variants or counts.
- You need to annotate protein-coding genes — use a dedicated gene-annotation workflow; this sketch deliberately skips mRNA/CDS models.
- You want de novo ncRNA/lncRNA discovery from RNA-seq reads — use an RNA-seq assembly/quantification sketch instead.
- You only want tRNAs with full isotype/anticodon detail — a dedicated tRNAscan-SE workflow will give richer output than the Rfam tRNA family alone.
- Your input is short reads rather than an assembled genome — assemble first.

## Analysis outline
1. (Optional) Filter the full Rfam covariance-model database to a clade-specific accession list with `filter_rfam_cm` (skipped in `mgnify-assembly` and `full` modes).
2. Split the genome FASTA into fixed-size windows with the local `GENOME_CHUNK` module to enable parallel searching.
3. Run Infernal `cmsearch` on every chunk against the (filtered) Rfam covariance models.
4. Parse and consolidate all cmsearch tables with `parse_rfam_results`: reject overlapping hits and apply per-model Rfam GA (gathering) bit-score thresholds.
5. Convert surviving hits to Ensembl-style GTF, GFF3, and 6-column BED with `rfam_to_formats`, assigning biotypes from Rfam family/seed metadata.
6. Aggregate software versions and per-step metrics with MultiQC.

## Key parameters
- `--fasta` — genome assembly to annotate (plain or gzipped FASTA).
- `--mode` — annotation strategy, one of:
  - `ensembl-vertebrates` (curated vertebrate Rfam subset, 1 Mbp chunks) — default for vertebrates.
  - `ensembl-invertebrates` (curated invertebrate Rfam subset, 100 kbp chunks) — use for compact invertebrate genomes.
  - `mgnify-assembly` (full Rfam, no clade filtering, 50 Mbp chunks, keeps prokaryotic rRNA) — use for metagenomic assemblies.
  - `full` (full Rfam, 1 Mbp chunks, eukaryotic output only) — generic eukaryote, no clade restriction.
- `--rfam_cm` — `Rfam.cm` from the Rfam FTP CURRENT release; must be `cmpress`-indexed.
- `--rfam_seed` — matching `Rfam.seed`; used to derive biotype labels.
- `--rfam_accessions` — optional override for the bundled per-mode accession list (`assets/rfam_accessions/{mode}.txt`).
- `--chunk_size` — override of the mode-default chunk length in bp (minimum 1000); lower it for memory-constrained hosts.
- `--outdir` — required output directory; `annotation/` holds the GTF/GFF3/BED, `rfam/rfam_hits.tsv` holds the raw hit table.

Scoring: hits are filtered with Rfam per-family GA thresholds, not a user-supplied E-value cutoff. Do not invent `--evalue` or `--score` flags; they are not exposed.

## Test data
The bundled `test` profile runs entirely from files in `tests/data/` with no downloads. Input is `takifugu_chr1_500kb.fa` — the first 500 kbp of *Takifugu rubripes* chromosome 1 — annotated in `ensembl-vertebrates` mode against a 10-model Rfam subset (`rfam_test.cm` / `rfam_test.seed` covering RF00001/2/3/4/5/7/25/26/01960/02543, i.e. 5S rRNA, 5.8S rRNA, U1/U2/U4/U5 snRNA and related families). A successful run publishes `annotation/annotation.{gtf,gff3,bed}`, a consolidated `rfam/rfam_hits.tsv` with one row per surviving hit (seqname, start, end, strand, Infernal bit score, E-value, Rfam model name, accession, biotype), and a `multiqc/multiqc_report.html`. The full-size profile instead annotates a human chromosome-scale FASTA and expects the user to supply the full `Rfam.cm`/`Rfam.seed`.

## Reference workflow
nf-core/ncrnannotator (version `dev`, nf-core template 3.5.2). Upstream tools: Infernal `cmsearch` + Rfam 15 covariance models, with MultiQC for reporting.
