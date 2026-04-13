---
name: lncrna-annotation-feelnc
description: Use when you need to identify and classify long non-coding RNAs (lncRNAs)
  in a eukaryotic genome from RNA-seq BAM alignments plus an existing reference annotation,
  producing a unified mRNA+lncRNA GTF. Uses StringTie for guided transcript assembly
  and FEELnc for coding-potential filtering and classification.
domain: annotation
organism_class:
- eukaryote
input_data:
- rna-seq-bam
- reference-fasta
- reference-gff3
source:
  ecosystem: iwc
  workflow: lncRNAs annotation workflow
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/genome_annotation/lncRNAs-annotation
  version: '0.1'
  license: MIT
tools:
- stringtie
- gffread
- feelnc
- map_param_value
- cat
tags:
- lncrna
- non-coding-rna
- rna-seq
- transcript-assembly
- genome-annotation
- feelnc
- stringtie
- gtf
test_data:
- role: genome_assembly
  url: https://zenodo.org/records/11367439/files/genome_assembly.fasta
  filetype: fasta
- role: genome_annotation
  url: https://zenodo.org/records/11367439/files/genome_annotation.gff3
  filetype: gff3
- role: alignments_from_rna_seq
  url: https://zenodo.org/records/14726111/files/SRR8534859_RNASeq_mapped_small_version.bam
  filetype: bam
expected_output:
- role: annotation
  description: Content assertions for `annotation`.
  assertions:
  - 'has_n_lines: {''n'': 137448}'
  - 'has_text: transcript'
- role: stringtie_gtf
  description: Content assertions for `stringtie gtf`.
  assertions:
  - 'has_n_lines: {''n'': 77365}'
  - 'has_text: transcript'
- role: candidate_lncrna
  description: Content assertions for `candidate lncRNA`.
  assertions:
  - 'has_n_lines: {''n'': 233}'
  - 'has_text: scaffold_21'
- role: classification
  description: Content assertions for `classification`.
  assertions:
  - 'has_n_lines: {''n'': 696}'
  - 'has_text: antisense'
- role: annotation_final
  description: Content assertions for `annotation final`.
  assertions:
  - 'has_n_lines: {''n'': 137681}'
  - 'has_text: StringTie'
---

# lncRNA annotation with StringTie + FEELnc

## When to use this sketch
- You have RNA-seq reads already aligned to a eukaryotic reference genome (BAM) and want to discover and annotate long non-coding RNAs.
- You already have a reference genome FASTA and an existing reference gene annotation (GFF3) containing protein-coding genes that FEELnc can use as a training set for coding potential.
- You want a single merged GTF containing both reference mRNAs and newly identified lncRNAs for downstream expression or regulatory analyses.
- Library strandedness is known (stranded-forward, stranded-reverse, or unstranded) so StringTie can be configured correctly.

## Do not use when
- You are starting from raw FASTQ reads with no alignment — run an RNA-seq alignment workflow (HISAT2/STAR) first, then feed the BAM here.
- You want differential expression of known genes rather than novel lncRNA discovery — use a standard rna-seq quantification sketch instead.
- You have no reference annotation of protein-coding genes — FEELnc's `codpot` step needs a coding training set.
- Your organism is prokaryotic — lncRNA annotation with FEELnc is designed for eukaryotes.
- You need small non-coding RNA (miRNA, snoRNA, piRNA) annotation — FEELnc targets long (>200 nt) transcripts only.
- You want structural / functional protein annotation of a new genome — use a genome annotation sketch (e.g. Funannotate/MAKER) instead.

## Analysis outline
1. Collect inputs: genome FASTA, reference annotation GFF3, RNA-seq BAM, and a strandedness label.
2. Map the strandedness label to a StringTie flag with `map_param_value` (`stranded - forward`→`--fr`, `stranded - reverse`→`--rf`, `unstranded`→empty).
3. Convert the reference GFF3 to GTF with `gffread` — this GTF is reused as the FEELnc reference and as one half of the final merge.
4. Assemble transcripts from the BAM with `StringTie` in guided mode, using the reference GFF3 as `-G` guide and the mapped strandedness flag.
5. Run `FEELnc` (filter → codpot → classifier) with the StringTie GTF as candidates, the reference GTF as the mRNA training set, and the genome FASTA, producing candidate lncRNA GTF, candidate mRNA GTF, and a classification table.
6. Concatenate the reference GTF and the FEELnc candidate lncRNA GTF with `cat` to produce a unified mRNA+lncRNA annotation GTF.

## Key parameters
- StringTie `guide.use_guide: yes` with the reference GFF3 from history — drives guided assembly.
- StringTie `rna_strandness`: derived from user-supplied strandedness (`--fr`, `--rf`, or empty for unstranded).
- StringTie `adv.min_tlen: 200`, `adv.fraction: 0.01`, `adv.min_anchor_len: 10`, `adv.min_bundle_cov: 1`, `adv.bdist: 50` (defaults sufficient for lncRNA discovery).
- gffread `gffs.gff_fmt: gtf` — forces GTF output from the GFF3 input.
- FEELnc requires three connected inputs: `candidate` (StringTie GTF), `reference` (gffread GTF of known mRNAs), `genome` (FASTA). Default FEELnc filter/codpot/classifier settings from the tool wrapper are used.
- Final merge uses plain `cat` of reference GTF + FEELnc candidate lncRNA GTF — no sorting or deduplication.

## Test data
The test profile uses a small eukaryotic dataset: a genome assembly FASTA and a Funannotate-derived GFF3 annotation hosted on Zenodo record 11367439, plus a downsampled RNA-seq BAM (`SRR8534859_RNASeq_mapped_small_version.bam`) from Zenodo record 14726111, run with `strandedness: unstranded`. The workflow is expected to emit: a gffread-converted reference annotation GTF (~137,448 lines, still containing `funannotate` and `transcript` tags); a StringTie assembly GTF (~77,365 lines, tagged with `StringTie version 2.2.3`); a FEELnc candidate lncRNA GTF (~233 lines, referencing `scaffold_21`); a FEELnc classification table (~696 lines, containing entries like `STRG.6410` classified `antisense`); and a final merged mRNA+lncRNA annotation GTF (~137,681 lines) that combines both `funannotate` reference lines and `StringTie` novel lncRNA lines.

## Reference workflow
Galaxy IWC `workflows/genome_annotation/lncRNAs-annotation` — *lncRNAs annotation workflow* v0.1 (MIT), authored by Romane Libouban, based on the Galaxy Training Network tutorial "Long non-coding RNAs (lncRNAs) annotation with FEELnc". Key tool versions: StringTie 2.2.3+galaxy0, gffread 2.2.1.4+galaxy0, FEELnc 0.2.1+galaxy0, map_param_value 0.2.0.
