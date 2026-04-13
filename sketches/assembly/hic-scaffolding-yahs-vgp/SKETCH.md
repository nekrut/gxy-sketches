---
name: hic-scaffolding-yahs-vgp
description: Use when you need to scaffold a draft contig-level genome assembly (GFA
  format) into chromosome-scale scaffolds using paired-end Hi-C reads with YAHS. Designed
  for VGP-style eukaryotic assemblies (vertebrates, plants, invertebrates) where a
  haplotype-resolved contig set already exists and Hi-C libraries (e.g. Arima, Dovetail)
  are available.
domain: assembly
organism_class:
- eukaryote
- vertebrate
- diploid
input_data:
- assembly-gfa
- hi-c-reads-paired
- estimated-genome-size
source:
  ecosystem: iwc
  workflow: Scaffolding with Hi-C data VGP8
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/VGP-assembly-v2/Scaffolding-HiC-VGP8
  version: '3.5'
  license: CC-BY-4.0
tools:
- yahs
- bwa-mem2
- samtools
- pairtools
- gfastats
- cutadapt
- pretextmap
- compleasm
- multiqc
tags:
- scaffolding
- hi-c
- yahs
- vgp
- chromosome-scale
- genome-assembly
- pretext
test_data:
- role: assembly_gfa
  url: https://zenodo.org/records/17190637/files/Assembly%20GFA.gfa1
  sha1: 674d80de5c15f407a7f8c194d0fa098bef9ae53b
  filetype: gfa1
- role: estimated_genome_size_parameter_file
  url: https://zenodo.org/records/17190637/files/Estimated%20genome%20size%20-%20Parameter%20File.expression.json
  sha1: 71cb196fbcdbf99c80d431de60704386d3a92d5f
  filetype: expression.json
- role: hi_c_reads__btaegut2_ari8_001_uspd16084394_ak5146_hjfmmccxy_l6_r1_fq_gz__forward
  url: https://zenodo.org/records/17190637/files/bTaeGut2_ARI8_001_USPD16084394-AK5146_HJFMMCCXY_L6_R1.fq.gz
  sha1: e28a3c03d447f75f9f4b1ebba638d7519718653f
- role: hi_c_reads__btaegut2_ari8_001_uspd16084394_ak5146_hjfmmccxy_l6_r1_fq_gz__reverse
  url: https://zenodo.org/records/17190637/files/bTaeGut2_ARI8_001_USPD16084394-AK5146_HJFMMCCXY_L6_R2.fq.gz
  sha1: a79ef11410b7d1f28f93dcbbd0c9ca12537c9df2
- role: hi_c_reads__btaegut2_ari8_001_uspd16084394_ak5146_hjfmfccxy_l8_r1_fq_gz__forward
  url: https://zenodo.org/records/17190637/files/bTaeGut2_ARI8_001_USPD16084394-AK5146_HJFMFCCXY_L8_R1.fq.gz
  sha1: f327e867f7e9b986b60196152c020b7c1a177e1b
- role: hi_c_reads__btaegut2_ari8_001_uspd16084394_ak5146_hjfmfccxy_l8_r1_fq_gz__reverse
  url: https://zenodo.org/records/17190637/files/bTaeGut2_ARI8_001_USPD16084394-AK5146_HJFMFCCXY_L8_R2.fq.gz
  sha1: cc4bf7af7686447bf9409aeb50f3825faca87e1b
- role: hi_c_reads__btaegut2_ari8_001_uspd16084394_ak5146_hjfmfccxy_l7_r1_fq_gz__forward
  url: https://zenodo.org/records/17190637/files/bTaeGut2_ARI8_001_USPD16084394-AK5146_HJFMFCCXY_L7_R1.fq.gz
  sha1: 9b67b4d69cc9b0bc8248a68550d2b2c19b3ac2ac
- role: hi_c_reads__btaegut2_ari8_001_uspd16084394_ak5146_hjfmfccxy_l7_r1_fq_gz__reverse
  url: https://zenodo.org/records/17190637/files/bTaeGut2_ARI8_001_USPD16084394-AK5146_HJFMFCCXY_L7_R2.fq.gz
  sha1: 10085c31a5d99205c52dca89b3df569165c226cc
- role: hi_c_reads__btaegut2_ari8_001_uspd16084394_ak5146_hjfmfccxy_l6_r1_fq_gz__forward
  url: https://zenodo.org/records/17190637/files/bTaeGut2_ARI8_001_USPD16084394-AK5146_HJFMFCCXY_L6_R1.fq.gz
  sha1: 688442b3d97416f02eadb6fc4e3b3021d6b2c8bf
