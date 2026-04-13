---
name: functional-gene-screening-prokaryotic-contigs
description: "Use when you need to screen assembled prokaryotic (bacterial/archaeal)\
  \ contigs or MAGs for functional genes of interest \u2014 antimicrobial resistance\
  \ genes (ARGs), antimicrobial peptides (AMPs), and/or biosynthetic gene clusters\
  \ (BGCs) \u2014 and get consolidated, standardised reports across multiple specialist\
  \ tools. Input is assembled FASTA (not raw reads)."
domain: annotation
organism_class:
- bacterial
- archaeal
- prokaryote
input_data:
- assembled-contigs-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/funcscan
  url: https://github.com/nf-core/funcscan
  version: 3.0.0
  license: MIT
tools:
- seqkit
- pyrodigal
- prodigal
- prokka
- bakta
- interproscan
- mmseqs2
- abricate
- amrfinderplus
- deeparg
- fargene
- rgi
- hamronization
- argnorm
- ampir
- amplify
- macrel
- hmmer
- ampcombi
- antismash
- deepbgc
- gecco
- combgc
tags:
- amr
- arg
- amp
- bgc
- secondary-metabolites
- natural-products
- metagenomics
- isolate-genome
- functional-annotation
- nf-core
test_data: []
expected_output: []
---

# Functional gene screening on prokaryotic contigs (ARG / AMP / BGC)

nf-core/funcscan is a one-stop functional-mining pipeline: it takes assembled prokaryotic nucleotide sequences (isolate genomes, MAGs or whole metagenome assemblies) and runs parallel ensembles of specialist screeners for antimicrobial resistance genes, antimicrobial peptides, and biosynthetic gene clusters, then harmonises each ensemble into a single summary table.

## When to use this sketch
- Input is **assembled contigs** (isolate genome, MAG, or whole-metagenome assembly) from bacteria/archaea, supplied as FASTA.
- The user wants to screen for one or more of: **antibiotic resistance genes (ARGs)**, **antimicrobial peptides (AMPs)**, or **biosynthetic gene clusters (BGCs)** encoding secondary metabolites / natural products.
- The user wants the **consensus / union across several tools** (e.g. ABRicate + AMRFinderPlus + DeepARG + fARGene + RGI for ARGs) rather than a single-tool answer, and wants the hits harmonised (hAMRonization, AMPcombi, comBGC).
- The user optionally wants each contig's taxonomic origin attached to every hit (MMseqs2 against GTDB/Kalamari/SILVA) or additional protein-family/domain annotation (InterProScan).
- The user is comfortable with one row per sample in a CSV samplesheet (`sample,fasta[,protein,gbk]`).

## Do not use when
- Input is **raw reads** — assemble first (e.g. with nf-core/mag or SPAdes) and then feed contigs here.
- Target is a **eukaryote / vertebrate / plant / fungal primary metabolism**; funcscan's annotators (Prodigal/Pyrodigal/Prokka/Bakta) are prokaryote-only. antiSMASH does support `--taxon fungi` for BGCs in fungal genomes, but the rest of the pipeline is bacterially-biased.
- You only need **variant calling** or **strain typing** — use a variant-calling sketch instead.
- You need **taxonomic profiling of a metagenome** (who is there?) rather than functional mining — use a metagenomic profiling sketch.
- You need **de novo assembly** from reads — funcscan does not assemble.
- You want **viral AMR / virulence on phage contigs** specifically — funcscan will tolerate it but is not tuned for it.

## Analysis outline
1. **Input QC & length filtering** — SeqKit splits contigs; BGC subworkflow keeps only contigs ≥ `bgc_mincontiglength` (default 3000 bp).
2. **Optional contig taxonomy** — MMseqs2 `taxonomy` against a chosen DB (default Kalamari; GTDB/SILVA supported) when `--run_taxa_classification` is set; lineage is later joined onto every hit.
3. **Gene prediction / annotation** — one of Pyrodigal (default, meta mode), Prodigal, Prokka, or Bakta produces CDS FASTA (`.faa`), nucleotide FASTA (`.ffn`/`.fna`) and GenBank (`.gbk`). Pre-annotated inputs can be supplied directly in the samplesheet (`protein`, `gbk` columns) to skip this step.
4. **Optional protein-family annotation** — InterProScan (PANTHER, Pfam, ProSiteProfiles, ProSitePatterns by default) on predicted CDS when `--run_protein_annotation` is set.
5. **ARG screening** (`--run_arg_screening`) — ABRicate, AMRFinderPlus, DeepARG (LS model), fARGene (HMM classes: class_a, class_b_1_2/3, class_c, class_d_1/2, qnr, tet_*), RGI against CARD. Results harmonised by hAMRonization and normalised to the Antibiotic Resistance Ontology by argNorm.
6. **AMP screening** (`--run_amp_screening`) — ampir, AMPlify, Macrel, and optional HMMER `hmmsearch` against user-supplied `.hmm` models. Results merged, clustered (MMseqs2) and annotated against DRAMP/APD/UniRef100 by AMPcombi.
7. **BGC screening** (`--run_bgc_screening`) — antiSMASH (bacteria or fungi), DeepBGC, GECCO, and optional HMMER `hmmsearch`. Results merged by comBGC; only long contigs (≥3 kbp) are screened.
8. **Final reporting** — per-workflow summary TSVs (`hamronization_combined_report.tsv`, `Ampcombi_summary_cluster.tsv`, `combgc_complete_summary.tsv`) plus a MultiQC software-versions/methods report.

