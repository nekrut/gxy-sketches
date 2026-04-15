---
name: ssds-single-stranded-dna-sequencing
description: Use when analyzing Single-Stranded DNA Sequencing (SSDS) libraries to
  map ssDNA-derived fragments (e.g. meiotic DSB hotspots via DMC1/RAD51 ChIP, or replication
  origins) from paired-end Illumina reads. Classifies ssDNA vs dsDNA fragments using
  the characteristic SSDS end-repair micro-homology signature and computes enrichment
  at user-supplied genomic intervals.
domain: epigenomics
organism_class:
- eukaryote
- vertebrate
input_data:
- short-reads-paired
- reference-fasta
- intervals-bed
source:
  ecosystem: nf-core
  workflow: nf-core/ssds
  url: https://github.com/nf-core/ssds
  version: dev
  license: MIT
  slug: ssds
tools:
- name: fastqc
  version: 0.11.9
- name: trim-galore
  version: 0.6.7
- name: bwa-mem
- name: picard
- name: samtools
- name: ssds_pipeline_accessory_scripts
- name: bedtools
- name: ucsc-bedgraphtobigwig
- name: deeptools
- name: multiqc
  version: '1.11'
tags:
- ssds
- ssdna
- meiotic-recombination
- dsb-hotspots
- dmc1
- replication-origins
- chip-seq
- paired-end
test_data: []
expected_output: []
---

# SSDS (Single-Stranded DNA Sequencing) analysis

## When to use this sketch
- You have paired-end Illumina FASTQs from an SSDS library (e.g. DMC1 or RAD51 ChIP-SSDS for meiotic double-strand break hotspots, or SSDS for mapping replication origins).
- You need to identify which read pairs are unambiguously derived from ssDNA using the characteristic 5' micro-homology / fill-in signature introduced by the SSDS end-repair protocol.
- You want per-sample ssDNA/dsDNA-split BAMs and BEDs of fragments, stranded coverage bigWigs, and SPoT (Signal Portion of Tags) enrichment at a defined set of BED intervals.
- Typical organisms: mouse, human, or other vertebrate genomes supported via iGenomes (e.g. `mm10`, `GRCh38`).

## Do not use when
- You have a standard ChIP-seq / ATAC-seq / CUT&RUN library without the SSDS end-repair chemistry — the ssDNA classifier will not be meaningful; use a generic ChIP-seq sketch instead.
- You have single-end reads: SSDS classification requires paired-end data to detect the micro-homology structure, and the pipeline will reject single-end input.
- You want peak calling / hotspot calling itself — this sketch stops at fragment BEDs and coverage tracks; downstream peak calling (e.g. MACS2, hotspot-specific callers) is a separate step.
- You need variant calling, assembly, or RNA quantification — pick the appropriate domain-specific sketch.

## Analysis outline
1. Raw read QC with FastQC.
2. Adapter and quality trimming with Trim Galore.
3. Align paired reads to the reference genome with BWA-MEM (index auto-built from `--fasta` if `--bwa` is not provided).
4. Coordinate-sort and mark duplicates with Picard; index with Samtools.
5. Parse the aligned BAM with the SSDS accessory scripts to classify read pairs as ssDNA vs unclassified (default `ss` mode) — or into five fragment classes in `all` mode — and emit per-class BAM and BED files.
6. Build stranded genome coverage tracks (FWD/REV/TOT and log2(FWD/REV)) with bedtools genomecov + UCSC `bedGraphToBigWig`.
7. Compute SPoT enrichment: fraction of each fragment class falling within user-supplied BED intervals defined in `conf/spot_intervals.conf`.
8. Additional coverage QC with deepTools.
9. Aggregate all metrics (FastQC, trimming, SSDS fragment composition, fragment property distributions, SPoT) into a MultiQC HTML report.

## Key parameters
- `--input samplesheet.csv`: CSV with header `sample,fastq_1,fastq_2`; paired-end only, one row per library (pool resequencing runs beforehand).
- `--genome mm10` (or another iGenomes ID) OR `--fasta <path>` plus optional `--bwa <bwa_index_dir>` — one of these reference routes is mandatory.
- `--spot_intervals conf/spot_intervals.conf`: config file listing BED files of genomic intervals (e.g. known hotspots) for SPoT enrichment testing; default points to the bundled config.
- `--spot_intervals_genome mm10`: key into the `spot_intervals` config selecting which interval set to use; falls back to the value of `--genome` if omitted.
- `--parse_extra_types false` (default): when true, switches the SSDS parser from `ss` mode (ssDNA + unclassified) to `all` mode, emitting type-2 ssDNA, high- and low-confidence dsDNA as additional low-confidence classes — use only if you understand that only type-1 ssDNA is unambiguous.
- `-profile docker|singularity|conda`: container/runtime selection; `test` profile runs a tiny sarscov2 demo.

## Test data
The `test` profile (`conf/test.config`) runs on a minimal paired-end Illumina FASTQ samplesheet borrowed from the nf-core viralrecon test-datasets (`samplesheet_test_illumina_sispa.csv`) aligned against a SARS-CoV-2 genome FASTA from the nf-core modules test-datasets, with a `spot_intervals` config from the `ssds` test-datasets branch keyed to `sarscov2`. It is capped at 2 CPUs / 6 GB / 6 h so it fits on GitHub Actions, and is only intended to verify that the pipeline graph executes end-to-end: FastQC HTML/zip, trimmed reads, sorted BAMs, per-class `<sample>.ssDNA.bam`/`.unclassified.bam` (+ BEDs), FWD/REV/TOT/FR bigWigs, SSDS fragment and SPoT reports, and a final `multiqc/multiqc_report.html`. The full-size profile (`conf/test_full.config`) runs real mouse SSDS samples against `mm10` with the mouse SPoT intervals.

## Reference workflow
nf-core/ssds (dev), https://github.com/nf-core/ssds — originally written by Kevin Brick. SSDS method: Khil et al., Genome Research 2012 (doi:10.1101/gr.130583.111); applications to meiotic DSB hotspots (Brick et al., Nature 2012) and replication origins (Pratto et al., Cell 2021).
