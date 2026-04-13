---
name: nanostring-ncounter-qc-normalization
description: Use when you have NanoString nCounter RCC files from a targeted gene-expression
  panel and need quality control, count normalization (housekeeping/GEO or GLM), per-sample
  annotation, optional gene-signature scoring (e.g. PLAGE, GSVA, singscore), and a
  MultiQC summary. Not for untargeted RNA-seq or single-cell data.
domain: rna-seq
organism_class:
- eukaryote
input_data:
- nanostring-rcc
- samplesheet-csv
source:
  ecosystem: nf-core
  workflow: nf-core/nanostring
  url: https://github.com/nf-core/nanostring
  version: 1.3.3
  license: MIT
tools:
- NACHO
- GSVA
- singscore
- MultiQC
- R
tags:
- nanostring
- ncounter
- rcc
- targeted-expression
- qc
- normalization
- gene-signature
- plage
- gsva
test_data: []
expected_output: []
---

# NanoString nCounter QC and normalization

## When to use this sketch
- Input is a set of NanoString nCounter `.RCC` files from a targeted codeset (endogenous + housekeeping + positive/negative controls).
- Goal is end-to-end QC, count normalization, annotated count tables, optional gene-signature scores, and a single MultiQC report.
- You want housekeeping-based normalization using NACHO (GEO by default, or GLM) and both HK-normalized and non-HK-normalized count matrices.
- You want to compute signature scores for one or more user-defined gene sets (e.g. MPAS) using PLAGE/GSVA/singscore/ssgsea/SAMS/mean/median, where the gene set is provided as a YAML file.
- You need a gene-count heatmap (all endogenous genes or a user-filtered subset) embedded in the MultiQC report.

## Do not use when
- Inputs are FASTQ from bulk RNA-seq (use an nf-core/rnaseq-based sketch instead).
- Inputs are single-cell or spatial data (e.g. 10x, Visium, CosMx imaging data — NanoString imaging platforms are not covered here).
- You need differential expression, survival modeling, or cohort statistics beyond gene-signature scoring and QC — this pipeline stops at normalized/annotated tables and scores.
- You need quantification from raw GeoMx DSP data or non-RCC NanoString outputs.

## Analysis outline
1. Parse samplesheet CSV (`RCC_FILE`, `RCC_FILE_NAME`, `SAMPLE_ID`, plus any extra metadata columns).
2. Quality control with NACHO (`bin/nacho_qc.R`): compute per-sample QC metrics, list detected housekeeping genes, produce `NanoQC.html` and `NanoQC_with_outliers.html`, and export MultiQC-ready tables/plots.
3. Normalize counts with NACHO (`bin/nacho_norm.R`) twice: once with housekeeping normalization (`housekeeping_norm=TRUE`) and once without, writing `*_normalized_counts.tsv` and `*_normalized_counts_wo_HKnorm.tsv`.
4. Annotate normalized tables (`bin/write_out_prepared_gex.R`) by joining samplesheet metadata, splitting endogenous vs housekeeping genes into `*_Norm_GEX_ENDO.tsv` / `*_Norm_GEX_HK.tsv` (for both HK-norm and wo-HK-norm variants).
5. Compute gene-signature scores from a user YAML via GSVA-family methods (`plage`, `plage.dir`, `GSVA`, `singscore`, `ssgsea`, `median`, `mean`, `sams`), checking each gene set against genes present in the codeset.
6. Render gene-count heatmaps for HK-normalized and wo-HK-normalized matrices, optionally restricted to a user-provided gene list.
7. Aggregate everything (QC tables, heatmaps, signature score tables) into a single MultiQC HTML report.

## Key parameters
- `input`: CSV samplesheet with required columns `RCC_FILE,RCC_FILE_NAME,SAMPLE_ID` plus arbitrary metadata.
- `outdir`: results directory (absolute path on cloud storage).
- `normalization_method`: `GEO` (default) or `GLM` — NACHO normalization backend.
- `gene_score_method`: default `plage.dir`; alternatives `plage`, `GSVA`, `singscore`, `ssgsea`, `median`, `mean`, `sams`. Directed PLAGE is the pipeline's recommendation for nCounter data.
- `gene_score_yaml`: YAML mapping `score_name: [GENE1, GENE2, ...]`; pipeline verifies genes exist in the codeset before scoring.
- `heatmap_id_column`: samplesheet column used for heatmap rows (default `SAMPLE_ID`); values must be unique.
- `heatmap_genes_to_filter`: YAML list of genes to restrict the heatmap to (default: all endogenous genes).
- `skip_heatmap`: boolean to disable heatmap generation.
- `-profile`: one of `docker`, `singularity`, `conda`, etc.; use `test` for the bundled minimal test profile.

## Test data
The `test` profile consumes a small samplesheet (`nanostring/samplesheets/samplesheet_test.csv`) from the nf-core test-datasets repo, pointing at a handful of public NanoString `.RCC` files with associated `SAMPLE_ID`s. Running `nextflow run nf-core/nanostring -profile test,docker --outdir results` exercises the full graph end-to-end and is expected to produce: per-sample normalized TSVs under `normalized_counts/` (with and without HK normalization), annotated ENDO/HK tables under `annotated_tables/`, NACHO QC artifacts under `QC/NACHO/` (including `NanoQC.html`, `NanoQC_with_outliers.html`, `hk_detected_mqc.txt`, `normalized_qc_mqc.txt`), gene-count heatmaps under `gene_heatmaps/`, and a final `multiqc/multiqc_report.html`. A `test_full` profile runs the same graph against a larger public samplesheet for AWS CI validation.

## Reference workflow
nf-core/nanostring v1.3.3 (MIT) — https://github.com/nf-core/nanostring. Cite Peltzer et al., *Bioinformatics* (2024), doi:10.1093/bioinformatics/btae019 and Canouil et al., *Bioinformatics* (2019), doi:10.1093/bioinformatics/btz647 for NACHO.
