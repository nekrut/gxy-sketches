---
name: influenza-a-subtyping-and-consensus-illumina
description: Use when you need to subtype Influenza A isolates (HA/NA typing, e.g.
  H1N1, H5N8) and generate per-segment consensus sequences from batches of Illumina
  paired-end sequencing data, building a best-match hybrid reference per sample from
  a segmented reference collection.
domain: variant-calling
organism_class:
- viral
- segmented-genome
input_data:
- short-reads-paired
- segmented-reference-fasta-collection
source:
  ecosystem: iwc
  workflow: Influenza A isolate subtyping and consensus sequence generation
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/virology/influenza-isolates-consensus-and-subtyping
  version: '0.3'
  license: AGPL-3.0-or-later
  slug: virology--influenza-isolates-consensus-and-subtyping
tools:
- name: vapor
  version: 1.0.3+galaxy0
- name: fastp
  version: 1.1.0+galaxy0
- name: bwa-mem
  version: 0.7.19
- name: samtools
  version: 1.22+galaxy1
- name: ivar
  version: 1.4.4+galaxy0
- name: qualimap
  version: 2.3+galaxy0
- name: mafft
- name: snipit
  version: 1.7+galaxy0
- name: iqtree
  version: 2.4.0+galaxy1
- name: seqtk
  version: 1.5+galaxy0
tags:
- influenza
- flu
- iav
- virology
- subtyping
- consensus
- HA
- NA
- segmented
- hybrid-reference
- phylogenetics
test_data: []
expected_output: []
---

# Influenza A isolate subtyping and consensus sequence generation (Illumina PE)

## When to use this sketch
- You have Illumina paired-end reads from one or more Influenza A isolates and need HA/NA subtype calls (e.g. H1N1, H5N1, H5N8) plus per-segment consensus sequences.
- The reference genome is segmented and highly variable, so a single fixed reference is unsuitable — you want VAPOR to pick the best-matching reference *per segment per sample* and compile a hybrid reference for mapping.
- You are processing a batch of isolates and want batch-level outputs: multiple sequence alignments per segment, Snipit SNP plots, and IQ-Tree ML trees across samples.
- You have (or can download) a well-formatted per-segment FASTA collection with headers following `>[segment]|[type]/[host]/[region]/[id]/[year]|subtype|[accession]` (required for subtyping to work).
- Works for Influenza A (tested) and in principle other Influenza types if a matching per-segment reference collection is supplied.

## Do not use when
- Reads are long (ONT/PacBio) — this pipeline is Illumina-only; use a long-read viral consensus workflow instead.
- You need variant-level VCFs with allele frequencies for intra-host diversity analysis — this workflow emits consensus FASTAs, not VCFs. Use an iVar-variants or lofreq-based viral variant-calling sketch.
- The organism has a non-segmented genome (SARS-CoV-2, Ebola, measles) — use a single-reference viral consensus sketch (e.g. ARTIC / viralrecon).
- You only want taxonomic classification / presence of Influenza without genome reconstruction — use a metagenomic classifier sketch.
- Your reference FASTA headers do not follow the `segment|strain|subtype|accession` scheme — subtyping will fail; fix headers first or use a generic viral consensus sketch.

## Analysis outline
1. **QC and read trimming** with fastp on the paired-end read collection (min length 30).
2. **Reference selection per segment per sample** with VAPOR against the per-segment reference FASTA collection, returning the top 500 matches by k-mer score.
3. **Hybrid reference compilation**: extract each sample's best-scoring segment sequences with seqtk subseq and concatenate into one per-sample FASTA.
4. **Subtyping report generation**: parse VAPOR top hits for HA and NA segments, regex-extract the H?N? subtype from reference headers; unresolved calls become `H?`, `N?`, or `H?N?`.
5. **Read mapping** with BWA-MEM against each sample's hybrid reference, filtered with samtools view (properly paired, MAPQ ≥ 20).
6. **Per-sample BAM QC** with Qualimap BamQC.
7. **Per-segment BAM splitting** with bamtools split, then **consensus calling per segment** with ivar consensus.
8. **Re-organize consensus** into per-segment multi-FASTAs combining all samples.
9. **Multiple sequence alignment** per segment with MAFFT (only for segments with ≥2 samples).
10. **SNP visualization** with Snipit per segment (first sample as reference in plot).
11. **Phylogenetic inference** with IQ-TREE per segment (only for segments with ≥3 samples), yielding ML tree, ML distance matrix, and report.

## Key parameters
- **VAPOR**: `kmer_length=21`, `threshold=0.1`, `min_kmer_cov=5`, `min_kmer_prop=0.1`, `top_seed_frac=1.0`, `return_best_n=500`, `output_type=scores`.
- **fastp**: `length_required=30`, adapter trimming enabled with `detect_adapter_for_pe=true`, quality filtering on, duplicate evaluation disabled.
- **BWA-MEM**: paired-collection mode, `analysis_type=illumina`, coordinate-sorted output, read group auto-set, platform=ILLUMINA.
- **samtools view** post-filter: `quality=20`, inclusive flag filter `1,2` (paired + properly paired), output BAM.
- **ivar consensus**: `min_depth=10`, `min_freq=0.7`, `min_indel_freq=0.8`, `min_qual=20`, uncovered positions emitted as `N` (`-n N`).
- **MAFFT**: FFT-NS flavour, nucleotide mode, Kimura scoring (coefficient 200); run only for segments with ≥2 consensus sequences.
- **IQ-TREE**: DNA seqtype, ModelFinder over nuclear models with AIC, `ninit=100`, `ntop=20`, `nbest=5`, `nstop=100`; run only for segments with ≥3 consensus sequences.
- **Snipit**: nucleotide mode, first sequence as reference, classic palette, sorted by mutation number, SNPs only (no indels).
- **Reference collection constraint**: dataset element identifiers must not contain `:`; sequences containing `N` are ignored by VAPOR.

## Test data
The IWC test profile provides a minimal Influenza A batch: a paired-end FASTQ collection of sequenced isolates and a per-segment FASTA reference collection formatted with the `>[segment]|[type]/[host]/[region]/[id]/[year]|subtype|[accession]` header scheme (well-formatted example collection linked from https://virology.usegalaxy.eu/published/page?id=a04ab8d6ecb698fa, underlying data at Zenodo DOI 10.5281/zenodo.15364147). A successful run produces: a subtyping results table with one row per sample listing the HA and NA subtypes (e.g. `H1N1`, or `H?N?` when unresolved); per-sample hybrid reference FASTAs; per-sample sorted BAMs and Qualimap HTML reports; per-sample × per-segment consensus FASTAs from ivar; per-segment combined consensus multi-FASTAs; per-segment MAFFT alignments, Snipit SNP PNG plots, and IQ-TREE ML trees + distance matrices (for segments meeting the ≥2 / ≥3 sample thresholds).

## Reference workflow
Galaxy IWC — `workflows/virology/influenza-isolates-consensus-and-subtyping/influenza-consensus-and-subtyping.ga`, release **0.3** (AGPL-3.0-or-later). Authors: Wolfgang Maier, Viktoria Isabel Schwarz, Aaron Kolbecher, Saim Momin. Related GTN tutorial: https://gxy.io/GTN:T00308.
