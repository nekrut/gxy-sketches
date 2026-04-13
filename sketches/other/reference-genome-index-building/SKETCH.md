---
name: reference-genome-index-building
description: Use when you need to pre-build a complete set of aligner indices and
  auxiliary reference files (BWA, BWA-MEM2, Bowtie1/2, STAR, HISAT2, Salmon, Kallisto,
  RSEM, DRAGMAP, dict, fai, intervals, MSIsensor-pro) from a genome FASTA plus optional
  GTF/GFF3 and VCF, for downstream alignment, RNA-seq, or variant-calling pipelines.
  Not for running an actual alignment or variant analysis.
domain: other
organism_class:
- any
input_data:
- reference-fasta
- gtf-or-gff3
- vcf
source:
  ecosystem: nf-core
  workflow: nf-core/references
  url: https://github.com/nf-core/references
  version: '0.1'
  license: MIT
tools:
- bwa
- bwa-mem2
- bowtie1
- bowtie2
- star
- hisat2
- salmon
- kallisto
- rsem
- dragmap
- gatk4
- samtools
- gffread
- msisensor-pro
- tabix
tags:
- reference
- index
- igenomes
- aligner-index
- preprocessing
- genome-assets
test_data: []
expected_output: []
---

# Reference genome index building

## When to use this sketch
- You have a genome FASTA (and optionally a GTF/GFF3 annotation and/or VCF) and need to produce a complete bundle of aligner indices and auxiliary files for reuse across many downstream pipelines.
- You want to replicate / replace AWS iGenomes assets for a new or custom organism (bacterial, viral, plant, vertebrate — any ploidy).
- You need only a subset of indices (e.g. just STAR + Salmon for RNA-seq, or just BWA + dict + fai + intervals for variant calling) and want to select them via the `tools` parameter.
- You want tabix-indexed VCFs alongside the FASTA-derived assets.

## Do not use when
- You want to actually align reads, call variants, quantify transcripts, or run any downstream analysis — use the matching analysis sketch (e.g. `haploid-variant-calling-bacterial`, `bulk-rnaseq-star-salmon`, `single-cell-10x-cellranger`) which will consume these indices.
- You only need a single index on-the-fly inside a larger workflow — most nf-core analysis pipelines build what they need internally from a FASTA/GTF.
- You need to download or curate raw reference sequences from NCBI/Ensembl — this sketch assumes the FASTA/GTF/VCF already exist at a known location.

## Analysis outline
1. Parse a YAML/CSV/TSV samplesheet describing one or more reference genomes (each with `fasta`, optional `gtf`/`gff3`, optional `vcf`, and metadata).
2. If only a GFF3 is supplied, convert it to GTF with `gffread`.
3. From the FASTA, build core sequence assets: `samtools faidx` (→ `.fai`), `samtools` sizes, `gatk4 CreateSequenceDictionary` (→ `.dict`), and `gatk4` intervals BED.
4. Build the requested DNA aligner indices: `bowtie1-build`, `bowtie2-build`, `bwa index`, `bwa-mem2 index`, `dragmap` hashtable.
5. Build MSIsensor-pro microsatellite list from the FASTA.
6. If a GTF is supplied, build transcriptome/RNA-seq assets: `hisat2-build` index, `hisat2_extract_splice_sites.py` splice sites, `STAR --runMode genomeGenerate`, `rsem-prepare-reference` (and `rsem-refseq-extract-primary-assembly` → transcript FASTA), `kallisto index`, `salmon index`.
7. If a VCF is supplied, compress/index it with `tabix`.
8. Publish all built assets under `--outdir`, organised per genome, ready to be referenced by downstream pipelines or uploaded to an S3/iGenomes-style bucket.

## Key parameters
- `input`: path to a samplesheet (CSV/TSV/YAML/YML) describing each reference (FASTA + optional GTF/GFF3/VCF + genome metadata). Required.
- `outdir`: output directory (absolute path for cloud storage). Required.
- `tools`: comma-separated subset of builders to run. Allowed values: `bowtie1, bowtie2, bwamem1, bwamem2, createsequencedictionary, dragmap, faidx, gffread, hisat2, hisat2_extractsplicesites, intervals, kallisto, msisensorpro, rsem, rsem_make_transcript_fasta, salmon, sizes, star, tabix`. Omit to build everything applicable to the supplied inputs.
- `kallisto_make_unique`: boolean, passes `--make-unique` to `kallisto index` when transcript names collide.
- `-profile`: one of `docker`, `singularity`, `podman`, `conda`, etc. (standard nf-core profile selection).

## Test data
The bundled `test` profile points at a single-genome YAML manifest, `GRCh38_chr21.yml`, hosted under the `nf-core/test-datasets` `references` branch. It describes a chromosome-21-only slice of human GRCh38 along with a matching GTF, and is small enough to run end-to-end under the pipeline's 4 CPU / 15 GB / 1 h resource cap. Running `nextflow run nf-core/references -profile test,docker --outdir results` is expected to produce, under `results/GRCh38_chr21/`, a FASTA `.fai`, sizes file, GATK `.dict`, intervals BED, every requested aligner index directory (BWA, BWA-MEM2, Bowtie1/2, DRAGMAP, STAR, HISAT2 with splice sites, Salmon, Kallisto, RSEM with transcript FASTA), an MSIsensor-pro list, and a MultiQC run report. The `test_full` profile uses the same manifest at full resolution for AWS CI.

## Reference workflow
nf-core/references v0.1 (dev) — https://github.com/nf-core/references. Reference assets live in the companion repo https://github.com/nf-core/references-assets. Tool versions follow the nf-core modules pinned in that release.