- role: hi_c_reads__btaegut2_ari8_001_uspd16084394_ak5146_hjfmfccxy_l6_r1_fq_gz__reverse
  url: https://zenodo.org/records/17190637/files/bTaeGut2_ARI8_001_USPD16084394-AK5146_HJFMFCCXY_L6_R2.fq.gz
  sha1: 9f3fdec98d03356b6dd73710e5ab723867b6b4a4
- role: hi_c_reads__btaegut2_ari8_001_uspd16084394_ak5146_hjfmfccxy_l5_r1_fq_gz__forward
  url: https://zenodo.org/records/17190637/files/bTaeGut2_ARI8_001_USPD16084394-AK5146_HJFMFCCXY_L5_R1.fq.gz
  sha1: cf4fea47b72d4f81f099a7a98729a53237b91441
- role: hi_c_reads__btaegut2_ari8_001_uspd16084394_ak5146_hjfmfccxy_l5_r1_fq_gz__reverse
  url: https://zenodo.org/records/17190637/files/bTaeGut2_ARI8_001_USPD16084394-AK5146_HJFMFCCXY_L5_R2.fq.gz
  sha1: 1b806853794f65b6292f3e7a16294543d09ccba8
- role: hi_c_reads__btaegut2_ari8_001_uspd16084394_ak5146_hjfmfccxy_l4_r1_fq_gz__forward
  url: https://zenodo.org/records/17190637/files/bTaeGut2_ARI8_001_USPD16084394-AK5146_HJFMFCCXY_L4_R1.fq.gz
  sha1: 17e493fc2b897bb8233ad3fe6d08010804f76e9d
- role: hi_c_reads__btaegut2_ari8_001_uspd16084394_ak5146_hjfmfccxy_l4_r1_fq_gz__reverse
  url: https://zenodo.org/records/17190637/files/bTaeGut2_ARI8_001_USPD16084394-AK5146_HJFMFCCXY_L4_R2.fq.gz
  sha1: 97dd20426ecaa0a85c098506354c2dcbc8abf534
- role: hi_c_reads__btaegut2_ari8_001_uspd16084394_ak5146_hjfmfccxy_l3_r1_fq_gz__forward
  url: https://zenodo.org/records/17190637/files/bTaeGut2_ARI8_001_USPD16084394-AK5146_HJFMFCCXY_L3_R1.fq.gz
  sha1: 7f7d69998da49d5d34a2801dff8485bddaa74750
- role: hi_c_reads__btaegut2_ari8_001_uspd16084394_ak5146_hjfmfccxy_l3_r1_fq_gz__reverse
  url: https://zenodo.org/records/17190637/files/bTaeGut2_ARI8_001_USPD16084394-AK5146_HJFMFCCXY_L3_R2.fq.gz
  sha1: 372ff52ecf58d379fa227a0392af88a2501eca54
- role: hi_c_reads__btaegut2_ari8_001_uspd16084394_ak5146_hjfmfccxy_l2_r1_fq_gz__forward
  url: https://zenodo.org/records/17190637/files/bTaeGut2_ARI8_001_USPD16084394-AK5146_HJFMFCCXY_L2_R1.fq.gz
  sha1: ae585d838170a5388f6a148328a6cf0a7d85afd1
- role: hi_c_reads__btaegut2_ari8_001_uspd16084394_ak5146_hjfmfccxy_l2_r1_fq_gz__reverse
  url: https://zenodo.org/records/17190637/files/bTaeGut2_ARI8_001_USPD16084394-AK5146_HJFMFCCXY_L2_R2.fq.gz
  sha1: 3b5a6f100e0ee9787b1a8aea7a255ac860e53346
- role: hi_c_reads__btaegut2_ari8_001_uspd16084394_ak5146_hjfmfccxy_l1_r1_fq_gz__forward
  url: https://zenodo.org/records/17190637/files/bTaeGut2_ARI8_001_USPD16084394-AK5146_HJFMFCCXY_L1_R1.fq.gz
  sha1: f873ddaa1822673498879dd6f4b37e16641fd430
- role: hi_c_reads__btaegut2_ari8_001_uspd16084394_ak5146_hjfmfccxy_l1_r1_fq_gz__reverse
  url: https://zenodo.org/records/17190637/files/bTaeGut2_ARI8_001_USPD16084394-AK5146_HJFMFCCXY_L1_R2.fq.gz
  sha1: c70c3e99b70ee81f4262ddba46cdc2a8abb7964b
expected_output:
- role: suffixed_agp
  description: Content assertions for `Suffixed AGP`.
  assertions:
  - 'has_text: scaffold_1.H1'
- role: reconciliated_scaffolds_gfa
  description: 'Content assertions for `Reconciliated Scaffolds: gfa`.'
  assertions:
  - 'has_n_lines: {''n'': 5}'
