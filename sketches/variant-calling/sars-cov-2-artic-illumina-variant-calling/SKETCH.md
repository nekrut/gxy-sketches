---
name: sars-cov-2-artic-illumina-variant-calling
description: Use when calling SARS-CoV-2 SNVs and indels from paired-end Illumina
  reads generated with an ARTIC (or similar) tiled-amplicon protocol against the Wuhan-Hu-1
  (NC_045512.2) reference. Handles ARTIC primer trimming, amplicon-bias correction
  for primer-binding-site mutations, low-frequency variant calling with LoFreq, and
  SnpEff annotation.
domain: variant-calling
organism_class:
- viral
- haploid
input_data:
- short-reads-paired
- reference-fasta
- primer-bed
- amplicon-info-tsv
source:
  ecosystem: iwc
  workflow: 'COVID-19: variation analysis on ARTIC PE data'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/sars-cov-2-variant-calling/sars-cov-2-pe-illumina-artic-variant-calling
  version: 0.5.4
  license: MIT
tools:
- fastp
- bwa-mem
- samtools
- lofreq
- ivar
- bcftools
- snpsift
- snpeff
- qualimap
- multiqc
tags:
- sars-cov-2
- covid-19
- artic
- amplicon
- illumina
- low-frequency-variants
- viral
- wastewater
- lofreq
test_data:
- role: nc_045512_2_fasta_sequence_of_sars_cov_2
  url: https://zenodo.org/record/4555735/files/NC_045512.2_reference.fasta?download=1
  filetype: fasta
- role: artic_primer_bed
  url: https://zenodo.org/record/4555735/files/ARTIC_nCoV-2019_v3.bed?download=1
  filetype: bed
- role: artic_primers_to_amplicon_assignments
  url: https://zenodo.org/record/4555735/files/ARTIC_amplicon_info_v3.tsv?download=1
  filetype: tabular
- role: paired_collection__srr11578257__forward
  url: https://zenodo.org/records/10174466/files/SRR11578257_R1.fastq.gz?download=1
- role: paired_collection__srr11578257__reverse
  url: https://zenodo.org/records/10174466/files/SRR11578257_R2.fastq.gz?download=1
expected_output:
- role: annotated_softfiltered_variants
  description: Content assertions for `annotated_softfiltered_variants`.
  assertions:
  - "SRR11578257: has_line: #CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"
  - 'SRR11578257: has_text_matching: {''expression'': ''NC_045512.2\t20209\t.\tAGTAGAAATT\tA\t[0-9]*\tPASS\tDP=[0-9]*;AF=0.9[0-9]*;SB=24;DP4=[0-9]*,[0-9]*,[0-9]*,[0-9]*;INDEL;HRUN=1;EFF=CODON_CHANGE_PLUS_CODON_DELETION\\(MODERATE||agtagaaattta/ata|SRNL6649I|7096|ORF1ab|protein_coding|CODING|GU280_gp01|2|A\\),CODON_CHANGE_PLUS_CODON_DELETION\\(MODERATE||agtagaaattta/ata|SRNL197I|345|ORF1ab|protein_coding|CODING|YP_009725310.1|1|A|WARNING_TRANSCRIPT_NO_START_CODON\\)''}'
---

# SARS-CoV-2 ARTIC paired-end Illumina variant calling

## When to use this sketch
- Input is paired-end Illumina FASTQ from a tiled-amplicon SARS-CoV-2 assay (ARTIC v3/v4/v4.1 or equivalent) with a matching primer BED and primer-to-amplicon assignment TSV.
- You need a LoFreq-based low-frequency variant call set (SNVs + indels) against NC_045512.2, including sub-consensus variants suitable for lineage / intra-host analyses.
- You want amplicon-bias correction: variants at primer-binding sites should trigger removal of reads from affected amplicons before re-calling, with an `AmpliconBias` INFO flag on calls where correction could not be applied.
- You want SnpEff functional annotation using the SARS-CoV-2-specific database plus a strand-bias soft filter on the final VCF.

## Do not use when
- Reads are Oxford Nanopore ARTIC data — use a medaka/longshot-based ONT ARTIC sketch instead.
- Reads are single-end Illumina — use the SE ARTIC sibling workflow.
- Data are SARS-CoV-2 metatranscriptomic / shotgun RNA-seq without amplicon primers — use a plain paired-end viral variant-calling sketch (no ivar trim, no amplicon-bias correction).
- You need consensus FASTA / Pangolin lineage assignment only — use a downstream consensus/reporting workflow; this sketch stops at an annotated VCF.
- Target organism is not SARS-CoV-2 — SnpEff database `NC_045512.2` and the amplicon scheme are SARS-CoV-2-specific.

