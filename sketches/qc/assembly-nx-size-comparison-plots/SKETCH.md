---
name: assembly-nx-size-comparison-plots
description: Use when you need to visually compare contiguity across two or more genome
  assemblies (e.g. successive scaffolding stages or haplotype assemblies) by generating
  Nx and cumulative-size plots from their FASTA files. Produces publication-ready
  PNGs showing how scaffold length and cumulative genome size evolve across assemblies.
domain: qc
organism_class:
- eukaryote
input_data:
- assembly-fasta-collection
source:
  ecosystem: iwc
  workflow: Generate Nx and Size plots for multiple assemblies
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/VGP-assembly-v2/Plot-Nx-Size
  version: 0.1.8
tools:
- gfastats
- datamash
- ggplot2
- galaxy-text-processing
tags:
- assembly-qc
- nx-plot
- size-plot
- contiguity
- vgp
- scaffolding
- comparison
test_data:
- role: collection_of_genomes_to_plot__primary
  url: https://zenodo.org/records/10047837/files/Hifiasm%20Primary%20assembly.fasta?download=1
  sha1: 0c2c964e5b5d8ca1025b6e9d8f24c8e2224e88c0
- role: collection_of_genomes_to_plot__alternate
  url: https://zenodo.org/records/10047837/files/Hifiasm%20Alternate%20assembly.fasta?download=1
  sha1: bbf0d8abfb61a93c1641aa901ad2f347024cfadc
expected_output:
- role: size_plot
  description: Content assertions for `Size Plot`.
  assertions:
  - 'has_size: {''value'': 100000, ''delta'': 2000}'
- role: nx_plot
  description: Content assertions for `Nx Plot`.
  assertions:
  - 'has_size: {''value'': 89000, ''delta'': 2000}'
---

# Assembly Nx and cumulative-size comparison plots

## When to use this sketch
- You have two or more genome assembly FASTA files (e.g. contigs vs. scaffolded versions, primary vs. alternate haplotype, or successive VGP scaffolding stages) and want to compare contiguity visually.
- You want both an Nx curve (scaffold length at cumulative fraction x of assembly) and a cumulative-size curve in a single comparison figure.
- You are tracking assembly improvement across pipeline stages (post-contigging, post-Bionano, post-Hi-C, post-curation) and need a quick visual QC.
- Input is whole-assembly FASTA only; no reads, alignments, or reference are needed.

## Do not use when
- You need full QUAST-style metrics (misassemblies, mismatches, indels against a reference) — use a reference-based assembly QC sketch instead.
- You want BUSCO completeness or k-mer-based QV/completeness (Merqury) — those are separate assembly-evaluation sketches.
- You only have a single assembly and just want N50/size numbers — run `gfastats` directly rather than this multi-assembly plotting workflow.
- You want to compare read-level quality or coverage — use a read-QC sketch.
- Your input is raw reads rather than assembled FASTA — run assembly first.

## Analysis outline
1. Accept a Galaxy-style **list collection of assembly FASTA files**; the element identifier of each item becomes its label on the plots.
2. Run **gfastats** in `statistics` mode with `size` output and `tabular=true` on each FASTA to emit per-sequence size tables.
3. **Sort** each table numerically descending by sequence length (column 2).
4. Use **awk** (`{total += $2; $3 = total}1`) to add a running cumulative-size column.
5. Use **datamash** `absmax` on column 3 to capture the total assembly size as a scalar.
6. Use **Add column** (iterate) to assign a rank / scaffold index per row.
7. Parse the total size as an integer and **compose** a text parameter `c3/<total>` to normalise cumulative size into Nx fraction space.
8. Use **Compute** (column_maker) to add three derived columns: the Nx fraction (`c3/total`), length in Mb (`c2/1000000`), and cumulative size in Mb (`c3/1000000`).
9. **Add input name as column** so each row carries its assembly label, then **collapse** the collection into a single tabular file (`gfastats data for plotting`).
10. **Cut** two projections: `c8,c5,c6` for the Nx plot and `c8,c4,c7` for the size plot.
11. Render both plots with **ggplot2 scatterplot** in `lines` mode, factoring by column 1 (assembly label), theme `bw`, Set1 palette, 7x7 in at 300 dpi: Nx plot (y = `Nx (Mb)`) and Size plot (x = `Scaffold number`, y = `Cumulative Size (Mb)`).

## Key parameters
- gfastats: `mode=statistics`, `statistics=size`, `out_size=c` (per-sequence sizes), `tabular=true`.
- Sort: column 2, numeric, descending, no header.
- Awk cumulative: `{total += $2; $3 = total}1`.
- Datamash: `absmax` on column 3 (total assembly size).
- Add column: `exp=1`, `iterate=yes` (scaffold rank).
- Compose text parameter: prefix `c3/` + parsed integer total → used as Nx fraction expression.
- Compute expressions (in order): `c3/<total>`, `c2/1000000`, `c3/1000000`.
- Cut columns: Nx plot = `c8,c5,c6`; Size plot = `c8,c4,c7` (tab delimiter).
- ggplot2: `type_options=lines`, `factorcol=1`, `colors=Set1`, `theme=bw`, `header=yes`, x=col2, y=col3, 7x7 in, 300 dpi, PNG.
- Collection element identifiers **must** be the names you want shown in the legend — rename before running.

## Test data
The test provides a Galaxy list collection of two *Hifiasm* assembly FASTA files hosted on Zenodo record 10047837 — one labelled `Primary` and one labelled `Alternate` — representing the two haplotype assemblies of a diploid genome. Running the workflow is expected to produce three outputs: a combined `gfastats data for plotting` tabular whose per-element rows are verified to contain the contents of `test-data/primary_head.tabular` and `test-data/alternate_head.tabular`, a `Nx Plot` PNG (~89 KB ± 2 KB), and a `Size Plot` PNG (~100 KB ± 2 KB). The assertions are size-based because the plots are rendered images.

## Reference workflow
Galaxy IWC — `workflows/VGP-assembly-v2/Plot-Nx-Size/Generate-Nx-and-Size-plots-for-multiple-assemblies.ga`, release 0.1.8. Authored by the Vertebrate Genomes Project (VGP) / Delphine Lariviere. Part of the VGP-assembly-v2 suite for comparing assembly contiguity across scaffolding stages.