- role: assembly_statistics_for_s2
  description: Content assertions for `Assembly Statistics for s2`.
  assertions:
  - "has_text: Total scaffold length\t5,788,676"
- role: scaffolding_plots
  description: Content assertions for `Scaffolding Plots`.
  assertions:
  - 'has_size: {''value'': 118911, ''delta'': 30000}'
- role: hi_c_alignment_stats_scaffolds
  description: Content assertions for `Hi-C Alignment Stats scaffolds`.
  assertions:
  - "has_text: SN\treads mapped and paired:\t33952"
- role: hi_c_alignments_on_scaffolds_stats_multiqc
  description: Content assertions for `Hi-C alignments on Scaffolds stats multiqc`.
  assertions:
  - "has_text: Hi-C Alignment Stats pre-scaffolding for Haplotype 1\t1.26354"
  - "has_text: Hi-C Alignment Stats scaffolds for Haplotype 1\t1.26353\t0.0\t0.033956"
- role: hi_c_maps
  description: Content assertions for `Hi-C maps`.
  assertions:
  - 'has_size: {''value'': 835200, ''delta'': 50000}'
- role: hi_c_alignment_stats_pre_scaffolding
  description: Content assertions for `Hi-C Alignment Stats pre-scaffolding`.
  assertions:
  - "has_text: SN\treads mapped and paired:\t33952"
- role: compleasm_full_table_busco
  description: Content assertions for `Compleasm Full Table Busco`.
  assertions:
  - 'has_n_lines: {''n'': 3355}'
- role: summary_numbers_scaffolds
  description: Content assertions for `Summary Numbers Scaffolds`.
  assertions:
  - "has_text: reads mapped and paired:\t33952"
- role: merged_alignment_stats
  description: Content assertions for `Merged Alignment stats`.
  assertions:
  - "has_text: bases mapped:\t5093400\t5093400"
- role: summary_numbers_contigs
  description: Content assertions for `Summary Numbers Contigs`.
  assertions:
  - "has_text: bases mapped:\t5093400"
- role: hi_c_duplication_stats_on_scaffolds_raw
  description: 'Content assertions for `Hi-C duplication stats on scaffolds: Raw`.'
  assertions:
  - "has_text: total_dups\t1327"
  - "has_text: total_nodups\t5990"
- role: hi_c_duplication_stats_on_scaffolds_multiqc
  description: 'Content assertions for `Hi-C duplication stats on scaffolds: MultiQc`.'
  assertions:
  - 'has_size: {''value'': 2185479, ''delta'': 500000}'
- role: deduplicated_hi_c_alignments_on_contigs
  description: Content assertions for `Deduplicated Hi-C alignments on contigs`.
  assertions:
  - 'has_size: {''value'': 3759316, ''delta'': 100000}'
- role: scaffolds_compleasm_summary
  description: Content assertions for `Scaffolds Compleasm Summary`.
  assertions:
  - 'has_text: S:0.00%, 0'
---

# Hi-C scaffolding of eukaryotic assemblies with YAHS (VGP8)

## When to use this sketch
- You already have a contig-level (or purged) assembly in **GFA 1.2 format** (with P lines and sequences) and want chromosome-scale scaffolds.
- You have paired-end **Hi-C reads** (Arima Hi-C 2.0, Dovetail, or similar) as a `list:paired` collection.
- You are working on a eukaryotic genome (vertebrate, plant, invertebrate) and want VGP-style QC: Compleasm BUSCO completeness, PretextMap contact maps before/after, Hi-C alignment and duplication statistics, Nx/size plots, and assembly statistics.
- You need per-haplotype scaffold naming (H1/H2/mat/pat/pri/alt suffixes appended to `scaffold_XX`).
- You are running the VGP trajectory step 8, following contigging (VGP3/4/5) and purge-dups (VGP6/7).

## Do not use when
- Your assembly is only in FASTA — first convert it to GFA with `gfastats` (or pick a FASTA-input scaffolding sketch).
- You are scaffolding a bacterial or small haploid genome — YAHS and this QC stack are overkill; use a targeted prokaryote assembly sketch.
- You only want to assemble contigs from raw reads — use a contigging sketch (hifiasm, Flye, Canu, VGP4) first.
- You want to polish or purge haplotigs — those are separate VGP steps (purge_dups / polishing sketches).
- You lack Hi-C data; for long-read-only scaffolding look at a scaffolding-with-long-reads sketch instead.