## Analysis outline
1. Adapter / quality trim paired reads with `fastp` (paired collection in, paired collection out; HTML + JSON reports retained for MultiQC).
2. Map trimmed reads to the NC_045512.2 reference with `bwa-mem` (coordinate-sorted BAM).
3. Filter the BAM with `samtools view`: require proper pair flag (1), drop unmapped (4), mate-unmapped (8), and secondary (256) alignments, MAPQ ≥ 20.
4. Realign reads around indels with `lofreq viterbi`.
5. Add indel base qualities with `lofreq indelqual` using the `dindel` model.
6. Primer-trim with `ivar trim` using the ARTIC primer BED + amplicon-info TSV (realignment is deliberately done before trimming so that near-primer indels are treated as read-internal).
7. First-pass variant calling with `lofreq call` (`--call-indels`, min-cov 5, min-BQ / min-alt-BQ 30, min-MQ 20, extended BAQ, sig 0.0005).
8. QC the primer-trimmed BAM with `qualimap bamqc`; aggregate fastp + samtools stats + qualimap into a `MultiQC` report.
9. Filter first-pass VCF with `SnpSift filter` using a composed expression on `(DP4[2]+DP4[3])/DP` to pick candidate primer-binding-site mutations in the `[min_af, max_af]` window.
10. Remove reads from tainted amplicons with `ivar removereads` using the filtered candidate VCF.
11. Second-pass `lofreq call` on the amplicon-corrected BAM (identical parameters to step 7).
12. `bcftools annotate` carries the second-pass QUAL / INFO onto the first-pass VCF and marks unresolved calls with an `AmpliconBias` INFO flag; a post-correction DP / DP_ALT filter is applied to both rounds and lost-but-originally-passing calls are rescued with the flag set.
13. Fix VCF header descriptions for `AF` and `AmpliconBias` via `Replace Text`.
14. Annotate with `SnpEff eff` using the `NC_045512.2` SARS-CoV-2 database (classic + formatEff output).
15. Apply `lofreq filter` strand-bias soft filter (FDR-corrected, alpha 0.001, compound) to produce the final annotated VCF.

## Key parameters
- Reference: `NC_045512.2` Wuhan-Hu-1 FASTA; SnpEff `genome_version: NC_045512.2`.
- Primer inputs: ARTIC primer BED + tab-separated primer-to-amplicon assignment TSV (one amplicon per line).
- `samtools view` filter: MAPQ ≥ 20, require flag 1, exclude 4+8+256.
- `lofreq call`: `min_cov=5`, `min_bq=30`, `min_alt_bq=30`, `min_mq=20`, `extended_baq=true`, `sig=0.0005`, `--call-indels`.
- Primer-binding-site candidate filter (SnpSift): `((DP4[2]+DP4[3]) >= min_af*DP) & ((DP4[2]+DP4[3]) <= max_af*DP)` with defaults `min_af=0.1`, `max_af=1.0` — AFs are recomputed from DP4/DP to avoid LoFreq's BQ-threshold AF underestimation.
- Post-correction DP filter: `DP > min_dp` and `AF*DP >= min_dp_alt - 0.5`, defaults `min_dp=1`, `min_dp_alt=10`.
- `ivar trim`: `min_len=1`, `min_qual=0`, `primer_pos_wiggle=0`, `inc_primers=true`.
- `lofreq filter`: strand-bias `mtc=fdr`, `sb_alpha=0.001`, compound, `--print-all` (soft filter, no drops).
- SnpEff: `-formatEff -classic`, `filterOut: -no-downstream,-no-intergenic,-no-upstream`, `udLength=0`.

## Test data
The IWC test profile uses a single paired-end Illumina ARTIC sample, `SRR11578257`, with `R1`/`R2` FASTQs hosted on Zenodo (record 10174466). Supporting inputs are the NC_045512.2 Wuhan-Hu-1 reference FASTA, the ARTIC nCoV-2019 v3 primer BED, and the matching amplicon-info TSV (all Zenodo record 4555735). A successful run must produce an `annotated_softfiltered_variants` VCF collection containing one VCF per sample that carries standard VCF 4.0 headers and the canonical `#CHROM POS ID REF ALT QUAL FILTER INFO` column line, plus a PASSing 10-bp deletion at `NC_045512.2:20209 AGTAGAAATT>A` with `AF≈0.9x`, DP4 stats, `INDEL;HRUN=1`, and SnpEff `CODON_CHANGE_PLUS_CODON_DELETION` annotations on ORF1ab (`SRNL6649I` / `SRNL197I`).

## Reference workflow
Galaxy IWC workflow `sars-cov-2-pe-illumina-artic-variant-calling` (`COVID-19: variation analysis on ARTIC PE data`), release `0.5.4`, MIT-licensed, authored by Wolfgang Maier, from `galaxyproject/iwc` under `workflows/sars-cov-2-variant-calling/`.
