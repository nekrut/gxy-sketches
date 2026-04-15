---
name: bcr-tcr-repertoire-bulk-umi
description: Use when you need to analyze B-cell or T-cell receptor (BCR/TCR) repertoires
  from bulk targeted AIRR-seq Illumina data with UMI barcodes (e.g. NEBNext Immune,
  Takara SMART-Seq, or custom multiplex PCR+UMI). Performs end-to-end pRESTO assembly,
  IgBLAST V(D)J annotation, SCOPer clonal inference, and Alakazam repertoire comparison
  via the Immcantation framework.
domain: other
organism_class:
- human
- mouse
- vertebrate
input_data:
- short-reads-paired
- umi-index-fastq
- primer-fasta
- imgt-reference
source:
  ecosystem: nf-core
  workflow: nf-core/airrflow
  url: https://github.com/nf-core/airrflow
  version: 5.0.0
  license: MIT
  slug: airrflow
tools:
- name: fastp
  version: 0.23.4
- name: pRESTO
- name: IgBLAST
- name: Change-O
- name: SHazaM
- name: SCOPer
- name: Alakazam
- name: Dowser
- name: EnchantR
- name: MultiQC
tags: []
test_data: []
expected_output: []
---

# Bulk BCR/TCR repertoire analysis with UMIs (Immcantation)

## When to use this sketch
- You have bulk targeted BCR (IG) or TCR (TR) Illumina paired-end FASTQ from human or mouse.
- Library was built with transcript-specific multiplex PCR + UMI barcodes, 5' RACE + UMI, or a commercial kit with a matching airrflow profile (NEBNext Immune, Takara SMART-Seq/SMARTer).
- You want an AIRR-compliant end-to-end run: quality filtering, primer masking, UMI consensus, mate assembly, deduplication, IgBLAST V(D)J assignment, SCOPer clonal grouping, and a repertoire comparison report.
- Inputs include C-region and (optionally) V-region primer FASTAs, and you know UMI length/position or are using a preset protocol profile.

## Do not use when
- Input is 10x Genomics single-cell VDJ FASTQ — use the single-cell scVDJ sketch (airrflow `--library_generation_method sc_10x_genomics` with a cellranger VDJ reference).
- You only have assembled AIRR rearrangement TSVs or assembled FASTA sequences — use airrflow's `--mode assembled` sketch that skips pRESTO and starts at IgBLAST reassignment.
- You want to mine BCR/TCR from untargeted bulk or single-cell RNA-seq — use a TRUST4-based sketch (`--library_generation_method trust4`).
- You need germline genotyping, SHM-based selection analysis (BASELINe), or non-Immcantation clonotyping tools not wired into airrflow.
- Your organism is not human or mouse (IgBLAST germline references are not shipped for other species).

## Analysis outline
1. Read QC and adapter trimming with `fastp`.
2. pRESTO `FilterSeq` — drop reads below Phred quality threshold (default 20).
3. pRESTO `MaskPrimers` — identify/mask V- and C-region primers on R1/R2.
4. pRESTO `PairSeq` — pair R1/R2 mates by coordinate.
5. pRESTO `ClusterSets` + `BuildConsensus` — collapse reads sharing a UMI barcode into one consensus sequence per molecule.
6. pRESTO `AssemblePairs` (align or sequential) — stitch R1/R2 consensus into full V(D)J amplicons.
7. pRESTO `CollapseSeq` + `SplitSeq` — deduplicate and keep sequences supported by ≥2 reads.
8. Change-O `AssignGenes` (IgBLAST) against IMGT — call V, D, J genes.
9. Change-O `MakeDb` — emit AIRR rearrangement TSV; filter for locus/v_call concordance, ≥200 informative positions, ≤10% N, productive, junction length %3 == 0.
10. EnchantR — annotate metadata, `CreateGermlines`, optional SHazaM chimera removal and contamination detection, `Alakazam collapseDuplicates`.
11. SHazaM `distToNearest` / `findThreshold` — auto-determine clonal Hamming distance threshold per `cloneby` group.
12. SCOPer `hierarchicalClones` — assign `clone_id` within V/J/junction-length partitions.
13. (Optional) Dowser + RAxML or IgPhyML — reconstruct BCR lineage trees when `--lineage_trees true`.
14. Alakazam repertoire report (`Airrflow_report.html`) + MultiQC.

