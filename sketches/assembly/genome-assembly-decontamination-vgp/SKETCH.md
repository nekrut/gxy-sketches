---
name: genome-assembly-decontamination-vgp
description: Use when you need to remove foreign contaminants (bacterial, viral, adaptor)
  and mitochondrial scaffolds from a scaffolded eukaryotic genome assembly before
  curation or submission. Targets VGP-style vertebrate assemblies but applies to any
  eukaryotic nuclear assembly post-scaffolding.
domain: assembly
organism_class:
- eukaryote
- vertebrate
input_data:
- assembly-fasta
source:
  ecosystem: iwc
  workflow: 'Assembly decontamination VGP9 '
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/VGP-assembly-v2/Assembly-decontamination-VGP9
  version: '1.3'
  license: BSD-3-Clause
tools:
- ncbi-fcs-adaptor
- ncbi-fcs-gx
- ncbi-blast+
- dustmasker
- parse_mito_blast
- gfastats
tags:
- vgp
- decontamination
- fcs-gx
- mitochondria
- adaptor
- scaffolding
- curation
test_data:
- role: scaffolded_assembly_fasta
  url: https://zenodo.org/records/16999526/files/Genome_assembly.fasta.gz
  sha1: 7ae7b2e76aad9ac560657a87faee53438dcfe708
  filetype: fasta.gz
expected_output:
- role: masking_action_report
  description: Content assertions for `Masking Action Report`.
  assertions:
  - "has_text: seq_00010\t745809\tFIX\t100001..100058"
- role: taxonomy_report
  description: Content assertions for `Taxonomy Report`.
  assertions:
  - "has_text: seq_00017\t85779\t0,13059,0,0,0,0,0\t3864\t|\tBacteroides massiliensis"
- role: contaminants_sequences
  description: Content assertions for `Contaminants sequences`.
  assertions:
  - 'has_text: >seq_00238'
  - 'has_n_lines: {''n'': 14}'
- role: mitochondrial_scaffolds
  description: Content assertions for `Mitochondrial Scaffolds`.
  assertions:
  - 'has_text: seq_00500'
- role: adaptor_report
  description: Content assertions for `Adaptor Report`.
  assertions:
  - "has_text: seq_00010\t745809\tACTION_TRIM\t100001..100058"
- role: final_decontaminated_assembly
  description: Content assertions for `Final Decontaminated Assembly`.
  assertions:
  - 'not_has_text: seq_00500'
  - 'not_has_text: seq_00238'
  - 'has_text: seq_00024'
---

# Genome assembly decontamination (VGP)

## When to use this sketch
- You have a scaffolded eukaryotic (typically vertebrate) nuclear genome assembly FASTA and need to clean it prior to curation, annotation, or INSDC submission.
- You need to screen for both foreign contaminants (bacteria, fungi, viruses, other cross-kingdom contamination) and leftover sequencing adaptors using NCBI FCS (Foreign Contamination Screen).
- You also need to identify and remove mitochondrial scaffolds from the nuclear assembly (typical VGP workflow where mitochondrion is assembled separately).
- You are running VGP workflow 9 (Assembly Decontamination) as the decontamination step of the VGP assembly suite.

## Do not use when
- You need to assemble the genome from raw reads — use an upstream VGP assembly / scaffolding sketch instead.
- You want to assemble the organellar (mitochondrial / chloroplast) genome itself — use a dedicated organelle assembly sketch (e.g. MitoHiFi); this sketch only flags and removes mito scaffolds from the nuclear assembly.
- Your input is a prokaryotic or metagenomic assembly — FCS-GX is tuned to eukaryotic references and the `--euk` adaptor profile is used here.
- You only want adaptor trimming of raw reads — this operates on an assembled FASTA, not FASTQ.

