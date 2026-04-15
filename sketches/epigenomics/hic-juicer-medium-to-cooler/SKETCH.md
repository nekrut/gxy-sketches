---
name: hic-juicer-medium-to-cooler
description: Use when you have Hi-C valid pairs already in Juicer medium tabix format
  and need to convert them into balanced .cool matrices at a chosen resolution for
  downstream visualization or analysis. Assumes mapping/filtering has already been
  done (e.g. by HiCUP) and you just want cooler-format output with ICE weights.
domain: epigenomics
organism_class:
- eukaryote
input_data:
- juicer-medium-tabix
- genome-name
source:
  ecosystem: iwc
  workflow: 'Hi-C Format Conversion: Juicer Medium to Cooler Files'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/epigenetics/hic-hicup-cooler
  version: '0.3'
  license: MIT
  slug: epigenetics--hic-hicup-cooler--hic-juicermediumtabix-to-cool-cooler
tools:
- name: cooler_makebins
  version: 0.9.3+galaxy0
- name: cooler_cload_tabix
  version: 0.9.3+galaxy1
- name: cooler_balance
  version: 0.9.3+galaxy0
tags:
- hi-c
- cooler
- juicer
- ice-normalization
- format-conversion
- chromatin-conformation
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

# Hi-C Juicer Medium Tabix to Balanced Cooler

## When to use this sketch
- You already have Hi-C valid pairs in Juicer medium tabix format (e.g. output of a HiCUP+hicup2juicer pipeline) and want `.cool` files.
- You need to (re)generate a cooler matrix at a specific bin size (e.g. 10 kb, 100 kb, 1 Mb) without rerunning upstream mapping.
- You want ICE-balanced matrices ready for cooltools, HiCExplorer, or pyGenomeTracks visualization.
- The reference genome is available as a Galaxy cached `.len`/fasta entry so chromosome sizes can be looked up by name (e.g. `hg19`, `mm10`).
- Applicable to Hi-C, capture Hi-C, or Hi-ChIP pairs (for Hi-ChIP, prefer the raw matrix over the ICE-balanced one).

## Do not use when
- You are starting from raw FASTQ — use the full `hic-fastq-to-cool-hicup-cooler` sibling workflow that runs HiCUP first.
- Your pairs are in 4DN `.pairs`, BEDPE, or HiC-Pro `validPairs` format rather than Juicer medium — use a `cooler cload pairs` / `cload pairix` variant instead.
- You need a `.hic` (Juicer) file as the final output — use a Juicer Pre-based conversion workflow.
- You are doing single-cell Hi-C, micro-C-specific QC, or loop/TAD calling — those are downstream and out of scope.

## Analysis outline
1. Accept a bin size (bp), a genome assembly name, a collection of Juicer medium tabix files, and a cis/trans policy as inputs.
2. `cooler_makebins` — build a BED of fixed-width bins across all chromosomes using the cached genome's chrom sizes and the requested bin size.
3. `cooler_cload_tabix` — load each Juicer medium tabix pair file into a `.cool` matrix using the bin BED and the assembly name (format: `juicer_medium`); output labeled "matrix with raw values".
4. `cooler_balance` — run ICE (iterative correction) normalization on each raw `.cool` to add a `weight` column; output labeled "matrix with iced values".

## Key parameters
- `binsize`: integer in bp (e.g. `10000` for 10 kb, `1000000` for 1 Mb). Drives resolution of both outputs.
- `genome name` / `assembly`: cached dbkey used by `cooler_makebins` and `cooler_cload_tabix` (e.g. `hg19`, `mm10`).
- `cooler_cload_tabix` format: fixed to `juicer_medium`.
- `cooler_balance` cis/trans: recommended `--cis-only` for most mammalian Hi-C (passed via the "Interactions to consider" parameter).
- `cooler_balance` defaults used here: `mad-max=5`, `min-nnz=10`, `min-count=0`, `ignore-diags=2`, `ignore-dist=0`, `tol=1e-05`, `max-iters=200`, weight column `weight`, `convergence-policy=error`.
- Optional `blacklist` BED for `cooler_balance` to exclude problematic regions from weight estimation.

## Test data
The upstream full workflow test supplies a paired-end FASTQ collection (`dataset1.fastq` / `dataset2.fastq` from the HiCUP test suite) with genome `hg19`, restriction enzyme `A^AGCTT,HindIII`, MAPQ≥30, bin size `1000000`, and `--cis-only` balancing. After HiCUP and conversion to Juicer medium tabix, this sub-conversion step is expected to emit a raw `.cool` (`matrix with raw values`, ~42 KB) and an ICE-balanced `.cool` (`matrix with iced values`, ~48 KB) for the `test_dataset` element. For sketch-level smoke testing, any pre-computed Juicer medium tabix of these HiCUP pairs plus `hg19` and `binsize=1000000` reproduces the two cool outputs.

## Reference workflow
IWC `workflows/epigenetics/hic-hicup-cooler/hic-juicermediumtabix-to-cool-cooler.ga`, release 0.3 (2023-09-08), MIT, by Lucille Delisle; subworkflow of the `(Capture) Hi-C Processing: FASTQ to Balanced Cool Files` IWC workflow. Uses `cooler_makebins`, `cooler_cload_tabix`, and `cooler_balance` at tool version `0.9.3+galaxy0/1`.
