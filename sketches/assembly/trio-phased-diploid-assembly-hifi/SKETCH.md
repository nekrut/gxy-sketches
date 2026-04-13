---
name: trio-phased-diploid-assembly-hifi
description: Use when you need a fully phased, haplotype-resolved diploid genome assembly
  of a vertebrate (or other diploid eukaryote) from PacBio HiFi reads of an offspring
  plus short-read Illumina data from both parents (trio binning). Produces separate
  paternal (hap1) and maternal (hap2) contig assemblies with VGP-standard QC.
domain: assembly
organism_class:
- vertebrate
- eukaryote
- diploid
input_data:
- pacbio-hifi-reads
- parental-illumina-short-reads
- meryl-kmer-db
- parental-hapmer-db
source:
  ecosystem: iwc
  workflow: Genome Assembly with Pacbio Hifi reads and Trio data for phasing - VGP5
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/VGP-assembly-v2/Assembly-Hifi-Trio-phasing-VGP5
  version: 0.9.9
  license: CC-BY-4.0
tools:
- hifiasm
- cutadapt
- gfastats
- bandage
- busco
- compleasm
- merqury
- multiqc
tags:
- vgp
- trio-binning
- phased-assembly
- haplotype-resolved
- hifi
- diploid
- contigging
test_data:
- role: meryl_database_child
  url: https://zenodo.org/records/10056319/files/Meryl%20Database%20-%20Child.meryldb?download=1
  sha1: d947eb6b317fcd30bc18e59f1ddd0afa52f72587
  filetype: meryldb
- role: hapmer_database_paternal
  url: https://zenodo.org/records/10056319/files/Hapmer%20Database%20-%20Paternal.meryldb?download=1
  sha1: cb3b00cbd6415c46ce2e4dc2d8a9f2430818a3ab
  filetype: meryldb
- role: hapmer_database_maternal
  url: https://zenodo.org/records/10056319/files/Hapmer%20Database%20-%20Maternal.meryldb?download=1
  sha1: 2fca1ca9b87ad48c7f1291bac29abd98eb5f43d8
  filetype: meryldb
- role: genomescope_summary
  url: https://zenodo.org/records/10056319/files/Genomescope%20Summary.txt?download=1
  sha1: c3614564b2c84ef811c5d8bc56c394624d283fe4
  filetype: txt
- role: pacbio_reads_collection_child__yeast_reads_sub1_fastq_gz
  url: https://zenodo.org/records/10056319/files/Pacbio%20Reads%20Collection.fastq.gz?download=1
  sha1: 6757ca53673956e3f536d8f3fe08c6b3c6287d37
- role: paternal_illumina_reads_hap1__hap1_2_fq
  url: https://zenodo.org/records/10056319/files/Sub_hap1_2.fastqsanger?download=1
  sha1: dccc29434921e0ac1b22819a2bc39c1a293f4f4a
- role: paternal_illumina_reads_hap1__hap1_1_fq
  url: https://zenodo.org/records/10056319/files/Sub_hap1_1.fastqsanger?download=1
  sha1: 18776ce58066ec81ec47cf5a9987a5f3ba911348
- role: maternal_illumina_reads_hap2__hap2_2_fq
  url: https://zenodo.org/records/10056319/files/Sub_hap2_2.fastqsanger?download=1
  sha1: dc93abf6733d6069c7fc5c1d250527844638a91c
- role: maternal_illumina_reads_hap2__hap2_1_fq
  url: https://zenodo.org/records/10056319/files/Sub_hap2_1.fastqsanger?download=1
  sha1: 450db0747f0d09b18e6b9c16b4d1aef8243bfa24
expected_output:
- role: assembly_statistics_for_hap1_and_hap2
  description: Content assertions for `Assembly statistics for Hap1 and Hap2`.
  assertions:
  - "has_line: # contigs\t81\t27"
- role: usable_hap1_gfa
  description: Content assertions for `usable hap1 gfa`.
  assertions:
  - 'has_n_lines: {''n'': 167}'
