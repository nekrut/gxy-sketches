"""Classify sketches into fine-grained workflow classes, then mine motifs per class.

Domain is too coarse: `variant-calling` lumps germline-human, somatic, viral-amplicon,
viral-shotgun, GWAS, imputation, ancient-DNA, etc. The motifs in those sub-classes
are completely different. This script:

1. Assigns each sketch a class label via slug/tags/tools heuristics.
2. Re-uses the extractor in extract_dag_motifs.py to pull canonical step sequences.
3. Mines frequent k-paths *within each class* with class-appropriate support thresholds.
4. Writes a per-class motif report to CLASS_MOTIFS.md.
"""

from __future__ import annotations

import importlib.util
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Reuse the canonicalisation + parser from the previous prototype.
spec = importlib.util.spec_from_file_location(
    "extract_dag_motifs", ROOT / "scripts" / "extract_dag_motifs.py"
)
edm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(edm)


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

# Each rule: (class_label, predicate). First match wins; order matters.
# Predicates take a record dict with keys: domain, slug, tags (set), tools (set).

def has(s: set, *keys: str) -> bool:
    return any(k in s for k in keys)


def slug_has(slug: str, *frags: str) -> bool:
    return any(f in slug for f in frags)


RULES: list[tuple[str, callable]] = [
    # ----- variant-calling sub-classes -----
    ("vc-viral-amplicon", lambda r: r["domain"] == "variant-calling"
        and (slug_has(r["slug"], "artic", "amplicon", "ivar")
             or "ivar" in r["tools"])),
    ("vc-viral-shotgun", lambda r: r["domain"] == "variant-calling"
        and (slug_has(r["slug"], "viral", "sars-cov-2", "influenza", "pox", "low-frequency")
             or has(r["tags"], "viral", "sars-cov-2"))),
    ("vc-pathogen-id", lambda r: r["domain"] == "variant-calling"
        and slug_has(r["slug"], "pathogen", "abo-blood", "allele-based-pathogen", "mycobacterium")),
    ("vc-haploid-microbial", lambda r: r["domain"] == "variant-calling"
        and slug_has(r["slug"], "haploid", "bacterial-reference")),
    ("vc-somatic-human", lambda r: r["domain"] == "variant-calling"
        and slug_has(r["slug"], "somatic", "tumor-normal", "tumour", "cancer", "panel-of-normals", "pacbio-hifi-tumor")),
    ("vc-germline-human", lambda r: r["domain"] == "variant-calling"
        and slug_has(r["slug"], "germline", "rare-disease", "population-variant", "deep-learning-germline", "ploidy-aware")),
    ("vc-rna-variants", lambda r: r["domain"] == "variant-calling"
        and slug_has(r["slug"], "rna-seq-germline", "rna-somatic")),
    ("vc-gwas-imputation", lambda r: r["domain"] == "variant-calling"
        and slug_has(r["slug"], "gwas", "imputation", "lcwgs", "rare-variant-burden", "radseq")),
    ("vc-crispr-amplicon", lambda r: r["domain"] == "variant-calling"
        and slug_has(r["slug"], "crispr")),
    ("vc-ancient-dna", lambda r: r["domain"] == "variant-calling"
        and slug_has(r["slug"], "ancient-dna")),
    ("vc-umi-consensus", lambda r: r["domain"] == "variant-calling"
        and slug_has(r["slug"], "umi-consensus")),
    ("vc-reporting-benchmark", lambda r: r["domain"] == "variant-calling"
        and slug_has(r["slug"], "report", "benchmark")),

    # ----- epigenomics sub-classes -----
    ("epi-chipseq", lambda r: r["domain"] == "epigenomics"
        and slug_has(r["slug"], "chip-seq", "chipseq")),
    ("epi-atacseq", lambda r: r["domain"] == "epigenomics"
        and slug_has(r["slug"], "atac")),
    ("epi-cutandrun", lambda r: r["domain"] == "epigenomics"
        and slug_has(r["slug"], "cutandrun", "cutandtag")),
    ("epi-bisulfite", lambda r: r["domain"] == "epigenomics"
        and slug_has(r["slug"], "bisulfite", "methylation-bismark")),
    ("epi-long-read-meth", lambda r: r["domain"] == "epigenomics"
        and slug_has(r["slug"], "long-read-methylation")),
    ("epi-hic", lambda r: r["domain"] == "epigenomics"
        and slug_has(r["slug"], "hic", "hi-c")),
    ("epi-mnase", lambda r: r["domain"] == "epigenomics"
        and slug_has(r["slug"], "mnase")),
    ("epi-other", lambda r: r["domain"] == "epigenomics"),

    # ----- rna-seq sub-classes -----
    ("rna-bulk-de", lambda r: r["domain"] == "rna-seq"
        and slug_has(r["slug"], "differential-expression", "two-condition", "bulk-rnaseq-quantification", "bulk-rnaseq-paired-end-star", "bulk-rnaseq-single-end-star", "dual-rnaseq")),
    ("rna-splicing", lambda r: r["domain"] == "rna-seq"
        and slug_has(r["slug"], "alternative-splicing", "splicing")),
    ("rna-mirna-smallrna", lambda r: r["domain"] == "rna-seq"
        and slug_has(r["slug"], "mirna", "small-rna")),
    ("rna-iclip-clip", lambda r: r["domain"] == "rna-seq"
        and slug_has(r["slug"], "iclip", "clip")),
    ("rna-ribosome", lambda r: r["domain"] == "rna-seq"
        and slug_has(r["slug"], "ribosome")),
    ("rna-circrna", lambda r: r["domain"] == "rna-seq"
        and slug_has(r["slug"], "circrna")),
    ("rna-fusion", lambda r: r["domain"] == "rna-seq"
        and slug_has(r["slug"], "fusion")),
    ("rna-de-novo", lambda r: r["domain"] == "rna-seq"
        and slug_has(r["slug"], "de-novo", "denovo")),
    ("rna-spatial", lambda r: r["domain"] == "rna-seq"
        and slug_has(r["slug"], "spatial", "visium")),
    ("rna-nascent", lambda r: r["domain"] == "rna-seq"
        and slug_has(r["slug"], "nascent", "slam")),
    ("rna-cage-tss", lambda r: r["domain"] == "rna-seq"
        and slug_has(r["slug"], "cage", "tss")),
    ("rna-other", lambda r: r["domain"] == "rna-seq"),

    # ----- assembly sub-classes -----
    ("asm-short-bacterial", lambda r: r["domain"] == "assembly"
        and slug_has(r["slug"], "bacterial-genome-assembly-short-read", "bacterial-short-read-assembly-shovill", "hybrid-denovo-assembly-bacterial")),
    ("asm-long-read", lambda r: r["domain"] == "assembly"
        and slug_has(r["slug"], "long-read", "hifi", "flye", "phased-diploid", "trio-phased")),
    ("asm-hic-scaffolding", lambda r: r["domain"] == "assembly"
        and slug_has(r["slug"], "hic", "scaffolding", "bionano")),
    ("asm-purge-haplotypes", lambda r: r["domain"] == "assembly"
        and slug_has(r["slug"], "purge-haplotypic")),
    ("asm-polishing", lambda r: r["domain"] == "assembly"
        and slug_has(r["slug"], "polishing")),
    ("asm-decontamination", lambda r: r["domain"] == "assembly"
        and slug_has(r["slug"], "decontamination")),
    ("asm-other", lambda r: r["domain"] == "assembly"),

    # ----- qc sub-classes -----
    ("qc-short-read", lambda r: r["domain"] == "qc"
        and slug_has(r["slug"], "short-read-fastq", "short-read-fastqc", "short-read-qc-trimming", "sequencing-read-qc", "short-read-qc-and", "amplicon-read-qc-single", "core-facility")),
    ("qc-long-read", lambda r: r["domain"] == "qc"
        and slug_has(r["slug"], "genome-skim", "kmer-profiling")),
    ("qc-decontamination", lambda r: r["domain"] == "qc"
        and slug_has(r["slug"], "host-read-decontamination", "nanopore-host-depletion", "bacterial-assembly-qc-contamination")),
    ("qc-bcl-demux", lambda r: r["domain"] == "qc"
        and slug_has(r["slug"], "bcl-demultiplexing")),
    ("qc-format-convert", lambda r: r["domain"] == "qc"
        and slug_has(r["slug"], "bam-cram-to-fastq", "fastq-repair")),
    ("qc-mtb", lambda r: r["domain"] == "qc"
        and slug_has(r["slug"], "mycobacterium")),
    ("qc-mito", lambda r: r["domain"] == "qc"
        and slug_has(r["slug"], "mitochondrial")),
    ("qc-asm", lambda r: r["domain"] == "qc"
        and slug_has(r["slug"], "assembly-nx", "multi-genome-assembly-qc")),
    ("qc-sra", lambda r: r["domain"] == "qc"
        and slug_has(r["slug"], "sra-accession")),
    ("qc-simulate", lambda r: r["domain"] == "qc"
        and slug_has(r["slug"], "simulate")),
    ("qc-other", lambda r: r["domain"] == "qc"),

    # ----- amplicon sub-classes -----
    ("amp-qiime2-dada2", lambda r: r["domain"] == "amplicon"
        and (slug_has(r["slug"], "dada2", "qiime2") or "qiime2" in r["tools"])),
    ("amp-mgnify", lambda r: r["domain"] == "amplicon"
        and slug_has(r["slug"], "mgnify")),
    ("amp-crispr", lambda r: r["domain"] == "amplicon"
        and slug_has(r["slug"], "crispr")),
    ("amp-viral", lambda r: r["domain"] == "amplicon"
        and slug_has(r["slug"], "pox", "virus")),
    ("amp-other", lambda r: r["domain"] == "amplicon"),

    # ----- metagenomics sub-classes -----
    ("meta-tax-profiling", lambda r: r["domain"] == "metagenomics"
        and slug_has(r["slug"], "taxonomic-profiling", "kraken2-krona", "classifier-database")),
    ("meta-assembly-binning", lambda r: r["domain"] == "metagenomics"
        and slug_has(r["slug"], "assembly-binning", "assembled-genomes", "gene-catalogue")),
    ("meta-functional", lambda r: r["domain"] == "metagenomics"
        and slug_has(r["slug"], "functional", "amr")),
    ("meta-metatranscriptome", lambda r: r["domain"] == "metagenomics"
        and slug_has(r["slug"], "metatranscriptome")),
    ("meta-host-decon", lambda r: r["domain"] == "metagenomics"
        and slug_has(r["slug"], "host-decontamination", "host-identification", "metagenome-read-mapping")),
    ("meta-mgnify", lambda r: r["domain"] == "metagenomics"
        and slug_has(r["slug"], "mgnify")),
    ("meta-other", lambda r: r["domain"] == "metagenomics"),

    # ----- annotation sub-classes -----
    ("annot-bacterial", lambda r: r["domain"] == "annotation"
        and slug_has(r["slug"], "bacterial", "amr-virulence", "cgmlst", "mag-functional", "prokaryote")),
    ("annot-eukaryotic", lambda r: r["domain"] == "annotation"
        and slug_has(r["slug"], "eukaryote", "eukaryotic", "metazoan", "helixer", "braker", "maker")),
    ("annot-functional", lambda r: r["domain"] == "annotation"
        and slug_has(r["slug"], "functional-annotation", "ortholog")),
    ("annot-other", lambda r: r["domain"] == "annotation"),

    # ----- single-cell -----
    ("sc-rna", lambda r: r["domain"] == "single-cell"),

    # ----- proteomics -----
    ("prot-dda", lambda r: r["domain"] == "proteomics"
        and slug_has(r["slug"], "dda")),
    ("prot-dia", lambda r: r["domain"] == "proteomics"
        and slug_has(r["slug"], "dia")),
    ("prot-other", lambda r: r["domain"] == "proteomics"),

    # ----- catch-all -----
    ("phylo", lambda r: r["domain"] == "phylogenetics"),
    ("sv", lambda r: r["domain"] == "structural-variants"),
    ("longread-other", lambda r: r["domain"] == "long-read"),
    ("other", lambda r: r["domain"] == "other"),
]


