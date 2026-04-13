---
name: purge-haplotypic-duplicates-diploid-assembly
description: Use when you have a diploid genome assembly produced by hifiasm (or similar)
  from PacBio HiFi long reads and need to remove haplotypic / overlap duplications
  from both the primary and alternate haplotypes using purge_dups, reassigning purged
  contigs from hap1 into hap2 before purging hap2. Typical for VGP-style vertebrate
  diploid assemblies with a companion meryl k-mer database.
domain: assembly
organism_class:
- eukaryote
- diploid
- vertebrate
input_data:
- long-reads-hifi
- primary-assembly-fasta
- alternate-assembly-fasta
- meryl-kmer-db
- genomescope-model
source:
  ecosystem: iwc
  workflow: Purge duplicate contigs from a diploid assembly VGP6
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/VGP-assembly-v2/Purge-duplicate-contigs-VGP6
  version: 0.10.5
  license: CC-BY-4.0
tools:
- purge_dups
- minimap2
- gfastats
- merqury
- compleasm
tags:
- vgp
- diploid
- purge_dups
- haplotig
- hifi
- assembly-qc
- hifiasm
test_data:
- role: hifiasm_primary_assembly
  url: https://zenodo.org/records/10047837/files/Hifiasm%20Primary%20assembly.fasta?download=1
  sha1: 0c2c964e5b5d8ca1025b6e9d8f24c8e2224e88c0
  filetype: fasta
- role: hifiasm_alternate_assembly
  url: https://zenodo.org/records/10047837/files/Hifiasm%20Alternate%20assembly.fasta?download=1
  sha1: bbf0d8abfb61a93c1641aa901ad2f347024cfadc
  filetype: fasta
- role: meryl_database
  url: https://zenodo.org/records/10047837/files/Meryl%20Database.meryldb?download=1
  sha1: d947eb6b317fcd30bc18e59f1ddd0afa52f72587
  filetype: meryldb
- role: genomescope_model_parameters
  url: https://zenodo.org/records/10047837/files/Genomescope%20model%20parameters.tabular?download=1
  sha1: 6daf4567ff37e9d5ceebf76ddeb15e0d5773f694
  filetype: tabular
- role: estimated_genome_size_parameter_file
  url: https://zenodo.org/records/10047837/files/Estimated%20genome%20size%20-%20Parameter%20File.expression.json?download=1
  sha1: 378f4f5733c91e6d6ea5be5b2b979ca865e78aae
  filetype: expression.json
- role: pacbio_reads_collection_trimmed__yeast_reads_sub1_fastq_gz
  url: https://zenodo.org/records/10047837/files/Pacbio%20Reads%20Collection%20-%20Trimmed_yeast_reads_sub1.fastq.gz.fastq.gz?download=1
  sha1: 22655cfeb863227dc07af755f6a892a4558c16cf
expected_output:
- role: cutoffs_for_primary_assembly
  description: Content assertions for `Cutoffs for primary assembly`.
  assertions:
  - "has_text: 1\t15\t15\t16\t16\t48"
- role: purged_primary_assembly
  description: Content assertions for `Purged Primary Assembly`.
  assertions:
  - 'has_n_lines: {''n'': 156}'
- role: purged_primary_assembly_gfa
  description: Content assertions for `Purged Primary Assembly (gfa)`.
  assertions:
  - 'has_n_lines: {''n'': 157}'
- role: cutoffs_for_alternate_assembly
  description: Content assertions for `Cutoffs for alternate assembly`.
  assertions:
  - "has_text: 1\t15\t15\t16\t16\t48"
- role: purged_alternate_assembly
  description: Content assertions for `Purged Alternate Assembly`.
  assertions:
  - 'has_n_lines: {''n'': 144}'
  - 'has_text: contig_2.alt'
- role: purged_alternate_assembly_gfa
  description: Content assertions for `Purged Alternate assembly (gfa)`.
  assertions:
  - 'has_n_lines: {''n'': 145}'
