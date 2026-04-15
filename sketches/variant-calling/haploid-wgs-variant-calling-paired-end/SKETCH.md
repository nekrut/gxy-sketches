---
name: haploid-wgs-variant-calling-paired-end
description: Use when you need to call SNVs and short indels from paired-end Illumina
  (or Element) short-read WGS data against a haploid reference genome (e.g. protozoan
  parasites like Plasmodium, fungi, or other haploid eukaryotes) and annotate the
  variants with gene-level consequences from a GTF. Assumes ploidy=1 and uses LoFreq
  for low-frequency-aware calling.
domain: variant-calling
organism_class:
- haploid
- eukaryote
input_data:
- short-reads-paired
- reference-fasta
- annotation-gtf
source:
  ecosystem: iwc
  workflow: Paired end variant calling in haploid system
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/variant-calling/haploid-variant-calling-wgs-pe
  version: '0.1'
  license: MIT
  slug: variant-calling--haploid-variant-calling-wgs-pe
tools:
- name: fastp
  version: 0.23.2+galaxy0
- name: bwa-mem
  version: 0.7.17.2
- name: samtools
  version: 1.13+galaxy1
- name: picard-markduplicates
  version: 2.18.2.2
- name: lofreq
  version: 2.1.5+galaxy0
- name: snpeff
  version: 4.3+T.galaxy2
- name: snpsift
  version: 4.3+t.galaxy0
- name: multiqc
  version: 1.11+galaxy0
tags:
- haploid
- wgs
- paired-end
- snv
- indel
- lofreq
- snpeff
- plasmodium
- veupath
test_data:
- role: annotation_gtf
  url: https://zenodo.org/records/14009320/files/Annotation%20GTF.gtf?download=1
  sha1: 7332cabb96a767d5cf6efbb5f3eb2dc8a40fb3d0
  filetype: gtf
- role: genome_fasta
  url: https://zenodo.org/records/14009320/files/Genome%20fasta.fasta.gz?download=1
  sha1: 912f1de146158d59bbd93b8fe3b2f63eb9a49162
  filetype: fasta.gz
- role: paired_collection__err018930__forward
  url: https://zenodo.org/records/14009320/files/ERR018930_forward.fastqsanger.gz?download=1
  sha1: 043b41d132449b815266061832f0d25d8f50bda6
- role: paired_collection__err018930__reverse
  url: https://zenodo.org/records/14009320/files/ERR018930_reverse.fastqsanger.gz?download=1
  sha1: 693dfe7dad64030b72b59ffe07e7e711ae11606d
- role: paired_collection__err1035492__forward
  url: https://zenodo.org/records/14009320/files/ERR1035492_forward.fastqsanger.gz?download=1
  sha1: b27dac7ed0a11942f8288b1c49868c81d6a8bff1
- role: paired_collection__err1035492__reverse
  url: https://zenodo.org/records/14009320/files/ERR1035492_reverse.fastqsanger.gz?download=1
  sha1: 1bad1ab8552365da08b86c0a8210ccba083b4550
expected_output:
- role: annotated_variants
  path: expected_output/Annotated Variants.tabular
  description: Expected output `Annotated Variants` from the source workflow test.
  assertions: []
- role: snpeff_variants
  description: Content assertions for `SnpEff variants`.
  assertions:
  - "ERR018930: has_line: NC_009906.1\t3204\t.\tA\tG\t120.0\tPASS\tDP=22;AF=0.727273;SB=2;DP4=2,3,3,14;EFF=INTRAGENIC(MODIFIER|||||PVX_087665||NON_CODING|||G)"
  - "ERR018930: has_line: NC_009906.1\t3261\t.\tC\tA\t52.0\tPASS\tDP=15;AF=0.333333;SB=0;DP4=3,7,2,3;EFF=INTRAGENIC(MODIFIER|||||PVX_087665||NON_CODING|||A)"
  - "ERR1035492: has_line: NC_009906.1\t2975\t.\tA\tG\t75.0\tPASS\tDP=26;AF=0.692308;SB=0;DP4=5,3,12,6;EFF=INTRAGENIC(MODIFIER|||||PVX_087665||NON_CODING|||G)"
---

# Haploid WGS paired-end variant calling

## When to use this sketch
- You have paired-end Illumina (or Element) short reads from a haploid organism with a multi-contig reference (e.g. *Plasmodium vivax*, *Plasmodium falciparum*, other protozoan parasites, haploid fungi).
- You want SNPs and small indels called against a reference FASTA, with gene-level functional annotation driven by a user-supplied GTF.
- You need low-frequency-aware variant calling (LoFreq) because allele frequencies may not be cleanly 0/1 (mixed infections, subclones) but the underlying genome is still haploid.
- You want a single tab-delimited summary of annotated variants plus a MultiQC report covering read QC and mapping.

