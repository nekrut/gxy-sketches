---
name: coprolite-host-identification-ancient
description: Use when you need to identify the host species of origin for a (paleo)faeces
  / coprolite shotgun metagenomic sample by combining competitive mapping of endogenous
  host DNA against two or more candidate reference genomes with machine-learning source
  prediction from microbiome taxonomic profiles, including ancient DNA damage estimation.
domain: metagenomics
organism_class:
- eukaryote
- ancient-dna
- metagenome
input_data:
- short-reads-paired
- short-reads-single
- reference-fasta-multi
- kraken2-db
- sourcepredict-sources
source:
  ecosystem: nf-core
  workflow: nf-core/coproid
  url: https://github.com/nf-core/coproid
  version: 2.0.1
  license: MIT
tools:
- fastqc
- fastp
- bowtie2
- samtools
- sam2lca
- pydamage
- damageprofiler
- kraken2
- sourcepredict
- quarto
- multiqc
tags:
- coprolite
- paleofaeces
- ancient-dna
- host-identification
- microbiome
- source-tracking
- adna
- metagenomics
test_data: []
expected_output: []
---

# Coprolite / paleofaeces host identification

## When to use this sketch
- You have shotgun Illumina reads from a suspected coprolite, paleofaeces, or modern faecal sample and need to determine which host species produced it (e.g. human vs. dog vs. pig).
- You have 2-3 candidate host reference genomes (from NCBI, so sam2lca can resolve taxids) and want a principled way to assign genome-specific reads to each.
- Ancient DNA is in scope: you want C→T damage patterns (pyDamage, DamageProfiler) reported per sample/reference to confirm endogenous ancient host DNA.
- You also want an orthogonal microbiome-based host prediction (sourcepredict vs. a reference panel of modern gut metagenomes) and a combined host proportion estimate.
- A prebuilt Kraken2 database and sourcepredict sources/labels CSVs are available or can be downloaded.

## Do not use when
- You only want generic shotgun metagenomic taxonomic profiling with no host-ID question → use a taxprofiler-style sketch instead.
- You are calling variants against a single known host genome → use a short-read variant-calling sketch.
- You are doing de novo metagenome assembly/binning → use a metagenome assembly sketch.
- You have no candidate host genomes, or references are not from NCBI (sam2lca cannot extract taxids) → this pipeline will not work.
- Long-read / ONT data: pipeline is designed for Illumina short reads.

## Analysis outline
1. Read QC with FastQC on raw FASTQs.
2. Adapter and low-complexity trimming with fastp (reads from the same `sample` across lanes are concatenated first).
3. Competitive mapping of trimmed reads against each reference genome in the genomesheet with Bowtie2 (index is built on the fly if not supplied).
4. Lowest-common-ancestor disambiguation of multi-mapping reads across references with sam2lca, keeping only genome-specific reads per taxid.
5. Ancient DNA authentication per sample×reference with pyDamage and DamageProfiler (C→T misincorporation at read termini).
6. Normalisation of mapped reads by reference `genome_size` to produce the host-DNA NormalisedProportion.
7. Taxonomic profiling of unmapped (non-host) reads with Kraken2 against the user-supplied database.
8. Source prediction with sourcepredict: embed sample kmer/read profile against `sp_sources` / `sp_labels` reference panel to get SourcepredictProportion per candidate host.
9. Combine NormalisedProportion (host DNA) and SourcepredictProportion (microbiome) into a final per-sample host call.
10. Aggregate everything into a Quarto HTML report and a MultiQC report.

## Key parameters
- `--input` samplesheet.csv with columns `sample,fastq_1,fastq_2` (fastq_2 blank for single-end; repeated `sample` values are merged).
- `--genome_sheet` CSV with `genome_name,taxid,genome_size,igenome,fasta,index` — one row per candidate host genome; NCBI taxids are mandatory for sam2lca.
- `--kraken2_db` path to a Kraken2 DB directory or `*.tar.gz`.
- `--sp_sources` / `--sp_labels` sourcepredict reference taxid count table and label CSV.
- `--sam2lca_identity` minimum alignment identity for sam2lca LCA assignment, default `0.9` (test profile lowers to `0.8` for damaged/short aDNA reads).
- `--sam2lca_acc2tax` `adnamap` when building a local sam2lca DB from the supplied genomes, `nucl` when pointing `--sam2lca_db` at a pre-built NCBI nucl DB.
- `--sam2lca_db` optional path to a pre-downloaded `~/.sam2lca` directory (required for offline / restricted HPC runs).
- `--taxa_sqlite` / `--taxa_sqlite_traverse_pkl` optional pre-downloaded ete3 taxonomy files to avoid network fetches.
- `--file_prefix` prefix for merged report filenames, default `coproid`.
- Bowtie2 sensitivity can be tuned via `ext.args` on `BOWTIE2_ALIGN` (test profile uses `-N 1 -D 20 -R 3 -L 20 -i S,1,0.50` for aDNA-friendly alignment).

## Test data
The bundled `test` profile pulls a small samplesheet and genomesheet from the `nf-core/test-datasets` `coproid` branch: a handful of Illumina FASTQ libraries (mix of paired- and single-end) together with two small NCBI reference genomes (e.g. *Escherichia coli* taxid 562 and *Bacillus subtilis* taxid 1423) listed in the genomesheet with their taxids and genome sizes. It also fetches a tiny Kraken2 database tarball and sourcepredict `test_sources.csv` / `test_labels.csv` reference panel, plus cached ete3 `taxa.sqlite` files. A successful run produces per-sample fastp/FastQC QC, Bowtie2 BAMs and logs per reference, `sam2lca/<sample>.sam2lca.csv` and a merged `coproid.sam2lca_merged_report.csv`, pyDamage and DamageProfiler reports per sample×reference, Kraken2 per-sample reports and a merged `coproid.kraken2_merged_report.csv`, sourcepredict `coproid.embedding.sourcepredict.csv` and `coproid.report.sourcepredict.csv`, a combined host-proportion table, a `coproid_report/coproid_report.html` Quarto report, and a MultiQC report. The `test_full` profile runs the same pipeline on the full-size samplesheet and genomesheet with matching Kraken2/sourcepredict references.

## Reference workflow
nf-core/coproid v2.0.1 (https://github.com/nf-core/coproid), originally by Maxime Borry & Meriam Van Os, DOI [10.5281/zenodo.2653756](https://doi.org/10.5281/zenodo.2653756).
