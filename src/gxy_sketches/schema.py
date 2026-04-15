"""Pydantic models that form the machine-readable contract for sketches.

`WorkflowRecord` — what an ingestor produces for the generator.
`SketchFrontmatter` — what the generator writes into each `SKETCH.md`.
`Sketch` — an in-memory representation of a loaded sketch directory.
`TestManifest` — the structured input/output manifest a parser lifts from a
source workflow's test spec (e.g. planemo `*-tests.yml`), used by the
sketch writer authoritatively so the LLM never has to hallucinate filenames.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


Ecosystem = Literal["nf-core", "iwc", "snakemake-workflows", "wdl"]


class WorkflowFile(BaseModel):
    """One file harvested from a source workflow (e.g., README.md, nextflow_schema.json).

    Content is inlined so that the generator can pass it straight to the LLM
    without a second filesystem round-trip.
    """

    model_config = ConfigDict(frozen=True)

    relative_path: str
    content: str


class TestDataRef(BaseModel):
    """One input declared by a sketch.

    Must have either a local `path` under `test_data/` (copied into the
    sketch directory) OR a remote `url` (fetched at run-time). Both may be
    set; the validator treats local as authoritative if so.
    """

    __test__ = False  # pytest, don't collect me

    model_config = ConfigDict(extra="forbid")

    role: str
    path: str | None = None
    url: str | None = None
    sha1: str | None = None
    filetype: str | None = None
    description: str | None = None

    @field_validator("path")
    @classmethod
    def _path_must_live_under_test_data(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if v.startswith("/") or ".." in Path(v).parts:
            raise ValueError(f"test_data path must be relative and inside the sketch dir: {v}")
        if not v.startswith("test_data/"):
            raise ValueError(f"test_data path must live under test_data/: {v}")
        return v

    @model_validator(mode="after")
    def _require_path_or_url(self) -> "TestDataRef":
        if not self.path and not self.url:
            raise ValueError(f"test data ref `{self.role}` needs either path or url")
        return self


class ExpectedOutputRef(BaseModel):
    """One expected output declared by a sketch.

    Must have at least one of: local `path` under `expected_output/`, a
    remote `url`, or non-empty `assertions` (human-readable content claims,
    e.g. "VCF contains line NC_009906.1:3204 A>G").
    """

    model_config = ConfigDict(extra="forbid")

    role: str | None = None
    path: str | None = None
    url: str | None = None
    kind: str | None = None
    description: str
    assertions: list[str] = Field(default_factory=list)

    @field_validator("path")
    @classmethod
    def _path_must_live_under_expected_output(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if v.startswith("/") or ".." in Path(v).parts:
            raise ValueError(f"expected_output path must be relative and inside the sketch dir: {v}")
        if not v.startswith("expected_output/"):
            raise ValueError(f"expected_output path must live under expected_output/: {v}")
        return v

    @model_validator(mode="after")
    def _require_at_least_one_anchor(self) -> "ExpectedOutputRef":
        if not self.path and not self.url and not self.assertions:
            raise ValueError(
                "expected output needs at least one of: path, url, or assertions"
            )
        return self


class ToolSpec(BaseModel):
    """One tool used by a sketch, with optional pinned version.

    Accepts a bare string in input (for backward compat with pre-version
    sketches); always serialises as a structured object.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    version: str | None = None


class TestManifest(BaseModel):
    __test__ = False  # stop pytest from treating this as a test class

    """Structured view of a source workflow's test spec.

    Populated by an ingestor from the ecosystem's native test format
    (planemo `*-tests.yml`, nf-core `conf/test.config`, …) and attached to
    a `WorkflowRecord`. The sketch writer uses it as the authoritative
    source for frontmatter `test_data` / `expected_output`.
    """

    inputs: list[TestDataRef] = Field(default_factory=list)
    outputs: list[ExpectedOutputRef] = Field(default_factory=list)
    # For IWC outputs whose `path:` points at a file that lives in the
    # source workflow's own test-data/ dir, we record the absolute source
    # path so the writer can copy it into `expected_output/` of the sketch.
    output_source_map: dict[str, Path] = Field(default_factory=dict)


