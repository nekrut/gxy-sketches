---
name: agent-based-industrial-revolution-simulation
description: "Use when you need to run parameter sweeps of a NetLogo agent-based model\
  \ (ABM) of the first industrial revolution (or a similarly structured NetLogo model)\
  \ in parallel batches and produce economic-parameter plots. Not a bioinformatics\
  \ analysis \u2014 pick this only for NetLogo/BehaviorSpace-style ABM experiments\
  \ driven by a values spreadsheet and an XML experiment template."
domain: other
organism_class:
- not-applicable
input_data:
- netlogo-model
- netlogo-experiment-xml
- variable-values-table
source:
  ecosystem: nf-core
  workflow: nf-core/spinningjenny
  url: https://github.com/nf-core/spinningjenny
  version: dev
  license: MIT
  slug: spinningjenny
tools:
- name: netlogo
- name: xmlmod
- name: r
- name: multiqc
tags:
- agent-based-model
- netlogo
- simulation
- parameter-sweep
- economics
- industrial-revolution
- non-bioinformatics
test_data: []
expected_output: []
---

# Agent-based simulation of the industrial revolution (NetLogo)

## When to use this sketch
- You have a NetLogo `.nlogo` model (e.g. the Industrial-Revolution model) and want to sweep parameter combinations across many replicate runs in parallel.
- You have an XML BehaviorSpace-style experiment template describing step count and initial values, plus a tab-separated values table listing the variables to vary.
- You want the pipeline to auto-generate per-batch XML input files, execute NetLogo headlessly, and emit R-based plots of economic output parameters.
- Non-bioinformatics use case: this is an ABM simulation workflow, not a sequencing analysis.

## Do not use when
- The task is any kind of sequencing / omics analysis — none of the domain-specific sketches (variant-calling, rna-seq, assembly, metagenomics, etc.) apply here, and neither does this one.
- You want to run a different ABM framework (Mesa, Repast, MASON). This sketch is NetLogo-specific.
- You only need a single NetLogo run with no parameter sweep — use NetLogo directly, the pipeline overhead is unjustified.
- You need full BehaviorSpace statistics rather than the fixed R plotting step built into this pipeline.

## Analysis outline
1. Read the variables spreadsheet (`--input`, tab-separated, 4 columns, no header) describing which model parameters to vary and over what ranges.
2. `xlmMod` expands the XML experiment template (`--template`) into one XML per batch, splitting replications into `--batches` chunks so they run in parallel.
3. Execute the NetLogo model (`--nlogo`) headlessly for each generated XML batch, collecting per-run output tables.
4. Aggregate results and draw plots of economic parameters via an R script.
5. Emit a MultiQC-style run report and the standard nf-core `pipeline_info/` artefacts under `--outdir`.

## Key parameters
- `--input` — path to the TSV values spreadsheet (must match `^\S+\.txt$`); 4 columns, no header, one row per varied variable.
- `--template` — path to the XML experiment template (`^\S+\.xml$`) defining step count and base variable values.
- `--nlogo` — path to the NetLogo model file (`^\S+\.nlogo$`).
- `--batches` — integer, default `1`. Set to `ceil(total_replications / max_cpus_per_job)` so each batch fits on one worker.
- `--outdir` — absolute output directory (required).
- `-profile` — pick one of `docker`, `singularity`, `conda`, etc.; use `test` for the bundled CI profile.
- Resource caps: `--max_cpus` (default 16), `--max_memory` (default `128.GB`), `--max_time` (default `240.h`).

## Test data
The `test` profile points at three small files hosted on `nf-core/test-datasets` (branch `spinningjenny`): a truncated values spreadsheet `values_spreadsheet_ci.txt`, an XML experiment template `template_netlogo_industrial_15_ci.xml`, and the NetLogo model `Industrial-Revolution.nlogo`. It caps resources to 2 CPUs / 6 GB / 6 h and writes to `small_out/`. A `test_full` profile swaps in the non-`_ci` variants of the spreadsheet and template and allows 8 CPUs / 12 GB, writing to `full_out/`. Expected outputs: per-batch NetLogo result tables, R-generated plots of the simulated economic parameters, a MultiQC HTML report, and the standard `pipeline_info/` directory (execution report, timeline, trace, DAG, `params.json`).

## Reference workflow
nf-core/spinningjenny (version `dev`, MIT) — https://github.com/nf-core/spinningjenny. Companion paper: Visonà & Riccetti, "Simulating the Industrial Revolution: A History-Friendly Model" (SSRN 4418148, 2023). Underlying engine: NetLogo (Wilensky, 1999; https://ccl.northwestern.edu/netlogo/). Plotting via R (https://www.r-project.org/).
