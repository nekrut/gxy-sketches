---
name: shotgun-metagenome-assembly-binning
description: Use when you need to recover metagenome-assembled genomes (MAGs) from
  shotgun metagenomic sequencing of a microbial community (e.g. gut, soil, environmental
  samples). Assembles short-read (optionally long-read/hybrid) data, bins contigs
  into putative genomes, and performs bin QC, taxonomic classification and annotation.
domain: metagenomics
organism_class:
- microbial-community
- bacterial
- archaeal
input_data:
- short-reads-paired
- long-reads-ont-optional
- host-reference-fasta-optional
source:
  ecosystem: nf-core
  workflow: nf-core/mag
  url: https://github.com/nf-core/mag
  version: 5.4.2
  license: MIT
  slug: mag
tools:
- name: fastp
- name: bowtie2
- name: megahit
- name: spades
- name: metabat2
  version: '2.17'
- name: maxbin2
  version: 2.2.7
- name: concoct
  version: 1.1.0
- name: semibin2
- name: dastool
  version: 1.1.7
- name: busco
- name: checkm2
- name: gtdbtk
- name: prokka
- name: cat
- name: quast
- name: prodigal
  version: 57f05cfa73f769d6ed6d54144cb3aa2a6a6b17e0-0
tags:
- metagenomics
- mag
- binning
- assembly
- microbiome
- shotgun
- wgs
- community
test_data: []
expected_output: []
---

# Shotgun metagenome assembly and genome binning

## When to use this sketch
- Input is shotgun (WGS) sequencing of a mixed microbial community, not a single isolate.
- Goal is to recover draft bacterial/archaeal genomes (MAGs) from the community, with per-bin completeness/contamination QC and taxonomic placement.
- Illumina paired-end short reads are available; optionally also long reads (ONT / PacBio HiFi) for hybrid or long-only assembly.
- You want an end-to-end pipeline: QC → assembly (MEGAHIT/metaSPAdes) → binning (MetaBAT2/MaxBin2/CONCOCT/SemiBin2) → bin QC (BUSCO/CheckM2) → GTDB-Tk classification → Prokka annotation.
- You may additionally want geNomad virus/plasmid identification or an ancient-DNA authentication subworkflow (PyDamage + freebayes consensus recall).

## Do not use when
- You need read-level taxonomic profiling only (no assembly, no MAGs) → use a taxonomic-profiling sketch built around Kraken2/Centrifuge/MetaPhlAn (nf-core/taxprofiler).
- Input is a single-isolate bacterial genome for SNV calling against a reference → use `haploid-variant-calling-bacterial`.
- Input is a single-isolate bacterial genome assembly → use an nf-core/bacass-style isolate assembly sketch.
- You only need 16S/amplicon community profiling → use an amplicon (DADA2/QIIME2) sketch, not assembly-based MAG recovery.
- You need eukaryotic-genome-focused metagenomics without any prokaryotic recovery → MetaEuk-only workflows are more appropriate.

## Analysis outline
1. Read QC and adapter/quality trimming of short reads with fastp (default; AdapterRemoval or Trimmomatic optional) and FastQC before/after.
2. Remove PhiX spike-in with Bowtie2, optionally remove host reads against `--host_fasta`/`--host_genome` with Bowtie2.
3. (Optional) Long-read QC: Porechop/Porechop_ABI adapter trim, Filtlong/Nanoq/Chopper filtering, NanoLyse lambda removal, NanoPlot stats.
4. (Optional) Digital normalisation of short reads with BBnorm before assembly.
5. Per-sample or per-group co-assembly with MEGAHIT and/or metaSPAdes (short-read) and/or SPAdesHybrid / Flye / metaMDBG (long-read or hybrid).
6. Assembly QC with metaQUAST and ALE (short-read assemblies only).
7. Map reads back to contigs (Bowtie2 for short, minimap2 for long) and compute per-contig depth with `jgi_summarize_bam_contig_depths`.
8. Metagenome binning with MetaBAT2 (default), MaxBin2, CONCOCT, SemiBin2, MetaBinner and/or COMEBin; optionally Tiara contig domain classification to split pro/eukaryote bins.
9. (Optional) Bin refinement with DAS Tool combining multiple binner outputs.
10. Bin QC with BUSCO and/or CheckM / CheckM2, optional GUNC chimerism check.
11. Taxonomic classification of bins with GTDB-Tk (bacteria/archaea) and/or CAT/BAT.
12. Gene prediction (Prodigal) and annotation of bins with Prokka (prokaryotes) and optionally MetaEuk (eukaryotes).
13. Optional geNomad virus/plasmid identification on assemblies.
14. Optional ancient-DNA subworkflow: PyDamage damage estimation + freebayes/bcftools consensus recall (`--ancient_dna`, ploidy=1).
15. Summarise all per-bin metrics into `GenomeBinning/bin_summary.tsv` and render a MultiQC report.