- role: assembly_statistics_for_purged_assemblies
  description: Content assertions for `Assembly statistics for purged assemblies`.
  assertions:
  - "has_text: # contigs\t78\t72"
- role: nx_plot
  description: Content assertions for `Nx Plot`.
  assertions:
  - 'has_size: {''value'': 61000, ''delta'': 5000}'
- role: merqury_on_phased_assemblies_stats
  description: 'Content assertions for `Merqury on Phased assemblies: stats`.'
  assertions:
  - "output_merqury.completeness: has_text: both\tall\t1212740\t1300032\t93.2854"
- role: compleasm_on_purged_primary_hap1_assembly_translated_proteins
  description: 'Content assertions for `Compleasm on purged primary/hap1 assembly:
    Translated Proteins`.'
  assertions:
  - 'has_n_lines: {''n'': 40390}'
- role: compleasm_on_purged_alternate_hap2_assembly_translated_proteins
  description: 'Content assertions for `Compleasm on purged alternate/hap2 assembly:
    Translated Proteins`.'
  assertions:
  - 'has_n_lines: {''n'': 40354}'
- role: name_mapping_alternate_assembly
  description: Content assertions for `Name mapping Alternate assembly`.
  assertions:
  - "has_text: h2tg000050l_path_1\tcontig_1.alt"
---

# Purge haplotypic duplicates from a diploid assembly (VGP6)

## When to use this sketch
- You have a diploid assembly with two haplotype FASTAs (primary/hap1 and alternate/hap2) produced by a contigging workflow such as hifiasm.
- Input reads are trimmed PacBio HiFi long reads and you have a matching meryl k-mer database plus a GenomeScope model from a prior k-mer profiling step.
- Both haplotypes likely contain haplotypic duplication or overlap duplication that needs to be removed, with purged contigs from hap1 reassigned to hap2 before hap2 is purged in turn.
- You need post-purge QC (Merqury QV/completeness, Compleasm/BUSCO-style lineage completeness, gfastats assembly metrics, Nx and size plots) for both resulting haplotypes.
- Target organisms are typically vertebrates / large eukaryotes following the VGP pipeline conventions.

## Do not use when
- Only one of the two haplotypes needs purging — use the sibling VGP6b single-haplotype purge workflow instead.
- You are working on a haploid or bacterial genome — use a haploid-assembly QC/polish sketch, not purge_dups-based haplotig removal.
- You have not yet generated a contig-level diploid assembly; run a contigging workflow (VGP3/4/5 equivalent with hifiasm) first.
- You lack a meryl database and GenomeScope model; run a k-mer profiling workflow first so Merqury QC and cutoff estimation can work.
- Your data is Illumina short-read or ONT-only without HiFi — purge_dups cutoffs in this sketch assume HiFi read-depth characteristics.

## Analysis outline
1. Map trimmed HiFi reads to the primary assembly with `minimap2` (preset `asm5`, PAF output) to get read-to-assembly alignments.
2. Self-align the split primary assembly against itself with `minimap2` (self-homology preset, custom scoring A=1 B=19 O=39 O2=81 E=3 E2=1 z=200, `min_occ_floor=100`, `m=40`) after `purge_dups split_fa`.
3. Derive coverage cutoffs: run `purge_dups pbcstat` and `calcuts` on the read alignments; transition and upper-depth cutoffs are computed from the GenomeScope model (using `1.5 * kcov` and `3 * hom_cov` via a Compute/Cut/Parse chain).
4. Run `purge_dups purge_dups` on the self-alignment using the coverage and cutoffs to produce a BED of duplicated regions, then `purge_dups get_seqs` to split the primary FASTA into retained primary contigs and purged (haplotig) sequences.
5. Concatenate the purged-from-primary sequences onto the original alternate assembly to form an augmented hap2, then repeat steps 1–4 on this augmented alternate assembly (mapping reads, self-alignment, pbcstat/calcuts with the same cutoffs, purge_dups, get_seqs) to produce the final purged alternate assembly.
6. Rename/unify the purged alternate FASTA headers via a `Rename and unify fasta` subworkflow (gfastats swiss-army-knife) so new contigs carry consistent `<hap>` tags, and emit a name-mapping table.
7. Emit GFA versions of both purged assemblies via `gfastats` (manipulation mode, terminal overlap length 500).
8. QC both purged haplotypes: `compleasm` (BUSCO mode) against a chosen lineage (e.g. vertebrata_odb10), `merqury` against the meryl db (QV, completeness, spectra-cn / spectra-asm plots), `gfastats` assembly statistics using the estimated genome size, plus Nx and size plots from a `gfastats_data_prep` subworkflow.

## Key parameters
- minimap2 read-to-assembly: preset `asm5`, output `paf`, `no_end_flt=true`.
- minimap2 self-homology: `A=1, B=19, O=39, O2=81, E=3, E2=1, z=200, min_occ_floor=100, m=40`, `analysis_type=self-homology`, PAF output.
- purge_dups pbcstat: `max_cov=500`, `min_map_ratio=0.0`, `flank=0`, `primary_alignments=true`.
- purge_dups calcuts: `min_depth=0.1`, `low_depth=1`, `ploidy=-d 0` (diploid), `transition` and `upper_depth` supplied from GenomeScope via Compute expressions `1.5*c3` and `3*c7`.
- purge_dups purge_dups: `min_bad=0.8`, `min_align=70`, `min_match=200`, `min_chain=500`, `max_gap=20000`, one chaining round, `min_chain_score=10000`, `max_extend=15000`.
- purge_dups get_seqs: `length=10000`, `min_ratio=0.05`, `end_trim=true`, `min_gap=10000`, haplotigs+coverage outputs disabled (split into retained and purged only).
- gfastats GFA export: `out_format=gfa`, `terminal_overlaps_length=500`.
- gfastats assembly statistics: `expected_genomesize` from the Estimated Genome Size parameter file.
- compleasm: `mode=busco`, lineage (e.g. `vertebrata_odb10`) and BUSCO DB version (e.g. `v5`) supplied as workflow parameters.
- merqury: two-assembly mode with the meryl db and both purged FASTAs; emits QV, stats, spectra-cn/spectra-asm PNGs, and histograms.
- Haplotype name restrictions: `Hap1/Hap2/Primary/Alternate/Maternal/Paternal`, no whitespace.
- Sequence type toggle: `contig` or `scaffold`.

## Test data
The source test profile uses a small yeast-sized diploid HiFi dataset: a primary and an alternate hifiasm assembly FASTA, a matching meryl k-mer database, a GenomeScope model parameters tabular, an estimated-genome-size expression.json, and a single-element collection of trimmed HiFi reads (`yeast_reads_sub1.fastq.gz`), all hosted on Zenodo record 10047837. The run is parameterised with `Database for Busco Lineage = v5`, `Lineage = vertebrata_odb10`, primary name `Primary`, alternate name `Alternate`, and sequence type `contig`. Expected outputs assert that calcuts cutoffs for both assemblies match `1\t15\t15\t16\t16\t48`, the purged primary FASTA has 156 lines (157 for its GFA), the purged alternate FASTA has 144 lines and contains contigs tagged `contig_2.alt` (145 for its GFA), the merged assembly-statistics table contains `# contigs\t78\t72`, Merqury completeness reports `both all 1212740 1300032 93.2854`, Compleasm translated-protein FASTAs have 40390 / 40354 lines for primary / alternate, and the Nx plot PNG is ~61 KB (±5 KB). A name-mapping file for the alternate assembly should map `h2tg000050l_path_1` to `contig_1.alt`.

## Reference workflow
Galaxy IWC workflow `VGP-assembly-v2/Purge-duplicate-contigs-VGP6` (release 0.10.5, CC-BY-4.0), the 6th step of the VGP assembly pipeline, run after a contigging workflow (VGP3/4/5). Sibling: `VGP6b` for purging only a single haplotype.
