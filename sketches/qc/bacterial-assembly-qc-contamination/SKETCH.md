---
name: bacterial-assembly-qc-contamination
description: Use when you need to assess the quality of an already-assembled bacterial
  genome (contigs FASTA) and check for contamination or taxonomic mis-assignment.
  Computes assembly contiguity metrics, completeness/contamination estimates, and
  species-level taxonomic classification of contigs.
domain: qc
organism_class:
- bacterial
- haploid
input_data:
- contigs-fasta
- short-reads-paired-optional
- kraken2-database
source:
  ecosystem: iwc
  workflow: Post-Assembly Quality Control and Contamination Check for Bacterial Genomes
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/bacterial_genomics/bacterial-quality-and-contamination-control-post-assembly
  version: 1.0.2
  license: GPL-3.0-or-later
  slug: bacterial_genomics--bacterial-quality-and-contamination-control-post-assembly
tools:
- name: quast
  version: 5.3.0+galaxy0
- name: checkm2
  version: 1.0.2+galaxy1
- name: kraken2
  version: 2.1.3+galaxy1
- name: bracken
- name: tooldistillator
  version: 1.0.4+galaxy0
tags:
- bacteria
- assembly-qc
- contamination
- completeness
- taxonomy
- post-assembly
- abromics
test_data:
- role: input_sequence_contigs_fasta
  url: https://zenodo.org/records/16779020/files/E-coli3_S194.fasta
  filetype: fasta
expected_output:
- role: quast_tabular_report_for_fasta_files
  description: Content assertions for `Quast tabular report for FASTA files`.
  assertions:
  - 'has_text: # contigs (>= 500 bp)'
  - 'has_n_columns: {''n'': 2}'
- role: bracken_tabular_report
  description: Content assertions for `Bracken tabular report`.
  assertions:
  - 'has_text: Escherichia coli'
  - 'has_n_columns: {''n'': 7}'
- role: bracken_kraken_tabular_report
  description: Content assertions for `Bracken Kraken tabular report`.
  assertions:
  - 'has_text: Escherichia coli'
  - 'has_n_columns: {''n'': 6}'
- role: kraken2_sequence_assignation
  description: Content assertions for `Kraken2 sequence assignation`.
  assertions:
  - 'has_text: contig00359'
- role: kraken2_tabular_report
  description: Content assertions for `Kraken2 tabular report`.
  assertions:
  - 'has_text: Escherichia fergusonii'
  - 'has_n_columns: {''n'': 6}'
- role: checkm2_tabular_report
  description: Content assertions for `Checkm2 tabular report`.
  assertions:
  - 'has_text: Completeness_General'
  - 'has_n_columns: {''n'': 15}'
- role: checkm2_diamond_files
  description: Content assertions for `Checkm2 diamond files`.
  assertions:
  - 'DIAMOND_RESULTS: has_text: UniRef100_B1IY62~K00116'
  - 'DIAMOND_RESULTS: has_n_columns: {''n'': 12}'
- role: checkm2_protein_files
  description: Content assertions for `Checkm2 protein files`.
  assertions:
  - 'E-coli3_S194.fasta: has_text: >contig00358_1'
- role: tooldistillator_summarize_control
  description: Content assertions for `Tooldistillator summarize control`.
  assertions:
  - 'that: has_text'
  - 'text: quast_report'
  - 'that: has_text'
  - 'text: ncbi_taxonomic_id'
  - 'that: has_text'
  - 'text: kraken2_report'
  - 'that: has_text'
  - 'text: checkm2_report'
---

# Post-assembly QC and contamination check for bacterial genomes

