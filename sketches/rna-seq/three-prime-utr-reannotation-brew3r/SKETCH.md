---
name: three-prime-utr-reannotation-brew3r
description: Use when you need to extend 3' UTR annotations in an existing reference
  GTF (Ensembl/GENCODE/UCSC) using evidence from full-length bulk RNA-seq BAM files,
  typically to improve quantification accuracy for 3'-biased assays such as 10x scRNA-seq
  or BRB-seq. Produces an extended GTF via de novo StringTie assembly followed by
  BREW3R.r merging.
domain: rna-seq
organism_class:
- eukaryote
- vertebrate
input_data:
- reference-gtf
- aligned-bam-collection
source:
  ecosystem: iwc
  workflow: BREW3R
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/transcriptomics/brew3r
  version: '0.2'
  license: GPL-3.0-or-later
  slug: transcriptomics--brew3r
tools:
- name: stringtie
  version: 2.2.3+galaxy0
- name: stringtie-merge
  version: 2.2.3+galaxy0
- name: brew3r.r
  version: 1.0.2+galaxy1
tags:
- annotation
- 3utr
- gtf
- stringtie
- brew3r
- reannotation
- scrna-seq-support
- brb-seq-support
test_data: []
expected_output:
- role: extended_gtf
  description: Content assertions for `extended_gtf`.
  assertions:
  - "has_line: chr12\tHAVANA\texon\t11206402\t11208972\t.\t-\t.\tgene_id \"ENSMUSG00000047002.2\"\
    ; gene_type \"protein_coding\"; gene_name \"Msgn1\"; level \"2\"; mgi_id \"MGI:1860483\"\
    ; havana_gene \"OTTMUSG00000065713.1\"; transcript_id \"ENSMUST00000049877.2\"\
    ; transcript_type \"protein_coding\"; transcript_name \"Msgn1-201\"; protein_id\
    \ \"ENSMUSP00000055001.1\"; transcript_support_level \"NA\"; tag \"CCDS\"; ccdsid\
    \ \"CCDS25814.1\"; havana_transcript \"OTTMUST00000159929.1\"; exon_number \"\
    1\"; exon_id \"ENSMUSE00000372682.2.ext\""
  - 'has_text: CDS'
---

# 3' UTR reannotation with BREW3R

## When to use this sketch
- You already have a reference GTF (Ensembl, GENCODE, UCSC, etc.) and want to extend 3' ends / UTRs using RNA-seq evidence.
- You have a collection of STAR (or equivalent) aligned BAM files from full-length bulk RNA-seq of the relevant tissue/condition.
- Your downstream goal is improved quantification for 3'-biased protocols (10x scRNA-seq, BRB-seq, Drop-seq, etc.) where reads pile up in 3' UTRs that are poorly annotated.
- Library strandedness is known and consistent across the BAM collection (forward-stranded, reverse-stranded, or unstranded).

## Do not use when
- You need a full de novo transcript assembly or novel isoform discovery — use a dedicated StringTie/Cufflinks assembly sketch instead.
- You want to quantify expression or run differential expression — use an RNA-seq quantification sketch (salmon/STAR+featureCounts) instead.
- Your input is 3'-tagged data itself (10x, BRB-seq); those reads should not be used to extend annotations here because they lack full-length coverage. Use full-length bulk RNA-seq BAMs as the evidence.
- You want to build a new reference from scratch with no prior GTF — BREW3R only extends an existing annotation.

## Analysis outline
1. Map the `strandedness` string to StringTie's `--fr`/`--rf`/empty flag and to a boolean used by BREW3R.r (`filter_unstranded=true` only when unstranded).
2. Run **StringTie** once per input BAM to produce a per-sample de novo assembly GTF, using the chosen strandedness and the minimum coverage threshold.
3. Run **StringTie merge** across all per-sample GTFs to produce a single merged de novo assembly GTF, filtered by the minimum FPKM threshold.
4. Run **BREW3R.r** with the original reference GTF as `gtf_to_extend` and the merged StringTie GTF as `gtf_to_overlap`; when unstranded, drop merged transcripts without orientation that overlap exons of both strands.
5. Emit the extended GTF as `extended_gtf` (renamed `<input> BREW3R extended`). Extended exons carry an `.ext` suffix on their `exon_id`.

## Key parameters
- `strandedness`: one of `stranded - forward` (→ StringTie `--fr`), `stranded - reverse` (→ `--rf`), or `unstranded` (→ no flag, and `filter_unstranded=true` in BREW3R.r).
- `minimum coverage` (StringTie `-c` / `-j`, min_bundle_cov / min_anchor_cov): default `10` reads/bp; raise for noisy libraries.
- `minimum FPKM for merge` (StringTie merge `-F`): default `1.0`; transcripts below this FPKM are excluded from the merged assembly.
- BREW3R.r is run with defaults: `no_add=false`, `sup_output=false`, empty `exclude_pattern`. The only toggled flag is `filter_unstranded`, driven by strandedness.
- StringTie is run without a guide GTF (`use_guide=no`) so the assembly is purely de novo evidence for extension.

## Test data
The source workflow ships with three subset BAM files (`GSM4196550`, `GSM4196551`, `GSM4196552`) from public mouse bulk RNA-seq, supplied as a Galaxy list collection, together with a small mouse reference GTF (`input.gtf`). The job runs with `strandedness = stranded - reverse`, `minimum coverage = 10`, and `minimum FPKM for merge = 1.0`. The expected `extended_gtf` is asserted to contain a CDS feature and a specific extended `Msgn1` exon line on `chr12:11206402-11208972` whose `exon_id` ends with the `.ext` suffix that BREW3R.r attaches to lengthened exons.

## Reference workflow
Galaxy IWC `workflows/transcriptomics/brew3r` (BREW3R, release 0.2, GPL-3.0-or-later). Key tools: `stringtie 2.2.3+galaxy0`, `stringtie_merge 2.2.3+galaxy0`, `brew3r_r 1.0.2+galaxy1`. Upstream R package: BREW3R.r on Bioconductor.