## Key parameters
- `--input` — CSV with columns `sample,fasta` (or `sample,fasta,protein,gbk` to skip annotation).
- `--outdir` — absolute path for results.
- **Which screens to run** (at least one required): `--run_arg_screening`, `--run_amp_screening`, `--run_bgc_screening`.
- **Annotator**: `--annotation_tool {pyrodigal|prodigal|prokka|bakta}` (default `pyrodigal`; avoid `prokka` if running antiSMASH — causes `translation longer than location allows`).
- **Bakta DB**: `--annotation_bakta_db` + `--annotation_bakta_db_downloadtype {full|light}`; add `--annotation_bakta_singlemode` for complete isolates instead of metagenomic `--meta` mode.
- **BGC contig filter**: `--bgc_mincontiglength 3000` (must be ≥3000 or antiSMASH can crash); `--bgc_antismash_contigminlength`, `--bgc_antismash_taxon {bacteria|fungi}`, `--bgc_antismash_hmmdetectionstrictness {relaxed|strict|loose}`.
- **ARG tool toggles**: `--arg_skip_{abricate,amrfinderplus,deeparg,fargene,rgi,argnorm}`; `--arg_fargene_hmmmodel` comma list; database paths `--arg_{amrfinderplus,deeparg,rgi,abricate}_db` (pipeline will auto-download if omitted).
- **AMP tool toggles**: `--amp_skip_{ampir,amplify,macrel}`; `--amp_run_hmmsearch` with `--amp_hmmsearch_models '/path/*.hmm'` (quoted wildcard!); AMPcombi cutoffs `--amp_ampcombi_parsetables_cutoff 0.6`, `--amp_ampcombi_parsetables_aalength 120`, `--amp_ampcombi_db_id {DRAMP|APD|UniRef100}`.
- **BGC tool toggles**: `--bgc_skip_{antismash,deepbgc,gecco}`; `--bgc_run_hmmsearch` + `--bgc_hmmsearch_models`; `--bgc_antismash_db`, `--bgc_deepbgc_db`.
- **Taxonomy add-on**: `--run_taxa_classification --taxa_classification_mmseqs_db_id Kalamari` (or supply `--taxa_classification_mmseqs_db`).
- **Protein annotation add-on**: `--run_protein_annotation` + optional `--protein_annotation_interproscan_db`.
- **Database caching**: `--save_db` to keep auto-downloaded databases in `<outdir>/databases/` for reuse.
- ⚠️ If running AMP screening, do **not** set `--annotation_pyrodigal_usespecialstopcharacter` — AMPlify cannot parse `*` stop codons.

## Test data
The bundled `test` profile (`conf/test.config`) uses a reduced nf-core/funcscan test samplesheet of tiny assembled bacterial contig FASTAs (`samplesheet_reduced.csv` from the nf-core test-datasets repository), with `--annotation_tool pyrodigal`, AMP + ARG screening enabled, fARGene restricted to beta-lactamase classes `class_a,class_b_1_2`, and HMMER hmmsearch driven by a small `mybacteriocin.hmm` model. Running it produces per-tool hit tables, a harmonised ARG report (`reports/hamronization_summarize/hamronization_combined_report.tsv`) and an AMP summary (`reports/ampcombi/Ampcombi_summary_cluster.tsv`). The `test_full` profile mirrors this on MGnify chicken-cecum metagenome assemblies (`samplesheet_full.csv`, study MGYS00005631) and additionally exercises the BGC subworkflow with a ToyB antiSMASH HMM (DeepBGC and AMPlify are skipped there for runtime).

## Reference workflow
nf-core/funcscan v3.0.0 (https://github.com/nf-core/funcscan), DOI 10.5281/zenodo.7643099. See `docs/usage.md` and `docs/output.md` in the repository for exhaustive parameter and output descriptions, and `CITATIONS.md` for the full list of underlying tools.
