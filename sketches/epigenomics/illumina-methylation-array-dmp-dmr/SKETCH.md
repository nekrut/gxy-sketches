---
name: illumina-methylation-array-dmp-dmr
description: Use when you need to analyze DNA methylation data from Illumina BeadChip
  arrays (450K/EPIC) starting from raw IDAT files, to perform QC, normalization, probe
  filtering, cell composition adjustment, and identify differentially methylated positions
  (DMPs) and regions (DMRs) between sample groups.
domain: epigenomics
organism_class:
- human
- vertebrate
- diploid
input_data:
- illumina-idat-red-green
- sample-metadata-csv
source:
  ecosystem: nf-core
  workflow: nf-core/methylarray
  url: https://github.com/nf-core/methylarray
  version: dev
  license: MIT
  slug: methylarray
tools:
- name: minfi
- name: DNAmCrosshyb
- name: ChAMP
- name: dmpFinder
- name: FastQC
  version: 0.12.1
- name: MultiQC
tags:
- methylation
- epigenetics
- illumina
- epic
- 450k
- dmp
- dmr
- idat
- array
test_data: []
expected_output: []
---

# Illumina methylation array DMP/DMR analysis

## When to use this sketch
- Input data are Illumina Infinium methylation BeadChip IDAT files (paired Red + Grn per sample), typically EPIC or 450K.
- Human samples where you want an end-to-end pipeline: IDAT ingest, QC, normalization, probe filtering, and differential methylation calling.
- You want to identify differentially methylated positions (DMPs), regions (DMRs), and optionally large DMR blocks between two or more sample groups.
- You need cell-type composition correction (e.g. whole-blood samples) and/or batch effect adjustment before DM calling.
- You want automatic removal of cross-reactive probes, SNP-overlapping probes, and sex-chromosome probes to reduce bias.

## Do not use when
- Your methylation data come from bisulfite sequencing (WGBS, RRBS, EM-seq) — use a bisulfite-sequencing / methylation-calling sketch instead, not this array-based sketch.
- You have Oxford Nanopore or PacBio long-read modified-base calls — use a long-read modification-calling sketch.
- You only have beta-value matrices without raw IDATs — this pipeline expects raw Red/Grn IDAT input via minfi.
- Non-human arrays or species without a supported BSgenome build for DNAmCrosshyb cross-reactive probe mapping.
- You only need raw QC of methylation arrays with no differential analysis — a lightweight minfi QC script is sufficient.

## Analysis outline
1. Read sample sheet (sample_id, idat_red, idat_green, optional group) and load IDATs with `minfi`.
2. Run raw-read QC with `FastQC` and aggregate with `MultiQC`.
3. Normalize intensities with minfi `preprocessQuantile` or `preprocessFunnorm` and compute beta/M-values.
4. Remove cross-reactive / multi-mapping probes using `DNAmCrosshyb::map_probes()` against a bisulfite-converted reference genome.
5. Annotate and drop SNP-overlapping probes via minfi SNP annotation utilities.
6. Optionally drop probes on sex chromosomes (X/Y) using EPIC/450K annotation.
7. Optionally identify and drop probes confounded by covariates (e.g. age) with `dmpFinder`.
8. Optionally adjust for cell-type composition with `ChAMP::champ.refbase` (reference-based deconvolution, tuned for whole blood).
9. Optionally adjust for batch effects on the filtered matrix.
10. Call DMPs and DMRs (and optional DMR blocks) between groups using `ChAMP` + `minfi` functions.
11. Collate results and generate a final `MultiQC` report.

## Key parameters
- `input`: CSV samplesheet with columns `sample_id,idat_red,idat_green[,group]`; `group` is required for DMP/DMR calling.
- `sample_metadata`: extra per-sample covariates CSV for confounder checks and batch/cell adjustment.
- `bs_genome_version`: BSgenome build used by DNAmCrosshyb, default `hg38`.
- `bs_genome_path`: path to the bisulfite-converted reference produced by DNAmCrosshyb utility scripts.
- `remove_xreactive` (default true) + `xreactive_chr_targets` (default `all`): cross-reactive probe filtering scope.
- `remove_snp_probes` (default true): drop SNP-overlapping probes.
- `remove_sex_chromosomes` (default true): drop chrX/chrY probes.
- `remove_confounding_probes` (default true): drop probes associated with nuisance covariates.
- `adjust_cell_composition` (default true): run ChAMP refbase deconvolution and correction.
- `adjust_batch_effect` (default true): correct for technical batches.
- `find_dmps` / `find_dmrs` (default true) and `find_blocks` (default false): which differential outputs to compute.
- `run_optional_steps` (default true): master switch for the filtering/adjustment optional steps.
- `methylarray_deps_container`: container image bundling minfi, ChAMP, DNAmCrosshyb and R dependencies.

## Test data
The pipeline ships a `test` profile pointing at a small IDAT samplesheet derived from GEO series GSE43976 (hosted on the `ajandria/test-datasets` `methylarray` branch) together with an extended per-sample metadata CSV. A larger `test_full` profile uses the same GSE43976-derived full-size samplesheet against hg38 with `bs_genome_version=hg38`, `remove_xreactive=true`, and `adjust_cell_composition=false`. Running either profile is expected to produce per-sample FastQC reports, a MultiQC HTML summary, normalized/filtered methylation matrices, and tables of DMPs and DMRs (plus optional DMR blocks) written under `--outdir`, alongside the standard nf-core `pipeline_info/` run reports.

## Reference workflow
nf-core/methylarray (version `dev`, template 3.5.1), https://github.com/nf-core/methylarray — original author Adrian Janucik, wrapping DNA methylation array scripts by Ghada Nouairia.
