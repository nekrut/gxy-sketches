"""Prototype: extract DAGs from SKETCH.md analysis outlines and mine frequent subgraphs.

Approach
--------
1. For each SKETCH.md, parse the "## Analysis outline" section. Each numbered
   step becomes a node-set (the bold-marked tool names within that step).
   Edges connect step i to step i+1 (chain semantics).
2. Canonicalise tool names via an equivalence map drawn from the redundancy
   table in COMMON_MODULES.md (e.g. bwa / bwa-mem / bwa-mem2 -> short_read_aln).
3. Mine frequent connected subgraphs by enumerating canonical k-paths
   (k=2..6) across the corpus. Since extracted graphs are near-linear, k-paths
   capture ~all of the structure; we additionally record "co-step" sets so
   parallel tool use (e.g. fastqc + fastp in one step) shows up as motifs.
4. Print top motifs by support and the sketches that exhibit them.

Limitations
-----------
- Heuristic extraction: relies on bold markers. Misses tools mentioned in
  prose but not bolded. Step ordering reflects the prose, not true data
  dependency (some "steps" run in parallel).
- Linearisation collapses true DAG branches. For a v1 the corpus is mostly
  linear so this is acceptable. To go further, add an LLM extraction pass.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKETCHES = ROOT / "sketches"

# Canonicalisation: legacy -> role token. Drawn from COMMON_MODULES.md.
EQUIV: dict[str, str] = {
    # trimming
    "fastp": "trim",
    "trim-galore": "trim",
    "trim_galore": "trim",
    "trimmomatic": "trim",
    "cutadapt": "trim_primer",  # kept distinct: primer-aware
    # short-read align
    "bwa": "sr_aln",
    "bwa-mem": "sr_aln",
    "bwa-mem2": "sr_aln",
    "bowtie2": "sr_aln_sensitive",  # kept distinct: ChIP/ATAC default
    # long-read align
    "minimap2": "lr_aln",
    # splice align
    "star": "splice_aln",
    "hisat2": "splice_aln",
    "tophat": "splice_aln",
    # pseudoalign
    "salmon": "pseudoalign",
    "kallisto": "pseudoalign",
    # bam utils
    "samtools": "bam_utils",
    "bamtools": "bam_utils",
    # dedup
    "picard": "markdup",
    "picard-markduplicates": "markdup",
    "markduplicates": "markdup",
    # qc
    "fastqc": "raw_qc",
    "nanoplot": "lr_qc",
    "pycoqc": "lr_qc",
    "qualimap": "bam_qc",
    "preseq": "lib_complexity",
    "rseqc": "rnaseq_qc",
    "multiqc": "qc_report",
    # variant callers
    "lofreq": "vc_lowfreq",
    "ivar": "vc_amplicon_viral",
    "gatk4": "vc_germline",
    "gatk": "vc_germline",
    "deepvariant": "vc_germline",
    "freebayes": "vc_germline",
    "bcftools": "vcf_utils",
    "varscan": "vc_legacy",
    # annotation
    "snpeff": "annot_var",
    "snpsift": "vcf_filter",
    "vep": "annot_var",
    # peaks
    "macs2": "peak_call",
    "macs3": "peak_call",
    "seacr": "peak_call",
    # coverage
    "deeptools": "coverage",
    # assembly
    "spades": "asm_short",
    "shovill": "asm_short",
    "unicycler": "asm_hybrid",
    "hifiasm": "asm_long",
    "flye": "asm_long",
    # asm qc
    "quast": "asm_qc",
    "busco": "asm_completeness",
    "compleasm": "asm_completeness",
    "merqury": "asm_kmer_qc",
    "gfastats": "asm_stats",
    # taxonomy
    "kraken2": "tax_kmer",
    "bracken": "tax_abundance",
    "krona": "tax_viz",
    # rnaseq quant
    "featurecounts": "count",
    "htseq": "count",
    "stringtie": "transcript_quant",
    # de
    "deseq2": "de",
    "edger": "de",
    "limma-voom": "de",
    # umi
    "umi-tools": "umi",
    "fgbio": "umi",
    # bact annot
    "prokka": "bact_annot",
    "bakta": "bact_annot",
    # search
    "diamond": "protein_search",
    # misc kept literal
    "tooldistillator": "tooldistillator",
    "qiime2": "qiime2",
    "openms": "openms",
    "bedtools": "intervals",
    "seqtk": "fastx_utils",
    "seqkit": "fastx_utils",
    "abricate": "amr",
}


def canon(tool: str) -> str:
    t = tool.lower().strip()
    return EQUIV.get(t, t)


# Match **Tool Name** or `tool` in a step's text.
BOLD_RE = re.compile(r"\*\*([^*]+?)\*\*")
CODE_RE = re.compile(r"`([^`]+?)`")
STEP_RE = re.compile(r"^\s*\d+\.\s+(.*?)$")


def parse_sketch(path: Path) -> dict | None:
    txt = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", txt, re.DOTALL)
    if not m:
        return None
    fm = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)
    declared = {
        (t.get("name") if isinstance(t, dict) else t).lower()
        for t in (fm.get("tools") or [])
        if t
    }
    # Pull "## Analysis outline" section.
    sec = re.search(
        r"##\s+Analysis outline\s*\n(.*?)(?=\n##\s+|\Z)", body, re.DOTALL | re.IGNORECASE
    )
    if not sec:
        return None
    steps: list[set[str]] = []
    for line in sec.group(1).splitlines():
        sm = STEP_RE.match(line)
        if not sm:
            continue
        text = sm.group(1)
        candidates = set()
        for rx in (BOLD_RE, CODE_RE):
            for hit in rx.findall(text):
                # split things like "samtools view" -> first token
                first = re.split(r"[\s/]+", hit.strip())[0].lower()
                first = re.sub(r"[^a-z0-9_-]", "", first)
                if first and (first in EQUIV or first in declared):
                    candidates.add(first)
        if candidates:
            steps.append(candidates)
    if not steps:
        return None
    return {
        "domain": path.parent.parent.name,
        "slug": path.parent.name,
        "steps": [sorted(s) for s in steps],
        "canon_steps": [sorted({canon(t) for t in s}) for s in steps],
        "declared_tools": sorted(declared),
    }


def extract_all() -> list[dict]:
    out = []
    for sk in sorted(SKETCHES.glob("*/*/SKETCH.md")):
        rec = parse_sketch(sk)
        if rec:
            out.append(rec)
    return out


def mine_kpaths(records: list[dict], k_min=2, k_max=5, min_support=4):
    """Mine frequent k-grams over the linearised canonical step sequence.

    For each sketch, build the sequence of canonical tool tokens by
    flattening steps in order. Same tool token in adjacent steps is collapsed.
    """
    seqs: list[tuple[str, list[str]]] = []
    for r in records:
        seq: list[str] = []
        for step in r["canon_steps"]:
            for t in step:
                if not seq or seq[-1] != t:
                    seq.append(t)
        seqs.append((f"{r['domain']}/{r['slug']}", seq))

    motifs: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for label, seq in seqs:
        for k in range(k_min, k_max + 1):
            seen_in_seq: set[tuple[str, ...]] = set()
            for i in range(len(seq) - k + 1):
                gram = tuple(seq[i : i + k])
                # skip motifs that are just one token repeated
                if len(set(gram)) < 2:
                    continue
                if gram in seen_in_seq:
                    continue
                seen_in_seq.add(gram)
                motifs[gram].append(label)
    return [
        (gram, sorted(set(labels))) for gram, labels in motifs.items() if len(set(labels)) >= min_support
    ]


def mine_costeps(records: list[dict], min_support=4):
    """Mine canonical step sets that occur as a single step (parallel tools)."""
    sets_: dict[frozenset[str], list[str]] = defaultdict(list)
    for r in records:
        label = f"{r['domain']}/{r['slug']}"
        for step in r["canon_steps"]:
            if len(step) < 2:
                continue
            sets_[frozenset(step)].append(label)
    return [
        (sorted(s), sorted(set(labels))) for s, labels in sets_.items() if len(set(labels)) >= min_support
    ]


def main():
    recs = extract_all()
    parsed = len(recs)
    total = sum(1 for _ in SKETCHES.glob("*/*/SKETCH.md"))
    print(f"Parsed analysis outlines: {parsed}/{total} sketches")
    avg_steps = sum(len(r["steps"]) for r in recs) / max(parsed, 1)
    print(f"Average steps per sketch: {avg_steps:.1f}")

    paths = mine_kpaths(recs, k_min=2, k_max=5, min_support=5)
    paths.sort(key=lambda x: (-len(x[1]), -len(x[0]), x[0]))

    print("\n=== Top frequent k-paths (canonical, support >=5) ===")
    seen_subs: list[set[tuple[str, ...]]] = []  # for dedupe of dominated motifs
    shown = 0
    for gram, labels in paths:
        # skip if a strict superset motif with same support exists
        if any(set(gram).issubset(set(g2)) and len(l2) >= len(labels) and gram != g2
               for (g2, l2) in paths):
            continue
        print(f"  [{len(labels):3d}] {' -> '.join(gram)}")
        for ex in labels[:5]:
            print(f"         {ex}")
        if len(labels) > 5:
            print(f"         ... +{len(labels) - 5} more")
        shown += 1
        if shown >= 25:
            break

    cos = mine_costeps(recs, min_support=4)
    cos.sort(key=lambda x: -len(x[1]))
    print("\n=== Frequent co-step sets (parallel tools in one step, support >=4) ===")
    for s, labels in cos[:15]:
        print(f"  [{len(labels):3d}] {{{', '.join(s)}}}")
        for ex in labels[:3]:
            print(f"         {ex}")

    # Persist for later analysis.
    out_path = ROOT / "scripts" / "dag_motifs.json"
    with out_path.open("w") as f:
        json.dump(
            {
                "parsed": parsed,
                "total": total,
                "kpath_motifs": [
                    {"motif": list(g), "support": len(l), "sketches": l} for g, l in paths
                ],
                "costep_motifs": [
                    {"costep": list(s), "support": len(l), "sketches": l} for s, l in cos
                ],
            },
            f,
            indent=2,
        )
    print(f"\nWrote {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
