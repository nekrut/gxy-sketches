"""Materialize a `GeneratedSketch` as a directory on disk.

Layout per sketch:
    sketches/<domain>/<name>/
        SKETCH.md
        test_data/<files copied from source, when checked-in locally>
        expected_output/<files copied from source or assertion stubs>

The writer never copies files larger than `MAX_BUNDLED_BYTES`; those are left
as URL references in the frontmatter instead.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from ..schema import (
    ExpectedOutputRef,
    SketchFrontmatter,
    TestDataRef,
    TestManifest,
    WorkflowRecord,
)
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

    _materialize_expected_output(record, target, generated.frontmatter)
    _materialize_test_data_readme(target, generated.frontmatter)
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


def _materialize_expected_output(
    record: WorkflowRecord,
    target: Path,
    frontmatter: SketchFrontmatter,
) -> None:
    """Copy expected outputs listed in the parsed test manifest.

    Only entries with a local `path:` get copied — URL-backed and
    assertion-only outputs become an ASSERTIONS.md note instead so the
    validator has an on-disk artifact to reference.
    """
    manifest = record.test_manifest
    copied_bytes = 0
    for eo in frontmatter.expected_output:
        if eo.path is None:
            continue
        source = None
        if manifest is not None:
            source = manifest.output_source_map.get(eo.path)
        if source is None or not source.exists():
            continue
        size = source.stat().st_size
        if copied_bytes + size > MAX_BUNDLED_BYTES:
            # Too big to bundle — drop the local path, leave URL/assertions.
            continue
        dest = target / eo.path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        copied_bytes += size

    # For expected outputs with assertions but no path, drop a stub file so
    # the sketch dir isn't empty of signal. Only if it would still fit.
    assertion_only = [
        eo for eo in frontmatter.expected_output if not eo.path and eo.assertions
    ]
    if assertion_only:
        stub = target / "expected_output" / "ASSERTIONS.md"
        lines = ["# Content assertions (no golden file checked in)\n"]
        for eo in assertion_only:
            lines.append(f"## {eo.role or '(unnamed)'}\n")
            lines.append(f"{eo.description}\n\n")
            for a in eo.assertions:
                lines.append(f"- {a}\n")
            lines.append("\n")
        stub.write_text("".join(lines))


def _materialize_test_data_readme(
    target: Path, frontmatter: SketchFrontmatter
) -> None:
    """Drop a README in test_data/ for URL-only inputs so the dir isn't empty.

    Validators and humans get a single source of truth listing the remote
    URLs + hashes.
    """
    url_only = [td for td in frontmatter.test_data if td.url and not td.path]
    if not url_only:
        return
    lines = [
        "# Remote test data\n",
        "\n",
        "These inputs are referenced by URL rather than bundled with the sketch. "
        "They come from the source workflow's planemo test manifest.\n",
        "\n",
    ]
    for td in url_only:
        lines.append(f"- **{td.role}**")
        if td.filetype:
            lines.append(f" ({td.filetype})")
        lines.append(f" — {td.url}")
        if td.sha1:
            lines.append(f"  (SHA-1 `{td.sha1}`)")
        lines.append("\n")
    (target / "test_data" / "README.md").write_text("".join(lines))