## Do not use when
- Your organism is diploid or polyploid (vertebrate, human, plant) — use a diploid GATK/DeepVariant-style sketch instead.
- Your reads are long reads (ONT, PacBio) — use a long-read haploid variant-calling sketch.
- You only have single-end reads — use the single-end haploid variant-calling sibling sketch.
- You are doing bacterial outbreak / reference-based prokaryote calling where a snpEff prebuilt database already exists and no custom GTF build is needed — a dedicated bacterial-haploid sketch is more direct.
- You need structural variants, CNVs, or phylogenomic/consensus building — those are separate sketches.
- You are doing viral intra-host variant calling with primer trimming (e.g. SARS-CoV-2 ARTIC) — use a viral amplicon sketch.

## Analysis outline
1. Adapter and quality trimming of paired reads with **fastp** (JSON + HTML reports retained for MultiQC).
2. Build a custom **SnpEff** database from the user-provided reference FASTA + GTF (`snpEff build` in GTF mode, Standard codon table).
3. Map trimmed pairs to the reference FASTA with **BWA-MEM** (coordinate-sorted BAM, read groups auto-set, `-Y` soft-clipping, `-T 30`, Illumina PL).
4. Filter alignments with **samtools view** to retain only properly paired, mapped reads (`-f 1 -f 2`).
5. Collect **samtools stats** on the filtered BAM for QC.
6. Remove PCR duplicates with **Picard MarkDuplicates** (`REMOVE_DUPLICATES=true`).
7. Aggregate fastp, samtools stats, and MarkDuplicates metrics into a **MultiQC** HTML report.
8. Indel-aware realignment of the dedup BAM with **LoFreq viterbi**.
9. Call SNVs and indels with **LoFreq call** (haploid, `--call-indels`, standard LoFreq filters).
10. Keep only bi-allelic SNV records (awk filter on single-base REF/ALT) to feed SnpEff cleanly.
11. Annotate variants with **SnpEff eff** against the custom database (classic + formatEff output, filtering out intergenic/intron/UTR/up/downstream noise).
12. Extract a flat per-variant table with **SnpSift extractFields** (CHROM, POS, FILTER, REF, ALT, DP, AF, DP4, SB, EFF impact/funclass/effect/gene/codon/AA/transcript), one effect per line.
13. Collapse per-sample TSVs into a single `Annotated Variants` table with **Collapse Collection** (tagged `VariantsAsTSV`).

## Key parameters
- Ploidy: **haploid** (LoFreq is inherently ploidy-agnostic; the downstream annotation assumes one allele per site).
- BWA-MEM: `-T 30` (min alignment score), `-Y` (soft-clipping supplementary), read group PL=ILLUMINA, auto SM/ID/LB from sample name.
- samtools view filter: include flags `1,2` (paired + properly paired); output BAM.
- Picard MarkDuplicates: `REMOVE_DUPLICATES=true`, `ASSUME_SORTED=true`, `VALIDATION_STRINGENCY=LENIENT`, optical duplicate pixel distance 100.
- LoFreq viterbi: default BQ2 handling (`replace_bq2=keep`, defqual 2).
- LoFreq call: `min_cov=10`, `max_depth=1000000`, `min_bq=20`, `min_alt_bq=20`, extended BAQ enabled, `min_mq=0`, LoFreq standard filter with significance `0.01` and dynamic Bonferroni, `--call-indels`.
- Post-call filter (awk): `/^#/ { print; next } ($4 ~ /^[ACGT]$/ && $5 ~ /^[ACGT]$/) { print }` — retains headers and single-base SNVs only before SnpEff.
- SnpEff build: `input_type=gtf`, `codon_table=Standard`, reference from history FASTA.
- SnpEff eff: `-formatEff -classic`, filter out `-no-downstream -no-intergenic -no-intron -no-upstream -no-utr`, `udLength=0`, custom DB source.
- SnpSift extractFields: `CHROM POS FILTER REF ALT DP AF DP4 SB EFF[*].IMPACT EFF[*].FUNCLASS EFF[*].EFFECT EFF[*].GENE EFF[*].CODON EFF[*].AA EFF[*].TRID`, one effect per line.

## Test data
The source workflow ships a test profile with a *Plasmodium vivax* reference FASTA (gzipped) and matching GTF hosted on Zenodo (record 14009320), plus a `list:paired` collection of two public Illumina paired-end runs, `ERR018930` and `ERR1035492`, each with forward and reverse `fastqsanger.gz` files. Running the workflow against these inputs is expected to produce a single collapsed `Annotated Variants` tabular file (golden file in `test-data/`) and a per-sample `SnpEff variants` VCF collection whose contents must include specific PASS records on contig `NC_009906.1`: for `ERR018930`, positions `3204 A>G` (DP=22, AF≈0.727) and `3261 C>A` (DP=15, AF≈0.333), both annotated as `INTRAGENIC` in gene `PVX_087665`; and for `ERR1035492`, position `2975 A>G` (DP=26, AF≈0.692) in the same gene. MultiQC and fastp HTML reports are also emitted but not asserted.

## Reference workflow
Galaxy IWC — `workflows/variant-calling/haploid-variant-calling-wgs-pe` — *Paired end variant calling in haploid system*, release 0.1 (2024-10-29), MIT license, by Anton Nekrutenko. Tagged `generic`, `VeuPath`, `Haploid`.
