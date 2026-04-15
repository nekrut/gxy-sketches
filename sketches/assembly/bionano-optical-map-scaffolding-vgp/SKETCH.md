---
name: bionano-optical-map-scaffolding-vgp
description: Use when you need to scaffold a contig-level genome assembly (typically
  a vertebrate or other large eukaryote) using Bionano Genomics optical map (CMAP)
  data as part of the VGP assembly pipeline. Takes a phased GFA contig assembly (e.g.
  from hifiasm) plus a Bionano CMAP and produces hybrid scaffolds with AGP, FASTA,
  and GFA outputs.
domain: assembly
organism_class:
- eukaryote
- vertebrate
- diploid
input_data:
- bionano-cmap
- contig-assembly-gfa
- genome-size-estimate
source:
  ecosystem: iwc
  workflow: Scaffolding-BioNano-VGP7
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/VGP-assembly-v2/Scaffolding-Bionano-VGP7
  version: 0.1.4
  license: CC-BY-4.0
  slug: VGP-assembly-v2--Scaffolding-Bionano-VGP7
tools:
- name: bionano_solve
- name: bionano_hybrid_scaffold
- name: gfastats
  version: 1.3.6+galaxy0
- name: ggplot2
  version: 3.4.0+galaxy1
tags:
- vgp
- scaffolding
- bionano
- optical-map
- hybrid-scaffold
- hifiasm
- long-read-assembly
test_data:
- role: bionano_data
  url: https://zenodo.org/records/10063794/files/Bionano%20Data.cmap?download=1
  sha1: adfb6481579e41f7e22a0862be2a9ac6f23e1615
  filetype: cmap
- role: estimated_genome_size_parameter_file
  url: https://zenodo.org/records/10063794/files/Estimated%20genome%20size%20-%20Parameter%20File.expression.json?download=1
  sha1: 387649fbac6ede96037bd8cf4a3d184645ce2d7b
  filetype: expression.json
- role: input_gfa
  url: https://zenodo.org/records/10063794/files/Input%20GFA.gfa1?download=1
  sha1: 9a7ae707193197354124d5d8fd71d3ab0ba4606d
  filetype: gfa1
expected_output:
- role: bionano_scaffolds_reconciliated_gfa
  description: 'Content assertions for `Bionano scaffolds reconciliated: gfa`.'
  assertions:
  - 'has_n_lines: {''n'': 67}'
- role: assembly_statistics_for_s1
  description: Content assertions for `Assembly Statistics for s1`.
  assertions:
  - "has_line: # scaffolds\t24"
- role: scaffolds_agp
  description: 'Content assertions for `Scaffolds: agp`.'
  assertions:
  - 'has_n_lines: {''n'': 50}'
- role: bionano_scaffolds_reconciliated_fasta
  description: 'Content assertions for `Bionano scaffolds reconciliated: fasta`.'
  assertions:
  - 'has_n_lines: {''n'': 390825}'
- role: nx_plot
  description: Content assertions for `Nx Plot`.
  assertions:
  - 'has_size: {''value'': 76000, ''delta'': 5000}'
---

# Bionano optical-map scaffolding (VGP)

## When to use this sketch
- You have a contig-level assembly in GFA1 format (typically from hifiasm or another long-read contigger) and want to upgrade it to scaffolds using Bionano Genomics optical map data.
- The target organism is a large eukaryote — this is stage 7 of the Vertebrate Genomes Project (VGP) assembly suite, downstream of contigging workflows 3/4/5.
- You have a Bionano CMAP file and know the enzyme used (default here: DLE-1 / CTTAAG) and an estimated genome size.
- You want the standard VGP hybrid-scaffold configuration plus QC (gfastats summary, Nx plot, cumulative size plot).

## Do not use when
- You are scaffolding with Hi-C reads — use a `hi-c-scaffolding-vgp` / YaHS / SALSA sketch instead.
- You only have a FASTA assembly without a GFA — first convert with `gfastats` to produce a GFA, or use a FASTA-native scaffolder.
- You still need to generate contigs — run an upstream VGP contigging workflow (hifiasm / HiFi + parental / trio) first.
- You need polishing, purging of haplotigs, or decontamination — those are separate VGP stages.
- Your organism is a small bacterial/haploid genome — Bionano hybrid scaffolding is overkill; use a lighter assembler+scaffolder pipeline.

## Analysis outline
1. Convert the input GFA1 contig assembly to FASTA with **gfastats** (manipulation mode).
2. Run **Bionano Hybrid Scaffold** on the FASTA + Bionano CMAP, with optional user-supplied conflict-resolution files, producing scaffold FASTA, non-scaffolded contig FASTA, an AGP, a conflicts report, and a results ZIP.
3. Reconcile the scaffolds back into a GFA with **gfastats** scaffolding mode, using the original GFA as the graph and the Bionano AGP as the path definition (`Bionano scaffolds reconciliated: gfa`).
4. Emit the reconciled scaffold FASTA (line length 60) with **gfastats** manipulation mode.
5. Parse the estimated genome size parameter file into an integer, then run **gfastats** in assembly-statistics mode on the reconciled GFA to compute N50, NG50, scaffold counts, etc.
6. Run a second **gfastats** pass in size-statistics mode to get per-scaffold sizes for plotting.
7. Clean the stats table with a find-and-replace (`#` → `Number of`) to produce `clean_stats`.
8. Via the `gfastats_data_prep` subworkflow (Sort → awk cumulative sum → Datamash absmax → Add column → compose path → Compute Mb columns), build a plotting table.
9. Render an **Nx plot** and a cumulative **Size plot** with **ggplot2 scatterplot** (lines geometry, bw theme, 7x7 in, 300 dpi).

## Key parameters
- Bionano Hybrid Scaffold `configuration`: `vgp` (VGP-tuned XML config).
- Bionano Hybrid Scaffold `enzyme`: `CTTAAG` (DLE-1); change if your sample used BssSI/BspQI/etc.
- `conflict_filter_genome`: `3`, `conflict_filter_sequence`: `3` (aggressive auto-resolution; override with a conflict-resolution file input for manual curation).
- `trim_cut_sites`: `true`, `zip_file`: `true`.
- gfastats statistics mode: `assembly` with `expected_genomesize` wired from the parsed parameter file (needed for NGx metrics).
- gfastats FASTA output `line_length`: `60`.
- ggplot2: `type_options: lines`, `theme: bw`, `xlab: "x"`/`Scaffold number`, `ylab: "Nx (Mb)"`/`Cumulative Size (Mb)`.

## Test data
The test job uses three inputs from Zenodo record 10063794: a Bionano optical-map `Bionano Data.cmap`, an `Estimated genome size - Parameter File` (expression.json holding a single integer), and an `Input GFA.gfa1` contig assembly. Running the workflow end-to-end is expected to yield a reconciled scaffold GFA of 67 lines, a reconciled scaffold FASTA of 390,825 lines, a `Scaffolds: agp` with 50 lines, an assembly-statistics table whose `# scaffolds` line equals 24, and an Nx plot PNG of roughly 76,000 bytes (±5,000). A user-supplied `Conflict resolution files` input is optional and left empty in the test.

## Reference workflow
Galaxy IWC — `workflows/VGP-assembly-v2/Scaffolding-Bionano-VGP7`, release 0.1.4 (CC-BY-4.0). Part of the VGP curated assembly suite; upstream of Hi-C scaffolding and downstream of hifiasm contigging workflows.
