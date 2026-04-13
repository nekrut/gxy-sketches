---
name: pox-virus-amplicon-consensus-itr
description: Use when you need to assemble consensus genomes from Illumina paired-end
  tiled-amplicon data of pox viruses (e.g. MPXV, LSDV, VACV) where each sample was
  sequenced as two half-genomes across separate pool runs in order to resolve Inverted
  Terminal Repeat (ITR) sequences. Requires a two-pool ARTIC-style primer scheme with
  pool IDs encoded in the BED score column.
domain: amplicon
organism_class:
- viral
input_data:
- short-reads-paired
- reference-fasta
- primer-scheme-bed
source:
  ecosystem: iwc
  workflow: Pox Virus Illumina Amplicon Workflow from half-genomes
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/virology/pox-virus-amplicon
  version: '0.4'
  license: MIT
tools:
- fastp
- bwa-mem
- samtools
- ivar
- qualimap
- multiqc
- emboss-maskseq
- datamash
tags:
- pox
- mpox
- monkeypox
- lsdv
- vaccinia
- artic
- amplicon
- itr
- half-genome
- consensus
- virology
- illumina
- ivar
test_data:
- role: reference_fasta
  url: https://www.ebi.ac.uk/ena/browser/api/fasta/AF325528.1?download=true
  sha1: 927d0d00b7db6ad60524bb9e50d3ab41c4ac5ecf
  filetype: fasta
- role: pe_reads_pool1__20l70__forward
  url: ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR151/076/SRR15145276/SRR15145276_1.fastq.gz
  sha1: 7a6bc145be5cacabb9d9b3f595e9d82bd065798f
  filetype: fastqsanger.gz
- role: pe_reads_pool1__20l70__reverse
  url: ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR151/076/SRR15145276/SRR15145276_2.fastq.gz
  sha1: f035049cb7a8adc3304eaa8a8d1f9d0a56253c07
  filetype: fastqsanger.gz
- role: pe_reads_pool2__20l70__forward
  url: ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR151/075/SRR15145275/SRR15145275_1.fastq.gz
  sha1: c11cf67a30caa9a713dd8cdae91f6ba08a17da06
  filetype: fastqsanger.gz
- role: pe_reads_pool2__20l70__reverse
  url: ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR151/075/SRR15145275/SRR15145275_2.fastq.gz
  sha1: 825cfcacf1029066cd2ceb3989e31736fd5b7c8a
  filetype: fastqsanger.gz
expected_output: []
---

# Pox Virus Illumina Amplicon Consensus from Half-Genome Sequencing

## When to use this sketch
- Samples are pox virus (e.g. Monkeypox/MPXV, Lumpy Skin Disease Virus, Vaccinia) sequenced with a tiled-amplicon ARTIC-style protocol.
- Each sample was split across **two sequencing runs**: pool1 covering the first half of the genome and pool2 covering the second half — specifically to allow resolution of Inverted Terminal Repeat (ITR) sequences.
- Reads are Illumina paired-end (short reads).
- A primer scheme BED file is available with pool identities (`pool1`/`pool2`, optionally `pool1a`/`pool1b` etc.) encoded in the score column.
- Goal is per-sample consensus FASTA genome sequences.

## Do not use when
- Samples were sequenced in a single pool (not split by half-genome): use a standard SARS-CoV-2-style iVar amplicon consensus sketch instead.
- Long-read (ONT/PacBio) amplicon data: use an ONT pox amplicon sketch.
- Whole-genome shotgun (not amplicon-tiled) data: use a viral WGS reference-mapping consensus sketch.
- Non-pox viruses with standard single-pool amplicon schemes (e.g. SARS-CoV-2 ARTIC): the half-genome masking logic is unnecessary overhead.

## Analysis outline
1. **Split primer scheme** (Select/Grep): separate pool1 and pool2 primer entries from the BED file.
2. **Compute reference masking coordinates** (Datamash + fasta_compute_length): derive the genomic coordinate ranges to mask for each pool using primer end positions and reference length.
3. **Mask reference** (EMBOSS maskseq): create two pool-specific masked reference FASTAs — pool1 reference has the second-half region hard-masked to N, and pool2 reference has the first-half region masked.
4. **Trim & QC reads** (fastp): adapter trimming and quality filtering independently for pool1 and pool2 read collections.
5. **Map reads to masked references** (BWA-MEM): map pool1 reads to the pool1-masked reference; map pool2 reads to the pool2-masked reference; coordinate-sorted BAM output with read group tags.
6. **Filter mappings** (samtools view): retain only properly paired, primary alignments with MAPQ ≥ 20.
7. **Mapping QC** (samtools stats + MultiQC): per-pool mapping statistics reports.
8. **Merge pool BAMs** (samtools merge): combine the filtered pool1 and pool2 BAMs into a single per-sample BAM.
9. **Coverage QC** (QualiMap BamQC + MultiQC): assess coverage depth and uniformity across the merged BAM.
10. **Trim primers** (ivar trim): remove primer sequences from the merged BAM using the full primer scheme BED.
11. **Call consensus** (ivar consensus): generate per-sample consensus FASTA with configurable base-quality, allele-frequency, and minimum-depth thresholds.
12. **Rename and combine** (sed + concatenate): clean up iVar FASTA headers and concatenate all per-sample consensus sequences into a single multi-FASTA.

## Key parameters
- `Minimum quality score to call base` (ivar consensus `min_qual`): default **20**; bases below this Phred score are ignored during consensus pileup.
- `Allele frequency to call SNV` (ivar consensus `min_freq`): default **0.7**; at least 70% of reads must support the alt allele for an SNV to be called.
- `Allele frequency to call indel` (ivar consensus `min_indel_freq`): default **0.8**; at least 80% support required for an indel call.
- `ivar consensus min_depth`: hard-coded **50**; positions with fewer than 50 reads are masked to `N` in the consensus.
- `samtools view MAPQ filter`: hard-coded **20**; low-quality or multi-mapping reads are excluded.
- `ivar trim min_qual / min_len`: **20 / 30**; bases below Q20 and reads shorter than 30 bp post-trimming are removed.
- Primer BED score column: must contain `pool1` or `pool2` (case-insensitive); subpools like `pool1a`/`pool1b` are accepted.

## Test data
The test uses a single sample (identifier `20L70`) of **Lumpy Skin Disease Virus (Capripoxvirus)** sequenced as two half-genomes. The reference is NCBI accession AF325528.1 (LSDV Neethling strain, ~151 kb). Pool1 paired-end reads come from SRR15145276 and pool2 from SRR15145275, both retrieved from the ENA. The primer scheme is a CaPV-V1 BED6 file with pool1/pool2 annotations. The expected final output is `combined_consensus_multifasta.fasta` containing the reconstructed full-length consensus genome for sample 20L70, with ITR regions resolved through the half-genome masking strategy.

## Reference workflow
Galaxy IWC workflow **Pox Virus Illumina Amplicon Workflow from half-genomes**, version 0.4 (released 2025-10-08).  
Source: https://github.com/galaxyproject/iwc/tree/main/workflows/virology/pox-virus-amplicon  
License: MIT  
Authors: Viktoria Isabel Schwarz (ORCID 0000-0001-6897-1215), Wolfgang Maier (ORCID 0000-0002-9464-6640).  
Conceptually extends the IWC SARS-CoV-2 PE Illumina ARTIC iVar workflow with split-genome masking for poxvirus ITR resolution.
