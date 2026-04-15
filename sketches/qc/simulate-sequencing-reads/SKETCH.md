---
name: simulate-sequencing-reads
description: "Use when you need to generate synthetic FASTQ files for benchmarking,\
  \ pipeline testing, or method development \u2014 specifically simulating Illumina\
  \ amplicon (metabarcoding), target-capture (UCE/bait), metagenomic, or whole-genome\
  \ short reads from a reference FASTA. Not for analyzing real sequencing data."
domain: qc
organism_class:
- eukaryote
- bacterial
- viral
input_data:
- reference-fasta
- samplesheet-csv
source:
  ecosystem: nf-core
  workflow: nf-core/readsimulator
  url: https://github.com/nf-core/readsimulator
  version: 1.0.1
  license: MIT
  slug: readsimulator
tools:
- name: art_illumina
- name: crabs
- name: capsim
- name: bowtie2
- name: samtools
- name: insilicoseq
- name: wgsim
- name: fastqc
  version: 0.12.1
- name: multiqc
  version: '1.21'
- name: ncbi-genome-download
  version: 0.3.3
tags:
- simulation
- synthetic-reads
- benchmarking
- amplicon
- target-capture
- metagenome
- wgs
- illumina
- pacbio
test_data: []
expected_output: []
---

# Simulate sequencing reads (amplicon / capture / metagenome / WGS)

## When to use this sketch
- You need synthetic FASTQ data to benchmark or stress-test a downstream pipeline.
- You want to generate simulated reads from a known reference FASTA so truth is available.
- You need to produce one of four read classes from the same samplesheet-driven framework:
  - **Amplicon / metabarcoding** Illumina reads (e.g. eDNA, 16S-style primers) via CRABS in-silico PCR + ART.
  - **Target-capture** reads (UCE bait sets, custom probe FASTA/BED) as Illumina or PacBio via Japsa CapSim.
  - **Metagenomic** Illumina reads from a community of genomes via InSilicoSeq.
  - **Whole-genome** Illumina paired reads from a single reference via wgsim.
- You want per-sample reproducibility driven by explicit RNG seeds.
- You want FastQC + MultiQC QC reports on the simulated reads out of the box.

## Do not use when
- You are analyzing real experimental reads — this pipeline only *creates* FASTQs, it does not call variants, assemble, classify taxa, or quantify expression. Use a domain-specific sketch (haploid-variant-calling-bacterial, bacterial-assembly, metagenome-taxonomic-profiling, bulk-rna-seq, etc.) for downstream analysis.
- You need long-read ONT simulation — this pipeline only supports Illumina (ART / InSilicoSeq / wgsim / CapSim-Illumina) and PacBio target capture (CapSim-PacBio). For ONT simulation use a different tool.
- You need to simulate structural variants, tumor/normal mixtures, or somatic mutation spike-ins — wgsim only models a flat point mutation + indel rate.
- You need bisulfite, Hi-C, ATAC, or single-cell read simulation — not supported.

## Analysis outline
1. Prepare a samplesheet CSV with columns `sample,seed` — one row per simulated sample, with an integer RNG seed.
2. Provide (or let the pipeline fetch) a reference: `--fasta <path>`, or `--genome <iGenomes ID>`, or `--ncbidownload_accessions` / `--ncbidownload_taxids` which invoke `ncbi-genome-download`.
3. Select one (or more) simulation modes via the boolean flags `--amplicon`, `--target_capture`, `--metagenome`, `--wholegenome`.
4. **Amplicon branch**: CRABS `db_import` → CRABS `insilico_pcr` with forward/reverse primers → `art_illumina` to generate paired FASTQs per amplicon.
5. **Target-capture branch**: unzip probe FASTA (or extract from BED via bedtools) → `bowtie2` align probes to reference → `samtools` index BAM → Japsa `capsim` in Illumina or PacBio mode.
6. **Metagenome branch**: `iss generate` (InSilicoSeq) against the genome set with a chosen abundance/error model.
7. **WGS branch**: `wgsim` against the reference FASTA to produce paired Illumina reads.
8. For every branch: build a samplesheet of FASTQ paths, run `FastQC` on all reads, aggregate with `MultiQC`.

