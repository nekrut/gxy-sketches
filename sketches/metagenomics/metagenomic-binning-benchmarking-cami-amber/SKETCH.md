---
name: metagenomic-binning-benchmarking-cami-amber
description: Use when you need to benchmark multiple metagenomic binners (CONCOCT,
  MetaBAT2, SemiBin, MaxBin2) plus refiners (DAS Tool, Binette) against a CAMI-style
  gold-standard biobox to measure MAG recovery quality. Assumes paired short reads,
  per-sample assemblies, and a gold-standard mapping of contigs to reference genomes
  are available.
domain: metagenomics
organism_class:
- bacterial
- archaeal
- microbial-community
input_data:
- short-reads-paired
- assembly-fasta
- gold-standard-biobox
source:
  ecosystem: iwc
  workflow: MAGs binning evaluation
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/microbiome/binning-evaluation
  version: '1.1'
  license: MIT
  slug: microbiome--binning-evaluation
tools:
- name: bowtie2
  version: 2.5.5+galaxy0
- name: samtools
  version: 2.0.8
- name: concoct
  version: 1.1.0+galaxy2
- name: metabat2
  version: 2.17+galaxy0
- name: semibin
  version: 2.1.0+galaxy1
- name: maxbin2
  version: 2.2.7+galaxy6
- name: das-tool
  version: 1.1.7+galaxy1
- name: binette
  version: 1.2.1+galaxy0
- name: cami-amber
  version: 2.0.7+galaxy0
tags:
- metagenomics
- binning
- mags
- benchmark
- cami
- amber
- gold-standard
- concoct
- metabat2
- semibin
- maxbin2
- dastool
- binette
test_data:
- role: biobox_file__marine_pooled_gsb_trimmed
  url: https://zenodo.org/records/17107943/files/workflow_test_gsb.tabular
- role: assemblies__marine_pooled_gsa_trimmed
  url: https://zenodo.org/records/17107943/files/workflow_test_assamble.fasta
- role: reads__trimmed__forward
  url: https://zenodo.org/records/17107943/files/workflow_test_forward.fastqsanger
- role: reads__trimmed__reverse
  url: https://zenodo.org/records/17107943/files/workflow_test_reverse.fastqsanger
expected_output:
- role: amber_html_report
  description: Content assertions for `AMBER HTML Report`.
  assertions:
  - 'has_size: {''value'': 2454860, ''delta'': 150000}'
- role: amber_result_table
  description: Content assertions for `AMBER Result Table`.
  assertions:
  - 'has_n_columns: {''n'': 39}'
  - 'has_n_lines: {''n'': 8}'
- role: amber_genome_metric
  description: Content assertions for `AMBER Genome Metric`.
  assertions:
  - 'has_n_columns: {''n'': 16}'
  - 'has_n_lines: {''n'': 1100, ''delta'': 10}'
- role: amber_bin_metric
  description: Content assertions for `AMBER Bin Metric`.
  assertions:
  - 'has_n_columns: {''n'': 16}'
  - 'has_n_lines: {''n'': 188, ''delta'': 10}'
---

# Metagenomic binning benchmarking with CAMI AMBER

## When to use this sketch
- You have paired-end short reads, a matching per-sample metagenome assembly, and a CAMI-format gold-standard biobox file mapping contigs to reference genomes.
- You want to compare multiple MAG binners (CONCOCT, MetaBAT2, SemiBin, MaxBin2) side-by-side on the same data.
- You also want refined bin sets from ensemble refiners (DAS Tool, Binette) included in the comparison.
- You need quantitative bin-quality and genome-recovery metrics plus an HTML report from CAMI AMBER for methods comparison, parameter tuning, or publication-grade benchmarking.
- Typical use case: CAMI challenge-style evaluations, internal binner tuning on simulated / mock communities where a truth set exists.

## Do not use when
- You only want to produce MAGs from a real sample without a gold standard — use a production MAG recovery sketch instead (no AMBER step, no biobox needed).
- Your reads are long (ONT / PacBio HiFi) — use a long-read metagenomic binning sketch; the preprocessing here is Bowtie2 short-read mapping.
- You want taxonomic profiling (what is present) rather than bin-quality benchmarking — use a Kraken2/MetaPhlAn-style taxonomic profiling sketch.
- You want to functionally annotate or taxonomically classify the resulting MAGs (GTDB-Tk, CheckM2 standalone, Prokka) — this workflow stops at AMBER metrics.
- You have no truth set / gold standard — CAMI AMBER cannot be run; pick a CheckM2 / BUSCO-based bin-QC sketch instead.

