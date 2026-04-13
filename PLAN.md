# gxy-sketches — Implementation Plan

## Context

`gxy3` (`../gxy3`) is a chat-driven bioinformatics desktop app whose Pi.dev agent composes analyses from natural language (e.g., "do variant calling on this MRSA genome"). Today the agent has no corpus of concrete analysis recipes — it reasons from scratch, which is error-prone for tasks with strict domain best practices (ploidy, read QC, caller choice, reference prep, etc.).

**Goal.** `gxy-sketches` ingests real community-maintained workflows from **nf-core** (Nextflow) and the **Galaxy Intergalactic Workflow Commission (IWC)**, uses an LLM to distill each into a short structured **sketch** — a `SKILL.md`-style markdown file that teaches an agent *when* and *how* to run that class of analysis — and stores the result as a git-tracked corpus.

An agent routing example: user asks for MRSA variant calling → agent scans `sketches/**/*.md` → selects the haploid-bacterial variant-calling sketch → constructs a concrete plan grounded in it.

The project is scoped to the **corpus + generator**. No runtime API, no embeddings. Agents consume sketches as plain files.

## Source Ecosystems (v1)

| Source | Repo | Count | Metadata to exploit |
|---|---|---|---|
| nf-core | https://github.com/nf-core | ~147 pipelines | `nextflow_schema.json`, `README.md`, `CITATIONS.md`, `docs/usage.md`, `docs/output.md`, per-module `meta.yml` |
| Galaxy IWC | https://github.com/galaxyproject/iwc | ~30–40 workflows | `*.ga` (Galaxy Format 2 JSON), `*-tests.yml`, per-workflow `README.md`, `CHANGELOG.md` |

Snakemake + WDL are deferred to v2 — the ingestor protocol makes adding them purely additive.

## Sketch Layout

Each sketch is a **directory**, not a single file. The directory bundles the markdown guidance with *small* test inputs and expected outputs, so any agent (or CI) can validate a sketch end-to-end without touching the network.

```
sketches/variant-calling/haploid-variant-calling-bacterial/
├── SKETCH.md                 # frontmatter + guidance (modeled on galaxy-skills/*/SKILL.md)
├── test_data/                # tiny inputs — fastq subsets, trimmed reference, etc.
│   ├── reads_1.fastq.gz
│   ├── reads_2.fastq.gz
│   └── reference.fasta
└── expected_output/          # known-good outputs for the test inputs
    ├── variants.vcf
    ├── summary.tsv
    └── README.md             # one-line description of each file
```

Where the test data comes from:

- **IWC**: workflows already ship a `test-data/` dir and a `*-tests.yml` planemo test definition — the IWC ingestor lifts both verbatim.
- **nf-core**: pipelines ship a `test` profile that points at `nf-core/test-datasets`. The ingestor records the test-profile config + dataset URLs; where data is small enough (<5 MB total) it mirrors into `test_data/`, otherwise it stores URLs and checksums and generates a small synthetic subset where feasible.

Hard size cap on anything checked into `test_data/` or `expected_output/`: **5 MB per sketch**, enforced by the validator. Use Git LFS-style URL references for anything larger.

Example `SKETCH.md`:

```markdown
---
name: haploid-variant-calling-bacterial
description: Call SNVs and small indels against a haploid bacterial reference (e.g., MRSA, M. tuberculosis) from short-read sequencing. Use when the organism is a single-chromosome prokaryote and ploidy=1 is appropriate.
domain: variant-calling
organism_class: [bacterial, haploid]
input_data: [short-reads-paired, reference-fasta]
source:
  ecosystem: nf-core
  workflow: nf-core/bacass
  url: https://github.com/nf-core/bacass
  version: 2.2.0
  license: MIT
tools: [fastp, bwa-mem2, samtools, bcftools, snpeff]
tags: [bacteria, wgs, snv, indel, haploid]
test_data:
  - path: test_data/reads_1.fastq.gz
    role: reads_forward
  - path: test_data/reads_2.fastq.gz
    role: reads_reverse
  - path: test_data/reference.fasta
    role: reference
expected_output:
  - path: expected_output/variants.vcf
    kind: vcf
    description: Final filtered haploid variants; ~15 SNVs expected on test data.
  - path: expected_output/summary.tsv
    kind: tsv
    description: Per-sample QC + variant counts.
---

# Haploid bacterial variant calling

## When to use this sketch
- Single-chromosome prokaryote (bacteria, archaea)
- Short-read Illumina data (paired-end preferred)
- You need SNVs + small indels, not structural variants

## Do not use when
- Eukaryotic / diploid samples → `diploid-germline-variant-calling`
- Long reads only → `long-read-variant-calling-bacterial`

## Analysis outline
1. QC + adapter/quality trimming (fastp)
2. Align to reference (bwa-mem2)
3. Sort, mark duplicates (samtools)
4. Call variants with ploidy=1 (bcftools call --ploidy 1)
5. Filter (QUAL, DP, MQ thresholds)
6. Annotate effects (snpEff)

## Test data
`test_data/` contains a ~50 kb subset of a Staph aureus run downsampled from the bacass test profile. Running the outlined pipeline on it should reproduce `expected_output/variants.vcf` byte-for-byte modulo timestamp headers.

## Reference workflow
Derived from nf-core/bacass v2.2.0.
```

