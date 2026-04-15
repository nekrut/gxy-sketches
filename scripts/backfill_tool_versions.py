"""One-shot backfill: enrich every existing SKETCH.md with tool versions
parsed deterministically from its source workflow.

No LLM calls. For each sketch in `sketches/`:
  1. Load + validate the frontmatter.
  2. Find the matching WorkflowRecord from the ingestors by `source.url`.
  3. Re-run `_enrich_tools_with_versions` on the current tool list.
  4. Also populate `source.slug` if missing.
  5. Write SKETCH.md back with the updated frontmatter.

Run via:
    PYTHONPATH=src .venv/bin/python scripts/backfill_tool_versions.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import frontmatter
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gxy_sketches.generate.llm import _enrich_tools_with_versions  # noqa: E402
from gxy_sketches.ingest.iwc import IwcIngestor  # noqa: E402
from gxy_sketches.ingest.nf_core import NfCoreIngestor  # noqa: E402
from gxy_sketches.schema import SketchFrontmatter, WorkflowRecord  # noqa: E402


CACHE = ROOT / "workflows_cache"
SKETCHES = ROOT / "sketches"


def _load_all_records() -> dict[str, WorkflowRecord]:
    """Walk both ingestors (using already-cloned cache) and index by source_url."""
    index: dict[str, WorkflowRecord] = {}
    print("Loading IWC records...", file=sys.stderr)
    for r in IwcIngestor().discover(CACHE):
        index[r.source_url] = r
    print(f"  {sum(1 for r in index.values() if r.ecosystem == 'iwc'):>4} IWC records", file=sys.stderr)
    print("Loading nf-core records (from local clones, no cloning)...", file=sys.stderr)
    nfcore_added = _walk_nfcore_local(index)
    print(f"  {nfcore_added:>4} nf-core records", file=sys.stderr)
    return index


def _walk_nfcore_local(index: dict[str, WorkflowRecord]) -> int:
    """Build minimal nf-core records from the on-disk clone tree without
    re-fetching the catalog or re-cloning. We only need tool_versions and a
    matching source_url.
    """
    from gxy_sketches.ingest.nf_core import _scan_modules_tool_versions

    count = 0
    nfcore_dir = CACHE / "nf-core"
    if not nfcore_dir.is_dir():
        return 0
    for pipeline_dir in sorted(nfcore_dir.iterdir()):
        if not pipeline_dir.is_dir():
            continue
        name = pipeline_dir.name
        url = f"https://github.com/nf-core/{name}"
        tool_versions = _scan_modules_tool_versions(pipeline_dir)
        index[url] = WorkflowRecord(
            ecosystem="nf-core",
            slug=name,
            display_name=f"nf-core/{name}",
            source_url=url,
            tool_versions=tool_versions,
            raw_root=pipeline_dir,
        )
        count += 1
    return count


def _backfill_sketch(sketch_md: Path, records: dict[str, WorkflowRecord]) -> str:
    post = frontmatter.load(str(sketch_md))
    data = dict(post.metadata)
    fm = SketchFrontmatter.model_validate(data)

    record = records.get(fm.source.url)
    if record is None:
        return "no-record"

    new_tools = _enrich_tools_with_versions(
        [t.model_dump(mode="json", exclude_none=True) for t in fm.tools],
        record.tool_versions,
    )

    # Slug backfill for older sketches.
    source_dict = fm.source.model_dump(mode="json", exclude_none=True)
    if not source_dict.get("slug"):
        source_dict["slug"] = record.slug

    data["tools"] = new_tools
    data["source"] = source_dict

    # Round-trip through SketchFrontmatter to re-validate.
    SketchFrontmatter.model_validate(data)

    # Rewrite the file with stable ordering + no empty keys.
    fm_yaml = yaml.safe_dump(
        SketchFrontmatter.model_validate(data).model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        default_flow_style=False,
    )
    body = post.content
    if not body.endswith("\n"):
        body += "\n"
    sketch_md.write_text(f"---\n{fm_yaml}---\n\n{body}")

    total = len(new_tools)
    hit = sum(1 for t in new_tools if t.get("version"))
    return f"{hit}/{total}"


def main() -> int:
    records = _load_all_records()
    total = 0
    hits = 0
    no_record = 0
    for sketch_md in sorted(SKETCHES.rglob("SKETCH.md")):
        status = _backfill_sketch(sketch_md, records)
        if status == "no-record":
            no_record += 1
            print(f"  [miss] {sketch_md.relative_to(ROOT)}", file=sys.stderr)
            continue
        hit_s, _total_s = status.split("/")
        if int(hit_s) > 0:
            hits += 1
        total += 1
    print(
        f"\nbackfilled {total} sketches "
        f"({hits} with at least one version hit, {no_record} unmatched)",
        file=sys.stderr,
    )
    return 0 if no_record == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