## Analysis outline
1. Run **NCBI FCS Adaptor** (`--euk`) on the scaffolded FASTA to produce an adaptor action report and a cleaned FASTA.
2. **Rewrite the adaptor action report** in a subworkflow: split adaptors into terminal (<=100 bp from end) vs mid-sequence hits, change mid-sequence `ACTION_TRIM` calls to `FIX` (mask rather than trim), and concatenate back into a "Masking Action Report". Gracefully no-ops if no mid-sequence adaptors are present.
3. Run **NCBI FCS GX in `clean` mode** using the modified action report to apply adaptor fixes to the assembly FASTA.
4. Run **NCBI BLAST+ dustmasker** on the adaptor-cleaned FASTA to soft-mask low-complexity regions (FASTA output).
5. Run **NCBI FCS GX in `screen` mode** against the FCS-GX database (with taxid + species name) to produce taxonomy and contaminants action reports.
6. Run **NCBI FCS GX `clean`** again, this time applying the contaminants action report to yield a contaminant-free FASTA plus a "Contaminants sequences" FASTA.
7. In parallel, **filter sequences by max length** (user-controlled cap, 0 = no cap) and **hard-mask** (`atcgn` → `N` via sed) to build a query suitable for BLAST against `refseq_mitochondrion`.
8. Run **blastn** against the `refseq_mitochondrion` database (evalue 0.001, columns including qcovs/qcovhsp/qlen) and pipe the hits into **Parse mitochondrial blast** to emit a BED of mitochondrial scaffold names.
9. Run **gfastats** in manipulation mode on the contaminant-free FASTA with `exclude_bed` set to the mito scaffold list, with `remove_terminal_gaps`, producing the final decontaminated assembly (`fasta.gz`).

## Key parameters
- NCBI FCS Adaptor `tax`: `--euk` (eukaryotic adaptor profile).
- Adaptor terminal-vs-middle cutoff: 100 bp from either end of the sequence (hardcoded in the action-report rewrite filters).
- Mid-sequence adaptor action rewrite: `ACTION_TRIM` → `FIX` (mask instead of trim).
- NCBI FCS GX `clean` mode `min_seq_len`: `200`.
- NCBI FCS GX `screen` mode: `split_fasta: true`, requires `config_tag` (FCS-GX database), NCBI `tax_id`, and species binomial name.
- dustmasker: `level=40`, `window=64`, `linker=1`, output `fasta` (soft-masked).
- Filter sequences by length: `min_length=0`, `max_length` user-supplied (0 = include all, raise only if BLAST chokes on very long contigs).
- Hard-masking sed expression: `/^>/!y/atcgn/NNNNN/` (only lowercased soft-masked bases become N; headers untouched).
- blastn: database `refseq_mitochondrion`, `evalue_cutoff=0.001`, extended columns include `qcovs`, `qcovhsp`, `qlen`.
- gfastats: `mode=manipulation`, `out_format=fasta.gz`, `remove_terminal_gaps=true`, scaffolds in `exclude_bed` are dropped.
- Required user inputs: scaffolded assembly FASTA, FCS-GX database tag, NCBI taxid (e.g. `9606`), species binomial (e.g. `Homo sapiens`), assembly name, haplotype label (`Haplotype 1|Haplotype 2|Paternal|Maternal`), and mito max-length cap.

## Test data
The IWC test profile runs the workflow against a synthetic *Homo sapiens* (taxid 9606, assembly label `Hg19`, Haplotype 1) scaffolded FASTA downloaded from Zenodo (`Genome_assembly.fasta.gz`, SHA-1 `7ae7b2e7…`) with the FCS-GX database set to the `test-only` tag and mito max length `0` (use all scaffolds). A second test case exercises the no-mid-sequence-adaptor code path with `Genome_assembly_2.fasta`. Expected outputs include an Adaptor Report containing `seq_00010\t745809\tACTION_TRIM\t100001..100058`, a Masking Action Report where that mid-sequence hit has been rewritten to `FIX`, a Taxonomy Report flagging `seq_00017` as *Bacteroides massiliensis* contamination, a Contaminants sequences FASTA containing `>seq_00238` across 14 lines, a Mitochondrial Scaffolds BED listing `seq_00500`, and a Final Decontaminated Assembly that retains `seq_00024` but no longer contains `seq_00500` or `seq_00238`.

## Reference workflow
Galaxy IWC `workflows/VGP-assembly-v2/Assembly-decontamination-VGP9` (Assembly decontamination VGP9), release 1.3, BSD-3-Clause, part of the VGP Suite (curated by Nadolina Brajuka and Delphine Lariviere).