- Frontmatter is the machine-readable contract an agent filters/ranks on; the body is guidance.
- `test_data` and `expected_output` are **both listed in frontmatter and present on disk** — the validator enforces that every referenced file exists and every file on disk is referenced.
- Every sketch is provenance-linked and version-pinned to a real workflow.

## Architecture

```
gxy-sketches/
├── README.md
├── PLAN.md
├── pyproject.toml
├── .env.example                # ANTHROPIC_API_KEY
├── .gitignore                  # ignores workflows_cache/
├── src/gxy_sketches/
│   ├── cli.py                  # typer CLI: ingest | generate | validate | list
│   ├── ingest/
│   │   ├── base.py             # Ingestor protocol: discover() -> [WorkflowRecord]
│   │   ├── nf_core.py
│   │   └── iwc.py
│   ├── generate/
│   │   ├── prompts.py          # system + user prompt templates + few-shot
│   │   ├── llm.py              # Anthropic client — prompt caching on
│   │   └── sketch_writer.py
│   ├── schema.py               # pydantic: WorkflowRecord, SketchFrontmatter
│   └── validate.py             # corpus linter
├── workflows_cache/            # gitignored raw sources
├── sketches/                   # the corpus — each leaf is a sketch DIRECTORY
│   ├── variant-calling/
│   │   └── haploid-variant-calling-bacterial/
│   │       ├── SKETCH.md
│   │       ├── test_data/
│   │       └── expected_output/
│   ├── assembly/
│   ├── rna-seq/
│   ├── single-cell/
│   ├── metagenomics/
│   └── ...
├── tests/
│   ├── test_schema.py
│   ├── test_ingest_iwc.py
│   ├── test_ingest_nf_core.py
│   ├── test_generate.py        # mocked LLM
│   ├── test_validate.py
│   └── fixtures/
└── scripts/
    └── regenerate_all.sh
```

**Flow.** `ingest` clones/updates repos into `workflows_cache/` and builds `WorkflowRecord`s. `generate` calls Claude with a cached system prompt and writes validated `sketches/<domain>/<slug>.md`. `validate` lints the corpus. `gxy3` reads `sketches/**/*.md` the same way Claude Code reads skills.

## Key design decisions

- **LLM over rule-based parsers.** Source metadata varies (nf-core schema JSON vs Galaxy `.ga` JSON); a single distillation prompt yields uniform sketches without ecosystem-specific templating. Prompt caching on the system prompt keeps re-runs cheap.
- **Markdown + frontmatter, not a database.** Grep-able, diff-able, PR-reviewable, and immediately consumable by any Claude-Code-style agent.
- **Pydantic schema is the contract.** Shared by generator (structured output target) and validator.
- **Scope fence.** No search API, no embeddings, no server. If discovery becomes painful, v2 adds an index.

## Verification

- `uv run pytest` — unit tests green (schema, ingestors against fixtures, mocked-LLM generate, validator).
- `uv run gxy-sketches ingest iwc && uv run gxy-sketches generate --source iwc --only <one>` — produces a valid sketch directory, `test_data/` and `expected_output/` populated from the source workflow's planemo test fixtures, passes validator.
- `uv run gxy-sketches validate` — for every sketch: frontmatter schema OK, referenced files exist, orphan files flagged, total bundled-data size ≤5 MB.
- **Manual quality gate:** human review of 5 sketches across domains.
- **Integration smoke test:** point gxy3 at `sketches/` and confirm it selects the haploid bacterial sketch for an MRSA query.

## Out of scope (v1)

- Snakemake, WDL ingestors
- Embedding / semantic search
- Cross-ecosystem dedup (manual for now)
- Runtime API server
- Any modification to gxy3 itself
