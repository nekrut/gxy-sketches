"""Prompt strings used by the sketch generator.

The system prompt is stable across every pipeline and therefore a perfect
target for Anthropic prompt caching. `build_system_prompt` composes it from:
    - the sketch format spec,
    - a single full few-shot example (so the model anchors on the target shape),
    - strict formatting rules.

Note: the LLM is deliberately NOT asked to produce the frontmatter fields
`test_data` and `expected_output`. Those are filled in authoritatively by
the caller from the source workflow's parsed test manifest, so the model
never has to hallucinate filenames or URLs.
"""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are a bioinformatics domain expert and workflow archaeologist. Your job is
to read a community-maintained workflow (Nextflow nf-core or Galaxy IWC) and
distill it into a single SKETCH.md file that teaches another LLM agent *when*
and *how* to run that class of analysis.

A sketch is NOT a tutorial. It is a compact decision aid: an agent reading it
in a few seconds should know (a) whether to pick this sketch for a user's
request, (b) the high-level recipe, and (c) where to dig for exact parameters.

## Output format — STRICT

Return a single JSON object and nothing else. No prose before or after.
The object has two fields:

    {
      "frontmatter": { ... YAML frontmatter as a JSON object ... },
      "body": "...markdown body, no front-matter fence..."
    }

### Required frontmatter fields

- name: kebab-case, 3-80 chars, lowercase a-z0-9 and hyphens only, globally
  unique in the corpus. Should read like an analysis class, not a workflow
  name (e.g. "haploid-variant-calling-bacterial", not "nfcore-bacass").
- description: single paragraph, 30-600 chars, MUST start with "Use when"
  or contain a clear "Use when ..." clause. This is how agents route.
- domain: one of:
    variant-calling, assembly, rna-seq, single-cell, metagenomics,
    epigenomics, proteomics, phylogenetics, long-read, amplicon,
    structural-variants, qc, annotation, other
- organism_class: list of tags like [bacterial, haploid], [vertebrate, diploid],
  [viral], [plant, polyploid], [eukaryote].
- input_data: list like [short-reads-paired, reference-fasta] or
  [long-reads-ont, reference-fasta] or [10x-scrna-fastq].
- tools: list of the key command-line tools / packages.
- tags: free-form search tags.

### DO NOT emit

- `source` — the caller fills it in authoritatively from the ingestor.
- `test_data` — the caller fills it in from the parsed planemo/nextflow test
  spec (see "PARSED TEST MANIFEST" in the user message).
- `expected_output` — same; filled in by the caller.

You MAY and SHOULD describe the test data and expected outputs in prose
inside the body section `## Test data` — e.g. "Two paired FASTQ samples
(ERR018930, ERR1035492) downsampled from public *Plasmodium vivax* runs,
with expected per-sample variants at NC_009906.1:3204 A>G …". Use the
parsed manifest in the user message as ground truth for this prose.

### Required body sections (in order)

1. `# <Title>` — one H1.
2. `## When to use this sketch` — bulleted.
3. `## Do not use when` — bulleted, explicit pointers to sibling sketches.
4. `## Analysis outline` — numbered, one line per step, naming the tool.
5. `## Key parameters` — the handful of parameters that actually matter,
   with their critical values (e.g. `ploidy: 1`).
6. `## Test data` — 2-5 sentences describing the inputs listed in the
   parsed manifest and the expected outputs / assertions.
7. `## Reference workflow` — cite the source workflow + version.

## Hard rules

- Never invent parameters the source doesn't support.
- If the source is a generic pipeline covering multiple scenarios, emit ONE
  sketch for the most prominent / representative class, named accordingly,
  and mention sibling sketches in "Do not use when".
- Never write "TODO", "TBD", placeholders, or uncertain language.
- Keep the body under 400 lines.
"""


FEW_SHOT_EXAMPLE = """\
## Few-shot example

INPUT (abridged):
    Workflow: nf-core/bacass
    Description: Simple bacterial assembly and annotation pipeline.
    README excerpt: "assembly of bacterial short-read data ... variant calling
    against a reference with bcftools and ploidy=1 ... snpEff annotation ..."
    Parsed test manifest inputs: reads_forward, reads_reverse, reference.
    Parsed test manifest outputs: variants.vcf (local golden), summary.tsv (local golden).

OUTPUT:
{
  "frontmatter": {
    "name": "haploid-variant-calling-bacterial",
    "description": "Use when you need to call SNVs and small indels against a haploid bacterial reference (e.g. MRSA, M. tuberculosis) from short-read Illumina data. Assumes ploidy=1.",
    "domain": "variant-calling",
    "organism_class": ["bacterial", "haploid"],
    "input_data": ["short-reads-paired", "reference-fasta"],
    "tools": ["fastp", "bwa-mem2", "samtools", "bcftools", "snpeff"],
    "tags": ["bacteria", "wgs", "snv", "indel", "haploid"]
  },
  "body": "# Haploid bacterial variant calling\\n\\n## When to use this sketch\\n- Single-chromosome prokaryote ...\\n\\n## Test data\\nTwo paired-end FASTQ files plus a reference FASTA, taken from the source pipeline's test profile. Running the workflow is expected to produce `variants.vcf` and a per-sample `summary.tsv` ...\\n"
}
"""


def build_system_prompt() -> str:
    return SYSTEM_PROMPT + "\n\n" + FEW_SHOT_EXAMPLE


def build_user_prompt(metadata_bundle: str) -> str:
    return (
        "Distill the workflow below into a single SKETCH.md JSON payload as "
        "specified in the system prompt. Remember: exactly one JSON object, "
        "no prose; do NOT include `source`, `test_data`, or `expected_output` "
        "in the frontmatter — the caller will fill those in.\n\n"
        f"{metadata_bundle}"
    )
