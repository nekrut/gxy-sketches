---
name: pathogen-surveillance-unknown-gdna
description: Use when you have raw gDNA sequencing reads (Illumina short-read or Nanopore/PacBio
  long-read) from one or more unknown bacterial or eukaryotic pathogen samples and
  need automated species identification, reference selection, variant calling, and
  a contextual phylogeny in one pass. Designed for diagnosticians and population-genomics
  users who do not want to pick references manually.
domain: variant-calling
organism_class:
- bacterial
- eukaryote
- haploid
- diploid
input_data:
- short-reads-paired
- short-reads-single
- long-reads-ont
- long-reads-pacbio
- sra-accession
source:
  ecosystem: nf-core
  workflow: nf-core/pathogensurveillance
  url: https://github.com/nf-core/pathogensurveillance
  version: 1.1.0
  license: MIT
tools:
- fastp
- sourmash
- bbmap-sendsketch
- spades
- flye
- bakta
- busco
- pirate
- bwa-mem
- picard
- graphtyper
- mafft
- iqtree2
- quast
- fastqc
- multiqc
tags:
- pathogen-id
- biosurveillance
- auto-reference
- population-genomics
- snp-phylogeny
- core-gene-phylogeny
- ani
- refseq
- unknown-sample
test_data: []
expected_output: []
---

# Automated pathogen identification and surveillance from unknown gDNA

## When to use this sketch
- User has FASTQ reads from one or more prokaryote or eukaryote isolates and does not know (or does not want to manually pick) the best reference genome.
- The goal is end-to-end: QC → assembly → species ID → reference download from NCBI RefSeq → read mapping → variant calling → contextual phylogeny → HTML report.
- Inputs can be mixed: local FASTQs, SRA accessions, or NCBI SRA search queries, and both Illumina short-read and Nanopore/PacBio long-read data in the same run.
- Multiple samples from the same outbreak / survey that the user wants placed on a SNP tree and a gene-based tree with automatically chosen context references.
- The user wants a single HTML report suitable for non-bioinformaticians, optionally split into report groups.
- Ploidy is low (default 1, configurable per sample via the samplesheet `ploidy` column — e.g. 2 for a diploid fungus).

## Do not use when
- Input is viral sequence — this pipeline explicitly excludes viruses.
- Input is not genomic DNA (assembled FASTA only, RNA-seq, RAD-seq, ChIP-seq, amplicon/16S) — use the appropriate domain-specific sketch instead (e.g. an RNA-seq or 16S amplicon sketch).
- Samples are mixed communities / metagenomes — use a metagenomics profiling sketch.
- You already know the exact reference and only want plain variant calling against it — use a leaner reference-based variant-calling sketch (e.g. `haploid-variant-calling-bacterial`) rather than paying the cost of sourmash-based reference discovery and core-gene phylogeny.
- You need fine-grained control over each tool's parameters or to benchmark callers — this pipeline is intentionally opinionated.
- You need structural-variant or CNV analysis — graphtyper here is configured for SNVs/small indels.

## Analysis outline
1. Parse samplesheet (`--input` CSV/TSV); optionally fetch reads from SRA by accession or NCBI query.
2. Read QC and adapter trimming with `fastp` (short reads) plus `fastqc`/`nanoplot` reporting.
3. Subsample reads to `max_depth` (default 100×) to bound runtime.
4. Assemble with `spades` (short reads) or `flye` (long reads); skip samples below `min_bases_to_assemble`.
5. Assess assemblies with `quast`; for eukaryotes run `busco` for completeness and single-copy ortholog extraction.
6. Initial ID with `bbmap sendsketch`; compute FracMinHash signatures with `sourmash sketch` and pairwise ANI with `sourmash compare`.
7. Query NCBI assembly DB and auto-select RefSeq references per sample using the `n_ref_*` quotas and `ref_min_ani` threshold; download via the persistent `data_dir` cache.
8. Annotate prokaryotic samples and references with `bakta` (light or full DB).
9. Cluster orthologs across prokaryote samples+refs with `pirate`; compute POCP pairwise matrix.
10. Align shared core genes (prokaryotes) or BUSCO genes (eukaryotes) with `mafft` and build gene trees with `iqtree2`, capped by `phylo_max_genes`.
11. Map reads to the selected per-sample reference with `bwa mem`, sort/mark duplicates with `picard`, index with `samtools`.
12. Call variants with `graphtyper genotype`, filter, and emit per-sample consensus FASTAs at variable sites.
13. Build a SNP tree with `iqtree2` (capped by `max_variants`) per report group × reference.
14. Aggregate QC with `multiqc` and render the per-report-group HTML report plus a `PathoSurveilR`-parseable directory tree.

