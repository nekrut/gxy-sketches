---
name: eukaryotic-genome-annotation-maker
description: Use when you need to produce a structural genome annotation (GFF3 of
  gene models) for a eukaryotic genome assembly using MAKER with protein homology,
  EST/transcript evidence, and pre-trained SNAP and Augustus ab initio models, followed
  by BUSCO and annotation-statistics QC and JBrowse visualization.
domain: annotation
organism_class:
- eukaryote
input_data:
- genome-fasta
- protein-fasta
- est-fasta
- augustus-hmm
- snap-hmm
source:
  ecosystem: iwc
  workflow: Genome annotation with Maker
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/genome_annotation/annotation-maker
  version: '0.1'
  license: MIT
tools:
- maker
- busco
- gffread
- jcvi-gff-stats
- maker-map-ids
- jbrowse
- fasta-stats
tags:
- genome-annotation
- maker
- busco
- gff3
- eukaryote
- gene-prediction
- jbrowse
test_data: []
expected_output: []
---

# Eukaryotic genome annotation with MAKER

## When to use this sketch
- You have a polished eukaryotic genome assembly (FASTA) and want structural gene models as GFF3.
- You already have, or can obtain, supporting evidence: a protein FASTA (e.g. SwissProt or a related species' proteome) and an EST/transcript FASTA (assembled transcripts, cDNAs, or ESTs).
- You have pre-trained ab initio models for this (or a closely related) species: a SNAP HMM and an Augustus species model.
- You want the annotation QC'd for completeness with BUSCO against a chosen OrthoDB lineage and summarized with gene/exon statistics.
- You want standardized, stable gene IDs and an interactive JBrowse instance for review.

## Do not use when
- You need a prokaryotic / bacterial annotation — use a Prokka/Bakta-style sketch instead.
- You do not yet have trained SNAP or Augustus models for the clade; first run a MAKER bootstrap / self-training sketch or BRAKER-based training workflow before this one.
- You want a transcriptome-only annotation from RNA-seq without a reference assembly — use an RNA-seq assembly/annotation sketch.
- You want functional annotation (GO terms, InterPro, KEGG) — this sketch stops at structural annotation; chain a functional-annotation sketch (e.g. InterProScan/eggNOG) afterwards.
- You want repeat library construction or de novo repeat modelling — this workflow only soft-masks via MAKER's built-in Dfam lookup.

## Analysis outline
1. Baseline genome QC: run Fasta Statistics on the assembly FASTA for contig/length summary.
2. Genome completeness: run BUSCO in `geno` mode with Augustus against a user-chosen OrthoDB lineage (e.g. `eukaryota_odb10`, `fungi_odb10`).
3. Structural annotation with MAKER, providing: genome FASTA, protein evidence, EST evidence, SNAP HMM, Augustus model, and Dfam-based repeat soft-masking.
4. Extract predicted exon/transcript sequences from the MAKER GFF3 with gffread using the genome FASTA as reference.
5. Annotation completeness: re-run BUSCO in `tran` (transcriptome) mode on the gffread-extracted sequences against the same lineage to compare pre- vs post-annotation BUSCO recovery.
6. Annotation statistics: run jcvi Genome Annotation Statistics on the MAKER GFF3 + genome to produce a text summary and PDF graphs (gene counts, exon/intron distributions, etc.).
7. Standardize gene IDs: run `maker_map_ids` on the MAKER GFF3 to assign zero-padded, stable identifiers.
8. Visualization: build a JBrowse instance from the genome FASTA with the renamed annotation GFF3 as a gene-calls track.

## Key parameters
- MAKER `organism_type`: `eukaryotic`.
- MAKER evidence wiring: `protein_evidences.protein` = protein FASTA, `est_evidences.est` = EST/transcript FASTA, `est2genome=false`, `protein2genome=false` (rely on ab initio + evidence reconciliation, not direct evidence-to-gene).
- MAKER ab initio: `abinitio_gene_prediction.snaphmm` = SNAP HMM input, `abinitio_gene_prediction.aug_prediction.augustus_mode=history` with the supplied Augustus model.
- MAKER repeat masking: `repeat_source.source_type=dfam`, `species_list=human` (default proxy Dfam library; change per organism), `softmask=true`.
- MAKER advanced defaults kept: `AED_threshold=1.0`, `max_dna_len=100000`, `min_contig=1`, `pred_flank=200`, `split_hit=10000`, `keep_preds=0.0`, `alt_peptide=C`, `single_exon=0`, `alt_splice=false`, `always_complete=false`.
- BUSCO lineage: selected from the cached OrthoDB v10 list (workflow input parameter); `mode=geno` for the assembly, `mode=tran` for the predicted transcripts; `evalue=0.001`, `limit=3`, `contig_break=10`, Augustus enabled.
- maker_map_ids: `justify=6` (6-digit zero-padded numeric suffix); optional `prefix` for project/species tag.
- JBrowse: `gencode=1`, track category `Maker annotation`, data format `gene_calls`, style labels `product,name,id`.

## Test data
The workflow ships with a small eukaryotic test case comprising a genome FASTA, a protein evidence FASTA, an EST/transcript evidence FASTA, a pre-trained Augustus species model, a pre-trained SNAP HMM, and a BUSCO lineage selection suitable for the test organism. Running the workflow end-to-end is expected to produce a MAKER GFF3 (`maker gff`, plus `maker full` and `maker evidences`), Fasta Statistics and BUSCO reports on the input genome, a gffread exons FASTA, a second BUSCO run on those predicted transcripts, a jcvi annotation statistics text summary and PDF, a renamed GFF3 with an ID map from `maker_map_ids`, and a JBrowse HTML instance containing the renamed annotation track.

## Reference workflow
iwc `workflows/genome_annotation/annotation-maker` — "Genome annotation with Maker" (release 0.1, MIT), using MAKER 2.31.11, BUSCO 5.7.1, gffread 2.2.1.4, jcvi_gff_stats 0.8.4, maker_map_ids 2.31.11, fasta_stats 2.0, and JBrowse 1.16.11.