## Key parameters
- Mode selectors (at least one required): `--amplicon`, `--target_capture`, `--metagenome`, `--wholegenome`.
- Amplicon: `--amplicon_fw_primer` (default `GTCGGTAAAACTCGTGCCAGC`), `--amplicon_rv_primer` (default `CATAGTGGGGTATCTAATCCCAGTTTG`), `--amplicon_read_count` (default 500), `--amplicon_read_length` (default 130), `--amplicon_seq_system` (default `HS25`; one of GA1/GA2/HS10/HS20/HS25/HSXn/HSXt/MinS/MSv1/MSv3/NS50), `--amplicon_crabs_ispcr_error` (default 4.5).
- Target capture: `--probe_file` or `--probe_ref_name` (default `Tetrapods-UCE-5Kv1`; ultraconserved bait sets for tetrapods, fish, arachnids, coleoptera, diptera, hemiptera, hymenoptera, anthozoa), `--target_capture_mode` (`illumina`|`pacbio`, default `illumina`), `--target_capture_fmedian` 500, `--target_capture_smedian` 1300, `--target_capture_num` 500000, `--target_capture_illen` 150, `--target_capture_pblen` 30000, `--target_capture_ilmode` (`pe`|`mp`|`se`).
- Metagenome: `--metagenome_abundance` (default `lognormal`, also `uniform`/`halfnormal`/`exponential`/`zero_inflated_lognormal`) or explicit `--metagenome_abundance_file` TSV, `--metagenome_coverage[_file]`, `--metagenome_input_format` (`genomes`|`draft`), `--metagenome_n_reads` (default `1M`, accepts K/M/G suffix), `--metagenome_mode` (`kde`|`basic`), `--metagenome_model` (`MiSeq`|`HiSeq`|`NovaSeq`), `--metagenome_gc_bias`.
- WGS: `--wholegenome_n_reads` (default 1,000,000 pairs), `--wholegenome_r1_length`/`--wholegenome_r2_length` (default 70), `--wholegenome_outer_dist` 500, `--wholegenome_standard_dev` 50, `--wholegenome_error_rate` 0.02, `--wholegenome_mutation_rate` 0.001, `--wholegenome_indel_fraction` 0.15, `--wholegenome_indel_extended` 0.3.
- Reference provisioning: `--fasta`, `--genome`, `--ncbidownload_accessions`, `--ncbidownload_taxids`, `--ncbidownload_group` (refseq taxonomy group), `--ncbidownload_section` (`refseq`|`genbank`).

## Test data
The pipeline's `test` profile uses a two-sample samplesheet (`sample,seed` rows) hosted in `nf-core/test-datasets` and a single small reference FASTA (`GCF_024334085.1_ASM2433408v1_genomic.fna.gz`). The `test_full` profile turns on all four simulation branches simultaneously with short custom primers (`AAAATAAT`/`GATTACTTT`), 1000 amplicon reads, 100K metagenome reads, and the `Diptera-2.7Kv1` UCE probe set. Successful runs produce per-sample paired FASTQ files under `art_illumina/`, `capsim_illumina/` or `capsim_pacbio/`, `insilicoseq/`, and `wgsim/`, a driver samplesheet listing the generated FASTQ paths, FastQC HTML/zip per sample, and a consolidated `multiqc/multiqc_report.html`.

## Reference workflow
nf-core/readsimulator v1.0.1 (https://github.com/nf-core/readsimulator), MIT licensed. Underlying simulators: ART (Huang 2012), Japsa CapSim (Cao 2018), CRABS (Jeunen 2022), InSilicoSeq (Gourlé 2018), wgsim (Li), with Bowtie2 + SAMtools + bedtools for probe handling and FastQC + MultiQC for QC aggregation.