## Key parameters
- `--input`: CSV/TSV samplesheet. Only the read-source column is required; useful columns include `sample_id`, `path`/`path_2`, `ncbi_accession`, `ncbi_query`, `sequence_type` (illumina|nanopore|pacbio), `ploidy`, `report_group_ids`, `ref_group_ids`, `color_by`.
- `--reference_data`: optional CSV/TSV to force specific references; `ref_primary_usage`/`ref_contextual_usage` ∈ {optional, required, exclusive, excluded}.
- `--outdir`: results directory (absolute path on cloud).
- `--data_dir` (default `path_surveil_data`): persistent cache for downloaded reads, assemblies, and databases — keep stable across runs to avoid re-downloads.
- `--bakta_db` or `--download_bakta_db` (default true) with `--bakta_db_type` ∈ {light (~2 GB), full (~40 GB)}. Pre-download `full` for production.
- `--max_samples` (default 1000), `--max_depth` (default 100×), `--min_bases_to_assemble` (default 100000).
- Reference auto-selection quotas: `--n_ref_closest` (2), `--n_ref_closest_named` (1), `--n_ref_context` (5), `--n_ref_strains` (5), `--n_ref_species` (20), `--n_ref_genera` (20); `--ref_min_ani` (0.95 — lower to force all samples onto one shared reference).
- Reference filters: `--only_latin_binomial_refs`, `--allow_non_refseq`, `--allow_unannotated`, `--allow_atypical_refs`.
- Phylogeny: `--phylo_min_genes` (10), `--phylo_max_genes` (500), `--max_variants` (100000), `--skip_core_phylogeny`.
- Performance: `--cpu_scale`, `--max_parallel_downloads`; use `-profile cloud` to raise download parallelism; set the `NCBI_API_KEY` Nextflow secret to lift NCBI rate limits.
- Always pass a container profile (`-profile docker` or `singularity`; `conda` only as fallback) and `-r 1.1.0` for reproducibility.

## Test data
The bundled `test` profile uses a single small genome sample from the nf-core/test-datasets `pathogensurveillance` branch (`samplesheets/test.csv`), with `max_samples=1`, `skip_core_phylogeny=true`, and tightly reduced reference quotas (`n_ref_closest=1`, `n_ref_context=3`, `phylo_max_genes=20`) so the run fits in ~1 h on 4 CPU / 15 GB RAM. The `test_full` profile runs the same samplesheet but with six samples and slightly larger quotas. Additional curated profiles exercise real-world datasets for sanity checks: `test_serratia` (10 *Serratia* isolates, Williams et al. 2022), `test_bordetella` (5 *B. pertussis*, Illumina + Nanopore, Wagner et al. 2023), `test_salmonella` (5 isolates, Hawkey et al. 2024), `test_mycobacteroides` (5 *M. abscessus*, Bronson et al. 2021), `test_klebsiella` (10 *K. pneumoniae*), `test_boxwood_blight` (5 eukaryotic *Cylindrocladium buxicola*, LeBlanc et al. 2020), `test_bacteria`, and `test_small_genomes`; each has a `_full` variant for the larger version. A successful run produces the per-report-group HTML report in `outdir/reports/<group>_report.html`, cleaned `metadata/{sample,ref}_metadata.tsv`, assemblies, `variants/*.vcf.gz`, aligned-gene FASTAs, and `trees/{core,busco,snp}/*.treefile`; `multiqc` and `pipeline_info` summaries should be present and green.

## Reference workflow
nf-core/pathogensurveillance v1.1.0 (https://github.com/nf-core/pathogensurveillance). See Foster et al., bioRxiv 2025.10.31.685798 (doi:10.1101/2025.10.31.685798) and the nf-core docs at https://nf-co.re/pathogensurveillance/1.1.0/ for the full parameter reference and the example HTML report.
