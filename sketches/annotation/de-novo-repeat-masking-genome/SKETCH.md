---
name: de-novo-repeat-masking-genome
description: Use when you need to identify and soft-mask transposable elements and
  low-complexity regions in a newly assembled eukaryotic genome FASTA using a de novo
  repeat library, typically as a preprocessing step before structural gene annotation.
domain: annotation
organism_class:
- eukaryote
input_data:
- genome-fasta
source:
  ecosystem: iwc
  workflow: Repeat masking with RepeatModeler and RepeatMasker
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/repeatmasking
  version: '0.1'
  license: MIT
tools:
- RepeatModeler
- RECON
- RepeatScout
- LtrHarvest
- Ltr_retriever
- RepeatMasker
- Dfam
tags:
- repeat-masking
- transposable-elements
- soft-masking
- de-novo-repeats
- genome-annotation-prep
- repeatmodeler
- repeatmasker
test_data:
- role: input
  url: https://zenodo.org/record/8116008/files/sequence.fasta?download=1
  sha1: 2ac5ce0eadf871798a5e8a978a3ddd42e341d15e
  filetype: fasta
expected_output: []
---

# De novo repeat masking of a eukaryotic genome

## When to use this sketch
- You have a newly assembled eukaryotic genome in FASTA format and need to identify and mask repetitive elements before gene prediction / structural annotation.
- No curated species-specific repeat library exists, so you need to build one de novo from the assembly itself with RepeatModeler (RECON + RepeatScout + LTR pipeline).
- You want soft-masked output (repeats in lowercase) suitable for downstream annotators such as MAKER, BRAKER, or Funannotate.
- You also want auxiliary artefacts: a GFF of repeat coordinates, a repeat catalog, a summary table, and the Stockholm seed alignments of the de novo families.

## Do not use when
- The target is a bacterial or archaeal genome — prokaryotes have minimal interleaved repeat content and this pipeline is overkill; use a dedicated prokaryotic annotation workflow instead.
- You already have a trusted curated repeat library (e.g. a Dfam species entry, RepBase family, or a manually curated consortium library) — skip RepeatModeler and run RepeatMasker directly with that library.
- You only need low-complexity masking for BLAST searches — use `dustmasker` or `tantan` instead; RepeatModeler is far too expensive.
- You are doing read-level variant calling or RNA-seq quantification — repeat masking is not required for those workflows.
- You need polished, manually curated TE family classifications — this automated pipeline produces draft families only; follow up with curation tools (e.g. MCHelper, TE-Aid) outside this sketch.

## Analysis outline
1. **Build de novo repeat library** — run `RepeatModeler` (v2.0.4) on the input genome FASTA. Internally this runs `BuildDatabase`, then iterative RECON and RepeatScout sampling, plus the LtrHarvest / LTR_retriever structural LTR pipeline, to produce consensus TE families.
2. **Collect RepeatModeler outputs** — capture the consensus families FASTA and the Stockholm seed alignments describing each family.
3. **Mask the genome** — run `RepeatMasker` (v4.1.5) using the RepeatModeler consensus FASTA as the custom library source, against Dfam, producing a soft-masked genome plus repeat annotations.
4. **Emit annotation artefacts** — export the masked FASTA, GFF of repeat coordinates, summary table, repeat catalog, and run log for downstream use.

## Key parameters
- **RepeatModeler input**: single genome FASTA; no reference library required.
- **RepeatMasker `repeat_source`**: `dfam` with a custom library supplied from RepeatModeler's `sequences` output (the de novo consensus FASTA).
- **RepeatMasker `species_from_list`**: `no` — do not constrain to a Dfam species; rely on the de novo library.
- **RepeatMasker `xsmall`: true** — soft-mask (lowercase) rather than hard-mask with Ns. This is critical for downstream gene predictors.
- **RepeatMasker `gff`: true** — emit a GFF of repeat coordinates alongside the masked FASTA.
- **RepeatMasker `excln`: true** — exclude runs of Ns from divergence / length statistics.
- **RepeatMasker `frag`: 40000** — fragment size for masking large sequences; leave at default unless memory-bound.
- **RepeatMasker advanced flags** (`nolow`, `noint`, `norna`, `alu`, `is_only`, `is_clip`, etc.): leave at defaults (false) for a generic eukaryote; tune only for specific lineages.

## Test data
A single small FASTA genome (`sequence.fasta`, SHA-1 `2ac5ce0e…`) fetched from Zenodo record 8116008 is used as the sole input. Running the workflow is expected to produce two RepeatModeler artefacts — a consensus families FASTA and a Stockholm seed alignment file — plus five RepeatMasker artefacts: the soft-masked genome FASTA, a tabular run log, a repeat statistics table, a repeat catalog text file, and a GFF of repeat coordinates. The test spec validates all seven outputs by approximate file size (`sim_size`) with generous deltas, since RepeatModeler's sampling is non-deterministic.

## Reference workflow
Galaxy IWC `workflows/repeatmasking` — *Repeat masking with RepeatModeler and RepeatMasker*, release 0.1 (2023-09-21), MIT licensed. Tool versions: RepeatModeler 2.0.4+galaxy1, RepeatMasker 4.1.5+galaxy0. Source: https://github.com/galaxyproject/iwc/tree/main/workflows/repeatmasking
