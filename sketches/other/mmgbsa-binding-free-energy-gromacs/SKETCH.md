---
name: mmgbsa-binding-free-energy-gromacs
description: Use when you need to estimate protein-ligand binding free energies using
  MM-GBSA with an ensemble of short GROMACS molecular dynamics simulations. Input
  is an apoprotein PDB and a small-molecule ligand SDF; output is an ensemble-averaged
  MMGBSA free energy.
domain: other
organism_class:
- protein-ligand-complex
input_data:
- protein-pdb
- ligand-sdf
source:
  ecosystem: iwc
  workflow: MMGBSA calculations with GROMACS
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/computational-chemistry/gromacs-mmgbsa
  version: 0.1.8
  license: MIT
tools:
- gromacs
- ambertools
- antechamber
- acpype
- parmed
- mmpbsa.py
- openbabel
- rdkit
- mdtraj
tags:
- molecular-dynamics
- mmgbsa
- binding-free-energy
- drug-discovery
- computational-chemistry
- gromacs
- amber
test_data: []
expected_output: []
---

# MM-GBSA binding free energy with GROMACS ensemble MD

## When to use this sketch
- You have a prepared apoprotein structure (PDB) and one small-molecule ligand (SDF) and want an estimate of the protein-ligand binding free energy.
- You want to run an ensemble of short MD replicas in GROMACS and post-process the trajectories with AmberTools MMPBSA.py in GB mode.
- You need a ligand parameterized with GAFF (via antechamber/acpype) and a protein parameterized with a standard AMBER/CHARMM/GROMOS/OPLS force field.
- You are screening or re-scoring a known binding pose rather than searching for one.

## Do not use when
- You need docking or pose prediction from scratch — use a docking workflow instead; this sketch assumes the ligand is already placed in the binding site of the input PDB.
- You want rigorous alchemical free energies (FEP/TI/BAR) — MM-GBSA is an end-point approximation and much less accurate.
- You need MM-PBSA (Poisson-Boltzmann) rather than GB; this sketch fixes `calctype=gb` (igb=5).
- Your system is a membrane protein, nucleic acid, or metalloprotein that needs special parameterization — GAFF+standard protein FF will not be adequate.
- You want long, single-replica production MD for conformational sampling — use a plain GROMACS MD workflow.

## Analysis outline
1. Ligand preprocessing: compute formal charge with RDKit Descriptors and protonate/convert SDF to PDB with OpenBabel at the requested pH.
2. Protein setup: run `gmx pdb2gmx` (GROMACS initial setup) with the chosen force field and water model to produce protein `.top`/`.gro` and position-restraint `.itp`.
3. Ligand parameterization: antechamber (GAFF atom types, BCC-like charges from user formal charge) then acpype to generate ligand `.itp` and `.gro`.
4. Merge protein and ligand topologies into a single complex `.top` and `.gro`.
5. Build simulation box with `gmx editconf` (triclinic, 1.0 nm padding), solvate and add neutralizing Na+/Cl- ions at the requested salt concentration (`gmx solvate`).
6. Energy minimization with `gmx mdrun` (steep, 50000 steps, emtol=1000).
7. Generate an ensemble by replicating the NVT→NPT→production chain N times (driven by the "Number of simulations" parameter and `split_file_to_collection`).
8. For each replica: NVT equilibration, NPT equilibration, then production MD (all `gmx mdrun`, 300 K, PME, 1 fs step, Verlet, h-bond constraints in equilibration, none in production).
9. Convert GROMACS topology + coordinates to AMBER `prmtop` files for ligand, receptor, complex and solvated complex via ParmEd (`parmconv`) using `mbondi` radii and strip masks to separate components.
10. Convert XTC trajectories to NetCDF with MDTraj for AmberTools compatibility.
11. Run MMPBSA.py in GB mode (`igb=5`, `saltcon=0.1`) over the trajectory frames to get per-replica ΔG_bind.
12. Aggregate: grep `DELTA TOTAL` lines across replicas, collapse to a table and compute Summary Statistics → ensemble-averaged MMGBSA free energy.

## Key parameters
- Force field: one of `oplsaa`, `amber99sb`, `amber03`, `charmm27`, `gromos54a7`, … (protein only; ligand always uses GAFF).
- Water model: one of `tip3p`, `tip4p`, `tips3p`, `tip5p`, `spc`, `spce`, `none`.
- pH: float; set to `-1.0` to skip OpenBabel protonation of the ligand.
- Salt concentration: float in mol/L (e.g. `0.1`), passed to `gmx solvate` with `-neutral`.
- Number of simulations: integer size of the MD ensemble averaged for the final ΔG.
- NVT / NPT / production steps: integer md_steps (step length 0.001 ps = 1 fs; temperature 300 K).
- MD settings (hardcoded): Verlet cutoffs, PME electrostatics, rcoulomb=rlist=rvdw=1.0 nm, write_freq=1000.
- Energy minimization: `integrator=steep`, `md_steps=50000`, `emtol=1000.0`, `emstep=0.01`.
- Antechamber: `at=gaff`, `c=bcc`, `resname=UNL`, net charge from RDKit formal charge.
- parmconv strip masks — receptor: `:NA,CL,SOL,UNL`; ligand: `!:UNL`; complex: `:NA,CL,SOL`; solvated complex: empty; radii: `mbondi`.
- MMPBSA.py: `calctype=gb`, `igb=5`, `saltcon=0.1`, `surfoff=0.0`, `probe=1.4`, `startframe=1`, `interval=10`, `strip_mask=:NA,CL,SOL`, entropy off.

## Test data
The workflow ships with a tiny smoke test using the SARS-CoV-2 main protease (`test-data/mpro.pdb`) as the apoprotein and a single small-molecule ligand (`test-data/lig.sdf`). Test parameters use `amber99sb` + `tip3p`, salt 0.1 M, 2 replicas, and deliberately tiny MD lengths (50 NVT / 50 NPT / 100 production steps) so the whole chain runs in minutes. Expected outputs: the `MMGBSA free energy` summary table has 2 lines (header + mean row), each per-replica `MMGBSA statistics` file contains the strings `DELTA TOTAL` and `Generalized Born ESURF calculated using LCPO`, and per-replica `XTC files` are ~138900 bytes (±500).

## Reference workflow
Galaxy IWC `workflows/computational-chemistry/gromacs-mmgbsa` — "MMGBSA calculations with GROMACS", release 0.1.8, authored by Simon Bray (MIT license). Uses GROMACS 2022 (`chemteam/gmx_*`), AmberTools 21.10 (`ambertools_antechamber`, `ambertools_acpype`, `parmconv`, `mmpbsa_mmgbsa`), OpenBabel 3.1.1, RDKit 2020.03, and MDTraj 1.9.x.
