# gxy-sketches

A corpus of **sketches** — short, structured markdown files that teach LLM agents how to perform different types of bioinformatics data analyses — and the generator that produces them from real, community-maintained workflows.

A sketch answers *"given this kind of data and this kind of question, what analysis should I run and how?"* — e.g., haploid variant calling on a bacterial genome, bulk RNA-seq on vertebrate samples, amplicon metagenomics.

Sketches are derived from:

- [nf-core](https://github.com/nf-core) — Nextflow pipelines
- [Galaxy IWC](https://github.com/galaxyproject/iwc) — Intergalactic Workflow Commission

Downstream agents such as [gxy3](../gxy3) load `sketches/**/*.md` the same way Claude Code loads skill files and use them to ground analysis planning.

## Layout

```
sketches/           # the corpus (git-tracked)
src/gxy_sketches/   # Python package
  ingest/           # one module per source ecosystem
  generate/         # LLM-based sketch synthesis (uses Anthropic prompt caching)
  schema.py         # pydantic contract
  validate.py       # corpus linter
  cli.py            # `gxy-sketches ingest|generate|validate|list`
tests/              # unit tests + checked-in fixtures
workflows_cache/    # gitignored raw sources
```

## Quick start

```bash
uv sync
cp .env.example .env            # add ANTHROPIC_API_KEY
uv run gxy-sketches ingest iwc
uv run gxy-sketches generate --source iwc --only <workflow-slug>
uv run gxy-sketches validate
uv run gxy-sketches list --domain variant-calling
```

See `PLAN.md` for the full design rationale.

## Sketch format

Each sketch is a **directory** containing:

- `SKETCH.md` — YAML frontmatter (machine-readable contract: name, description, domain, source provenance, tools, test/output manifests) + markdown guidance (when to use / not use, analysis outline, key parameters).
- `test_data/` — small inputs (≤5 MB total) lifted from the source workflow's test fixtures.
- `expected_output/` — known-good outputs from running the analysis on `test_data/`.

The validator enforces the 5 MB bundle cap and that every file on disk is referenced in frontmatter and vice versa. See `PLAN.md` for the full schema and an example.

## Status

Early. v1 covers nf-core + Galaxy IWC only. Snakemake and WDL are planned for v2.