def classify(r: dict) -> str:
    record = {
        "domain": r["domain"],
        "slug": r["slug"],
        "tags": set(t.lower() for t in r.get("tags", []) if isinstance(t, str)),
        "tools": set(t.lower() for t in r.get("declared_tools", [])),
    }
    for label, pred in RULES:
        try:
            if pred(record):
                return label
        except Exception:
            continue
    return "unclassified"


# ---------------------------------------------------------------------------
# Per-class motif mining
# ---------------------------------------------------------------------------


def kpath_motifs(records: list[dict], k_min=2, k_max=5, min_support=2):
    seqs = []
    for r in records:
        seq: list[str] = []
        for step in r["canon_steps"]:
            for t in step:
                if not seq or seq[-1] != t:
                    seq.append(t)
        seqs.append((f"{r['domain']}/{r['slug']}", seq))

    motifs: dict[tuple[str, ...], set[str]] = defaultdict(set)
    for label, seq in seqs:
        for k in range(k_min, k_max + 1):
            for i in range(len(seq) - k + 1):
                gram = tuple(seq[i : i + k])
                if len(set(gram)) < 2:
                    continue
                motifs[gram].add(label)
    out = [(g, sorted(s)) for g, s in motifs.items() if len(s) >= min_support]
    return out


def filter_dominated(motifs):
    """Drop motifs that are strict subsequences of an equally-supported larger motif."""
    by_support_len = sorted(motifs, key=lambda x: (-len(x[1]), -len(x[0])))
    keep = []
    for gram, labels in by_support_len:
        dominated = False
        for g2, l2 in keep:
            if len(l2) >= len(labels) and len(g2) > len(gram) and is_subseq(gram, g2):
                dominated = True
                break
        if not dominated:
            keep.append((gram, labels))
    return keep


