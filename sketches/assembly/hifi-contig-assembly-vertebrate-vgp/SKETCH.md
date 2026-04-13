---
name: hifi-contig-assembly-vertebrate-vgp
description: Use when you need to generate a draft diploid contig-level genome assembly
  from PacBio HiFi reads for a vertebrate or other eukaryote, following the VGP (Vertebrate
  Genomes Project) pipeline. Produces primary and alternate contig sets plus BUSCO/Compleasm,
  Merqury and gfastats QC. Requires a pre-computed Meryl k-mer database and GenomeScope
  profile from an upstream k-mer profiling step.
domain: assembly
organism_class:
- vertebrate
- eukaryote
- diploid
input_data:
- long-reads-pacbio-hifi
- meryl-db
- genomescope-profile
source:
  ecosystem: iwc
  workflow: Genome Assembly from Hifi reads - VGP3
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/VGP-assembly-v2/Assembly-Hifi-only-VGP3
  version: 0.3.5
  license: CC-BY-4.0
tools:
- hifiasm
- cutadapt
- gfastats
- bandage
- compleasm
- merqury
- multiqc
- ggplot2
tags:
- vgp
- hifi
- pacbio
- long-read
- contig
- diploid
- primary-alternate
- merqury
- compleasm
- hifiasm
test_data:
- role: meryl_database
  url: https://zenodo.org/record/8371053/files/Meryl-db.meryldb?download=1
  sha1: 95615073e670e81ca03e6582b7da437c915cfccd
  filetype: meryldb
- role: genomescope_summary
  url: https://zenodo.org/record/8371053/files/GenomeScope_Summary.txt?download=1
  sha1: 42c6e189d26791e637dbaee533ad13cab39a7c1b
  filetype: txt
- role: pacbio_reads_collection__yeast_reads_sub1_fastq_gz
  url: https://zenodo.org/record/8371053/files/yeast_reads_sub1.fastq.gz?download=1
  sha1: 6757ca53673956e3f536d8f3fe08c6b3c6287d37
  filetype: fastqsanger.gz
expected_output:
- role: hifiasm_primary_assembly
  description: Content assertions for `Hifiasm Primary assembly`.
  assertions:
  - 'has_n_lines: {''n'': 168}'
- role: hifiasm_alternate_assembly
  description: Content assertions for `Hifiasm Alternate assembly`.
  assertions:
  - 'has_n_lines: {''n'': 6}'
- role: assembly_stats_on_alternate_assembly
  description: Content assertions for `Assembly Stats on Alternate Assembly`.
  assertions:
  - "has_line: # scaffolds\t3"
- role: assembly_stats_on_primary_assembly
  description: Content assertions for `Assembly Stats on Primary assembly`.
  assertions:
  - "has_line: # scaffolds\t84"
- role: assembly_statistics
  description: Content assertions for `Assembly statistics`.
  assertions:
  - "has_line: # scaffolds\t84\t3"
- role: compleasm_on_primary_assembly_contigs_summary
  description: 'Content assertions for `Compleasm on Primary Assembly contigs: Summary`.'
  assertions:
  - 'has_text: S:1.16%, 39'
- role: nx_and_size_plots
  description: Content assertions for `Nx and Size plots`.
  assertions:
  - 'has_size: {''value'': 400000, ''delta'': 200000}'
