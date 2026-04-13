---
name: haploid-wgs-variant-calling-lofreq-pe
description: Use when you need to call SNVs and small indels from paired-end Illumina
  (or Element) whole-genome short-read data against a haploid reference genome (e.g.
  microbial eukaryotes like Plasmodium, bacteria, or other single-copy genomes) and
  annotate the variants against a user-supplied GTF. Uses LoFreq, which is well suited
  to haploid/low-frequency allele detection.
domain: variant-calling
organism_class:
- haploid
- eukaryote
- bacterial
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
tools:
- fastp
- bwa-mem
- samtools
- picard-markduplicates
- lofreq
- snpeff
- snpsift
- multiqc
tags:
- haploid
- wgs
- paired-end
- snv
- indel
- lofreq
- snpeff
- illumina
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

# Haploid WGS paired-end variant calling with LoFreq

## When to use this sketch
- Input is paired-end Illumina (or Element) short reads in fastqsanger format and you want per-sample SNVs plus small indels.
- The organism is effectively haploid: bacteria, archaea, apicomplexan parasites (e.g. *Plasmodium vivax/falciparum*), mitochondria, or other single-copy genomes — including multi-contig/multi-chromosome assemblies.
- You have a reference FASTA and a matching GTF gene annotation, and you want functional effect annotation on the called variants.
- You want a caller tuned for low-frequency / haploid allele calling (LoFreq) rather than a diploid genotyper.
- You need a MultiQC report of read QC, mapping stats, and duplication rates alongside the variant table.

## Do not use when
- Samples are diploid/polyploid germline (use a diploid GATK/DeepVariant-style sketch instead).
- You are calling somatic variants in tumor/normal pairs (use a somatic Mutect2-style sketch).
- You only have long reads (ONT/PacBio) — use a long-read variant-calling sketch (Clair3/medaka).
- You need viral consensus or lineage assignment from amplicon data (use an amplicon/viral consensus sketch).
- You need structural variant discovery (use an SV-calling sketch with Manta/Delly).
- You have single-end reads only (the proper-pair filter here will drop everything).
- You lack a GTF — this workflow's SnpEff-build step requires one; swap in a prebuilt SnpEff database otherwise.

## Analysis outline
1. Adapter and quality trim paired reads with **fastp** (JSON+HTML reports retained).
2. Build a custom **SnpEff** database from the reference FASTA + GTF (`snpEff build`, GTF mode, Standard codon table).
3. Align trimmed pairs to the reference with **BWA-MEM** (coordinate-sorted, read groups auto-assigned, `-Y` soft-clip supplementary, `-T 30`, `-h 5`).
4. Filter alignments with **samtools view** to keep only properly paired mapped reads (require flags 1+2).
5. Collect **samtools stats** for MultiQC input.
6. Remove PCR duplicates with **Picard MarkDuplicates** (`REMOVE_DUPLICATES=true`).
7. Aggregate fastp, samtools stats, and MarkDuplicates metrics into a **MultiQC** HTML report.
8. Realign indels with **LoFreq Viterbi** against the reference.
9. Call variants with **LoFreq call** including indels, with LoFreq standard filters.
10. Keep only biallelic SNV records (awk filter on `REF`/`ALT` in `[ACGT]`) before annotation.
11. Annotate effects with **SnpEff eff** against the custom DB (classic + formatEff output, intergenic/upstream/downstream/intron/UTR filtered out).
12. Flatten with **SnpSift ExtractFields** to a tabular per-effect report, then **Collapse Collection** into a single per-cohort TSV tagged `VariantsAsTSV`.

## Key parameters
- Ploidy assumption: **haploid** (LoFreq is frequency-based; no explicit ploidy flag needed).
- BWA-MEM: `-T 30` (min alignment score), `-h 5`, `-Y` (soft-clip supplementary), `-q` set, read group auto-named, `PL=ILLUMINA`.
- samtools view filter: inclusive flags `1,2` (paired + proper pair), min MAPQ `0`.
- MarkDuplicates: `REMOVE_DUPLICATES=true`, `SUM_OF_BASE_QUALITIES` scoring, optical pixel distance `100`, validation `LENIENT`.
- LoFreq call: `min_cov=10`, `max_depth=1000000`, `min_bq=20`, `min_alt_bq=20`, `min_mq=0`, extended BAQ on, significance `0.01`, dynamic Bonferroni, `--call-indels`.
- LoFreq Viterbi: keep BQ2, `defqual=2`.
- Post-call SNV-only filter: awk regex `($4 ~ /^[ACGT]$/ && $5 ~ /^[ACGT]$/)` — indels from LoFreq are dropped before SnpEff.
- SnpEff build: `input_type=gtf`, `codon_table=Standard`, `genome_version=snpeff_db`.
- SnpEff eff: `annotations=[-formatEff,-classic]`, `filterOut=[-no-downstream,-no-intergenic,-no-intron,-no-upstream,-no-utr]`, `udLength=0`, `generate_stats=true`.
- SnpSift ExtractFields columns: `CHROM POS FILTER REF ALT DP AF DP4 SB EFF[*].IMPACT EFF[*].FUNCLASS EFF[*].EFFECT EFF[*].GENE EFF[*].CODON EFF[*].AA EFF[*].TRID`, one effect per line.

## Test data
The source test profile provides two paired-end Illumina samples — `ERR018930` and `ERR1035492` — as a `list:paired` collection of gzipped fastqsanger files, together with a haploid *Plasmodium vivax*-style reference (`Genome fasta.fasta.gz`, contig `NC_009906.1`) and a matching `Annotation GTF.gtf`, all hosted on Zenodo record 14009320. Running the workflow on these inputs should produce the collapsed `Annotated Variants` TSV (compared to a golden file) and a per-sample annotated VCF collection. Representative expected lines include `NC_009906.1 3204 A>G` (DP=22, AF≈0.73) and `NC_009906.1 3261 C>A` (DP=15, AF≈0.33) for ERR018930, and `NC_009906.1 2975 A>G` (DP=26, AF≈0.69) for ERR1035492 — all PASS, all annotated as `INTRAGENIC` effects on gene `PVX_087665`. A MultiQC HTML report and a SnpEff stats HTML report are also produced as side outputs.

## Reference workflow
Galaxy IWC — `workflows/variant-calling/haploid-variant-calling-wgs-pe` ("Paired end variant calling in haploid system"), release 0.1 (2024-10-29), MIT licensed, authored by Anton Nekrutenko. Source: https://github.com/galaxyproject/iwc/tree/main/workflows/variant-calling/haploid-variant-calling-wgs-pe
