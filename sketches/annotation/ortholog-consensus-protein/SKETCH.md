---
name: ortholog-consensus-protein
description: Use when you need to compile a consensus ortholog list for one or more
  query proteins by reconciling predictions from multiple public orthology databases
  (OMA, PANTHER, OrthoInspector, EggNOG). Accepts UniProt accessions or protein FASTA
  as input and produces per-query ortholog lists, agreement statistics, and an HTML
  report.
domain: annotation
organism_class:
- eukaryote
input_data:
- protein-uniprot-id
- protein-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/reportho
  url: https://github.com/nf-core/reportho
  version: 1.1.0
  license: MIT
tools:
- oma
- panther
- orthoinspector
- eggnog
- diamond
- uniprot
- multiqc
tags:
- orthology
- orthologs
- comparative-genomics
- consensus
- protein
- uniprot
- report
test_data: []
expected_output: []
---

# Ortholog consensus for query proteins

## When to use this sketch
- You have one or a handful of query proteins (given as UniProt accessions or FASTA sequences) and want a high-confidence ortholog list.
- You want to compare predictions across multiple orthology resources (OMA, PANTHER, OrthoInspector, EggNOG) and build a consensus with explicit agreement scoring.
- You need agreement statistics (pairwise Jaccard, consensus fraction, privates, goodness) and a human-readable HTML report per query.
- Your queries are eukaryotic proteins with good public annotation (bacteria/archaea are possible with custom OrthoInspector version; viral genes are unsupported).
- You want the option to run fully offline against local database snapshots for batch processing.

## Do not use when
- You need to *compute* orthogroups de novo from assembled proteomes — use an orthology inference pipeline (e.g. OrthoFinder-based workflows), not this reporter.
- You are doing phylogenomics / species-tree reconstruction from orthogroups — use a phylogenomics sketch.
- Your input is nucleotide reads or genomes without protein annotation — annotate first, then supply UniProt IDs or protein FASTA.
- You want functional enrichment or GO-term analysis of orthologs — this pipeline only produces the ortholog lists.

## Analysis outline
1. **Query identification** — resolve each input (UniProt ID or FASTA) to a canonical UniProt accession and NCBI taxon ID; for FASTA, OMA is used to find the closest annotated homolog.
2. **Ortholog fetching** — query each enabled database (OMA, PANTHER, OrthoInspector, EggNOG) via API or local snapshot and collect per-database ortholog lists.
3. **Sequence fetching** — retrieve protein sequences for all reported ortholog IDs from UniProt, RefSeq, Ensembl, and OMA (skipped if `--skip_merge`).
4. **Identifier merging** — cluster sequences with `diamond cluster` to unify synonymous IDs across databases into one entity.
5. **Scoring & filtering** — build a combined score table (score = number of supporting databases); emit per-threshold lists (`minscore_1..N`), a `centroid` list (highest-agreement source), and a final `filtered_hits` list.
6. **Plotting & statistics** — generate support barplots, Venn diagrams, pairwise Jaccard tile plots, and per-query stats (consensus %, privates %, goodness).
7. **Report generation** — render a per-query React/HTML report plus a MultiQC summary across all samples.

## Key parameters
- `input`: CSV samplesheet with columns `id,query` (UniProt accession) *or* `id,fasta` (path to FASTA). UniProt takes precedence if both given.
- `use_all`: set `true` to enable every database source (mixes online + local as needed).
- `skip_oma` / `skip_panther` / `skip_orthoinspector` / `skip_eggnog`: disable individual sources. EggNOG is local-only.
- `local_databases`: `true` to use on-disk snapshots; then supply `oma_path`, `oma_uniprot_path`, `oma_ensembl_path`, `oma_refseq_path`, `panther_path`, `eggnog_path`, `eggnog_idmap_path`, `orthoinspector_path`.
- `offline_run`: `true` to skip online query identification (FASTA input is then disallowed).
- `orthoinspector_version`: default `Eukaryota2023`; change only for bacteria/archaea or reproducibility.
- `use_centroid`: pick the highest-agreement single source as the final list (overrides `min_score`).
- `min_score`: minimum supporting-database count for the final list (default `2`; test profile uses `3`).
- `min_identity` / `min_coverage`: Diamond clustering thresholds for ID merging (defaults `90` / `80`).
- `skip_merge`: skip sequence fetching + Diamond ID merging entirely (faster; less clean IDs).
- `skip_report` / `skip_orthoplots` / `skip_multiqc`: toggle downstream outputs for large batch runs.

## Test data
The bundled `test` profile points at the nf-core test-datasets `reportho` branch samplesheet (a small CSV of UniProt-ID queries such as BicD2 / HBB), runs with `skip_eggnog = true` and `min_score = 3`, and exercises the online database path. The `test_full` profile enables `use_all = true` with mini local snapshots for OMA-Ensembl / OMA-RefSeq and full EggNOG downloads. A successful run produces, per query: `seqinfo/*_id.txt` and `*_taxid.txt`, per-database `orthologs/<db>/*_group.csv`, a merged `score_table/*_score_table.csv`, threshold lists `filter_hits/*_minscore_*.txt` plus `*_centroid.txt` and `*_filtered_hits.txt`, plots (`*_supports.png`, `*_venn.png`, `*_jaccard.png`), `stats/*_stats.yml`, a per-sample HTML report in `*_dist/`, and a global `multiqc/multiqc_report.html`.

## Reference workflow
nf-core/reportho v1.1.0 — https://github.com/nf-core/reportho (MIT). Upstream docs: https://nf-co.re/reportho/1.1.0/docs/usage and https://nf-co.re/reportho/1.1.0/docs/output.
