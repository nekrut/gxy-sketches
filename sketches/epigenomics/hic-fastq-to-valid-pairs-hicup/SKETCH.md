---
name: hic-fastq-to-valid-pairs-hicup
description: Use when you need to process paired-end Hi-C (or Hi-ChIP / Capture Hi-C)
  FASTQ reads into validated, de-duplicated interaction pairs in Juicebox medium format,
  ready for downstream matrix building with cooler. Handles ligation-junction truncation,
  restriction-fragment assignment, artifact filtering, and MAPQ filtering.
domain: epigenomics
organism_class:
- eukaryote
input_data:
- short-reads-paired
- bowtie2-index
- restriction-enzyme-spec
source:
  ecosystem: iwc
  workflow: 'Hi-C Data Processing: FASTQ to Valid Interaction Pairs'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/epigenetics/hic-hicup-cooler
  version: '0.3'
  license: MIT
  slug: epigenetics--hic-hicup-cooler--hic-juicermediumtabix-to-cool-cooler
tools:
- name: hicup
- name: bowtie2
- name: hicup2juicer
- name: galaxy-filter1
tags:
- hi-c
- hi-chip
- capture-hi-c
- 3d-genome
- chromatin-conformation
- interaction-pairs
- hicup
- juicebox
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

# Hi-C FASTQ to Valid Interaction Pairs (HiCUP)

## When to use this sketch
- You have paired-end Hi-C (or Hi-ChIP, or Capture Hi-C) FASTQ files and need validated, de-duplicated read pairs as a starting point for contact-matrix construction.
- You know the restriction enzyme(s) used in the library and whether the protocol included a biotin fill-in of sticky ends.
- A bowtie2 index for the target genome is available (e.g. hg19, hg38, mm10) on the Galaxy server.
- You want outputs in Juicer medium format (`readname str1 chr1 pos1 frag1 str2 chr2 pos2 frag2 mapq1 mapq2`) with fragment-midpoint coordinates, optionally MAPQ-filtered.
- Multi-enzyme protocols (e.g. Arima) are supported via HiCUP's `:`-separated enzyme syntax.

## Do not use when
- You only need raw pairs and plan to use a different pipeline (e.g. distiller/pairtools, HiC-Pro) — pick those sketches instead.
- You want a complete end-to-end Hi-C workflow that also builds balanced `.cool` matrices and plots — use the sibling `hic-fastq-to-balanced-cool-hicup-cooler` sketch, which wraps this one plus `hic_tabix_to_cool_cooler`.
- You already have valid pairs in `juicer_medium_tabix.gz` and just want to re-bin at new resolutions — use the sibling `hic-tabix-to-cool-cooler` sketch.
- You are working with micro-C, DNase Hi-C, or other restriction-enzyme-free protocols — HiCUP's digest step does not apply.
- Your data are single-cell Hi-C — this pipeline is bulk-only.

## Analysis outline
1. Supply a paired FASTQ collection (`list:paired`), a bowtie2 genome index, the restriction enzyme spec, and the no-fill-in flag.
2. Run **HiCUP Pipeline** (`hicup_hicup` 0.9.2+galaxy0): truncate reads at the ligation junction, map mates independently with bowtie2, pair mates (keeping uniquely mapped / MAPQ≥30), filter out self-ligated, dangling-end, internal-fragment, and size-outlier pairs, and remove duplicates. Emits a qname-sorted BAM plus the genome digest file and an HTML/tabular QC report.
3. Run **HiCUP to Juicer converter** (`hicup2juicer` 0.9.2+galaxy0) with the digester file and `usemid=true` to produce valid pairs in Juicer medium format using restriction-fragment midpoints as coordinates.
4. Build a MAPQ filter expression via **Compose text parameter value** (`(c10>=N) and (c11>=N)`) driven by the `minimum MAPQ` input.
5. Apply Galaxy **Filter1** on the juicer-format pairs using that expression to retain only pairs where both mates meet the MAPQ threshold.

## Key parameters
- `genome`: bowtie2 index name for the target assembly (e.g. `hg19`, `hg38`, `mm10`).
- `re1`: restriction enzyme spec with `^` marking the cut site, e.g. `A^AGCTT,HindIII`, `A^GATCT,BglII`, `^GATC,DpnII`. Join multiple enzymes with `:` (e.g. `A^GATCT,BglII:A^AGCTT,HindIII`); `N` is permitted in the recognition sequence.
- `advanced_options.nofill` (boolean): `false` for biotin fill-in protocols (standard Hi-C) so that reads are truncated at the ligation junction; `true` for protocols without fill-in, so reads are truncated at the restriction site sequence.
- `minimum MAPQ` (integer): threshold applied to both mates after conversion; set to `0` to skip (HiCUP already enforces unique mapping / MAPQ30 internally). Typical value: `30`.
- `library.type`: `paired_collection` — input must be a `list:paired` FASTQ collection.
- `hicup2juicer.digester.usemid`: `true` — pair coordinates are the midpoint of the assigned restriction fragment, not the 5' end.
- `advanced_options.re2 / longest / shortest`: left empty by default; set only for unusual digest or fragment-size windows.

## Test data
A single paired FASTQ sample named `test_dataset` is taken from the HiCUP tool test data: `dataset1.fastq` (forward) and `dataset2.fastq` (reverse) from `bgruening/galaxytools`. It is run against the `hg19` bowtie2 index with restriction enzyme `A^AGCTT,HindIII`, `No fill-in = false`, and `minimum MAPQ = 30`. Expected results: a HiCUP HTML report (~4.6 MB) and a tabular report containing a specific summary line of per-step read counts; valid pairs in Juicebox format containing lines such as `1\t1\tchr10\t100023987\t28055\t1\tchr10\t101500419\t28474\t42\t42`; the MAPQ-filtered pairs retaining the MAPQ-42 lines but dropping the line with `mapq1=0`; and (when chained into the full parent workflow) a sorted-and-indexed pairs file ~807 bytes plus raw and ICE-balanced cooler matrices around 42 KB and 47 KB respectively.

## Reference workflow
Galaxy IWC `workflows/epigenetics/hic-hicup-cooler/hic-fastq-to-pairs-hicup.ga`, release 0.3 (2023-09-08), by Lucille Delisle. Subworkflow of `Hi-C_fastqToCool_hicup_cooler`; pairs with `hic_tabix_to_cool_cooler` for matrix construction. Tools: HiCUP 0.9.2, hicup2juicer 0.9.2, compose_text_param 0.1.1, Galaxy Filter1 1.1.1.