## Analysis outline
1. Map paired reads to the per-sample assembly with **Bowtie2**, sort BAM with **samtools sort**.
2. Build coverage signals: **CONCOCT cut_up_fasta** + **concoct_coverage_table** for CONCOCT; **jgi_summarize_bam_contig_depths** (MetaBAT2) for depth-based binners.
3. Run four primary binners in parallel on the assembly + coverage: **CONCOCT**, **MetaBAT2**, **SemiBin** (single-sample mode, pretrained model), **MaxBin2**.
4. For CONCOCT: merge cut-up clustering (`concoct_merge_cut_up_clustering`) and extract bin FASTAs (`concoct_extract_fasta_bins`).
5. Convert each binner's FASTA bins to contig→bin tables with **Fasta_to_Contig2Bin**.
6. Refine with **DAS Tool** (consensus of all four binners) and **Binette** (score-based refinement over the same contig→bin tables).
7. Convert every bin set (CONCOCT, MetaBAT2, SemiBin, MaxBin2, DAS Tool, Binette) to **CAMI AMBER biobox** format and add a length column to the gold standard (`cami_amber_add`).
8. Rewrite `@SampleID` headers to a common identifier (Replace Text + Compose text parameter) and concatenate per-sample biobox files per binner.
9. Run **CAMI AMBER** with the gold standard plus all six labelled binning submissions; emit HTML report, result table, genome-level metrics, and bin-level metrics.

## Key parameters
- CONCOCT: `clusters=400`, `kmer_length=4`, `length_threshold=1000`, `read_length=100`, `total_percentage_pca=90`, `iterations=500`, `seed=1`.
- MetaBAT2: `minContig=1500` (floor enforced by tool), `maxP=95`, `minS=60`, `maxEdges=200`, `pTNF=0`, `minCV=1.0`, `minCVSum=1.0`, `minClsSize=200000`.
- SemiBin: `mode=single`, pretrained reference `cached_db=17102022`, `epoches=20`, `batch_size=2048`, `orf_finder=fast-naive`, `ml_threshold` left empty to auto-compute.
- MaxBin2: `min_contig_length=1000`, `max_iteration=50`, `prob_threshold=0.5`, `markerset=107`.
- DAS Tool: `score_threshold=0.5`, `duplicate_penalty=0.6`, `megabin_penalty=0.5`, `max_iter_post_threshold=10`, `search_engine=diamond`, labels `CONCOCT,MetaBAT2,SemiBin,MaxBin2`.
- Binette: `min_completeness=40`, `contamination_weight=2`, cached CheckM2-style database.
- CAMI AMBER: `filter=0`, NCBI taxonomy off, six labelled submissions (`MetaBat2, CONCOCT, SemiBin2, DAS Tool, MaxBin2, Binette`); gold standard passed through `cami_amber_add` to add contig lengths.
- Global: shared `Seed` parameter for binner reproducibility; `jgi_summarize_bam_contig_depths percentIdentity=97`.

## Test data
The test profile uses a trimmed marine pooled mock community from Zenodo record 17107943: one paired-end FASTQ pair (`workflow_test_forward.fastqsanger` / `workflow_test_reverse.fastqsanger`), one matching assembly FASTA (`workflow_test_assamble.fasta`), and one CAMI-format gold-standard biobox (`workflow_test_gsb.tabular`). Parameters are mostly defaults, with MetaBAT2 loosened for the small test (`maxP=2`, `minS=2`, `minCV=0.001`, `minCVSum=0.001`) so bins are actually produced. Expected outputs are the four CAMI AMBER artefacts: an HTML report of ~2.45 MB (±150 KB), a 39-column × 8-line `result` table, a 16-column genome-level metrics table of ~1100 rows (±10), and a 16-column bin-level metrics table of ~188 rows (±10). Assertions are structural (size, row and column counts), not exact content matches.

## Reference workflow
Galaxy IWC `workflows/microbiome/binning-evaluation` — *MAGs binning evaluation*, release **1.1** (2026-03-09), MIT, author Santino Faack. Source: https://github.com/galaxyproject/iwc/tree/main/workflows/microbiome/binning-evaluation
