---
name: protein-ligand-complex-parameterization-gromacs
description: Use when you need to prepare a protein-ligand complex for GROMACS molecular
  dynamics by generating matched GRO coordinate and TOP topology files. Parameterizes
  the protein with a standard biomolecular force field and the small-molecule ligand
  with GAFF/AM1-BCC charges, then merges them into a single complex. Intended as a
  preprocessing step before solvation, energy minimization, equilibration, and production
  MD (including MMGBSA or dcTMD free-energy workflows).
domain: other
organism_class:
- other
input_data:
- protein-pdb
- ligand-sdf
source:
  ecosystem: iwc
  workflow: Create GRO and TOP complex files
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/computational-chemistry/protein-ligand-complex-parameterization
  version: 0.1.4
  license: MIT
  slug: computational-chemistry--protein-ligand-complex-parameterization
tools:
- name: openbabel
  version: 3.1.1+galaxy0
- name: rdkit
- name: gromacs
- name: ambertools-antechamber
  version: 21.10+galaxy0
- name: ambertools-acpype
  version: 21.10+galaxy0
- name: gmx_merge_topology_files
  version: 3.4.3+galaxy0
tags:
- molecular-dynamics
- gromacs
- parameterization
- protein-ligand
- force-field
- gaff
- amber
- computational-chemistry
- md-setup
test_data: []
expected_output:
- role: complex_gro
  path: expected_output/complex.gro
  description: Expected output `Complex GRO` from the source workflow test.
  assertions: []
- role: complex_topology
  path: expected_output/complex.top
  description: Expected output `Complex topology` from the source workflow test.
  assertions: []
---

# Protein-ligand complex parameterization for GROMACS

## When to use this sketch
- User has a protein structure (PDB, apo form with ligand/cofactor/waters already stripped) and a small-molecule ligand (SDF) and needs GROMACS-ready `.gro` coordinate and `.top` topology files for the complex.
- User is setting up a GROMACS molecular dynamics simulation of a non-covalent protein-ligand complex and needs consistent parameterization (protein force field + GAFF for ligand).
- User wants a preprocessing subworkflow before solvation, minimization, equilibration, production MD, MMGBSA, or dcTMD pulling experiments.
- Ligand protonation state needs to be assigned from a given pH (or can be skipped if the SDF is already prepared).

## Do not use when
- You only need to parameterize the protein (no ligand) — run GROMACS initial setup (`gmx pdb2gmx`) directly instead.
- The ligand is a standard amino acid, nucleotide, or ion already covered by the protein force field — no GAFF/antechamber step is required.
- You want to run the actual MD simulation (minimization, NVT/NPT, production) — this sketch stops at parameterization; chain it into a GROMACS simulation/MMGBSA/dcTMD workflow afterwards.
- The ligand is covalently bound to the protein, or is a metal/organometallic complex — GAFF + AM1-BCC will not give meaningful parameters; use QM/MM or specialized tooling.
- You need CHARMM-GUI-style parameters or a non-GROMACS engine (AMBER, NAMD, OpenMM native) — the outputs here are GROMACS-format only.

## Analysis outline
1. Convert the ligand SDF to PDB at a target pH using Open Babel (`openbabel_compound_convert`), adding hydrogens consistent with the chosen protonation state.
2. Compute the ligand formal charge with RDKit descriptors (`ctb_rdkit_descriptors`), then extract it as an integer parameter (Cut + `param_value_from_file`) to feed downstream charge assignment.
3. Filter the converted ligand PDB to HETATM records only using a grep step, giving Antechamber a clean ligand-only input.
4. Parameterize the ligand with AmberTools Antechamber (`ambertools_antechamber`) using GAFF atom types and AM1-BCC charges (`at=gaff`, `c=bcc`, residue name `UNL`), passing the computed net charge.
5. Generate GROMACS-format ligand topology and coordinates with ACPYPE (`ambertools_acpype`), reusing the user-supplied net charge (`charge_method=user`, `atomtype=gaff`, `multiplicity=1`), producing ligand `.itp` and `.gro`.
6. Run GROMACS initial setup (`gmx_setup`, wrapping `gmx pdb2gmx`) on the apoprotein PDB with the chosen protein force field and water model, producing protein `.top`, `.gro`, and a position-restraints `.itp`.
7. Merge protein and ligand topologies/coordinates with `gmx_merge_topology_files` into a single complex `.top` and `.gro`, renamed `Complex topology` and `Complex GRO`.

## Key parameters
- `pH` (Open Babel): float used to assign ligand protonation. Set to `-1.0` to skip protonation adjustment and keep the SDF as supplied.
- `Force field` (gmx_setup): protein force field; must be one of `oplsaa`, `amber03`, `amber94`, `amber96`, `amber99`, `amber99sb`, `amberGS`, `charmm27`, `gromos43a1/2`, `gromos45a3`, `gromos53a5/6`, `gromos54a7`. Test profile uses `amber99sb`.
- `Water model` (gmx_setup): one of `tip3p`, `tip4p`, `tips3p`, `tip5p`, `spc`, `spce`, `none`. Must be compatible with the chosen protein force field (e.g. `tip3p` with AMBER). Test profile uses `tip3p`.
- Ligand atom type: fixed to `gaff` in both Antechamber and ACPYPE — do not change; the workflow assumes GAFF for the small molecule regardless of the protein force field.
- Ligand charge method: Antechamber `c=bcc` (AM1-BCC); ACPYPE `charge_method=user` so the net charge from RDKit is trusted rather than recomputed.
- Ligand residue name: `UNL` (Antechamber `resname`) — downstream MD analyses should reference this residue name.
- Ligand multiplicity: `1` (closed-shell singlet) — the workflow does not support radicals.
- RDKit descriptor: `FormalCharge` only; this integer is reused for both Antechamber `-nc` and ACPYPE charge, so the input SDF must have correct formal charges assigned.

## Test data
The source test profile supplies two files from `test-data/`: `mpro.pdb`, an apo SARS-CoV-2 main protease PDB with ligand/cofactor/waters removed, and `lig.sdf`, a small-molecule inhibitor in SDF format. Runtime parameters are `Force field = amber99sb` and `Water model = tip3p`; `pH` is left at its default (`-1.0`, skip re-protonation). Running the workflow is expected to produce two named outputs — `Complex GRO` (matching `test-data/complex.gro` exactly) and `Complex topology` (matching `test-data/complex.top` with up to 16 lines of diff allowed, since topology files include a date/version header). A position-restraints `.itp` from `gmx_setup` is also surfaced as a workflow output.

## Reference workflow
Galaxy IWC — `workflows/computational-chemistry/protein-ligand-complex-parameterization` ("Create GRO and TOP complex files"), release 0.1.4, MIT-licensed. Built on Galaxy tools `openbabel_compound_convert` 3.1.1, `ctb_rdkit_descriptors` 2020.03.4, `gmx_setup` 2021.3 (GROMACS), `ambertools_antechamber` 21.10, `ambertools_acpype` 21.10, and `gmx_merge_topology_files` 3.4.3. Designed by the Galaxy ComputeChem team as a reusable subworkflow for GROMACS MMGBSA and dcTMD pipelines.