class WorkflowRecord(BaseModel):
    """Everything an ingestor knows about one source workflow.

    This is the unit the generator consumes to produce a sketch. It bundles
    the metadata the LLM needs (description, README, schema) *and* a
    structured `TestManifest` the writer uses to materialize the bundled
    test inputs / expected outputs without round-tripping file names
    through the LLM.
    """

    ecosystem: Ecosystem
    slug: str
    display_name: str
    source_url: str
    version: str | None = None
    license: str | None = None
    files: list[WorkflowFile] = Field(default_factory=list)
    test_manifest: TestManifest | None = None
    tool_versions: dict[str, str] = Field(default_factory=dict)
    raw_root: Path

    def metadata_bundle(self) -> str:
        """Render the harvested files + test manifest as a string for the LLM."""
        parts = [
            f"# Workflow: {self.display_name}",
            f"Ecosystem: {self.ecosystem}",
            f"Source: {self.source_url}",
            f"Version: {self.version or 'unknown'}",
            f"License: {self.license or 'unknown'}",
            "",
        ]
        for f in self.files:
            parts.append(f"## FILE: {f.relative_path}")
            parts.append("```")
            parts.append(f.content)
            parts.append("```")
            parts.append("")
        if self.test_manifest is not None:
            parts.append("## PARSED TEST MANIFEST")
            parts.append(
                "The following inputs and expected outputs were parsed from the "
                "source workflow's test spec. You do NOT need to include "
                "`test_data` or `expected_output` in the frontmatter — the "
                "caller fills them in from this manifest. Describe them in the "
                "`## Test data` body section in prose."
            )
            parts.append("")
            parts.append("### Inputs")
            for inp in self.test_manifest.inputs:
                loc = inp.path or inp.url or "?"
                parts.append(f"- role={inp.role}  ({inp.filetype or '?'}) -> {loc}")
            parts.append("")
            parts.append("### Expected outputs")
            for out in self.test_manifest.outputs:
                loc = out.path or out.url or "(assertions only)"
                asserts = f"  assertions: {len(out.assertions)}" if out.assertions else ""
                parts.append(
                    f"- {out.role or '?'}  {out.kind or ''} -> {loc}{asserts}"
                )
                for a in out.assertions[:4]:
                    parts.append(f"    * {a}")
            parts.append("")
        return "\n".join(parts)


class SketchSource(BaseModel):
    ecosystem: Ecosystem
    workflow: str
    url: str
    version: str | None = None
    license: str | None = None
    slug: str | None = None  # ingestor slug so backfill/dedup can round-trip


class SketchFrontmatter(BaseModel):
    """The YAML frontmatter block of every SKETCH.md."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", min_length=3, max_length=80)
    description: str = Field(min_length=30, max_length=600)
    domain: str
    organism_class: list[str] = Field(default_factory=list)
    input_data: list[str] = Field(default_factory=list)
    source: SketchSource
    tools: list[ToolSpec] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    test_data: list[TestDataRef] = Field(default_factory=list)
    expected_output: list[ExpectedOutputRef] = Field(default_factory=list)

    @field_validator("tools", mode="before")
    @classmethod
    def _tools_accept_bare_strings(cls, v: object) -> object:
        """Backward compat: let existing sketches load with `tools: [str, ...]`."""
        if isinstance(v, list):
            return [{"name": x} if isinstance(x, str) else x for x in v]
        return v


class Sketch(BaseModel):
    """A loaded-from-disk sketch directory."""

    directory: Path
    frontmatter: SketchFrontmatter
    body: str

    @property
    def sketch_md(self) -> Path:
        return self.directory / "SKETCH.md"

    @property
    def test_data_dir(self) -> Path:
        return self.directory / "test_data"

    @property
    def expected_output_dir(self) -> Path:
        return self.directory / "expected_output"
