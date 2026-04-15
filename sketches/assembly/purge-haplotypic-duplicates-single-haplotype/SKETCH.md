---
name: purge-haplotypic-duplicates-single-haplotype
description: Use when you have a contig-level genome assembly (typically one haplotype
  of a phased diploid assembly from PacBio HiFi) that contains false haplotypic or
  overlap duplications and you want to remove them with purge_dups against self-alignment
  read depth, then QC the cleaned assembly with Merqury, Compleasm and gfastats. Assumes
  the purged contigs should be discarded, not reassigned to the sister haplotype.
domain: assembly
organism_class:
- eukaryote
- diploid
input_data:
- contig-assembly-fasta
- long-reads-hifi
- meryl-kmer-db
- genomescope-model
source:
  ecosystem: iwc
  workflow: Purging duplicates in one haplotype VGP6b
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/VGP-assembly-v2/Purge-duplicates-one-haplotype-VGP6b
  version: 0.8.5
  license: CC-BY-4.0
  slug: VGP-assembly-v2--Purge-duplicates-one-haplotype-VGP6b
tools:
- name: purge_dups
  version: 1.2.6+galaxy1
- name: minimap2
  version: 2.28+galaxy2
- name: merqury
  version: 1.3+galaxy4
- name: compleasm
  version: 0.2.6+galaxy3
- name: gfastats
  version: 1.3.11+galaxy1
- name: meryl
tags:
- vgp
- purge_dups
- haplotigs
- hifi
- phased-assembly
- qc
- diploid
test_data:
- role: genomescope_model_parameters
  url: https://zenodo.org/records/10632760/files/Genomescope%20model%20parameters.tabular?download=1
  sha1: 6daf4567ff37e9d5ceebf76ddeb15e0d5773f694
  filetype: tabular
- role: assembly_to_purge
  url: https://zenodo.org/records/10632760/files/hap1.fasta?download=1
  sha1: 0c2c964e5b5d8ca1025b6e9d8f24c8e2224e88c0
  filetype: fasta
- role: meryl_database
  url: https://zenodo.org/records/10632760/files/Meryl%20Database.meryldb?download=1
  sha1: d947eb6b317fcd30bc18e59f1ddd0afa52f72587
  filetype: meryldb
- role: estimated_genome_size_parameter_file
  url: https://zenodo.org/records/10632760/files/Estimated%20genome%20size%20-%20Parameter%20File.expression.json?download=1
  sha1: 378f4f5733c91e6d6ea5be5b2b979ca865e78aae
  filetype: expression.json
- role: assembly_to_leave_alone_for_merqury_comparison
  url: https://zenodo.org/records/10632760/files/hap2.fasta?download=1
  sha1: bbf0d8abfb61a93c1641aa901ad2f347024cfadc
  filetype: fasta
- role: pacbio_reads_collection_trimmed__yeast_reads_sub1_fastq_gz
  url: https://zenodo.org/records/10632760/files/Trimmed_yeast_reads_sub1.fastq.gz?download=1
  sha1: 6757ca53673956e3f536d8f3fe08c6b3c6287d37
expected_output:
- role: removed_haplotigs
  description: Content assertions for `Removed haplotigs`.
  assertions:
  - 'has_n_lines: {''n'': 14}'
- role: purged_assembly
  description: Content assertions for `Purged assembly`.
  assertions:
  - 'has_n_lines: {''n'': 158}'
- role: purged_assembly_gfa
  description: Content assertions for `Purged assembly (GFA)`.
  assertions:
  - 'has_n_lines: {''n'': 160}'
- role: assembly_statistics_for_both_assemblies
  description: Content assertions for `Assembly statistics for both assemblies`.
  assertions:
  - "has_text: # scaffolds\t79\t79"
- role: cutoffs
  description: Content assertions for `Cutoffs`.
  assertions:
  - 'has_text: 48'
- role: purged_assembly_statistics
  description: Content assertions for `Purged assembly statistics`.
  assertions:
  - "has_text: # scaffolds\t79"
- role: nx_plot
  description: Content assertions for `Nx Plot`.
  assertions:
  - 'has_size: {''value'': 57000, ''delta'': 5000}'
- role: size_plot
  description: Content assertions for `Size Plot`.
  assertions:
  - 'has_size: {''value'': 84000, ''delta'': 5000}'
- role: merqury_on_phased_assemblies_stats
  description: 'Content assertions for `Merqury on Phased assemblies: stats`.'
  assertions:
  - 'output_merqury.completeness: has_text: 95.7636'
- role: compleasm_on_purged_assembly_translated_proteins
  description: 'Content assertions for `Compleasm on purged Assembly: Translated Proteins`.'
  assertions:
  - 'has_n_lines: {''n'': 40374}'
---

# Purge haplotypic duplicates from a single haplotype (VGP6b)

Removes contigs flagged as haplotypic or overlap duplicates from one haplotype of a phased assembly using purge_dups read-depth cutoffs, then quantifies the effect with Merqury k-mer QV/completeness, Compleasm BUSCO-style completeness, and gfastats contiguity metrics. This is step 6b of the Vertebrate Genomes Project (VGP) assembly pipeline and runs after the contigging workflow (VGP3/4/5).