- role: compleasm_on_primary_assembly_contigs_translated_proteins
  description: 'Content assertions for `Compleasm on Primary Assembly contigs: Translated
    Proteins`.'
  assertions:
  - 'has_n_lines: {''n'': 41772}'
- role: compleasm_on_primary_assembly_contigs_miniprot
  description: 'Content assertions for `Compleasm on Primary Assembly contigs: Miniprot`.'
  assertions:
  - 'has_n_lines: {''n'': 739425}'
- role: compleasm_on_alternate_assembly_contigs_summary
  description: 'Content assertions for `Compleasm on Alternate Assembly contigs: Summary`.'
  assertions:
  - 'has_text: M:100.00%, 3354'
- role: compleasm_on_alternate_assembly_contigs_miniprot
  description: 'Content assertions for `Compleasm on Alternate Assembly contigs: Miniprot`.'
  assertions:
  - 'has_n_lines: {''n'': 671623}'
---

# HiFi-only contig assembly (VGP phase 3)

## When to use this sketch
- You have PacBio HiFi long reads for a diploid eukaryote (vertebrate, insect, plant, etc.) and want a draft contig-level assembly with primary + alternate haplotypes.
- You have already run an upstream k-mer profiling workflow (VGP1) that produced a Meryl k-mer database, a GenomeScope summary, and GenomeScope model parameters.
- You want standard VGP QC bundled in: raw-unitig Bandage image, gfastats assembly statistics, Nx/size plots, Merqury QV + spectra-cn plots, and Compleasm (BUSCO-compatible) completeness on both haplotypes.
- You want contigs only — no Hi-C phasing, no scaffolding, no polishing, no curation.

## Do not use when
- Your input is Illumina short reads, ONT long reads, or hybrid data — this workflow is HiFi-only and will not accept them.
- You need a scaffolded or Hi-C-phased assembly: use the VGP Hi-C scaffolding / trio-binning / hic-phasing sibling workflows instead.
- You are assembling a haploid bacterium or small microbial genome — prefer a dedicated bacterial assembly sketch (e.g. nf-core/bacass or Unicycler-based flows).
- You have no upstream k-mer profiling outputs (Meryl db + GenomeScope) — run the VGP k-mer profiling (VGP1) workflow first.
- You need gene annotation, variant calling, or repeat masking — those are downstream of this sketch.

## Analysis outline
1. Adapter-trim HiFi reads with Cutadapt (removes PacBio SMRTbell/hairpin remnants; discards trimmed reads).
2. Aggregate trimming statistics with MultiQC.
3. Derive the homozygous read coverage from the GenomeScope model (doubled kcov), or use the user-supplied override; extract estimated genome size from the GenomeScope summary.
4. Assemble contigs with Hifiasm in standard (HiFi-only) mode, passing the bloom-filter bit width (`-f`) and homozygous coverage (`--hom-cov`). Produces raw unitigs, processed unitigs, and primary + alternate contig GFAs.
5. Render a Bandage image of the raw unitig graph for visual QC.
6. Convert primary and alternate contig GFAs to FASTA with gfastats, and also emit sequence-free GFAs.
7. Compute assembly statistics on both haplotypes with gfastats (using the estimated genome size for NG/LG metrics) and build Nx and cumulative size plots via a gfastats_plot subworkflow + ggplot2.
8. Run Merqury against the Meryl database with both assemblies to get QV, k-mer completeness, and spectra-cn/spectra-asm plots; tile the spectra PNGs with ImageMagick montage.
9. Run Compleasm (BUSCO mode) on both primary and alternate contigs against the requested lineage database.
10. Emit a workflow report with species/assembly name, unitig graph, Merqury tables and plots, Compleasm summaries, cleaned assembly stats and Nx/size plots.

## Key parameters
- `Bits for Hifiasm bloom filter` (`-f`): default `37`; use `38`–`39` for genomes much larger than human to save memory during k-mer counting.
- `Homozygous Read Coverage` (`--hom-cov`): optional integer override; if left empty the workflow computes `2 × kcov` from the GenomeScope model parameters (column 3, row tagged `Haploid`).
- Hifiasm advanced options are set to: k-mer length 51, window 51, max overlaps 100, correction rounds 3, max k-occurrences 20000, cleaning rounds 4, purge level 0 (no purging — purging is handled downstream in VGP), similarity threshold 0.75.
- `Database for Busco Lineage`: Compleasm BUSCO database version (recommended: `v5`).
- `Lineage`: Compleasm/BUSCO lineage dataset (recommended: `vertebrata_odb10`, or the closest clade to your organism).
- `Name of primary assembly` / `Name of alternate assembly`: labels used in stats tables and Nx/size plots (defaults `Primary` / `Alternate`).
- Cutadapt is configured with two PacBio SMRTbell-style anywhere adapters, `--discard-trimmed`, `--revcomp`, overlap 35, error rate 0.1.

## Test data
The test profile uses a downsampled yeast PacBio HiFi read set (`yeast_reads_sub1.fastq.gz`) provided as a single-element FASTQ collection, together with a pre-computed Meryl k-mer database (`Meryl-db.meryldb`) and a GenomeScope summary plus model-parameters tabular file generated by the upstream VGP k-mer profiling workflow. The `Bits for Hifiasm bloom filter` parameter is lowered to 32 for the small test genome, Compleasm is run with the `vertebrata_odb10` lineage against the `v5` BUSCO database, and haplotype labels default to `Primary`/`Alternate`. Running the workflow is expected to produce a Hifiasm primary assembly FASTA (~168 lines, 84 scaffolds) and an alternate assembly FASTA (~6 lines, 3 scaffolds), a merged assembly-statistics table whose `# scaffolds` row reads `84\t3`, an estimated genome size near 2.29 Mb, Compleasm summaries reporting `S:1.16%, 39` on the primary and `M:100.00%, 3354` on the alternate contigs (reflecting how little of the vertebrata lineage hits a truncated yeast sample), deterministic line counts for the Compleasm miniprot GFF3 and translated-protein FASTA, and a combined Nx/size plot PNG of roughly 400 kB (±200 kB).

## Reference workflow
Galaxy IWC `workflows/VGP-assembly-v2/Assembly-Hifi-only-VGP3`, release `0.3.5` (CC-BY-4.0). Part of the VGP (Vertebrate Genomes Project) assembly v2 suite; run after the VGP1 k-mer profiling workflow and, for scaffolded assemblies, followed by VGP Hi-C scaffolding / purging workflows.
