---
name: ecdna-identification-eukaryotic
description: Use when you need to detect extrachromosomal circular DNAs (ecDNAs/eccDNAs)
  in eukaryotic samples from short-read Illumina Circle-seq, ATAC-seq, or WGS data.
  Covers junction-based detection of small eccDNAs via Circle-Map, CIRCexplorer2,
  or Circle_finder against a reference genome.
domain: structural-variants
organism_class:
- eukaryote
- vertebrate
input_data:
- short-reads-paired
- reference-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/circdna
  url: https://github.com/nf-core/circdna
  version: 1.1.0
  license: MIT
tools:
- fastqc
- trim-galore
- bwa-mem
- samtools
- picard-markduplicates
- circle-map
- circexplorer2
- circle-finder
- unicycler
- minimap2
- multiqc
tags:
- ecdna
- eccdna
- circular-dna
- circle-seq
- atac-seq
- wgs
- junctions
- nf-core
test_data: []
expected_output: []
---

# Eukaryotic ecDNA / eccDNA identification from short reads

## When to use this sketch
- You have paired-end Illumina Circle-seq, ATAC-seq, or WGS data from a eukaryotic sample (human, mouse, etc.) and want to discover extrachromosomal circular DNAs.
- You want junction-level detection of small eccDNAs/microDNAs against a reference genome (GRCh37/GRCh38/mm10) using Circle-Map Realign, Circle-Map Repeats, CIRCexplorer2, or Circle_finder.
- You optionally want to de novo assemble circular contigs from Circle-seq reads with Unicycler and map them back with Minimap2.
- Inputs are FASTQ (paired-end) or pre-aligned BAM, described in a 2- or 3-column samplesheet CSV (`sample,fastq_1,fastq_2` or `sample,bam`).

## Do not use when
- You need to reconstruct large focal amplicons / classify ecDNA amplicons from WGS using AmpliconArchitect + AmpliconClassifier — use a dedicated `focal-amplicon-ecdna-ampliconarchitect` sketch (still an nf-core/circdna branch, but requires the AA data repo and Mosek license).
- You are looking for circular RNAs from RNA-seq back-splicing — use a circRNA-from-rnaseq sketch; CIRCexplorer2 here is repurposed on DNA alignments.
- You are assembling bacterial plasmids or phage circles — use a bacterial assembly sketch (e.g. nf-core/bacass).
- You want germline/somatic SNV calling or general structural variant discovery — use variant-calling / SV sketches.
- Your input is long-read (ONT/PacBio) — this pipeline expects short reads.

## Analysis outline
1. Concatenate re-sequenced FASTQs per sample (`cat`) when multiple lanes share a sample ID.
2. Raw-read QC with FastQC.
3. Adapter and quality trimming with Trim Galore (Cutadapt).
4. Align paired reads to the reference with BWA-MEM; sort and index with SAMtools.
5. Mark duplicates with Picard/GATK MarkDuplicates; by default filter duplicates with `samtools view` (Circle_finder branch requires duplicates kept — set `--keep_duplicates false` is NOT used for it).
6. Run one or more ecDNA identifier branches selected via `--circle_identifier`:
   - `circle_map_realign`: Circle-Map ReadExtractor → Circle-Map Realign → per-sample `*_circularDNA_coordinates.bed`.
   - `circle_map_repeats`: Circle-Map ReadExtractor → Circle-Map Repeats → `*_circularDNA_repeats_coordinates.bed`.
   - `circexplorer2`: CIRCexplorer2 parse on the BAM → `*.circexplorer_circdna.bed`.
   - `circle_finder`: Samblaster split/discordant extraction → Circle_finder → `*.microDNA-JT.txt` BED-like table (uses unfiltered BAM).
   - `unicycler`: de novo assembly of circular contigs with Unicycler, then Minimap2 mapping back to reference (`.paf`).
7. Aggregate QC across FastQC, Trim Galore, SAMtools stats/flagstat/idxstats, MarkDuplicates with MultiQC.

## Key parameters
- `--input`: path to samplesheet CSV (required).
- `--input_format`: `FASTQ` (default) or `BAM`.
- `--bam_sorted`: set true if supplying already-sorted BAMs to skip re-sorting.
- `--outdir`: absolute output path (required).
- `--genome` or `--fasta` (+ optional `--bwa_index`): reference; set `--igenomes_ignore true` when supplying a custom FASTA.
- `--circle_identifier`: comma-separated list from `circle_map_realign,circle_map_repeats,circexplorer2,circle_finder,unicycler,ampliconarchitect` (required). Pick branches matching your data class — Circle-seq/ATAC-seq for the first four and Unicycler; WGS for ampliconarchitect.
- `--skip_markduplicates` / `--keep_duplicates`: control duplicate handling; Circle_finder specifically depends on unfiltered BAM (`--keep_duplicates true`).
- `--save_markduplicates_bam`, `--save_circle_map_intermediate`, `--save_circle_finder_intermediate`, `--save_unicycler_intermediate`: retain intermediates per branch.
- `--skip_trimming`, `--clip_r1/--clip_r2`, `--three_prime_clip_r1/r2`, `--trim_nextseq`: Trim Galore tuning.
- `--skip_qc`, `--skip_multiqc`: QC control.
- AmpliconArchitect-only (not covered by this sketch): `--aa_data_repo`, `--mosek_license_dir`, `--reference_build`, `--aa_cngain` (default 4.5), `--cnvkit_cnn`.

## Test data
The nf-core/circdna `test` profile streams a tiny paired-end FASTQ samplesheet and a small genome FASTA from the `nf-core/test-datasets` `circdna` branch, with `igenomes_ignore = true` and `skip_markduplicates = false`. It runs every non-AmpliconArchitect branch at once (`circle_identifier = 'circexplorer2,circle_finder,circle_map_realign,circle_map_repeats,unicycler'`) against `reference_build = GRCh38`, capped at 2 CPUs / 6 GB / 6 h so it fits GitHub Actions. A successful run produces per-sample BED/TXT outputs under `results/circlemap/realign/*_circularDNA_coordinates.bed`, `results/circlemap/repeats/*_circularDNA_repeats_coordinates.bed`, `results/circexplorer2/*.circexplorer_circdna.bed`, `results/circlefinder/*.microDNA-JT.txt`, Unicycler assemblies plus a Minimap2 `.paf`, and a MultiQC HTML aggregating FastQC/Trim Galore/SAMtools/MarkDuplicates metrics.

## Reference workflow
nf-core/circdna v1.1.0 (https://github.com/nf-core/circdna), DOI 10.5281/zenodo.8085422. See `docs/usage.md`, `docs/output.md`, and `nextflow_schema.json` for the authoritative parameter list.
