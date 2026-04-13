---
name: metatranscriptome-denovo-assembly-annotation
description: Use when you have short-read metatranscriptomic or metagenomic Illumina
  data from a microbial community (prokaryotic, eukaryotic, viral, or mixed) with
  no suitable reference genome, and you need to de novo assemble contigs, call ORFs,
  quantify expression per gene, and add functional plus taxonomic annotation.
domain: metagenomics
organism_class:
- bacterial
- eukaryote
- viral
- mixed-community
input_data:
- short-reads-paired
- short-reads-single
source:
  ecosystem: nf-core
  workflow: nf-core/metatdenovo
  url: https://github.com/nf-core/metatdenovo
  version: 1.3.0
  license: MIT
tools:
- fastqc
- trim-galore
- bbduk
- bbnorm
- megahit
- spades
- prodigal
- prokka
- transdecoder
- bbmap
- featurecounts
- eggnog-mapper
- kofamscan
- hmmer
- eukulele
- diamond
- taxonkit
tags:
- metatranscriptomics
- metagenomics
- de-novo-assembly
- orf-calling
- functional-annotation
- taxonomic-annotation
- microbial-community
test_data: []
expected_output: []
---

# De novo metatranscriptome/metagenome assembly and annotation

## When to use this sketch
- Short-read Illumina metatranscriptomic (RNA-seq of a community) or metagenomic data where no reference genome is appropriate.
- Microbial communities — prokaryotic, eukaryotic, viral, or mixed — that must be assembled de novo and then annotated per-ORF.
- You want a single pipeline that goes from raw FASTQ through QC, assembly, ORF calling, per-gene quantification, and both functional and taxonomic annotation.
- Single-organism or single-transcriptome de novo projects where an assembly + quantification + annotation recipe is appropriate (the pipeline does not require a community sample).
- You need standardized, tidy `summary_tables/` TSVs suitable for downstream R/Python analysis across many samples.

## Do not use when
- You already have a reference genome and want read-based variant calling — use a reference-based variant-calling sketch instead.
- You need reference-based bulk RNA-seq quantification against an annotated transcriptome — use an `rna-seq` alignment/quantification sketch.
- You are doing 16S/18S/ITS amplicon profiling — use an `amplicon` (DADA2/QIIME2) sketch.
- You want MAG recovery, binning, and genome-resolved metagenomics (CheckM, MetaBAT, GTDB-Tk on bins) — use a dedicated metagenomic binning sketch.
- Long-read (ONT/PacBio) assembly — this pipeline is built around Illumina short reads.

## Analysis outline
1. Read QC with FastQC and aggregated reporting with MultiQC.
2. Adapter and quality trimming with Trim Galore (optionally skipped via `--skip_trimming`).
3. Optional contaminant/rRNA filtering with BBDuk against a user-supplied FASTA (`--sequence_filter`).
4. Optional digital normalization with BBNorm prior to assembly (`--bbnorm`), used only for the assembly step.
5. Merge trimmed paired-end reads with Seqtk.
6. De novo assembly with Megahit (default) or SPAdes (with a selectable `--spades_flavor` such as `rna`, `meta`, `rnaviral`, `metaviral`). A user-supplied assembly can be injected with `--user_assembly`.
7. ORF calling with Prodigal (default), Prokka (prokaryotes, adds functional annotation), or TransDecoder (eukaryotes); or bring-your-own ORFs via `--user_orfs_faa`/`--user_orfs_gff`.
8. Quantification: BBMap indexes the assembly and maps cleaned reads back; featureCounts produces per-ORF read counts.
9. Functional annotation with eggNOG-mapper and KofamScan (KEGG KOs); optional HMMER `hmmsearch` against user-supplied HMM profiles (`--hmmdir`/`--hmmfiles`).
10. Taxonomic annotation with EUKulele (PhyloDB/MMETSP/GTDB/EukProt) and/or Diamond blastp + TaxonKit LCA against user-supplied Diamond taxonomy databases.
11. Summary statistics and tidy TSVs consolidated under `summary_tables/` (counts, overall stats, emapper, kofamscan, eukulele, diamond taxonomy, hmmrank, prokka annotations).

## Key parameters
- `--input`: CSV samplesheet with `sample,fastq_1,fastq_2` (fastq_2 empty for single-end; same sample name on multiple rows is concatenated).
- `--outdir`: results directory (absolute path on cloud storage).
- `--assembler`: `megahit` (default, low memory) or `spades`; with `--spades_flavor` in {`rna`,`isolate`,`sc`,`meta`,`plasmid`,`metaplasmid`,`metaviral`,`rnaviral`} — pick `rna` for prokaryote metatranscriptomes, `rnaviral` for viral metatranscriptomes, `metaviral` for viral metagenomes.
- `--orf_caller`: `prodigal` (prokaryote ORFs, default), `prokka` (prokaryote ORFs + functional annotation), or `transdecoder` (eukaryotes).
- `--min_contig_length`: drop short contigs before ORF calling/quantification.
- `--bbmap_minid`: mapping identity threshold (default 0.9) for read-to-contig assignment.
- `--sequence_filter`: FASTA of sequences (e.g. rRNA SILVA) to remove with BBDuk before assembly.
- `--bbnorm` with `--bbnorm_target` (default 100) and `--bbnorm_min` (default 5) for digital normalization of the assembly input only.
- Functional annotation: `--skip_eggnog`, `--skip_kofamscan`, `--eggnog_dbpath`, `--kofam_dir`, `--hmmdir`/`--hmmfiles`/`--hmmpattern`.
- Taxonomic annotation: `--skip_eukulele`, `--eukulele_db` in {`phylodb`,`mmetsp`,`marmmetsp`,`gtdb`,`eukprot`}, `--eukulele_dbpath`, `--eukulele_method` (`mets` or `mags`), `--diamond_dbs` CSV/TSV/JSON/YAML of Diamond databases with `db,dmnd_path,taxdump_names,taxdump_nodes[,ranks,parse_with_taxdump]`, and `--diamond_top` (default 10).

## Test data
The bundled `test` profile points at the nf-core/test-datasets `metatdenovo` branch: a small samplesheet of paired-end Illumina FASTQs, a gzipped rRNA FASTA (`rrna.fna.gz`) used via `--sequence_filter`, and four Pfam HMM profiles (PF00317, PF00848, PF03477, PF13597) wired in through `--hmmfiles`. It runs Megahit + Prodigal end-to-end while skipping EUKulele, eggNOG, and KofamScan to keep the test fast. Successful completion produces a Megahit assembly, Prodigal ORFs, BBMap alignments, featureCounts per-ORF counts, HMMER hit tables, a MultiQC report, and consolidated `summary_tables/*.overall_stats.tsv.gz`, `*.counts.tsv.gz`, and `*.hmmrank.tsv.gz` files. The `test_full` profile exercises the same path on a larger samplesheet and additionally runs EUKulele with a preloaded GTDB database plus eggNOG-mapper with a preloaded database.

## Reference workflow
nf-core/metatdenovo v1.3.0 (https://github.com/nf-core/metatdenovo), MIT license; Zenodo DOI 10.5281/zenodo.10666590.
