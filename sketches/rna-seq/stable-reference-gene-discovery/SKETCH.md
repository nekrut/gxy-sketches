---
name: stable-reference-gene-discovery
description: Use when you need to identify the most stably expressed genes in a species
  (e.g. to pick RT-qPCR reference/housekeeping genes) by aggregating multiple public
  and/or user-supplied RNA-seq and microarray expression datasets and ranking genes
  by stability across conditions.
domain: rna-seq
organism_class:
- eukaryote
input_data:
- species-name
- public-expression-accessions
- count-matrix-csv
- experimental-design-csv
source:
  ecosystem: nf-core
  workflow: nf-core/stableexpression
  url: https://github.com/nf-core/stableexpression
  version: dev
  license: MIT
tools:
- expression-atlas
- ncbi-geo
- gprofiler
- scikit-learn
- normfinder
- genorm
- multiqc
- dash-plotly
tags:
- reference-genes
- housekeeping-genes
- rt-qpcr
- stability
- expression-atlas
- geo
- microarray
- rnaseq
- normalisation
- meta-analysis
test_data: []
expected_output: []
---

# Stable reference gene discovery across expression datasets

## When to use this sketch
- User wants to select RT-qPCR reference / housekeeping genes for a specific species and (optionally) specific conditions.
- User wants to aggregate many public expression datasets (EBI Expression Atlas and/or NCBI GEO microarray) for a species and score genes by cross-dataset stability.
- User has their own RNA-seq raw counts and/or pre-normalised microarray matrices and wants to combine them with public data to find invariant genes.
- User just wants to bulk-download Expression Atlas / GEO accessions for a species (with optional keyword filtering) without running the stability analysis.
- Any eukaryote supported by Expression Atlas / g:Profiler (plants, vertebrates, fungi, etc.); species is passed as genus + species string.

## Do not use when
- You need standard differential expression between conditions from FASTQ reads — use a dedicated bulk RNA-seq quantification + DE sketch (e.g. nf-core/rnaseq-based workflows), not this meta-analysis pipeline.
- You want to quantify transcripts from raw FASTQ for a single experiment — this pipeline consumes count matrices, not reads.
- You are looking for stable features in single-cell data — use a single-cell sketch instead.
- You want to call variants, assemble genomes, or annotate — wrong domain entirely.
- You need prokaryote-specific reference gene selection from custom qPCR assays without any transcriptome-wide expression data.

## Analysis outline
1. **Fetch accessions** — query EBI Expression Atlas for the species (optionally filtered by `--keywords` using nltk stemming); optionally also query NCBI GEO microarray (`--fetch_geo_accessions`, experimental). Honours `--accessions` / `--excluded_accessions` include/exclude lists.
2. **Download datasets** — pull raw/normalised count matrices and experimental designs from Expression Atlas and GEO; merge with any user-supplied datasets from `--datasets` CSV/YAML.
3. **Clean + map gene IDs** — clean gene ID strings, then map to a common namespace (Ensembl `ENSG` by default) via g:Profiler; drop unmappable genes. Optional custom `--gene_id_mapping` / `--gene_metadata` overrides.
4. **Filter rare genes** — remove genes below `--min_occurrence_quantile` and `--min_occurrence_freq` frequency across datasets.
5. **Filter poor samples** — drop samples exceeding `--max_zero_ratio` / `--max_null_ratio`.
6. **Normalise expression** — RNA-seq raw counts to TPM (needs GFF or `--gene_length`) or CPM via `--normalisation_method`; each dataset then quantile-normalised independently with scikit-learn `quantile_transform` to a uniform or normal target distribution.
7. **Merge datasets** — concatenate all normalised matrices into a single gene × sample dataframe.
8. **Impute missing values** — scikit-learn imputer chosen by `--missing_value_imputer` (iterative, knn, or gene_mean).
9. **Per-gene statistics** — compute mean, CV, RCVM, etc. overall and per platform (RNA-seq vs microarray).
10. **Candidate selection + stability scoring** — bin genes into `--nb_sections` expression-level sections, pick top `--nb_candidates_per_section` low-CV candidates per bin, then run scalable reimplementations of NormFinder and GeNorm (skippable with `--skip_genorm`); combine with weighted `--stability_score_weights` (NormFinder, GeNorm, CV, RCVM).
11. **Report** — aggregate ranked gene stability table, build a MultiQC report, and emit a Dash Plotly app for interactive per-gene/per-sample inspection.