def is_subseq(short, long_):
    i = 0
    for x in long_:
        if i < len(short) and x == short[i]:
            i += 1
    return i == len(short)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    recs = edm.extract_all()
    for r in recs:
        r["class"] = classify(r)

    by_class: dict[str, list[dict]] = defaultdict(list)
    for r in recs:
        by_class[r["class"]].append(r)

    # also classify the unparsed sketches (no analysis outline) so we know what
    # we're missing per class.
    import yaml
    all_classified: dict[str, dict] = defaultdict(lambda: {"parsed": 0, "total": 0, "slugs": []})
    for sk in sorted(edm.SKETCHES.glob("*/*/SKETCH.md")):
        txt = sk.read_text()
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", txt, re.DOTALL)
        if not m:
            continue
        fm = yaml.safe_load(m.group(1)) or {}
        slim = {
            "domain": sk.parent.parent.name,
            "slug": sk.parent.name,
            "tags": fm.get("tags") or [],
            "declared_tools": [
                (t.get("name") if isinstance(t, dict) else t) or "" for t in (fm.get("tools") or [])
            ],
        }
        cls = classify(slim)
        all_classified[cls]["total"] += 1
        all_classified[cls]["slugs"].append(slim["slug"])
    for cls, recs_in in by_class.items():
        all_classified[cls]["parsed"] = len(recs_in)

    # Build report
    md = ["# Per-class motif mining\n"]
    md.append(
        "Sketches classified into fine-grained workflow classes (sub-domains), "
        "then frequent k-paths mined within each class. Class-internal motifs are "
        "the actually-reusable modules — generic cross-domain motifs (qc, alignment) "
        "from the previous pass are deliberately suppressed by the per-class scope.\n"
    )

    md.append("## Classification summary\n")
    md.append("| Class | Parsed / Total | Example slugs |\n| --- | --- | --- |\n")
    for cls, info in sorted(all_classified.items(), key=lambda kv: -kv[1]["total"]):
        examples = ", ".join(info["slugs"][:3]) + ("..." if len(info["slugs"]) > 3 else "")
        md.append(f"| `{cls}` | {info['parsed']} / {info['total']} | {examples} |\n")
    md.append("\n")

    md.append("## Motifs per class\n")
    for cls in sorted(by_class.keys()):
        recs_in = by_class[cls]
        n = len(recs_in)
        if n < 2:
            continue
        # Support threshold: at least 2, or 30% of class, whichever is larger.
        min_sup = max(2, int(0.3 * n))
        motifs = kpath_motifs(recs_in, k_min=2, k_max=6, min_support=min_sup)
        motifs = filter_dominated(motifs)
        motifs.sort(key=lambda x: (-len(x[1]), -len(x[0])))
        if not motifs:
            continue
        md.append(f"### `{cls}` — {n} sketches (parsed)\n")
        md.append(f"min_support = {min_sup}; "
                  f"sketches: {', '.join(sorted(r['slug'] for r in recs_in)[:6])}"
                  f"{'...' if n > 6 else ''}\n\n")
        md.append("| Support | Motif |\n| --- | --- |\n")
        for gram, labels in motifs[:10]:
            md.append(f"| {len(labels)} / {n} | `{' → '.join(gram)}` |\n")
        md.append("\n")

    out_md = ROOT / "CLASS_MOTIFS.md"
    out_md.write_text("".join(md))
    print(f"Wrote {out_md.relative_to(ROOT)}")

    # Also dump JSON for programmatic use
    out_json = ROOT / "scripts" / "class_motifs.json"
    payload = {
        "classification": {
            cls: {"parsed": info["parsed"], "total": info["total"], "slugs": info["slugs"]}
            for cls, info in all_classified.items()
        },
        "motifs_by_class": {},
    }
    for cls, recs_in in by_class.items():
        n = len(recs_in)
        if n < 2:
            continue
        min_sup = max(2, int(0.3 * n))
        motifs = filter_dominated(kpath_motifs(recs_in, k_min=2, k_max=6, min_support=min_sup))
        payload["motifs_by_class"][cls] = [
            {"motif": list(g), "support": len(l), "sketches": l}
            for g, l in motifs
        ]
    with out_json.open("w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {out_json.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
