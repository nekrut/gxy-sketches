# DAG motif mining — prototype findings

Prototype implementation in `scripts/extract_dag_motifs.py`. Raw output in `scripts/dag_motifs.json`.

## What it does

1. **Extract.** For each `SKETCH.md`, parse the `## Analysis outline` section and lift each numbered step's bold-marked tool name(s). Each sketch becomes a near-linear DAG (ordered list of step-sets).
2. **Canonicalise.** Map tools to *role tokens* using the redundancy table from `COMMON_MODULES.md` (e.g. `bwa | bwa-mem | bwa-mem2 → sr_aln`; `fastp | trim-galore | trimmomatic → trim`). Bowtie2 is kept as a distinct token (`sr_aln_sensitive`) because it is the canonical aligner for ChIP/ATAC/Bismark and not interchangeable with bwa-mem in those contexts.
3. **Mine.** Enumerate frequent k-paths (k=2..5) over the canonical sequence; report motifs with support ≥5 and suppress motifs that are strict subsequences of equally-supported larger motifs. Also enumerate "co-step" sets (tools appearing in the same numbered step → parallel use).

## Coverage

- Parsed analysis outlines from **175 / 258** sketches (68 %). The 83 unparsed sketches either use a different section heading, don't bold tool names, or are very short. With an LLM extraction pass coverage approaches 100 %.
- Average **5.1 steps** per parsed sketch.

## Headline motifs

| Support | Motif | Interpretation |
| ------- | ----- | -------------- |
| 16 | `bam_utils → markdup` | Universal post-alignment cleanup. |
| 11 | `sr_aln → bam_utils` | Short-read align + sort/index. |
|  9 | `raw_qc → trim` | FastQC then trim (M1+M2 head). |
|  6 | `sr_aln → bam_utils → markdup` | Module **M3** (short-read align stack). |
|  6 | `raw_qc → qc_report` | Module **M1** (FastQC → MultiQC). |
|  6 | `markdup → qc_report` | Tail of M3+M4. |
|  6 | `sr_aln_sensitive → bam_utils` | Module **M11** head (Bowtie2 → samtools, ChIP/ATAC). |
|  6 | `sr_aln → sr_aln_sensitive` | Sketches using **both** bwa-mem and bowtie2 (worth auditing — likely alternatives, not sequential). |
|  5 | `trim → sr_aln → bam_utils` | Module **M3** (full head: trim + align + sort). |
|  5 | `vc_lowfreq → annot_var` | Module **M16** (LoFreq → SnpEff). |
|  5 | `annot_var → vcf_filter` | Module **M17** (SnpEff → SnpSift). |

## What this confirms vs. the frequency-based catalogue

Comparing against `COMMON_MODULES.md`:

- **M1, M2, M3, M11, M16, M17** all surface as frequent k-paths with the *correct ordering*. The frequency-table approach in v1 of the catalogue couldn't tell us "fastqc precedes trim precedes align" — only that the three co-occur. Motif mining gives that ordering for free.
- **M4 (BAM QC bundle)** doesn't surface as a long k-path because the constituent QC tools (qualimap, preseq, samtools stats) are usually listed in separate steps that don't always appear consecutively. Treating QC tools as a co-step *bag* (rather than an ordered chain) would catch this — a future refinement.
- **M21 (kraken2 → bracken → krona)** is under-supported because most metagenomics sketches don't bold the tool names. An LLM extraction pass would lift coverage there specifically.

## Surprises / leads

1. **`sr_aln → sr_aln_sensitive` (6 sketches)** — sketches mention both `bwa` and `bowtie2`. Spot-checked `epigenomics/sammy-seq-chromatin-solubility` and `variant-calling/ancient-dna-short-read-preprocessing-mapping`: these legitimately use both (bwa for one read class, bowtie2 for another). Not redundancy — keep as-is.
2. **Step order ≠ data dependency.** Motifs are ordered by prose listing, which usually matches the DAG topology but not always (e.g. QC tools that run in parallel often listed sequentially). For a more rigorous pass, extract explicit `(producer, consumer)` edges via LLM and run a real subgraph miner (gSpan).

## Next-step refinements

Cheap, in roughly increasing cost:

1. **Treat trailing QC steps as a bag.** Group consecutive steps whose tokens are all in `{raw_qc, bam_qc, lib_complexity, rnaseq_qc, qc_report}` into one "qc bag" before mining. Should surface M4 and M8 cleanly.
2. **Lower support threshold for domain-scoped mining.** Run the miner per-domain (e.g. variant-calling alone has 42 sketches; min_support 5 means motifs supported by 12 % of them — too high). Per-domain min_support of 3 will surface domain-specific modules (e.g. ARTIC primer trim chains, GATK BQSR head).
3. **LLM-based step extraction.** Replace the bold-marker heuristic with an LLM pass that emits `{step_id, tool, depends_on: [...]}`. Boosts coverage past 95 % and produces real DAG edges instead of linearised chains.
4. **Real subgraph mining.** Once edges are honest, run `gspan-mining` or `pyfsg` on the corpus. Will catch branching motifs the linear miner can't see (e.g. one alignment fanning out to qualimap, samtools stats, and a variant caller in parallel).
5. **Tool-substitution matrix → workflow alignment.** Use the `EQUIV` map as a substitution score and run pairwise Needleman-Wunsch on canonical sequences. Output: a similarity matrix over all 258 sketches that respects "bwa-mem ≈ bwa-mem2" while penalising "bwa-mem ≠ minimap2". Useful for clustering and for "find me the most similar sketch" agentic queries.

## How to reproduce

```bash
uv run python scripts/extract_dag_motifs.py
# writes scripts/dag_motifs.json with full motif/sketch lists
```

No new dependencies — uses only `pyyaml` (already in the project).
