---
name: single-cell-proximity-network-assay
description: Use when processing Pixelgen Proximity Network Assay (PNA) sequencing
  data to generate single-cell protein abundance and protein interactomics (PXL) datasets
  from paired-end Illumina reads. Produces per-cell graphs, spatial proximity scores,
  and 3D layouts for downstream interactome visualization.
domain: single-cell
organism_class:
- eukaryote
input_data:
- short-reads-paired
- pna-panel
- pna-design
source:
  ecosystem: nf-core
  workflow: nf-core/pixelator
  url: https://github.com/nf-core/pixelator
  version: 3.0.1
  license: MIT
  slug: pixelator
tools:
- name: pixelator
- name: pixelatores
- name: fastp
- name: cutadapt
tags:
- pna
- proximity-network-assay
- pixelgen
- protein-interactome
- single-cell-proteomics
- pxl
test_data: []
expected_output: []
---

# Single-cell Proximity Network Assay (PNA) processing

## When to use this sketch
- You have Illumina paired-end FASTQ files produced by a Pixelgen Technologies Proximity Network Assay (PNA) kit (e.g. `proxiome-immuno-155-v2`).
- You need to turn raw PNA reads into per-sample PXL files containing single-cell protein abundance, protein–protein proximity scores, and graph layouts.
- The experiment uses a known PNA design (e.g. `pna-2`) and a matching panel file (predefined name or custom CSV) that corresponds to the kit lot.
- You want standard QC + amplicon reconstruction + demux + UMI collapse + graph construction + denoise + spatial analysis + 3D layout + a combined Proxiome Experiment Summary HTML report.

## Do not use when
- The data is Molecular Pixelation (MPX), not PNA — use the legacy nf-core/pixelator 2.3.1 MPX sketch instead.
- You have generic single-cell RNA-seq (10x, Smart-seq, etc.) — use a scRNA-seq sketch.
- You only need bulk antibody-derived tag / CITE-seq quantification — this pipeline is specific to the PNA graph-based interactome model.
- You need to call SNVs/indels, assemble genomes, or do metagenomics — unrelated domains.

## Analysis outline
1. Build full-length amplicons from R1+R2 with quality, polyG, low-complexity UMI, and LBS filters (`pixelator single-cell-pna amplicon`).
2. Assign reads to marker groups via antibody barcodes and partition into parquet chunks (`pixelator single-cell-pna demux`).
3. Error-correct UMIs and collapse duplicate molecules into an edge list (`pixelator single-cell-pna collapse`).
4. Construct the component graph, recover multiplets via Leiden community detection, and emit a PXL file (`pixelator single-cell-pna graph`).
5. Denoise component graphs by trimming over-expressed markers in the one-core layer (`pixelator single-cell-pna denoise`).
6. Compute spatial statistics: proximity scores, k-core summaries, SVD variance explained (`pixelator single-cell-pna analysis`).
7. Generate 3D graph layouts (default `wpmds_3d`) for visualization (`pixelator single-cell-pna layout`).
8. Aggregate per-sample metrics into a Proxiome Experiment Summary HTML via `pixelatores`.

## Key parameters
- `input`: samplesheet CSV with columns `sample,sample_alias,condition,design,panel,fastq_1,fastq_2` (use `panel_file` for custom panels; `panel` and `panel_file` are mutually exclusive).
- `design`: pixelator assay design name, e.g. `pna-2` (must match the kit).
- `panel` / `panel_file`: must match the kit lot version, e.g. `proxiome-immuno-155-v2`.
- `pna_amplicon_quality_cutoff`: default `20`; `pna_amplicon_mismatches`: `0.1` (fraction of LBS length).
- `pna_demux_mismatches`: `1` (0–2); `pna_demux_strategy`: `independent` (default) or `paired`.
- `pna_collapse_algorithm`: `directional` (default) or `cluster`; `pna_collapse_mismatches`: `2`.
- `pna_graph_multiplet_recovery`: `true`; `pna_graph_component_size_min_threshold`: `8000` (lower, e.g. `100`, for small test datasets).
- `pna_graph_initial_stage_leiden_resolution`: `1`; `pna_graph_refinement_stage_leiden_resolution`: `0.01`.
- `pna_analysis_proximity_nbr_of_permutations`: `100`; `pna_analysis_compute_k_cores`: `true`.
- `pna_layout_layout_algorithm`: `wpmds_3d` (default) or `pmds_3d`.
- Skip toggles: `skip_denoise`, `skip_analysis`, `skip_layout`, `skip_experiment_summary`.
- Intermediate retention: `save_all`, plus per-stage `save_pna_*` flags.
- Containers: only `docker` or `singularity` profiles are supported (conda is disabled in 3.0.1).

## Test data
The `test` profile uses a small PNA samplesheet from `nf-core/test-datasets` (branch `pixelator`) at `samplesheet/pna/samplesheet_pna.csv`, with FASTQs resolved relative to `testdata/pna/`. Samples are configured with `design=pna-2` and a matching PNA immuno panel. Because the inputs are tiny, the profile lowers `pna_graph_component_size_min_threshold` to `100` so small components are retained, and the experiment summary is run in `test_mode=TRUE`. A successful run produces, per sample, a `<sample>.layout.pxl` (the most complete PXL including graph+analysis+layout), a `<sample>.qc-report.html` interactive QC report, and a top-level `experiment_summary.html` aggregating all samples, plus the usual `pipeline_info/` Nextflow reports.

## Reference workflow
nf-core/pixelator v3.0.1 (https://github.com/nf-core/pixelator), PNA track only. MPX data must use release 2.3.1.
