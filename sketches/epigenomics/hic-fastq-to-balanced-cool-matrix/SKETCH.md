---
name: hic-fastq-to-balanced-cool-matrix
description: Use when you need to process paired-end Hi-C (or Hi-ChIP) FASTQ reads
  into a balanced, multi-resolution contact matrix in cool format. Covers adapter
  truncation at the religation motif, independent mate mapping, di-tag filtering,
  MAPQ filtering, fragment-midpoint pair generation, and ICE normalization at a user-chosen
  bin size.
domain: epigenomics
organism_class:
- eukaryote
- vertebrate
input_data:
- short-reads-paired
- bowtie2-index
- restriction-enzyme-spec
source:
  ecosystem: iwc
  workflow: 'Hi-C Processing: FASTQ to Balanced Cool Files'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/epigenetics/hic-hicup-cooler
  version: '0.3'
  license: MIT
  slug: epigenetics--hic-hicup-cooler--hic-juicermediumtabix-to-cool-cooler
tools:
- name: hicup
- name: bowtie2
- name: hicup2juicer
- name: cooler
  version: 0.9.3+galaxy0
- name: cooler_csort
- name: cooler_balance
  version: 0.9.3+galaxy0
- name: pygenometracks
tags:
- hi-c
- hi-chip
- 3d-genome
- contact-matrix
- chromatin-conformation
- cooler
- hicup
- ice-normalization
test_data:
- role: pe_fastq_input__test_dataset__forward
  url: https://github.com/bgruening/galaxytools/raw/master/tools/hicup/test-data/dataset1.fastq
  sha1: 44e770082bebc78d3fd4a0ab36a310e3a9b2b30b
  filetype: fastqsanger
- role: pe_fastq_input__test_dataset__reverse
  url: https://github.com/bgruening/galaxytools/raw/master/tools/hicup/test-data/dataset2.fastq
  sha1: fad880234676f3402c2293baf559ff75d5106b81
  filetype: fastqsanger
expected_output:
- role: hicup_report_html
  description: Content assertions for `HiCUP report (html)`.
  assertions:
  - 'test_dataset: has_size: {''value'': 4602173, ''delta'': 4000000}'
- role: hicup_report_txt
  description: Content assertions for `HiCUP report (txt)`.
  assertions:
  - "test_dataset: has_text: \t99742\t99742\t92512\t92628\t7230\t7114\t22.45\t22.63\t\
    2658\t2476\t73431\t72142\t17767\t18475\t5886\t6649\t57671\t57671\t39966\t1652\t\
    17997\t20317\t17705\t481\t2432\t13452\t1340\t0\t0\t39962\t1652\t17996\t20314\t\
    57.82\t69.30\t99.99\t50.83\t40.07"
- role: valid_pairs_in_juicebox_format
  description: Content assertions for `valid pairs in juicebox format`.
  assertions:
  - 'test_dataset: that: has_line'
  - "test_dataset: line: 1\t1\tchr10\t100023987\t28055\t1\tchr10\t101500419\t28474\t\
    42\t42"
  - 'test_dataset: that: has_line'
  - "test_dataset: line: 2\t1\tchr10\t100091500\t28079\t1\tchr10\t122245984\t34516\t\
    38\t42"
  - 'test_dataset: that: has_line'
  - "test_dataset: line: 3\t0\tchr10\t100127492\t28094\t1\tchr10\t50864290\t13489\t\
    0\t42"
- role: valid_pairs_in_juicebox_format_mapq_filtered
  description: Content assertions for `valid pairs in juicebox format MAPQ filtered`.
  assertions:
  - 'test_dataset: that: has_line'
  - "test_dataset: line: 1\t1\tchr10\t100023987\t28055\t1\tchr10\t101500419\t28474\t\
    42\t42"
  - 'test_dataset: that: has_line'
  - "test_dataset: line: 2\t1\tchr10\t100091500\t28079\t1\tchr10\t122245984\t34516\t\
    38\t42"
  - 'test_dataset: that: not_has_text'
  - "test_dataset: text: 3\t0\tchr10\t100127492\t28094\t1\tchr10\t50864290\t13489\t\
    0\t42"
- role: valid_pairs_filtered_and_sorted
  description: Content assertions for `valid pairs filtered and sorted`.
  assertions:
  - 'test_dataset: has_size: {''value'': 807, ''delta'': 80}'
- role: matrix_with_raw_values
  description: Content assertions for `matrix with raw values`.
  assertions:
  - 'test_dataset: has_size: {''value'': 42118, ''delta'': 4000}'
- role: matrix_with_iced_values
  description: Content assertions for `matrix with iced values`.
  assertions:
  - 'test_dataset: has_size: {''value'': 47830, ''delta'': 4000}'
---

# Hi-C FASTQ to balanced cool matrix (HiCUP + cooler)

## When to use this sketch
- You have paired-end Hi-C FASTQ files from a restriction-enzyme based protocol (HindIII, DpnII, MboI, BglII, multi-enzyme Arima, etc.) and want a balanced `.cool` contact matrix ready for downstream 3D genome analysis.
- The reference genome is available as a pre-built bowtie2 index (HiCUP uses bowtie2 for mate mapping).
- You need fragment-aware filtering (removing self-ligations, dangling ends, re-ligations, PCR duplicates) before binning.
- You want ICE-balanced matrices at a specific bin size (e.g. 10 kb, 40 kb, 1 Mb) and a quick pyGenomeTracks sanity plot over a chosen locus.
- You are processing Hi-ChIP data and plan to use the raw (non-balanced) matrix — the same pipeline works; just take the `matrix with raw values` output instead of the ICE-balanced one.