## When to use this sketch
- You already have a bacterial assembly (contigs FASTA) from short-read data and need to judge whether it is good enough to publish or submit downstream.
- You need combined metrics: contiguity (N50, # contigs, total length), completeness and contamination, and taxonomic identity of contigs.
- You suspect contamination, chimeric contigs, or mis-identified isolates and want Kraken2 + Bracken species-level assignment on the assembly.
- You have an optional pair of trimmed Illumina FASTQs and want QUAST to also use read alignment statistics against the assembly.
- You want a single aggregated JSON summary (ToolDistillator) that downstream dashboards (e.g. ABRomics) can parse.

## Do not use when
- You need to *produce* the assembly from raw reads — use a bacterial assembly sketch (e.g. nf-core/bacass, Unicycler/SPAdes-based) first, then feed its contigs here.
- You are working on eukaryotic or metagenomic assemblies — CheckM2 and the recommended Kraken2 databases are tuned for prokaryotic single-isolate QC; use BUSCO/EukCC for eukaryotes or a dedicated metagenome-binning QC workflow (CheckM2 can run on MAGs but binning is out of scope here).
- You need variant calling, annotation, AMR profiling, or MLST — those are downstream of this QC and belong to separate sketches.
- You only have long reads from an ONT/PacBio assembly and no short reads — the workflow still runs on contigs alone, but QUAST's read-based metrics block is skipped; consider a long-read-specific QC sketch if available.
- You want read-level QC (adapter trimming, per-base quality) — that is a pre-assembly step (fastp/FastQC), not this sketch.

## Analysis outline
1. Provide the assembled contigs FASTA (required) and, optionally, the paired trimmed Illumina R1/R2 FASTQs used to build it.
2. Select an execution branch via two boolean flags: `Fasta boolean=true` for contigs-only QC, or `Fastq boolean=true` to additionally feed reads into QUAST.
3. Run **QUAST** on the contigs to compute assembly contiguity and conserved-gene metrics; when reads are supplied, QUAST also reports read-mapping-based stats.
4. Run **CheckM2** (`--allmodels`, translation table 11) on the contigs to estimate genome completeness and contamination.
5. Run **Kraken2** against a user-selected prebuilt database to classify each contig taxonomically.
6. Run **Bracken** on the Kraken2 report to re-estimate species-level (`level=S`) relative abundance, giving a contamination breakdown.
7. Collapse CheckM2 per-contig protein and DIAMOND collections into single datasets for reporting.
8. Aggregate QUAST, CheckM2, Kraken2 and Bracken results with **ToolDistillator** and then **ToolDistillator Summarize** into one JSON summary for downstream dashboards.

## Key parameters
- `Fasta boolean` / `Fastq boolean`: mutually exclusive switches that gate the two QUAST branches; set `Fasta boolean=true, Fastq boolean=false` for contigs-only runs.
- QUAST: `min_contig=200`, `contig_thresholds=0,200,500,1000`, `min_identity=95.0`, `conserved_genes_finding=true`, `assembly.type=genome`, no reference used.
- CheckM2: `model=--allmodels`, `ttable=11` (bacterial genetic code), `database=1.0.2`.
- Kraken2: `confidence=0.0`, `min_base_quality=10`, `minimum_hit_groups=2`, input treated as unpaired contigs; database chosen via the `Select a taxonomy database` parameter (tests use `k2_minusb_20210517`).
- Bracken: `level=S` (species), `threshold=1` (lowered from 10 in 1.0.2 so assemblies with few contigs still produce estimates), `read_len=100` in the ToolDistillator section.
- ToolDistillator: aggregates kraken2, bracken, quast, checkm2 into one JSON; the Bracken/Kraken entries are tagged with the chosen reference database version.

## Test data
The test profile runs the FASTA-only branch on a single *Escherichia coli* isolate assembly (`E-coli3_S194.fasta`, fetched from Zenodo record 16779020) with `Fasta boolean=true`, `Fastq boolean=false`, and the `k2_minusb_20210517` Kraken2/Bracken database. Expected results include a QUAST tabular report containing the `# contigs (>= 500 bp)` metric, a CheckM2 report with a `Completeness_General` column (15 columns total), Kraken2 and Bracken tabular reports that assign contigs to *Escherichia coli* (with some *Escherichia fergusonii* cross-hits in the raw Kraken2 report), per-contig CheckM2 protein predictions (e.g. `>contig00001_1`…`>contig00358_1`) and DIAMOND hits (e.g. `UniRef100_B1IY62~K00116`), and a final ToolDistillator summary JSON containing `quast_report`, `kraken2_report`, `checkm2_report` and `ncbi_taxonomic_id` keys.

## Reference workflow
Galaxy IWC — `workflows/bacterial_genomics/bacterial-quality-and-contamination-control-post-assembly`, release 1.0.2 (ABRomics consortium), GPL-3.0-or-later. Key tool versions: QUAST 5.3.0+galaxy0, CheckM2 1.0.2+galaxy1, Kraken2 2.1.3+galaxy1, Bracken 3.1+galaxy0, ToolDistillator 1.0.4+galaxy0.
