---
name: untargeted-viral-consensus-metagenomic
description: Use when you have short-read Illumina metagenomic or hybrid-capture sequencing
  of a clinical/environmental sample and need to reconstruct viral consensus genomes
  de novo (without knowing the exact reference in advance) and call intra-host variants.
  Handles unknown viruses by assembling, clustering contigs, picking a reference from
  a pool, and iteratively polishing the consensus.
domain: variant-calling
organism_class:
- viral
- eukaryote-host
input_data:
- short-reads-paired
- short-reads-single
- reference-pool-fasta
- kraken2-db
- kaiju-db
source:
  ecosystem: nf-core
  workflow: nf-core/viralmetagenome
  url: https://github.com/nf-core/viralmetagenome
  version: 1.1.1
  license: MIT
  slug: viralmetagenome
tools:
- name: fastp
- name: trimmomatic
  version: '0.39'
- name: bbduk
- name: prinseq++
  version: 1.2.3
- name: kraken2
- name: kaiju
  version: 1.10.0
- name: bracken
- name: spades
- name: megahit
- name: trinity
  version: 2.15.2
- name: blastn
- name: cd-hit-est
  version: 4.8.1
- name: vsearch
- name: mmseqs2
- name: mash
- name: minimap2
- name: bwa-mem2
- name: bowtie2
- name: picard
- name: umi-tools
- name: mosdepth
- name: bcftools
- name: ivar
- name: snpeff
- name: snpsift
- name: checkv
- name: quast
- name: prokka
- name: mafft
- name: multiqc
tags:
- virus
- metagenomics
- hybrid-capture
- consensus
- intra-host
- denovo
- iterative-refinement
- rnaviral
test_data: []
expected_output: []
---

# Untargeted viral consensus reconstruction from metagenomic short reads

## When to use this sketch
- You have Illumina short reads (paired or single-end) from a metagenomic, virome-enriched, or hybrid-capture experiment and want a consensus genome for the viral content.
- You do not necessarily know which virus/strain is present and need the workflow to pick a reference from a pool (e.g. RVDB, Virosaurus, or a curated set) rather than being told one up front.
- You want both a de novo consensus route AND an optional reference-constrained route (`--mapping_constraints`) running in parallel.
- You also need intra-host minor variants (SNVs/indels with allele frequencies) against the reconstructed consensus.
- You want iterative polishing: reads are remapped to the new consensus and it is re-called for multiple cycles.
- Hosts are eukaryotic (human/vertebrate tissue, cell culture, arthropod vector) and reads need Kraken2-based host removal before assembly.
- Segmented viruses (e.g. Lassa, Hazara) are acceptable — each segment is handled as its own reference/cluster.

