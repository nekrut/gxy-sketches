---
name: phased-diploid-assembly-hifi-hic
description: Use when you need to produce a fully phased, haplotype-resolved diploid
  genome assembly from PacBio HiFi long reads combined with Hi-C reads from the same
  individual, typically for vertebrate or other diploid eukaryotes following the VGP
  standard. Requires k-mer profiling (meryl + GenomeScope) to have already been run.
domain: assembly
organism_class:
- eukaryote
- vertebrate
- diploid
input_data:
- long-reads-pacbio-hifi
- hi-c-paired
- meryl-db
- genomescope-summary
source:
  ecosystem: iwc
  workflow: Genome Assembly from Hifi reads with HiC phasing - VGP4
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/VGP-assembly-v2/Assembly-Hifi-HiC-phasing-VGP4
  version: '0.6'
  license: CC-BY-4.0
  slug: VGP-assembly-v2--Assembly-Hifi-HiC-phasing-VGP4
tools:
- name: hifiasm
  version: 0.25.0+galaxy3
- name: cutadapt
  version: 5.2+galaxy1
- name: gfastats
  version: 1.3.11+galaxy0
- name: bandage
  version: 2022.09+galaxy4
- name: compleasm
  version: 0.2.6+galaxy3
- name: merqury
  version: 1.3+galaxy4
- name: multiqc
  version: 1.33+galaxy0
- name: ggplot2
tags:
- vgp
- phased-assembly
- haplotype-resolved
- hifi
- hi-c
- diploid
- contigging
test_data:
- role: hi_c_reads__hi_c_reads__forward
  url: https://zenodo.org/records/10068595/files/HiC%20forward%20reads.fastqsanger.gz?download=1
  sha1: eb2e87b12418c0665f5de6d97101a4fc088f8bdf
  filetype: fastqsanger.gz
- role: hi_c_reads__hi_c_reads__reverse
  url: https://zenodo.org/records/10068595/files/HiC%20reverse%20reads.fastqsanger.gz?download=1
  sha1: 538110c9b14a5b11088a6999244ee04983389d80
  filetype: fastqsanger.gz
- role: genomescope_summary
  url: https://zenodo.org/records/10068595/files/Genomescope%20Summary.txt?download=1
  sha1: 42c6e189d26791e637dbaee533ad13cab39a7c1b
  filetype: txt
- role: meryl_database
  url: https://zenodo.org/records/10068595/files/Meryl%20Database.meryldb?download=1
  sha1: 95615073e670e81ca03e6582b7da437c915cfccd
  filetype: meryldb
- role: pacbio_reads__yeast_reads_sub1_fastq_gz
  url: https://zenodo.org/records/10068595/files/Pacbio%20Reads%20Collection_yeast_reads_sub1.fastq.gz.fastq.gz?download=1
  sha1: 6757ca53673956e3f536d8f3fe08c6b3c6287d37
expected_output:
- role: hifiasm_hi_c_hap1
  description: Content assertions for `Hifiasm Hi-C hap1`.
  assertions:
  - 'has_n_lines: {''n'': 114}'
- role: nx_plot
  description: Content assertions for `Nx Plot`.
  assertions:
  - 'has_size: {''value'': 65000, ''delta'': 10000}'
- role: usable_hap1_gfa
  description: Content assertions for `usable hap1 gfa`.
  assertions:
  - 'has_n_lines: {''n'': 119}'
- role: no_sequences_hap2_gfa
  description: Content assertions for `No Sequences hap2 gfa`.
  assertions:
  - "has_text: S\th2tg000001l\t*\tLN:i:43860\tLN:i:43860\trd:i:45"
- role: assembly_statistics_for_hap1_and_hap2
  description: Content assertions for `Assembly statistics for Hap1 and Hap2`.
  assertions:
  - "has_text: # scaffolds\t57\t51"
- role: compleasm_on_contigs_hap1_full_table
  description: Content assertions for `Compleasm on Contigs hap1 Full Table`.
  assertions:
  - 'has_n_lines: {''n'': 3356}'
- role: compleasm_on_contigs_hap1_translated_proteins
  description: Content assertions for `Compleasm on Contigs hap1 Translated Proteins`.
  assertions:
  - 'has_n_lines: {''n'': 31142}'
- role: compleasm_on_contigs_hap2_full_table
  description: Content assertions for `Compleasm on Contigs hap2 Full Table`.
  assertions:
  - 'has_n_lines: {''n'': 3356}'
- role: compleasm_on_contigs_hap2_translated_proteins
  description: Content assertions for `Compleasm on Contigs hap2 Translated Proteins`.
  assertions:
  - 'has_n_lines: {''n'': 23694}'
- role: compleasm_on_contigs_hap1_summary
  description: Content assertions for `Compleasm on Contigs hap1 Summary`.
  assertions:
  - 'has_text: S:0.81%, 27'
- role: compleasm_on_contigs_hap2_summary
  description: Content assertions for `Compleasm on Contigs hap2 Summary`.
  assertions:
  - 'has_text: S:0.60%, 20'
---

# Phased diploid assembly from HiFi + Hi-C (VGP4)

## When to use this sketch
- You have PacBio HiFi long reads and Hi-C paired-end reads from the **same individual** and want a haplotype-resolved, fully phased contig-level assembly.
- Target organism is a diploid eukaryote (vertebrate, plant, invertebrate) that benefits from the VGP reference-quality standard.
- You have already run a k-mer profiling step (VGP1-style: meryl k-mer database + GenomeScope summary/model) to estimate genome size and homozygous coverage.
- You want assembly QC out of the box: gfastats stats, Bandage unitig image, Compleasm (BUSCO-style) completeness, Merqury QV/completeness, Nx and cumulative size plots.

