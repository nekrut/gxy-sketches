---
name: eukaryote-genome-annotation-metazoan
description: "Use when you need to produce a draft structural annotation (gene models,\
  \ ncRNAs) for a eukaryotic genome assembly\u2014especially a metazoan\u2014by integrating\
  \ protein, transcript, and RNA-seq evidence into ab-initio and consensus gene builds.\
  \ Assumes a reasonably contiguous assembly (BUSCO > 80%)."
domain: annotation
organism_class:
- eukaryote
- metazoan
input_data:
- genome-fasta
- protein-fasta
- transcript-fasta
- short-reads-paired
- reference-gtf
source:
  ecosystem: nf-core
  workflow: nf-core/genomeannotator
  url: https://github.com/nf-core/genomeannotator
  version: dev
  license: MIT
tools:
- augustus
- pasa
- evidencemodeler
- spaln
- minimap2
- star
- trinity
- repeatmasker
- infernal
- satsuma2
- kraken
- busco
tags:
- annotation
- gene-prediction
- eukaryote
- metazoan
- augustus
- evm
- pasa
- ncrna
- repeat-masking
test_data: []
expected_output: []
---

# Eukaryote (metazoan) genome structural annotation

## When to use this sketch
- You have a eukaryotic (typically metazoan) genome assembly in FASTA format and need draft gene models.
- You can supply at least one evidence source: related-organism proteins, species-specific proteins, ESTs/transcripts, Illumina RNA-seq reads, or related reference genomes with GTF annotations.
- Assembly is of reasonable quality (BUSCO completeness above ~80%, at most a few thousand contigs, up to ~human-sized).
- You want a consensus gene build combining ab-initio prediction, evidence alignments, and optionally transcript-based assembly into a single GFF3 annotation.
- You also want optional ncRNA predictions (Rfam/Infernal) and BUSCO-based completeness evaluation of the resulting gene set.

## Do not use when
- The target is a prokaryote/bacterial or archaeal genome — use a prokaryotic annotation workflow (e.g. Prokka/Bakta-based sketches) instead.
- You only want variant calling or assembly QC rather than gene model construction — see the relevant variant-calling or assembly-QC sketches.
- The assembly is highly fragmented (tens of thousands of contigs) or BUSCO completeness is very low — alignment heuristics will perform poorly.
- You need functional annotation only (InterProScan, KEGG, GO terms) on an existing gene set — this pipeline produces structural annotation, not functional labels.
- You are annotating a transcriptome without a genome — use a Trinity/Trinotate-style transcriptome annotation sketch instead.

## Analysis outline
1. Preprocess the assembly: drop contigs below `min_contig_size`, sanitize FASTA headers, split into chunks of `npart_size`.
2. Repeat-mask the assembly with RepeatMasker, either from a user-supplied repeat library (`rm_lib`), a DFam taxonomic group (`rm_species`), or de-novo modeling via RepeatModeler.
3. Align protein evidence to the masked assembly with SPALN (general proteins and, if given, targeted/species-specific proteins).
4. Align transcripts/ESTs with Minimap2 and, if RNA-seq reads are provided, align them with STAR; optionally assemble genome-guided transcripts with Trinity.
5. Optionally lift annotations from related reference genomes by whole-genome synteny alignment with Satsuma2 and projection with Kraken.
6. Run ab-initio gene prediction with AUGUSTUS, using the alignments above as extrinsic hints (protein, EST, RNA-seq splice, wiggle coverage, and trans-mapped hints) weighted via the AUGUSTUS extrinsic config.
7. Optionally build transcript-based gene models with PASA from the aligned transcripts and/or Trinity assemblies; optionally retrain AUGUSTUS from the best PASA models when `aug_training` is enabled.
8. Compute a consensus gene build with EvidenceModeler, combining AUGUSTUS, PASA, and evidence tracks using `evm_weights`.
9. Predict non-coding RNAs with Infernal against Rfam 14 when `--ncrna` is set.
10. Evaluate the resulting gene set with BUSCO against `busco_lineage` and aggregate reports via MultiQC.

## Key parameters
- `--assembly`: genome FASTA to annotate (required).
- Evidence inputs (at least one recommended): `--proteins`, `--proteins_targeted`, `--transcripts`, `--rnaseq_samples` (4-column CSV: sample,fastq_1,fastq_2,strandedness), `--references` (3-column CSV: species,fasta,gtf).
- Repeat masking: `--rm_lib` (preferred, FASTA of known repeats) or `--rm_species` (DFam taxon) or neither (de-novo, slow). `--rm_db` points to the DFam h5 archive.
- Assembly handling: `--min_contig_size` (default 5000), `--npart_size` (default 2×10^8), `--max_intron_size` (critical — set to reflect organism biology).
- AUGUSTUS: `--aug_species` (prediction profile, e.g. `caenorhabditis`, `human`); `--aug_options` (default enables alternative transcripts); `--aug_chunk_length` (default 3,000,000); `--aug_training` to retrain from PASA; `--aug_extrinsic_cfg` for custom hint weights; evidence priorities `pri_prot`, `pri_prot_target`, `pri_est`, `pri_rnaseq`, `pri_wiggle`, `pri_trans` (1–5, defaults 3/5/4/4/2/4).
- SPALN: `--spaln_taxon` (e.g. `NematodC`, `Mammals`) — must be chosen per target clade; `--spaln_protein_id` (60) and `--spaln_protein_id_targeted` (90); `--min_prot_length` (35).
- Sub-pipeline toggles: `--trinity`, `--pasa`, `--evm`, `--ncrna` (all boolean, off by default).
- PASA/EVM: `--pasa_nmodels` (1000), `--evm_weights` (evidence-weight file), `--nevm` (jobs per chunk).
- Evaluation: `--busco_lineage` in `<clade>_odb10` form, optionally `--busco_db_path` for a local BUSCO download.

## Test data
The bundled `test` profile annotates a small *C. elegans*-like test contig (`contig.fa`) from the nf-core `test-datasets/esga` branch, together with targeted proteins (`proteins.fa`), transcripts (`transcripts.fa`), a C. elegans repeat library (`repeats.celegans.fa`), and a minimal RNA-seq samplesheet (`samples.csv`). It runs AUGUSTUS with the `caenorhabditis` species model and SPALN with the `NematodC` taxon. The full-size test additionally enables `--evm`, `--trinity`, and BUSCO evaluation against `nematoda_odb10`. Expected outputs are structural annotations published under `annotations/augustus/` (and `annotations/evm/`, `annotations/pasa/`, `annotations/ncrna/` when the respective sub-pipelines are enabled) containing `*.augustus.gff`/`*.evm.gff`/`*.pasa.gff`/`*.rfam.gff` plus matching `*.proteins.fa`, `*.cdna.fa`, and `*.cds.fa`, together with a MultiQC report under `multiqc/` and pipeline run metadata under `pipeline_info/`.

## Reference workflow
nf-core/genomeannotator (DSL2, dev branch) — https://github.com/nf-core/genomeannotator. Core tools: AUGUSTUS, PASA, EvidenceModeler, SPALN, Minimap2, STAR, Trinity, RepeatMasker/RepeatModeler, Infernal/Rfam 14, Satsuma2, Kraken, BUSCO, MultiQC.