## When to use this sketch
- You have a phased diploid eukaryotic assembly (e.g. VGP hifiasm output) with one haplotype that is visibly over-assembled — extra contigs, inflated size versus genome estimate, bimodal purge_dups coverage histogram.
- Long reads are PacBio HiFi and have already been trimmed (e.g. cutadapt for adapters/chimeras).
- You already ran k-mer profiling (meryl + GenomeScope) upstream and have the meryl DB, the GenomeScope model parameters, and an estimated genome size.
- You are confident the duplicated contigs are junk (not misplaced) and should simply be dropped from this haplotype.
- You want the standard VGP QC bundle (Merqury, Compleasm, gfastats, Nx/size plots) on the purged result.

## Do not use when
- You suspect the duplicates actually belong to the sister haplotype and should be reassigned — use the sibling `purge-haplotypic-duplicates-reassign-VGP6` workflow instead.
- You are working on a primary+alternate haploid-style assembly where both haps must be purged jointly — run the two-haplotype variant of VGP6.
- Input reads are ONT or Illumina short reads — purge_dups cutoff heuristics here assume HiFi coverage distributions.
- You have not yet built a meryl k-mer database and GenomeScope model — run the k-mer profiling workflow first.
- You need scaffolding, polishing, or contamination screening — those are separate VGP workflows (VGP7+, decontamination).

## Analysis outline
1. Map trimmed HiFi reads to the haplotype assembly with **minimap2** (`asm5` preset, PAF output) to get per-base coverage input for purge_dups.
2. Run **purge_dups `pbcstat` + `calcuts`** on the PAF to derive read-depth cutoffs (low/mid/high) from the coverage histogram, seeded by GenomeScope-derived bounds (1.5× and 3× of model columns).
3. Run **purge_dups `split_fa`** on the assembly and self-align it with **minimap2** in self-homology mode (`-DP`, PAF) to detect overlap duplications.
4. Run **purge_dups `purge_dups`** using the self-alignment PAF, per-base coverage, and calcuts cutoffs to produce a BED of regions to remove; filter out `REPEAT`-tagged intervals.
5. Run **purge_dups `get_seqs`** with the filtered BED and original FASTA to emit the purged primary assembly and the removed haplotigs FASTA.
6. Convert the purged FASTA to GFA and compute size/assembly statistics with **gfastats** (both purged and untouched haplotype, using the estimated genome size for NG*/LG* metrics).
7. Run **Merqury** against the meryl DB with both assemblies (purged + untouched) to compute joint QV, k-mer completeness, spectra-cn / spectra-asm plots.
8. Run **Compleasm** (BUSCO miniprot mode) on the purged assembly against the chosen lineage (e.g. `vertebrata_odb10`) for gene-content completeness.
9. Build Nx and cumulative-size comparison plots (ggplot2) from gfastats output for the two assemblies and assemble a workflow report.

## Key parameters
- **minimap2 read-to-assembly**: preset `asm5`, `--no-end-flt`, PAF output.
- **minimap2 self-alignment**: preset `self-homology`, `-A 1 -B 19 -O 39,81 -E 3,1 -z 200`, `--min-occ-floor 100`, `-m 40`, PAF output (canonical purge_dups self-hit settings).
- **purge_dups pbcstat**: `max_cov=500`, `min_map_ratio=0.0`, `flank=0`, primary alignments only.
- **purge_dups calcuts**: `min_depth=0.1`, `low=1`, `ploidy=-d 0` (diploid-aware cutoff picking); transition and upper bounds are computed from the GenomeScope model as `1.5 × kcov` and `3 × hom_peak` respectively.
- **purge_dups purge_dups**: `min_bad=0.8`, `min_align=70`, `min_match=200`, `min_chain=500`, `max_gap=20000`, single chaining round, `min_chain_score=10000`, `max_extend=15000`.
- **purge_dups get_seqs**: `length=10000`, `min_ratio=0.05`, `end_trim=true`, `min_gap=10000`, default (non-haplotig) mode.
- **BED filter**: drop lines matching `REPEAT` (case-insensitive, literal) before `get_seqs` to preserve repetitive contigs.
- **Compleasm**: `mode=busco`, lineage and database exposed as workflow parameters (VGP default: `vertebrata_odb10`, latest BUSCO DB).
- **gfastats (assembly stats)**: `statistics/assembly`, locale on, tabular, `expected_genomesize` wired from the parsed genome-size parameter file.

## Test data
A yeast-scale smoke test from VGP Zenodo record 10632760: a trimmed PacBio HiFi read subset (`Trimmed_yeast_reads_sub1.fastq.gz`) as a one-element collection, `hap1.fasta` as the haplotype to purge, `hap2.fasta` as the untouched companion for Merqury, plus the pre-computed GenomeScope model parameters tabular, meryl k-mer database, and estimated-genome-size expression.json. Lineage is set to `vertebrata_odb10` against the `v5` BUSCO DB. Running the workflow should produce a purged FASTA of 158 lines, its GFA of 160 lines, a 14-line removed-haplotigs FASTA, a purge_dups cutoffs file containing `48`, gfastats reports showing `# scaffolds\t79` for both assemblies, a Merqury completeness value of `95.7636`, a Compleasm translated-proteins FASTA of 40374 lines, and Nx/size PNGs of ~57 KB and ~84 KB respectively.

## Reference workflow
Galaxy IWC `VGP-assembly-v2/Purge-duplicates-one-haplotype-VGP6b`, release 0.8.5 (CC-BY-4.0), 6th step of the VGP assembly v2 pipeline — https://github.com/galaxyproject/iwc/tree/main/workflows/VGP-assembly-v2/Purge-duplicates-one-haplotype-VGP6b