## Do not use when
- You already have a single fixed reference and just need a targeted reference-based consensus + variant call — use a lighter amplicon/reference pipeline (e.g. nf-core/viralrecon amplicon mode).
- The dataset is tiled amplicon sequencing (ARTIC-style PrimalSeq) of a known virus — viralrecon with primer trimming is the right tool.
- You are calling variants in a diploid/polyploid host (human germline/somatic, plant) — use a human/vertebrate variant-calling sketch; this pipeline assumes haploid viral genomes and uses `--ploidy 2` only inside bcftools with viral-tuned filters.
- You are doing bacterial WGS variant calling or assembly — use a bacterial-assembly or haploid-bacterial-variant sketch.
- You only need taxonomic profiling of a metagenome (who's there) without consensus reconstruction — use a dedicated Kraken2/Bracken profiling sketch.
- Input is long-read only (ONT/PacBio) — this pipeline expects Illumina-style paired/single short reads.

## Analysis outline
1. Raw read QC with FastQC.
2. Adapter/quality trimming with fastp (default) or Trimmomatic.
3. Optional UMI extraction/deduplication at the read level with UMI-tools + HUMID.
4. Low-complexity filtering with prinseq++ (default) or bbduk.
5. Host read removal with Kraken2 against a host k2 database (e.g. human).
6. Read-level taxonomic profiling with Kraken2 + Bracken and/or Kaiju, visualized via Krona.
7. De novo assembly with SPAdes (`rnaviral` mode by default), MEGAHIT, and/or Trinity; per-assembler contigs are merged.
8. Optional contig extension with SSPACE-Basic and low-complexity contig filtering with prinseq++.
9. BLASTn of contigs against a reference pool (e.g. RVDB) to pull in candidate references (top 5 hits per contig).
10. Optional preclustering of contigs by Kraken2/Kaiju taxonomy.
11. Contig clustering into per-virus bins with CD-HIT-EST (default), vsearch, MMseqs2 linclust/cluster, vRhyme, or Mash + Clusty.
12. Optional removal of clusters whose cumulative mapped-read fraction is below `perc_reads_contig`.
13. Scaffold each cluster to its centroid reference with Minimap2 + iVar consensus.
14. Optional best-reference selection for `--mapping_constraints` via Mash sketch + Mash screen.
15. Map the cleaned reads back to the scaffolded consensus (and to mapping constraints) with BWA-MEM2 (default) or Bowtie2.
16. Deduplicate alignments with Picard MarkDuplicates, or UMI-tools dedup if UMIs are present.
17. Collect mapping stats with samtools flagstat/stats/idxstats, Picard CollectMultipleMetrics, and mosdepth.
18. Call variants with iVar (default) or BCFtools mpileup + norm + filter, then build/refine consensus with iVar or bcftools consensus.
19. Iteratively refine: remap reads to the new consensus, recall variants, rebuild consensus for `iterative_refinement_cycles` cycles (default 2).
20. Optional SnpEff + SnpSift annotation of final VCFs.
21. Consensus QC: QUAST, CheckV (completeness/contamination), BLASTn, MMseqs-search annotation against Virosaurus-style database, Prokka gene annotation (`--kingdom Viruses`), and MAFFT alignment of iterations vs. final consensus.
22. MultiQC report plus custom `contigs_overview.tsv`, `mapping_overview.tsv`, and `samples_overview.tsv` summary tables.

## Key parameters
- `input`: CSV samplesheet with `sample,fastq_1,fastq_2` (optional `group` for per-sample merging).
- `outdir`: absolute output directory.
- `mapping_constraints`: optional TSV of reference sequences (id, species, segment, selection, samples, sequence, gff) for a parallel reference-constrained route; set `selection=true` on multi-FASTA refs to trigger Mash-based best-reference picking.
- `reference_pool`: FASTA used for BLAST-based scaffolding (default `C-RVDBvCurrent.fasta.gz`).
- `host_k2_db`: Kraken2 database for host removal (default human Kraken2 db).
- `kraken2_db` / `kaiju_db` / `bracken_db`: classifier databases for read-level diversity profiling; `read_classifiers` (default `kraken2,kaiju`) picks which run.
- `assemblers` (default `spades,megahit`, optional `trinity`) and `spades_mode` (default `rnaviral`; also `corona`, `metaviral`, `meta`, `isolate`).
- `cluster_method` (default `cdhitest`) with `identity_threshold` (default 0.85), `min_contig_size` (500), `max_contig_size` (10,000,000), `max_n_perc` (50), `perc_reads_contig` (5).
- `precluster_classifiers` (default `kraken2,kaiju`) and `keep_unclassified` (default true).
- `mapper` / `intermediate_mapper` (default `bwamem2`, alt `bowtie2`).
- `variant_caller` / `intermediate_variant_caller` (default `ivar`, alt `bcftools`); `consensus_caller` / `intermediate_consensus_caller` likewise.
- `iterative_refinement_cycles` (default 2), `skip_iterative_refinement` to disable.
- `deduplicate` (default true — Picard, or UMI-tools when `with_umi`).
- `min_mapped_reads` (default 200), `min_consensus_depth` (default 5), `allele_frequency` (default 0.75 for major allele in consensus).
- `checkv_db`, `annotation_db` (default Virosaurus vertebrate), `prokka_db` for consensus QC/annotation.
- `skip_vcf_annotation` to turn off SnpEff; `skip_polishing`, `skip_assembly`, `skip_variant_calling` to prune routes.

## Test data
The bundled `test` profile (`conf/test.config`) runs on a small synthetic samplesheet from `nf-core/test-datasets/viralmetagenome/`: a few paired-end Illumina samples with a matching `metadata_test.tsv`. It uses a miniature human Kraken2 database (`kraken2_hs22.tar.gz`), a small Kaiju database, a SARS-CoV-2 `reference_pool` FASTA, a `mapping_constraints.csv` pointing at that SARS-CoV-2 reference, and a subset Virosaurus annotation database. The test enables fastp trimming, `spades,megahit` assembly, complexity filtering, merges reads per group, skips read-level classification and CheckV for speed, disables deduplication, sets `min_mapped_reads=100`, and runs `iterative_refinement_cycles=1`. Expected outputs include per-sample SARS-CoV-2 consensus FASTA under `consensus/seq/`, filtered variant VCFs under `variants/variant_calling/{ivar,bcftools}/`, QUAST and mapping metrics, `overview-tables/{contigs_overview,mapping_overview,samples_overview}.tsv`, and a MultiQC HTML report. The `test_full` profile uses a larger samplesheet (`samplesheet_full.csv`) plus a CheckV minimal DB and Prokka protein DB to additionally exercise SSPACE-Basic scaffolding and CheckV/Prokka annotation.

## Reference workflow
nf-core/viralmetagenome v1.1.1 — https://github.com/nf-core/viralmetagenome. Citation: Klaps J, Lemey P, nf-core community, Kafetzopoulou LE. "nf-core/viralmetagenome: A Novel Pipeline for Untargeted Viral Genome Reconstruction." bioRxiv 2025.06.27.661954; doi:10.1101/2025.06.27.661954.
