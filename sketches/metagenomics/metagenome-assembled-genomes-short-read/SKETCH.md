---
name: metagenome-assembled-genomes-short-read
description: Use when you need to recover, dereplicate, annotate, and quantify Metagenome-Assembled
  Genomes (MAGs) from paired-end short-read metagenomic samples. Covers assembly,
  multi-binner binning with refinement, CheckM2-based dereplication across samples,
  taxonomic classification, annotation, and per-sample abundance estimation in one
  integrated pipeline.
domain: metagenomics
organism_class:
- bacterial
- archaeal
- prokaryote
input_data:
- short-reads-paired
- quality-trimmed-fastq
source:
  ecosystem: iwc
  workflow: Metagenome-Assembled Genomes (MAGs) generation
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/microbiome/mags-building
  version: '0.4'
  license: MIT
tools:
- megahit
- metaspades
- bowtie2
- metabat2
- maxbin2
- semibin
- concoct
- binette
- checkm2
- drep
- gtdb-tk
- bakta
- quast
- checkm
- coverm
- multiqc
tags:
- metagenomics
- mags
- binning
- co-assembly
- dereplication
- microbiome
- shotgun
- microgalaxy
test_data:
- role: trimmed_reads__50contig_reads__forward
  url: https://zenodo.org/records/15089018/files/MAG_reads_forward.fastqsanger.gz
- role: trimmed_reads__50contig_reads__reverse
  url: https://zenodo.org/records/15089018/files/MAG_reads_reverse.fastqsanger.gz
- role: trimmed_reads_from_grouped_samples__50contig_reads__forward
  url: https://zenodo.org/records/15089018/files/MAG_reads_forward.fastqsanger.gz
- role: trimmed_reads_from_grouped_samples__50contig_reads__reverse
  url: https://zenodo.org/records/15089018/files/MAG_reads_reverse.fastqsanger.gz
expected_output:
- role: full_multiqc_report
  description: Content assertions for `Full MultiQC Report`.
  assertions:
  - 'that: has_text'
  - 'text: 50contig_reads_bin'
  - 'that: has_text'
  - 'text: QUAST'
  - 'that: has_text'
  - 'text: CheckM'
- role: assembly_report
  description: Content assertions for `Assembly Report`.
  assertions:
  - '50contig_reads: that: has_text'
  - '50contig_reads: text: All statistics are based on contigs of size'
  - '50contig_reads: that: has_size'
  - '50contig_reads: value: 372000'
  - '50contig_reads: delta: 50000'
---

# Metagenome-Assembled Genomes (MAGs) from short-read metagenomes

## When to use this sketch
- You have paired-end Illumina shotgun metagenomic reads (already quality-trimmed and host-depleted) and want to recover draft bacterial/archaeal genomes (MAGs).
- You need a full MAG pipeline: assembly, binning, bin refinement, dereplication across samples, quality assessment, taxonomy, annotation, and per-sample abundance.
- You want a consensus across multiple binners (MetaBAT2, MaxBin2, SemiBin, CONCOCT) rather than trusting a single binner.
- You plan to run on one sample, a pooled co-assembly, or a grouped/hybrid co-assembly strategy.
- You want a single integrated MultiQC report plus joined per-bin tables (QUAST, CheckM2, CoverM, Bakta) across all samples.

## Do not use when
- Your reads are long (ONT/PacBio) — use a long-read metagenome assembly/binning sketch instead.
- You only want taxonomic profiling of reads without genome recovery — use a read-based metagenomic profiling sketch (Kraken2/MetaPhlAn/mOTUs).
- You need only quality filtering and host removal of raw metagenomic reads — use the sibling IWC "metagenomics quality control / host removal" workflow upstream of this one.
- You want viral MAGs / vMAGs — use a viral-binning sketch (e.g. vRhyme/CheckV-based).
- You only need assembly QC of a single isolate genome — use a bacterial-isolate-assembly sketch.
- You need strain-level variation within a population rather than consensus MAGs — use a strain-resolved metagenomics sketch (inStrain, StrainPhlAn).

