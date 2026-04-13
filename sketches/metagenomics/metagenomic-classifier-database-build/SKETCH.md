---
name: metagenomic-classifier-database-build
description: Use when you need to build custom reference databases for one or more
  metagenomic taxonomic classifiers/profilers (Kraken2, Bracken, Centrifuge, DIAMOND,
  ganon, Kaiju, KMCP, KrakenUniq, MALT, sourmash, sylph, MetaCache) from the same
  set of reference genomes, typically as a companion step before running taxprofiler
  on shotgun metagenomic reads.
domain: metagenomics
organism_class:
- bacterial
- viral
- eukaryote
input_data:
- reference-fasta-nucleotide
- reference-fasta-protein
- ncbi-taxonomy-dump
- accession2taxid
source:
  ecosystem: nf-core
  workflow: nf-core/createtaxdb
  url: https://github.com/nf-core/createtaxdb
  version: 2.1.0
  license: MIT
tools:
- kraken2
- bracken
- centrifuge
- diamond
- ganon
- kaiju
- kmcp
- krakenuniq
- malt
- sourmash
- sylph
- metacache
tags:
- metagenomics
- database-build
- taxonomy
- classifier
- reference
- taxprofiler
- kraken2
- diamond
test_data: []
expected_output: []
---

# Metagenomic classifier database construction

## When to use this sketch
- You have a curated set of reference genomes (nucleotide and/or protein FASTAs) and need to turn them into indexed databases for one or more metagenomic classifiers.
- You want to build databases for several tools (e.g. Kraken2 + Bracken + DIAMOND + ganon) from the *same* reference set in a single parallelised run.
- You are preparing custom databases to feed into nf-core/taxprofiler or an equivalent taxonomic profiling workflow.
- You have (or can obtain) NCBI-style taxonomy files: `nodes.dmp`, `names.dmp`, `nucl_gb.accession2taxid`, and/or `prot.accession2taxid`.
- You need both a nucleotide database (e.g. Kraken2, Centrifuge, sylph) and a protein database (e.g. DIAMOND, Kaiju) built consistently.

## Do not use when
- You want to *classify* reads against an existing database — that is a taxonomic profiling task; use a taxprofiler/metagenomic-profiling sketch instead.
- You only need a generic genome index for read alignment (BWA/Bowtie2) rather than a k-mer/taxonomy classifier index.
- You want de novo metagenome assembly and binning — use a metagenomic-assembly sketch.
- You are doing 16S/amplicon taxonomy assignment against SILVA/GTDB — use an amplicon-classification sketch.
- You want pre-built standard databases (RefSeq, Standard-8, etc.) downloaded rather than built from your own FASTAs — fetch them directly from the tool authors instead of running this pipeline.

## Analysis outline
1. Parse the input samplesheet CSV (`id,taxid,fasta_dna,fasta_aa`) listing each reference genome with its taxonomy ID and FASTA path(s).
2. Decompress any gzipped FASTAs in batches (`unzip_batch_size`) and concatenate per-type into combined nucleotide / amino-acid FASTAs as required by each builder (SeqKit2).
3. For each enabled `--build_<tool>` flag, build the corresponding database in parallel using the shared taxonomy files (`nodes.dmp`, `names.dmp`, `accession2taxid`, `nucl2taxid`, `prot2taxid`):
   - **Kraken2** (`kraken2-build`) — nucleotide k-mer database; optionally extended with **Bracken** (`bracken-build`) which reuses the Kraken2 library/taxonomy.
   - **KrakenUniq** (`krakenuniq-build`) — k-mer database with unique-kmer counting.
   - **Centrifuge** (`centrifuge-build`) — nucleotide FM-index.
   - **ganon** (`ganon buildcustom`) — HIBF bloom filter index + taxonomy tree.
   - **KMCP** (`kmcp compute` + `kmcp index`) — nucleotide pseudo-mapping index.
   - **sylph** (`sylph sketch`) — nucleotide multi-genome sketch `.syldb`.
   - **MetaCache** (`metacache build`) — locality-sensitive hashing signature DB.
   - **MALT** (`malt-build`) — nucleotide or protein DB using a MEGAN mapping file (`malt_mapdb` + `malt_mapdb_format`).
   - **DIAMOND** (`diamond makedb`) — protein `.dmnd` database.
   - **Kaiju** (`kaiju-mkbwt` + `kaiju-mkfmi`) — protein FMI index.
   - **sourmash** (`sourmash sketch dna` / `sketch protein`) — SBT signatures for DNA and/or protein.