## Do not use when
- You only have HiFi and no Hi-C — use a HiFi-only / primary+alt sketch (e.g. VGP2 HiFi-only assembly) instead.
- You are assembling a **haploid bacterial** genome — use `haploid-variant-calling-bacterial` or a bacterial de novo assembly sketch.
- You have only ONT long reads or only short reads — this workflow is HiFi-specific; use a Flye/Canu-ONT or SPAdes short-read sketch.
- You need scaffolding, gap-filling, decontamination, or manual curation — those are downstream VGP workflows (VGP5+), not this sketch.
- You have not yet produced a meryl DB and GenomeScope model — run the k-mer profiling (VGP1) sketch first; this workflow consumes its outputs.
- You want trio-binning phasing from parental reads — this sketch uses Hi-C for phasing, not parental k-mers.

## Analysis outline
1. **Adapter trim HiFi reads** with Cutadapt using PacBio SMRTbell anywhere-adapter sequences (revcomp on, discard trimmed reads).
2. **Optionally trim Hi-C reads** with Cutadapt (cut 5 bp from 5' of R1 and R2) — enable for noisy Arima Hi-C; otherwise pass through.
3. **Collapse / pick Hi-C collection** so hifiasm receives a single forward and single reverse file (handles single or multi-sample Hi-C collections via a subworkflow).
4. **Parse genome profile** — grep the Haploid line of the GenomeScope summary to extract estimated genome size; optionally parse the GenomeScope model to derive homozygous read coverage when the user does not provide one.
5. **Run Hifiasm in Hi-C phasing mode** (`--h1/--h2`) on the trimmed HiFi reads, with homozygous coverage and bloom-filter bits passed through, producing balanced hap1 and hap2 contig graphs plus a raw unitig graph.
6. **Convert GFA → FASTA per haplotype** with gfastats (and emit light GFAs with no sequence for sharing).
7. **Assembly statistics per haplotype** via gfastats (expected genome size aware) and per-contig size tables for Nx / cumulative-size plotting.
8. **Visualize unitig graph** with Bandage (PNG).
9. **Completeness QC** with Compleasm against a user-chosen BUSCO lineage (e.g. vertebrata_odb10) for each haplotype.
10. **K-mer QC** with Merqury using the meryl DB from VGP1, producing QV, completeness, spectra-CN, and combined-haplotype plots.
11. **Plots & report** — ggplot2 Nx and size plots (hap1 vs hap2), MultiQC over cutadapt, and a bundled workflow report.

## Key parameters
- `hifiasm`: mode `standard`, `hic_partition` set with `h1`/`h2` (Hi-C forward/reverse), `hom_cov` from GenomeScope or user override, `filter_bits` (bloom filter `-f`, default **37**; use 38–39 for genomes much larger than human), `l_msjoin=500000`, cleaning rounds 4, `min_overlap=0.2`, `max_overlap=0.8`, `pop_contigs=10000000`, `pop_unitigs=100000`.
- `cutadapt` (HiFi): anywhere adapters `ATCTCTCTCAACAACAACAACGGAGGAGGAGGAAAAGAGAGAGAT` and `ATCTCTCTCTTTTCCTCCTCCTCCGTTGTTGTTGTTGAGAGAGAT`, `revcomp=true`, `overlap=35`, `discard_trimmed=true`, `minimum_length=1`.
- `cutadapt` (Hi-C, conditional): `cut=5`, `cut2=5`, paired_collection mode, run only when `Trim Hi-C reads? = true`.
- `gfastats`: `statistics/assembly` with `expected_genomesize` wired from parsed GenomeScope estimate (doubled and column-extracted); separate size-mode runs feed the Nx/size plots.
- `compleasm`: user-selected `busco_database` (e.g. `v5`) and `lineage_dataset` (e.g. `vertebrata_odb10`), run independently on hap1 and hap2 contigs.
- `merqury`: uses the meryl DB from VGP1 together with both haplotype FASTAs for joint QV/completeness.
- Haplotype name inputs must match regex `^\S+$` (no whitespace); defaults `Hap1` / `Hap2`.

## Test data
The test profile runs the workflow on a subsampled yeast dataset (a single PacBio HiFi FASTQ `yeast_reads_sub1.fastq.gz`) with Hi-C forward/reverse paired reads from Zenodo record 10068595, plus a precomputed GenomeScope summary, GenomeScope model parameters tabular, and meryl database from the VGP1 k-mer profiling workflow. Lineage is set to `vertebrata_odb10` (chosen for coverage, not biological fit), bloom-filter bits = 32, Hi-C trimming disabled. A second test variant exercises the multi-Hi-C-pair code path by supplying two paired collections. Expected outputs include an estimated genome size of 2,288,021 bp, a 114-line hap1 FASTA, a 119-line usable hap1 GFA, a no-sequence hap2 GFA containing line `S\th2tg000001l\t*\tLN:i:43860\tLN:i:43860\trd:i:45`, a joint assembly-statistics table containing `# scaffolds\t57\t51`, Compleasm full tables of 3356 lines per haplotype with translated-protein FASTAs of 31142 (hap1) and 23694 (hap2) lines, Compleasm summaries matching `S:0.81%, 27` (hap1) and `S:0.60%, 20` (hap2), and an ~65 kB Nx plot PNG.

## Reference workflow
Galaxy IWC `VGP-assembly-v2/Assembly-Hifi-HiC-phasing-VGP4`, version 0.6 (CC-BY-4.0), part of the Vertebrate Genomes Project assembly suite. Must be preceded by the VGP1 k-mer profiling workflow, which produces the meryl database and GenomeScope summary/model inputs consumed here.