## Analysis outline
1. **Convert GFA → FASTA** reference with `gfastats` (manipulation mode).
2. **Optional Hi-C trimming** with `cutadapt` — trim 5 bp from R1 and R2 (`cut: 5`, `cut2: 5`) when using raw Arima data.
3. **Index** the contig FASTA with `bwa-mem2 index`.
4. **Align** each Hi-C pair with `bwa-mem2 mem` using Hi-C-appropriate flags (`-S`, `-P`, `-5`, `-T 30`), name-sorted output.
5. **Fixmate + sort** alignments with `samtools fixmate` / `samtools sort`; merge multi-lane libraries with `samtools merge`.
6. **Pair classification & dedup** with `pairtools parse` (`min_mapq: 1`, `max_molecule_size: 2000`, `walks_policy: mask`) followed by `pairtools dedup`.
7. **Remove duplicates** from BAM with `samtools markdup -r`; collect dup stats and `MultiQC` pairtools report.
8. **MAPQ filter** deduplicated BAM with `bamtools filter` using the user's minimum mapping quality (default 20).
9. **Scaffold** with `YAHS` using the filtered BAM, contig FASTA, and the preconfigured restriction enzyme (e.g. `arima2`); emit final AGP and FASTA. `no_contig_ec: true` disables contig error correction.
10. **Rename scaffolds** per haplotype suffix (`scaffold_01` → `scaffold_01.H1`) with find-and-replace on the AGP.
11. **Reconcile GFA** by feeding the renamed AGP + original GFA back through `gfastats` in scaffolding mode to produce a scaffold-level GFA and FASTA.
12. **QC**: `gfastats` assembly/size stats vs. estimated genome size, Nx/size plots, `Compleasm` BUSCO completeness, `PretextMap` + `Pretext Snapshot` before and after scaffolding, `samtools stats` on Hi-C alignments to contigs and scaffolds, and aggregated `MultiQC` reports.

## Key parameters
- `YAHS.enzyme`: preconfigured restriction enzyme, `arima2` for Arima Hi-C 2.0 (VGP default).
- `YAHS.no_contig_ec`: `true` (trust upstream contigs, do not break them).
- `bwa-mem2`: algorithmic options `-k 19 -w 100 -r 1.5 -T 30`, Hi-C flags `-S -P -5` (skip mate rescue/pairing, use 5' end as primary).
- `pairtools parse`: `min_mapq: 1`, `max_molecule_size: 2000`, `max_inter_algn_gap: 20`, `walks_policy: mask`, `drop_sam: true`, `drop_seq: true`.
- `pairtools dedup`: `mark_dups: true`, `max_mismatch: 0`.
- `samtools markdup`: `mode: s`, `remove: true`, `odist: 2500`.
- `bamtools filter`: mapQuality ≥ user `Minimum Mapping Quality` (default 20; set 0 to disable).
- `cutadapt`: `cut: 5`, `cut2: 5` only when `Trim Hi-C Data? = yes` (typical for raw Arima).
- `PretextMap.map_qual`: 20; `highRes: false`.
- `Compleasm.lineage`: `vertebrata_odb10` recommended for VGP vertebrates (set to match taxon otherwise).
- `Haplotype`: one of `Haplotype 1 | Haplotype 2 | Maternal | Paternal | Primary | Alternate`, mapped to suffix `H1/H2/mat/pat/pri/alt` appended to scaffold names.
- Estimated genome size: integer text file from upstream contigging workflow, used by `gfastats` for NG/LG statistics.

## Test data
The IWC test profile uses a *Taenopygia guttata* (zebra finch, bTaeGut2) Hi-C subset: a small `Assembly GFA.gfa1` contig graph, an `Estimated genome size` parameter file, and a `list:paired` collection of eight lanes of Arima Hi-C reads (`bTaeGut2_ARI8_001_..._L1..L8_R1/R2.fq.gz`) hosted on Zenodo record 17190637. The run is configured with `Haplotype 1`, `Trim Hi-C Data? = false`, `Minimum Mapping Quality = 10`, `Lineage = vertebrata_odb10`, and `Restriction enzymes = arima2`. Expected assertions: scaffolds in the suffixed AGP contain `scaffold_1.H1`; reconciliated scaffold GFA has 5 lines; `gfastats` assembly stats report `Total scaffold length  5,788,676`; `samtools stats` reports 33,952 Hi-C reads mapped and paired and 5,093,400 bases mapped on both contigs and scaffolds; Hi-C dedup yields `total_dups 1327` / `total_nodups 5990` on scaffolds; Compleasm summary records `S:0.00%, 0` (expected on the tiny test subset); PretextMap PNG and scaffolding plots fall within the declared size ranges; and the Compleasm full vertebrata table has 3,355 rows.

## Reference workflow
Galaxy IWC `VGP-assembly-v2 / Scaffolding-HiC-VGP8`, version 3.5 (CC-BY-4.0), VGP + Galaxy. Implements YAHS 1.2a.2, bwa-mem2 2.3, pairtools 1.1.3, samtools 1.22, gfastats 1.3.11, PretextMap 0.2.3, Compleasm 0.2.6, MultiQC 1.33.
