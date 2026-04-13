"""Materialize a `GeneratedSketch` as a directory on disk.

Layout per sketch:
    sketches/<domain>/<name>/
        SKETCH.md
        test_data/<files copied from the source workflow>
        expected_output/<placeholder or harvested files>

The writer never copies files larger than `MAX_BUNDLED_BYTES`; those are left
as URL references in the frontmatter instead.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from ..schema import SketchFrontmatter, WorkflowRecord
from .llm import GeneratedSketch


MAX_BUNDLED_BYTES = 5 * 1024 * 1024  # 5 MB per sketch


def write_sketch(
    generated: GeneratedSketch,
    record: WorkflowRecord,
    sketches_root: Path,
    overwrite: bool = False,
) -> Path:
    """Write `generated` into `sketches_root/<domain>/<name>/` and return the dir."""
    target = sketches_root / generated.frontmatter.domain / generated.frontmatter.name
    if target.exists() and not overwrite:
        raise FileExistsError(f"sketch already exists: {target}")
    target.mkdir(parents=True, exist_ok=True)
    (target / "test_data").mkdir(exist_ok=True)
    (target / "expected_output").mkdir(exist_ok=True)

    _copy_test_data(record, target, generated.frontmatter)
    _write_expected_output_placeholders(target, generated.frontmatter)
    _write_sketch_md(target, generated)

    return target


def _write_sketch_md(target: Path, generated: GeneratedSketch) -> None:
    fm_yaml = yaml.safe_dump(
        generated.frontmatter.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        default_flow_style=False,
    )
    body = generated.body if generated.body.endswith("\n") else generated.body + "\n"
    (target / "SKETCH.md").write_text(f"---\n{fm_yaml}---\n\n{body}")


def _copy_test_data(
    record: WorkflowRecord,
    target: Path,
    frontmatter: SketchFrontmatter,
) -> None:
    """Copy source test data into target/test_data/, honoring the 5 MB cap.

    The frontmatter lists the *shape* the LLM expects; we copy every source
    file we have and let the validator reconcile shape vs. reality.
    """
    if not record.test_data_paths:
        return
    dest = target / "test_data"
    total = 0
    for src in record.test_data_paths:
        size = src.stat().st_size
        if total + size > MAX_BUNDLED_BYTES:
            break
        shutil.copy2(src, dest / src.name)
        total += size


def _write_expected_output_placeholders(
    target: Path, frontmatter: SketchFrontmatter
) -> None:
    """For each declared expected_output, ensure a file exists.

    v1 writes a stub explaining the file was declared by the generator but
    has not yet been produced by an actual run of the analysis. A later pass
    (running the workflow against `test_data/`) replaces the stubs with real
    outputs.
    """
    for eo in frontmatter.expected_output:
        p = target / eo.path
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            continue
        p.write_text(
            f"# STUB — {eo.kind}\n"
            f"# {eo.description}\n"
            f"# Replace with real output from running the analysis on ../test_data/.\n"
        )