## Key parameters
- `--input`: CSV samplesheet with `sample,group,short_reads_1,short_reads_2,long_reads,short_reads_platform,long_reads_platform` columns; `group` drives co-assembly/co-binning.
- `--coassemble_group` (default off): pool reads by `group` before assembly with MEGAHIT/SPAdes.
- `--binning_map_mode` (default `group`; `all` | `group` | `own`): which samples are mapped back to each assembly for co-abundance. Use `own` for reproducibility, especially with `--ancient_dna`.
- Assembler toggles: `--skip_megahit`, `--skip_spades`, `--skip_spadeshybrid`, `--skip_flye`, `--skip_metamdbg`; `--spades_options`, `--megahit_options` for extra flags.
- Binning: `--skip_metabat2/maxbin2/concoct/semibin/comebin/metabinner`, `--min_contig_size` (default 1500), `--min_length_unbinned_contigs` (default 1,000,000), `--max_unbinned_contigs` (default 100), `--semibin_environment` (e.g. `human_gut`, `soil`, `global`).
- Bin refinement: `--refine_bins_dastool`, `--refine_bins_dastool_threshold` (default 0.5), `--postbinning_input` (`raw_bins_only`|`refined_bins_only`|`both`).
- Bin QC: `--run_busco`, `--run_checkm`, `--run_checkm2`, `--run_gunc`; `--busco_db`, `--busco_db_lineage` (e.g. `bacteria_odb10`, `auto`), `--checkm2_db`, `--gunc_db`.
- Taxonomy: `--skip_gtdbtk`, `--gtdb_db`, `--gtdbtk_min_completeness` (50), `--gtdbtk_max_contamination` (10), `--gtdbtk_use_full_tree`, `--gtdbtk_skip_aniscreen`; `--cat_db` / `--cat_db_generate`.
- Host/contaminant removal: `--host_fasta` or `--host_genome`, `--keep_phix`, `--keep_lambda`.
- Virus id: `--run_virus_identification`, `--genomad_db`, `--genomad_min_score` (0.7).
- Ancient DNA: `--ancient_dna`, `--pydamage_accuracy` (0.5), `--freebayes_ploidy` (1), `--freebayes_min_basequality` (20).
- Reproducibility: `--megahit_fix_cpu_1`, `--spades_fix_cpus`, `--metabat_rng_seed` (default 1), `--semibin_rng_seed` (default 1).

## Test data
The bundled `-profile test` runs a minimal multi-run Illumina paired-end samplesheet (`mag/samplesheets/samplesheet.multirun.v4.csv` from nf-core test-datasets), using tiny mock databases for BUSCO (`bacteria_odb10`), GTDB-Tk (a ~20 MB mockup package) and CAT (`minigut_cat.tar.gz`). It skips ALE, CONCOCT, COMEBin and MetaBinner, fixes MEGAHIT and SPAdes to single-CPU for reproducibility, and sets `gtdbtk_min_completeness=0.01` so the mock DB is usable. A successful run produces MEGAHIT and metaSPAdes assemblies, MetaBAT2/MaxBin2/SemiBin2 bins, QUAST/BUSCO/CheckM2 bin-QC tables, GTDB-Tk classifications, Prokka annotations, a merged `GenomeBinning/bin_summary.tsv` and a MultiQC report. The full-size profile (`test_full`) uses the published human-gut hybrid metagenome benchmark from Bertrand et al. 2019 with host removal against a masked hg19.

## Reference workflow
nf-core/mag v5.4.2 (https://github.com/nf-core/mag), Krakau et al., *NAR Genom Bioinform* 2022; doi:10.1093/nargab/lqac007. See `nextflow_schema.json` for the authoritative parameter set and `docs/usage.md` / `docs/output.md` for input/output conventions.