- role: hifiasm_trio_hap1
  description: Content assertions for `Hifiasm Trio hap1`.
  assertions:
  - 'has_n_lines: {''n'': 162}'
- role: busco_summary_hap1
  description: Content assertions for `Busco Summary Hap1`.
  assertions:
  - 'has_text: C:1.2%[S:1.1%,D:0.0%],F:0.4%,M:98.4%'
- role: nx_plot
  description: Content assertions for `Nx Plot`.
  assertions:
  - 'has_size: {''value'': 65000, ''delta'': 5000}'
- role: no_sequence_hap1_gfa
  description: Content assertions for `No Sequence hap1 gfa`.
  assertions:
  - 'not_has_text: GTCAAGGCGA'
- role: compleasm_on_hap1_paternal_contigs_translated_proteins
  description: 'Content assertions for `Compleasm on Hap1 (paternal) contigs: Translated
    Proteins`.'
  assertions:
  - 'has_n_lines: {''n'': 41268}'
- role: compleasm_on_hap2_maternal_contigs_translated_proteins
  description: 'Content assertions for `Compleasm on Hap2 (maternal)  contigs: Translated
    Proteins`.'
  assertions:
  - 'has_n_lines: {''n'': 13376}'
---

# Trio-phased diploid assembly from PacBio HiFi + parental Illumina

## When to use this sketch
- You have PacBio HiFi reads from an offspring and short-read Illumina data from BOTH parents and want a fully phased, haplotype-resolved contig assembly (hap1 = paternal, hap2 = maternal).
- Target organism is a diploid eukaryote (typically vertebrate; VGP-style project) where parental phasing is the gold standard.
- Trio k-mer profiling (VGP2) has already been run: you already have a child meryl DB, paternal hapmer DB, maternal hapmer DB, and a GenomeScope model + summary.
- You want the standard VGP QC bundle (gfastats, BUSCO/Compleasm, Merqury QV + spectra, Nx/size plots, MultiQC of read trimming) over both haplotypes.

## Do not use when
- Parental data is unavailable → use a Hi-C-phased HiFi assembly sketch (VGP4 / Assembly-Hifi-HiC-phasing) instead.
- Only HiFi reads are available with no phasing data → use an unphased primary/alt HiFi assembly sketch (VGP3 / Assembly-Hifi-VGP3).
- Input is ONT long reads or short-read-only → choose long-read ONT or short-read assembly sketches.
- Target is a haploid prokaryote or a small microbial genome → use a bacterial/SPAdes assembly sketch, not hifiasm trio mode.
- You have not yet produced the meryl/hapmer databases → run the Trio k-mer Profiling (VGP2) workflow first, then return here.

## Analysis outline
1. Adapter/artifact trim the child's HiFi reads with Cutadapt (PacBio SMRTbell-style adapter sequences, revcomp-aware, discard trimmed).
2. Summarize read trimming with MultiQC for QC reporting.
3. Derive homozygous read coverage from the GenomeScope model (2 × kcov) unless an explicit coverage is provided; pick the effective value with `pick_value`.
4. Run Hifiasm in trio mode (`--h1`/`--h2` parental reads, HiFi reads from child) with `--trio-dual` on by default to correct trio-phasing errors, user-controlled bloom-filter bits, and the computed homozygous coverage. Emit raw unitigs, processed unitigs, and phased hap1/hap2 contig GFAs plus bin files.
5. Convert hap1 and hap2 GFAs to FASTA with gfastats, and also emit no-sequence GFAs for lightweight downstream use.
6. Render the raw unitig graph as a PNG with Bandage.
7. Compute per-haplotype assembly statistics with gfastats (size + assembly stats using estimated genome size parsed from the GenomeScope model), then merge the two tables into a single clean stats table.
8. Generate Nx and cumulative-size plots for both haplotypes via the `gfastats_plot` subworkflow (ggplot2).
9. Evaluate gene-space completeness on each haplotype with BUSCO (genome mode, metaeuk) and Compleasm (busco mode) against the user-supplied lineage (e.g. vertebrata_odb10).
10. Evaluate k-mer-based QV, completeness, and phasing with Merqury in trio mode using the child meryl DB + paternal/maternal hapmer DBs, producing spectra-cn, spectra-asm, per-haplotype spectra-cn plots, and QV/completeness tables.

## Key parameters
- Hifiasm mode: `trio` with `hap1_reads` = paternal Illumina, `hap2_reads` = maternal Illumina, child HiFi as main reads.
- `--trio-dual` (Utilize homology information to correct trio-phasing errors): default true.
- `filter_bits` (hifiasm `-f`): default 37; set 38–39 for genomes much larger than human to save memory.
- Homozygous coverage (`hom_cov`): user-supplied, else computed as 2 × GenomeScope kcov.
- Hifiasm cleaning: cleaning_rounds=4, pop_contigs=10,000,000, pop_unitigs=100,000, remove_tips=3, max_overlap=0.8, min_overlap=0.2.
- Trio k-mer settings: yak_kmer_length=31, min_kmers=5, max_kmers=2.
- Cutadapt: anywhere adapters `ATCTCTCTCAACAACAACAACGGAGGAGGAGGAAAAGAGAGAGAT` and `ATCTCTCTCTTTTCCTCCTCCTCCGTTGTTGTTGTTGAGAGAGAT`, error_rate=0.1, overlap=35, revcomp=true, discard_trimmed=true, minimum_length=1.
- BUSCO: mode=geno, augustus backend=metaeuk, evalue=0.001, limit=3, lineage from user parameter (e.g. `vertebrata_odb10`), database version from user parameter (e.g. `v5`).
- Compleasm: mode=busco, same lineage/DB as BUSCO.
- Merqury: mode=trio with child meryl + paternal/maternal hapmer DBs, both hap1/hap2 assemblies, label `output_merqury`.
- Haplotype labels: `Hap1`/`Hap2` (default), tagged paternal/maternal respectively.

## Test data
The workflow ships with a tiny yeast-scale trio test (Zenodo record 10056319): a single child HiFi FASTQ collection (`yeast_reads_sub1.fastq.gz`), paired paternal Illumina reads (`Sub_hap1_1/2.fastqsanger`), paired maternal Illumina reads (`Sub_hap2_1/2.fastqsanger`), plus precomputed child meryl DB, paternal and maternal hapmer DBs, a GenomeScope summary, and a GenomeScope model-parameters tabular. Scalars: bloom filter bits=32, BUSCO DB=`v5`, lineage=`vertebrata_odb10`, hap labels `Hap1`/`Hap2`, no explicit homozygous coverage (derived from GenomeScope). A successful run yields an estimated genome size of ~2,288,021 bp; a merged stats table whose contig count line reads `# contigs\t81\t27`; a usable hap1 GFA of 167 lines and a hap1 FASTA of 162 lines; a hap1 no-sequence GFA that contains no raw sequence (asserted via absence of `GTCAAGGCGA`); a BUSCO hap1 summary line `C:1.2%[S:1.1%,D:0.0%],F:0.4%,M:98.4%` (low, as expected for the tiny subset against vertebrata); Compleasm translated-protein FASTAs of 41,268 lines (hap1/paternal) and 13,376 lines (hap2/maternal); and an Nx plot PNG of roughly 65 kB (±5 kB).

## Reference workflow
Galaxy IWC `VGP-assembly-v2/Assembly-Hifi-Trio-phasing-VGP5`, release 0.9.9 (CC-BY-4.0), part of the Vertebrate Genomes Project (VGP) Galaxy workflow suite; must be run after VGP2 Trio k-mer Profiling. Core tool versions: hifiasm 0.25.0, gfastats 1.3.11, BUSCO 5.8.0, Compleasm 0.2.6, Merqury 1.3, Cutadapt 5.1, MultiQC 1.27, Bandage 2022.09.