## Do not use when
- You need capture Hi-C / region-restricted matrices — use the sibling `capture-hic-fastq-to-cool` sketch which additionally filters pairs to a capture region before binning.
- You have Micro-C or any non-restriction-enzyme 3C variant — HiCUP's truncation and digest-based filtering are inappropriate; use a pairtools/distiller-style workflow instead.
- You are starting from already-processed pairs files (`.pairs`, juicer medium tabix) — skip HiCUP and use only the tabix→cool subworkflow.
- You want a `.hic` (juicer) multi-resolution file for Juicebox rather than `.cool` — convert downstream or use a juicer-based pipeline.
- You need TAD calling, loop calling, or compartment analysis — that's downstream of this sketch; feed its `.cool` output into HiCExplorer / cooltools / FAN-C.

## Analysis outline
1. **HiCUP pipeline** (`hicup_hicup`) — truncate reads at the religation motif, map each mate independently with bowtie2 against the chosen genome index, pair mates requiring uniquely mapped / MAPQ30, filter invalid di-tags (self-ligation, dangling end, re-ligation, internal, size), remove PCR duplicates. Emits a qname-sorted BAM, an HTML + tabular QC report, and a digester file.
2. **hicup2juicer** — convert the HiCUP BAM to juicer medium format pairs, using the digester file and `usemid=true` so each pair's position is the midpoint of its restriction fragment (not the read 5' end). Produces `<readname> <str1> <chr1> <pos1> <frag1> <str2> <chr2> <pos2> <frag2> <mapq1> <mapq2>`.
3. **MAPQ filter** (`Filter1` via `compose_text_param`) — keep only pairs where both `c10 >= minMAPQ` and `c11 >= minMAPQ`; `minMAPQ=0` disables filtering (HiCUP already enforces unique/MAPQ30).
4. **cooler csort + tabix** — sort the filtered juicer-medium pairs by chromosome/position and build a tabix index using cached chromosome sizes from the genome index. Output datatype is `juicer_medium_tabix.gz`.
5. **cooler makebins** — generate a genome-wide BED of fixed-width bins at the requested resolution.
6. **cooler cload tabix** — load the sorted tabix pairs into the bin grid, producing the raw `.cool` contact matrix.
7. **cooler balance** — ICE-normalize the matrix, storing weights in the `weight` column. Uses `cistrans` (empty / `--cis-only` / `--trans-only`) to choose which interactions drive weight estimation.
8. **pyGenomeTracks** — plot the balanced matrix over a user-supplied region (e.g. HoxD locus) as a PNG for visual QC.

## Key parameters
- `genome name`: must correspond to an installed bowtie2 index on the Galaxy instance (e.g. `hg19`, `hg38`, `mm10`, `mm39`); also used to fetch chromosome sizes for binning.
- `Restriction enzyme`: HiCUP syntax `A^AGCTT,HindIII`; `^` marks the cut site. Multi-enzyme protocols (Arima, Omni-C-style) use `:` to separate, e.g. `A^GATCT,BglII:A^AGCTT,HindIII:^GATC,DpnII`. `N` is allowed, e.g. `:A^ANCTT`.
- `No fill-in` (boolean): `true` if the protocol did NOT include a biotin fill-in of sticky ends (reads should be truncated at the restriction site sequence); `false` for standard biotin-fill-in Hi-C.
- `minimum MAPQ`: integer; `30` is typical, `0` disables (HiCUP's unique-mapping filter still applies).
- `Bin size in bp`: resolution of the output matrix (e.g. `10000` for 10 kb, `1000000` for 1 Mb). The tabix→cool subworkflow can be rerun alone to generate additional resolutions without redoing HiCUP.
- `Interactions to consider ... normalization`: one of empty string (genome-wide), `--cis-only` (recommended default), or `--trans-only`, passed to `cooler_balance`.
- `region for matrix plotting`: UCSC-style `chr:start-end` for the pyGenomeTracks QC plot (e.g. HoxD locus `chr2:174,692,032-177,585,317` on hg38).
- cooler_balance internal defaults: `mincount=0`, `minnnz=10`, `madmax=5`, `ignorediags=2`, `tol=1e-5`, `maxiters=200`, `convergencepolicy=error`, weight column `weight`.

## Test data
A single paired Hi-C sample named `test_dataset` provided as a `list:paired` collection of two `fastqsanger` files (`dataset1.fastq` forward, `dataset2.fastq` reverse) taken from the HiCUP Galaxy tool test data. The test job runs against the `hg19` bowtie2 index with restriction enzyme `A^AGCTT,HindIII`, `No fill-in=false`, `minimum MAPQ=30`, `Bin size=1,000,000 bp`, and `--cis-only` balancing. Expected outputs: a HiCUP HTML report (~4.6 MB), a HiCUP tabular report containing the exact ditag-classification stats line, a juicer-medium pairs file containing specific ditags (e.g. `chr10:100023987 ↔ chr10:101500419` with MAPQs `42/42`), a MAPQ-filtered pairs file that retains the MAPQ≥30 lines but drops the `MAPQ=0` pair, a sorted+tabix pairs archive (~807 bytes), a raw 1 Mb cool matrix (~42 KB), an ICE-balanced cool matrix (~48 KB), and a pyGenomeTracks PNG compared by size against a golden `plot_chic.png`.

## Reference workflow
Galaxy IWC — `workflows/epigenetics/hic-hicup-cooler` — "Hi-C Processing: FASTQ to Balanced Cool Files" v0.3 (HiCUP 0.9.2, cooler 0.9.3, pyGenomeTracks 3.8), MIT, by Lucille Delisle (ORCID 0000-0002-1964-4960).
