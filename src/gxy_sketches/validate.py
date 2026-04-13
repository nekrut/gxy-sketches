"""Corpus linter.

A sketch passes validation iff:
    1. `SKETCH.md` exists and has YAML frontmatter parseable by pydantic.
    2. Every `test_data` path in the frontmatter has a corresponding file on disk.
    3. Every `expected_output` path in the frontmatter has a corresponding file.
    4. Every file under `test_data/` or `expected_output/` is referenced in
       the frontmatter (no orphans).
    5. The total bytes under `test_data/` + `expected_output/` is <= 5 MB.
    6. Sketch `name` is globally unique across the corpus.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import frontmatter as fm_lib
import yaml

from .generate.sketch_writer import MAX_BUNDLED_BYTES
from .schema import Sketch, SketchFrontmatter


@dataclass
class ValidationIssue:
    sketch_dir: Path
    code: str
    message: str

    def __str__(self) -> str:
        return f"[{self.code}] {self.sketch_dir}: {self.message}"


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)
    sketches_checked: int = 0

    @property
    def ok(self) -> bool:
        return not self.issues

    def add(self, issue: ValidationIssue) -> None:
        self.issues.append(issue)


def load_sketch(sketch_dir: Path) -> Sketch:
    md_path = sketch_dir / "SKETCH.md"
    if not md_path.exists():
        raise FileNotFoundError(md_path)
    post = fm_lib.load(str(md_path))
    fm = SketchFrontmatter.model_validate(post.metadata)
    return Sketch(directory=sketch_dir, frontmatter=fm, body=post.content)


def validate_sketch(sketch_dir: Path, report: ValidationReport) -> None:
    report.sketches_checked += 1
    try:
        sketch = load_sketch(sketch_dir)
    except FileNotFoundError:
        report.add(ValidationIssue(sketch_dir, "MISSING_SKETCH_MD", "no SKETCH.md"))
        return
    except (yaml.YAMLError, ValueError) as e:
        report.add(ValidationIssue(sketch_dir, "BAD_FRONTMATTER", str(e)))
        return

    fm = sketch.frontmatter
    declared: set[str] = set()

    for td in fm.test_data:
        declared.add(td.path)
        if not (sketch_dir / td.path).exists():
            report.add(
                ValidationIssue(
                    sketch_dir, "TEST_DATA_MISSING", f"declared file not on disk: {td.path}"
                )
            )

    for eo in fm.expected_output:
        declared.add(eo.path)
        if not (sketch_dir / eo.path).exists():
            report.add(
                ValidationIssue(
                    sketch_dir,
                    "EXPECTED_OUTPUT_MISSING",
                    f"declared file not on disk: {eo.path}",
                )
            )

    for sub in ("test_data", "expected_output"):
        sub_dir = sketch_dir / sub
        if not sub_dir.is_dir():
            continue
        for f in sub_dir.rglob("*"):
            if not f.is_file():
                continue
            rel = f.relative_to(sketch_dir).as_posix()
            if rel not in declared:
                report.add(
                    ValidationIssue(
                        sketch_dir, "ORPHAN_FILE", f"file on disk not in frontmatter: {rel}"
                    )
                )

    total_bytes = _bundle_bytes(sketch_dir)
    if total_bytes > MAX_BUNDLED_BYTES:
        report.add(
            ValidationIssue(
                sketch_dir,
                "BUNDLE_TOO_BIG",
                f"test_data + expected_output = {total_bytes} bytes > {MAX_BUNDLED_BYTES}",
            )
        )


def validate_corpus(sketches_root: Path) -> ValidationReport:
    report = ValidationReport()
    seen_names: dict[str, Path] = {}
    for md in sorted(sketches_root.rglob("SKETCH.md")):
        sketch_dir = md.parent
        validate_sketch(sketch_dir, report)
        # duplicate-name check
        try:
            sketch = load_sketch(sketch_dir)
        except Exception:
            continue
        name = sketch.frontmatter.name
        if name in seen_names:
            report.add(
                ValidationIssue(
                    sketch_dir,
                    "DUPLICATE_NAME",
                    f"name `{name}` also defined in {seen_names[name]}",
                )
            )
        else:
            seen_names[name] = sketch_dir
    return report


def _bundle_bytes(sketch_dir: Path) -> int:
    total = 0
    for sub in ("test_data", "expected_output"):
        sub_dir = sketch_dir / sub
        if not sub_dir.is_dir():
            continue
        for f in sub_dir.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
    return total