## Analysis outline
1. Provide two paired-end read collections: per-sample trimmed reads (for abundance) and grouped/merged reads (for assembly; identical to per-sample for individual-mode).
2. Assemble contigs with **MEGAHIT** or **metaSPAdes** (selectable via `Choose Assembler`; a `Custom Assembly` input is also supported).
3. Evaluate assembly with **QUAST** (metagenome mode, per sample).
4. Map per-sample trimmed reads back to the chosen assembly with **Bowtie2** + **samtools sort** to produce coverage BAMs.
5. Compute contig depths with **metabat2 jgi_summarize_bam_contig_depths**; cut contigs and build coverage tables for **CONCOCT**.
6. Run four binners in parallel: **MetaBAT2**, **MaxBin2**, **SemiBin** (built-in environment model), and **CONCOCT** (with cut-up + merge + extract).
7. Convert each binner's outputs to contig2bin tables and combine them with **Binette** for bin refinement, scored with a **CheckM2** database.
8. Pool refined bins from all samples, run **CheckM2** for genome-info table, and **dRep dereplicate** across the whole sample set using completeness/contamination/length/ANI thresholds.
9. Annotate the dereplicated MAG set: **Bakta** (rRNAs only by default, to save resources) with bundled Bakta + AMRFinderPlus DBs.
10. Classify taxonomy with **GTDB-Tk classify_wf** (optional toggle, uses pre-staged GTDB-Tk DB).
11. Quality-assess final MAGs with **QUAST**, **CheckM** `lineage_wf`, and **CheckM2**.
12. Estimate per-sample abundance of dereplicated MAGs with **CoverM genome** (minimap2-sr, relative_abundance).
13. Join per-bin QUAST / CheckM2 / CoverM / Bakta tables with `collection_column_join` and summarize everything in a **MultiQC** report.

## Key parameters
- `Choose Assembler`: `MEGAHIT` | `metaSPAdes` | `Custom Assembly` — selected via `Map parameter value` gates; metaSPAdes is forced into per-sample mode via a sub-workflow so it does not implicitly co-assemble.
- `Minimum length of contigs to output`: MEGAHIT `--min-contig-len`, default `200`.
- `Environment for the built-in model (SemiBin)`: one of `global, human_gut, dog_gut, ocean, soil, cat_gut, human_oral, mouse_gut, pig_gut, built_environment, wastewater, chicken_caecum`; default `global`.
- `Read length (CONCOCT)`: default `100` — should match mean read length from FastQC.
- `Minimum MAG completeness percentage` (Binette + dRep filter): default `75` for high-quality MAGs; lower (e.g. 50) to report medium-quality MAGs.
- `Contamination weight (Binette)`: default `2` — lower favors completeness over purity.
- `Maximum MAG contamination percentage` (dRep): default `25`.
- `Minimum MAG length` (dRep): default `50000` bp.
- `ANI threshold for dereplication` (dRep secondary clustering): default `0.95` (species-level); use ≥0.98 for strain-level, ≤0.95 for broader clustering. Constrained to [0.9, 1.0].
- `Run GTDB-Tk on MAGs`: boolean toggle (default on) — disable on resource-constrained servers.
- Database inputs: `CheckM2 Database`, `GTDB-tk Database`, `Bakta Database`, `AMRFinderPlus Database for Bakta` — must be pre-installed data-manager entries on the Galaxy server.
- Fixed in the workflow: MetaBAT2 `minContig=1500`, `minClsSize=200000`; MaxBin2 markerset 107, `min_contig_length=1000`; CONCOCT `chunk_size=10000`, `clusters=400`, `length_threshold=1000`; dRep secondary algorithm `ANImf`; CoverM mapper `minimap2-sr`, method `relative_abundance`, `min_covered_fraction=10`.

## Test data
The source test exercises the pipeline with a single tiny synthetic paired-end sample, `50contig_reads`, drawn from both the `Trimmed reads` and `Trimmed reads from grouped samples` collections (same FASTQ pair used twice, i.e. individual-mode assembly). Reads come from Zenodo record 15089018 as `MAG_reads_forward.fastqsanger.gz` / `MAG_reads_reverse.fastqsanger.gz`. For the test, the assembler is set to `MEGAHIT`, GTDB-Tk is disabled, `Minimum MAG completeness percentage` is relaxed to 1 and `Minimum MAG length` to 100 so that tiny synthetic bins survive dRep. Expected outputs include a per-sample QUAST `Assembly Report` containing `All statistics are based on contigs of size` and of size ~372 KB, and a full MultiQC HTML report mentioning `50contig_reads_bin`, `QUAST`, and `CheckM`.

## Reference workflow
Galaxy IWC — `workflows/microbiome/mags-building/MAGs-generation.ga`, release 0.4 (maintained by the microGalaxy community; authors Bérénice Batut, Paul Zierep, Mina Hojat Ansari, Patrick Bühler, Santino Faack, Anna Syme). License MIT. Supports swapping Binette for DAS_Tool and expanding Bakta annotation categories via the workflow editor.