## Key parameters
- `--mode fastq` (vs `assembled`).
- `--library_generation_method`: one of `specific_pcr_umi`, `specific_pcr`, `dt_5p_race_umi`, `dt_5p_race`. Prefer a preset profile (`nebnext_umi_bcr`, `nebnext_umi_tcr`, `takara_smartseq_umi_bcr`, `takara_smartseq_umi_tcr`, `takara_smarter_umi_bcr`, `takara_smarter_umi_tcr`) when applicable — it fixes primers and UMI settings automatically.
- Primers: `--cprimers CPrimers.fasta`, `--vprimers VPrimers.fasta` (skip `vprimers` for 5' RACE and provide `--race_linker` instead).
- UMI handling: `--umi_length` (nt; set `0` for sans-UMI), `--umi_position R1|R2`, `--umi_start`, `--index_file true` if UMIs live in a separate I1 FASTQ; `--cprimer_position R1|R2`.
- pRESTO tuning: `--filterseq_q 20`, `--primer_r1_maxerror 0.2`, `--buildconsensus_maxerror 0.1`, `--cluster_sets true`.
- VDJ references: `--reference_fasta` + `--reference_igblast` (zipped IMGT/IgBLAST caches), or `--fetch_imgt true` to re-download. Set per-sample `species` = `human` or `mouse` and `pcr_target_locus` = `IG` or `TR` in the samplesheet.
- Clonal inference: `--clonal_threshold auto` (BCR; override to `0.1` for small datasets), **set `--clonal_threshold 0` for TCR**. Group with `--cloneby subject_id` (default) and `--crossby subject_id`.
- Lineage trees: `--lineage_trees true`, `--lineage_tree_builder raxml|igphyml`, `--lineage_tree_exec /usr/local/bin/raxml-ng`.
- Optional filters: `--remove_chimeric true`, `--detect_contamination true`, `--productive_only true`, `--skip_report` / `--skip_multiqc`.

## Samplesheet (input.tsv)
Tab-separated with required columns: `sample_id`, `filename_R1`, `filename_R2`, optional `filename_I1`, `subject_id`, `species` (`human`/`mouse`), `pcr_target_locus` (`IG`/`TR`), `tissue`, `sex`, `age`, `biomaterial_provider`, `single_cell` (`FALSE` for bulk). Rows sharing `sample_id` are merged across lanes. Use the same `subject_id` across timepoints/tissues so clones are defined consistently, since airrflow groups by `subject_id` prior to clonal inference by default.

## Test data
The airrflow `test` profile uses a small human BCR bulk dataset from nf-core/test-datasets (`testdata-bcr/Metadata_small_test_airr.tsv`) with paired FASTQ + I1 index files, accompanying `C_primers.fasta` and `V_primers.fasta`, and cached IMGT/IgBLAST databases (`database-cache/imgtdb_base.zip`, `igblast_base.zip`). It is configured as `specific_pcr_umi` with `umi_length=8`, `umi_start=6`, `umi_position=R1`, `index_file=true`, and `lineage_trees=true`. A successful run produces per-sample pRESTO logs, AIRR rearrangement TSVs under `vdj_annotation/`, a SCOPer `clone-pass.tsv` per subject under `clonal_analysis/clonal_assignment/`, a SHazaM threshold report, Dowser lineage trees, an `Airrflow_report.html` with Alakazam diversity/abundance/V-family plots, and a MultiQC report. The `test_full` profile exercises the same recipe on a ~300-sample bulk human BCR dataset (`testdata-bcr/metadata_pcr_umi_airr_300.tsv`) with `umi_length=15` and full IMGT references.

## Reference workflow
nf-core/airrflow v5.0.0 (MIT) — https://github.com/nf-core/airrflow. Built on the Immcantation framework (pRESTO, Change-O, SHazaM, SCOPer, Alakazam, Dowser, EnchantR) with IgBLAST and fastp; AIRR-C sw-tools v1 compliant. See Gabernet et al., PLOS Comput Biol 20(7):e1012265 (2024).