## Key parameters
- `--species` (required): genus + species, e.g. `"arabidopsis thaliana"` / `homo_sapiens` / `"drosophila melanogaster"`.
- `--outdir` (required): results directory.
- `--keywords`: comma-separated free-text filter for Expression Atlas / GEO (e.g. `"leaf,stress"`); matched with nltk stemming.
- `--datasets`: CSV/YAML of user-supplied count datasets with columns `counts,design,platform,normalised`; `platform` ∈ {`rnaseq`, `microarray`}. Microarray must already be normalised (RMA recommended when mixing with public data).
- `--skip_fetch_eatlas_accessions`: disable automatic Expression Atlas query (use when providing your own accessions/datasets only).
- `--fetch_geo_accessions`: enable the experimental NCBI GEO microarray fetch (off by default).
- `--accessions` / `--accessions_file` / `--excluded_accessions[_file]`: whitelist/blacklist specific Expression Atlas / GEO IDs.
- `--platform`: restrict public fetch to `rnaseq` or `microarray`.
- `--accessions_only` / `--download_only`: early-exit stages for just collecting accessions or raw downloads.
- `--normalisation_method`: `tpm` (default, needs gene lengths) or `cpm`. Supply `--gff` or `--gene_length` if automatic annotation fetch fails or species is non-standard.
- `--quantile_norm_target_distrib`: `uniform` (default) or `normal`.
- `--missing_value_imputer`: `iterative` (default) / `knn` / `gene_mean`.
- `--skip_id_mapping` / `--gene_id_mapping` / `--gene_metadata` / `--gprofiler_target_db` (`ENSG` default): control gene ID harmonisation.
- `--min_occurrence_quantile` (0.2), `--min_occurrence_freq` (0.1): rare-gene filters.
- `--max_zero_ratio` (0.9), `--max_null_ratio` (0.9), `--max_null_ratio_valid_sample` (0.75): sample filters.
- `--nb_sections`, `--nb_candidates_per_section`: control candidate binning for scoring.
- `--skip_genorm`: drop GeNorm from the score (NormFinder only).
- `--stability_score_weights`: comma-separated weights for NormFinder,GeNorm,CV,RCVM (e.g. `0.5,0.5,0.0,0`).
- `--random_sampling_size` / `--random_sampling_seed`: cap and seed random subsampling for species with huge public catalogues (prevents OOM / 137 exits).
- `--target_genes` / `--target_gene_file`: flag genes of interest in the final report.

## Test data
The `test` profile runs with only `species = 'beta vulgaris'` and `outdir = results/test`; it fetches the (small) real Expression Atlas catalogue for sugar beet live from EBI and exercises the full accession-fetch → download → normalise → score → report path on whatever minimal set of public datasets is available. The `test_full` profile runs the same end-to-end flow against the full Expression Atlas catalogue for `arabidopsis_thaliana` as a scalability check. Expected outputs for a successful run are a populated `multiqc/multiqc_report.html`, a stability-ranked gene table at `dash_app/data/all_genes_summary.csv`, merged imputed counts at `dash_app/data/all_counts.imputed.parquet`, and the raw downloaded matrices under `public_data/expression_atlas/datasets/`. No local golden files are shipped; correctness is judged by the pipeline completing and emitting these artefacts.

## Reference workflow
nf-core/stableexpression (dev, nf-core template 3.5.1; Nextflow ≥ 25.04.0) — https://github.com/nf-core/stableexpression. Combines EBI Expression Atlas + NCBI GEO downloads with g:Profiler ID mapping, scikit-learn normalisation/imputation, and scalable NormFinder + GeNorm implementations, reported via MultiQC and a Dash Plotly app.