4. Optionally emit pre-filled downstream samplesheets (currently nf-core/taxprofiler) via `--generate_downstream_samplesheets --generate_pipeline_samplesheets taxprofiler`.
5. Aggregate build logs and tool versions into a MultiQC report.

## Key parameters
- `--input samplesheet.csv` — CSV with columns `id,taxid,fasta_dna,fasta_aa` (at least one FASTA column populated per row).
- `--dbname <prefix>` — prefix for all produced database files (required).
- `--outdir <dir>` — output root; each tool writes to its own subdirectory.
- Taxonomy inputs: `--nodesdmp`, `--namesdmp`, `--accession2taxid` (4-column `nucl_gb.accession2taxid`), `--nucl2taxid` (2-col; required for Centrifuge, optional for Kraken2), `--prot2taxid` (2-col; for protein tools).
- Build toggles (at least one required, no default): `--build_kraken2`, `--build_bracken` (implies Kraken2 with intermediates), `--build_krakenuniq`, `--build_centrifuge`, `--build_diamond`, `--build_ganon`, `--build_kaiju`, `--build_kmcp`, `--build_malt`, `--build_sourmash_dna`, `--build_sourmash_protein`, `--build_sylph`, `--build_metacache`.
- Per-tool build-option passthroughs (must be quoted): e.g. `--kraken2_build_options '--kmer-len 45'`, `--ganon_build_options '--kmer-size 45'`, `--diamond_build_options '--no-parse-seqids'`, `--krakenuniq_build_options '--jellyfish-bin "$(which jellyfish)"'`.
- MALT-specific: `--malt_build_options '--sequenceType DNA'` (or `Protein`), `--malt_mapdb` + `--malt_mapdb_format` (one of `mdb`, `a2t`, `s2t`, `a2seed`, ...) — required for MALT only.
- sourmash defaults: `--sourmash_build_dna_options "--param-string 'scaled=1000,k=31,noabund'"`, `--sourmash_build_protein_options "--param-string 'scaled=200,k=10,noabund'"`, `--sourmash_batch_size 100`.
- Housekeeping: `--unzip_batch_size 10000` (FASTA decompression batching), `--save_concatenated_fastas`, `--kraken2_keepintermediate`, `--kaiju_keepintermediate`, `--krakenuniq_keepintermediate`.
- Profile: `-profile docker` / `singularity` / `conda` / institutional — containers strongly recommended due to the many tool builds.

## Test data
The pipeline's `test` profile uses a small samplesheet from the nf-core test-datasets repo (`createtaxdb/samplesheets/samplesheet_test.csv`) listing a handful of tiny reference genomes with both nucleotide and amino-acid FASTAs and associated taxids. Taxonomy inputs are miniaturised NCBI-style files (`nodes.dmp`, `names.dmp`, `nucl_gb.accession2taxid`, `nucl2tax.map`, `prot.accession2taxid.gz`) plus a zipped MALT MEGAN mapping file (`nucl_acc2tax-Jul2019.abin.zip`, format `a2t`). With all `build_*` flags enabled, running the profile yields per-tool subdirectories under `<outdir>/` — e.g. `kraken2/database/{hash,opts,taxo}.k2d`, `bracken/database/database100mers.kmer_distrib`, `diamond/database.dmnd`, `ganon/database.{hibf,tax}`, `kaiju/database.fmi`, `centrifuge/database-centrifuge/*.cf`, `kmcp/database-kmcp-index/`, `krakenuniq/database.{idx,kdb}` + `taxDB`, `malt/malt_index/`, `sourmash/database-sourmash-{dna,protein}-*mer.sbt.zip`, `sylph/database-sylph.syldb`, `metacache/database.{meta,cache0}` — plus a MultiQC report and a `downstream_samplesheets/taxprofiler.csv` ready to feed into nf-core/taxprofiler.

## Reference workflow
nf-core/createtaxdb v2.1.0 (https://github.com/nf-core/createtaxdb, DOI 10.5281/zenodo.15696114). Companion pipeline to nf-core/taxprofiler. Requires Nextflow ≥ 25.04.2.
