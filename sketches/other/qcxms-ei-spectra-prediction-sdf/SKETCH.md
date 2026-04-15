---
name: qcxms-ei-spectra-prediction-sdf
description: Use when you need to predict in silico electron ionization (EI) mass
  spectra for small organic molecules starting from a 3D SDF structure (e.g. a PubChem
  conformer) using the QCxMS quantum-chemical fragmentation simulator. Produces an
  MSP-format predicted spectrum suitable for library matching in untargeted metabolomics
  or GC-MS identification workflows.
domain: other
organism_class:
- small-molecule
input_data:
- sdf-3d-structure
source:
  ecosystem: iwc
  workflow: QCxMS Spectra Prediction from SDF
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/metabolomics/qcxms-sdf
  version: '0.3'
  license: MIT
  slug: metabolomics--qcxms-sdf
tools:
- name: openbabel
  version: 3.1.1+galaxy2
- name: qcxms
  version: 5.2.1+galaxy7
- name: xtb
tags:
- metabolomics
- mass-spectrometry
- ei-ms
- gc-ms
- in-silico-spectra
- qcxms
- xtb
- cheminformatics
- spectral-library
test_data: []
expected_output:
- role: predicted_spectra
  description: Content assertions for `Predicted Spectra`.
  assertions:
  - 'has_n_lines: {''min'': 30, ''max'': 50}'
---

# QCxMS EI mass spectrum prediction from an SDF structure

## When to use this sketch
- You have a small organic molecule (or a handful) as a 3D SDF file, typically downloaded from PubChem with pre-generated conformers, and need a predicted EI-MS fragmentation spectrum.
- You are building or augmenting a GC-EI-MS spectral library for compounds lacking experimental reference spectra, or trying to rationalize observed fragment peaks via quantum-chemical molecular dynamics.
- You want a physics-based (QCxMS + GFN2-xTB) prediction rather than a rule-based fragmenter, and can tolerate the heavy CPU cost of a full neutral + production trajectory run.
- The target ionization is 70 eV electron ionization as used in classical GC-MS.

## Do not use when
- You need electrospray / CID / HCD tandem MS predictions — QCxMS has a separate positive/negative-ion CID mode; this sketch covers only the neutral EI workflow.
- You only have a 2D SMILES with no conformer — generate 3D coordinates first (e.g. RDKit/OpenBabel `gen3d`) and then enter this sketch.
- You want fast, heuristic spectrum prediction across thousands of compounds — prefer CFM-ID or similar ML/rule-based predictors; QCxMS is orders of magnitude slower.
- The task is processing experimental LC-MS/GC-MS raw data (peak picking, alignment, annotation) rather than predicting spectra from structures.
- The molecule is a metal complex, polymer, or system outside GFN2-xTB's reliable chemical space.

## Analysis outline
1. Ingest a 3D SDF file containing one or more molecules with conformers (e.g. from PubChem).
2. Convert SDF to XYZ Cartesian coordinates with Open Babel (`openbabel_compound_convert`, oformat `xyz`, canonical SMILES appended as property).
3. Run `qcxms_neutral_run` to equilibrate the neutral molecule and emit the three QCxMS coordinate/control files (`coord`, `start`, `xyz`) needed for production.
4. Run `qcxms_production_run` on the three coordinate artifacts to launch the molecular-dynamics fragmentation trajectories and collect per-trajectory `res` files.
5. Run `qcxms_getres` with the original molecule and the collected `res` files to aggregate trajectories into a predicted EI spectrum and emit an MSP-format file.

## Key parameters
- QCxMS neutral run (`qcxms_neutral_run`):
  - `QC_Level: xtb2` — GFN2-xTB as the quantum-chemical method (default, well balanced for organics).
  - `keywords.tmax: 5` — maximum simulation time per trajectory (ps). Dominant cost knob.
  - `keywords.tinit: 500` — initial temperature (K) for equilibration.
  - `keywords.ieeatm: 0.6` — internal excess energy per atom (eV) modelling the 70 eV ionization impact.
  - `keywords.tstep: 0.5` — MD integration step (fs).
  - `keywords.etemp: 5000` — electronic temperature (K) for SCF convergence of hot fragments.
  - `keywords.ntraj`: left unset → QCxMS default (scales with heavy-atom count); raise for better statistics, lower for quick tests.
- QCxMS production run: takes the three linked outputs (`in_file`, `start_file`, `xyz_file`) from the neutral run unchanged; `store_extended_output: false` keeps only `res` files.
- QCxMS get results: consumes the original converted XYZ (`mol`) plus the collected `res_files` to bin fragment m/z into an MSP spectrum.

## Test data
The workflow ships with a single small-molecule test case: one SDF file (`Input SDF File.sdf`, SHA-1 `bf1965b6…`) containing a 3D structure with pre-generated conformers, analogous to a PubChem 3D download. Running the full pipeline end-to-end is expected to yield one `Predicted Spectra` MSP file whose content has between 30 and 50 lines — i.e. a compact MSP record with a header block and a few dozen predicted m/z / intensity peaks. No numerical peak-list golden file is shipped; the assertion is purely structural (line-count bounds) because trajectory-based predictions are non-deterministic at the intensity level.

## Reference workflow
Galaxy IWC `workflows/metabolomics/qcxms-sdf` — *QCxMS Spectra Prediction from SDF*, release 0.3 (RECETOX; Helge Hecht). Tool stack: `openbabel_compound_convert 3.1.1+galaxy2`, `qcxms_neutral_run 5.2.1+galaxy7`, `qcxms_production_run 5.2.1+galaxy5`, `qcxms_getres 5.2.1+galaxy4`. Upstream method: QCxMS (https://github.com/recetox/qcxms).
