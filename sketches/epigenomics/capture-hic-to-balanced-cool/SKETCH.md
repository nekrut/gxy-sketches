---
name: capture-hic-to-balanced-cool
description: Use when you need to process Capture Hi-C (or Hi-ChIP) paired-end FASTQ
  data into balanced .cool contact matrices at a chosen resolution, including HiCUP
  read processing, MAPQ filtering, restriction-aware pairing, capture-region filtering,
  and ICE normalization with cooler.
domain: epigenomics
organism_class:
- vertebrate
- eukaryote
input_data:
- short-reads-paired
- bowtie2-index
- restriction-enzyme-spec
source:
  ecosystem: iwc
  workflow: 'Capture Hi-C Processing: FASTQ to Balanced Cool Files'
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
- capture-hi-c
- chic
- hi-chip
- 3d-genome
- contact-matrix
- cool
- ice-normalization
- hicup
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

# Capture Hi-C processing: FASTQ to balanced cool files

## When to use this sketch
- You have paired-end Illumina FASTQs from a Capture Hi-C (cHi-C) experiment targeting a defined genomic region, and you want balanced contact matrices (.cool) at a chosen bin size.
- You know the restriction enzyme used (e.g. `A^AGCTT,HindIII` or `A^GATCT,BglII`) and whether the protocol involved a biotin fill-in of sticky ends.
- You want HiCUP-style read handling (truncation at religation motif, independent mate mapping with bowtie2, valid-pair filtering, duplicate removal) followed by cooler-based binning and ICE balancing.
- You need to restrict the final matrix to a capture region defined by chromosome/start/end.
- Also applicable to Hi-ChIP experiments — in that case keep the raw (unbalanced) matrix and ignore the ICE-balanced one.
- A reference genome with a pre-built bowtie2 index is available (cached by name, e.g. `hg19`, `mm10`).

## Do not use when
- You have genome-wide (non-capture) Hi-C and want a whole-genome contact map — use a genome-wide Hi-C sketch instead; this workflow includes a capture-region filter step that will drop most reads.
- You are starting from already-aligned BAM or from a valid-pairs/tabix file — use the `hic_tabix_to_cool_cooler` entry point instead of running HiCUP from scratch.
- You need micro-C, single-cell Hi-C, or in-situ Hi-C with DNase/MNase digestion — HiCUP with a fixed restriction motif is inappropriate.
- You want TAD calling, loop calling, or differential interaction analysis — this sketch only produces the normalized matrices; downstream analysis belongs in a separate sketch.
- Your organism has no bowtie2 index cached on the Galaxy instance.

## Analysis outline
1. HiCUP pipeline on the paired FASTQ collection: truncate reads at the religation motif, map mates independently with bowtie2, pair uniquely-mapped/MAPQ30 mates, filter out undigested/self-ligated fragments, and remove PCR duplicates. Produces a qname-sorted BAM, a digester file, and HiCUP HTML + tabular QC reports.
2. Convert HiCUP BAM to Juicer medium-format valid pairs with `hicup2juicer` (uses the fragment midpoint, not the 5' end).
3. Filter valid pairs by minimum MAPQ using a composed expression on columns c10/c11 (Galaxy `Filter1`). Set to 0 to skip.
4. Filter valid pairs so that both mates fall inside the capture region: `(c3=='<chr>' and c4<end and c4>start) and (c7=="<chr>" and c8<end and c8>start)`.
5. Sort and tabix-index the filtered pairs with `cooler csort` in `juicer_medium` format, using cached chromosome sizes from the genome name.
6. Build a fixed-width bin BED with `cooler makebins` at the requested resolution.
7. Load pairs into a raw `.cool` matrix with `cooler cload tabix` (`juicer_medium` format).
8. Balance the matrix with `cooler balance` (ICE), using `--cis-only` / `--trans-only` / genome-wide according to the normalization-scope parameter. This yields the final balanced cool file.
9. Render a QC contact-map plot of the capture region with pyGenomeTracks on the balanced matrix.

## Key parameters
- `genome name`: must correspond to a bowtie2 index cached on the Galaxy instance; also drives chromosome sizes for `cooler csort`/`makebins`.
- `Restriction enzyme`: HiCUP `re1` spec, `SITE,NAME` with `^` marking the cut (e.g. `A^AGCTT,HindIII`). Multiple enzymes separated by `:`. `N` is allowed.
- `No fill-in` (boolean): `true` when the protocol did NOT biotin-fill sticky ends — reads are truncated at the restriction site. Set `false` for standard biotin fill-in Hi-C.
- `minimum MAPQ`: integer applied to both mates (c10 and c11); typical value `30`, use `0` to skip (HiCUP already enforces unique/MAPQ30).
- `Bin size in bp`: resolution of the output matrix (e.g. `1000000` for 1 Mb, `10000` for 10 kb). The `hic_tabix_to_cool_cooler` subworkflow can be re-run to produce additional resolutions.
- `Interactions to consider ...` for cooler_balance: empty (genome-wide), `--cis-only` (recommended for Capture Hi-C), or `--trans-only`.
- `capture region`: `chromosome`, `start`, `end` — used both for pair filtering and for the final pyGenomeTracks region string (`chr:start-end`).
- cooler_balance defaults used: `ignorediags=2`, `madmax=5`, `maxiters=200`, `minnnz=10`, `tol=1e-5`, `convergencepolicy=error`, weight column `weight`.
- pyGenomeTracks defaults: `colormap=RdYlBu_r`, `depth=8000000`, PNG output.

## Test data
A single paired sample (`test_dataset`) built from two public HiCUP test FASTQs — `dataset1.fastq` (forward) and `dataset2.fastq` (reverse) from `bgruening/galaxytools` — run against the cached `hg19` bowtie2 index with enzyme `A^AGCTT,HindIII`, `No fill-in=false`, `minimum MAPQ=30`, `Bin size=1000000`, cis-only balancing, and capture region `chr2:170000000-180000000`. Expected outputs: a HiCUP HTML report (~4.6 MB, size-tolerant), a HiCUP tabular report containing the exact mapping/pairing/dedup statistics line `99742\t99742\t92512\t92628\t...\t57.82\t69.30\t99.99\t50.83\t40.07`, a Juicer-medium valid-pairs file containing specific chr10 pair lines (including a MAPQ=0 pair that must NOT appear in the MAPQ-filtered version), a sorted/tabix'd pairs file (~807 bytes), a raw cool matrix (~42 kB), an ICE-balanced cool matrix (~48 kB), and a pyGenomeTracks PNG compared by approximate size.

## Reference workflow
IWC `workflows/epigenetics/hic-hicup-cooler` — *Capture Hi-C Processing: FASTQ to Balanced Cool Files*, release 0.3 (2023-09-08), MIT, by Lucille Delisle. Uses HiCUP 0.9.2, hicup2juicer 0.9.2, cooler 0.9.3 (csort/makebins/cload_tabix/balance), and pyGenomeTracks 3.8.
