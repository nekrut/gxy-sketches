"""Pydantic models that form the machine-readable contract for sketches.

`WorkflowRecord` — what an ingestor produces for the generator.
`SketchFrontmatter` — what the generator writes into each `SKETCH.md`.
`Sketch` — an in-memory representation of a loaded sketch directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Ecosystem = Literal["nf-core", "iwc", "snakemake-workflows", "wdl"]


class WorkflowFile(BaseModel):
    """One file harvested from a source workflow (e.g., README.md, nextflow_schema.json).

    Content is inlined so that the generator can pass it straight to the LLM
    without a second filesystem round-trip.
    """

    model_config = ConfigDict(frozen=True)

    relative_path: str
    content: str


class WorkflowRecord(BaseModel):
    """Everything an ingestor knows about one source workflow.

    This is the unit the generator consumes to produce a sketch. It bundles
    the metadata the LLM needs (description, README, schema) *and* pointers to
    any test data the ingestor located in the source repo.
    """

    ecosystem: Ecosystem
    slug: str
    display_name: str
    source_url: str
    version: str | None = None
    license: str | None = None
    files: list[WorkflowFile] = Field(default_factory=list)
    test_data_paths: list[Path] = Field(default_factory=list)
    raw_root: Path

    def metadata_bundle(self) -> str:
        """Render the harvested files as a single string for the LLM user turn."""
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
        return "\n".join(parts)


class TestDataRef(BaseModel):
    __test__ = False  # stop pytest from treating this as a test class

    path: str
    role: str

    @field_validator("path")
    @classmethod
    def _no_escape(cls, v: str) -> str:
        if v.startswith("/") or ".." in Path(v).parts:
            raise ValueError(f"test_data path must be relative and inside the sketch dir: {v}")
        if not v.startswith("test_data/"):
            raise ValueError(f"test_data path must live under test_data/: {v}")
        return v


class ExpectedOutputRef(BaseModel):
    path: str
    kind: str
    description: str

    @field_validator("path")
    @classmethod
    def _no_escape(cls, v: str) -> str:
        if v.startswith("/") or ".." in Path(v).parts:
            raise ValueError(f"expected_output path must be relative and inside the sketch dir: {v}")
        if not v.startswith("expected_output/"):
            raise ValueError(f"expected_output path must live under expected_output/: {v}")
        return v


class SketchSource(BaseModel):
    ecosystem: Ecosystem
    workflow: str
    url: str
    version: str | None = None
    license: str | None = None


class SketchFrontmatter(BaseModel):
    """The YAML frontmatter block of every SKETCH.md."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", min_length=3, max_length=80)
    description: str = Field(min_length=30, max_length=600)
    domain: str
    organism_class: list[str] = Field(default_factory=list)
    input_data: list[str] = Field(default_factory=list)
    source: SketchSource
    tools: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    test_data: list[TestDataRef] = Field(default_factory=list)
    expected_output: list[ExpectedOutputRef] = Field(default_factory=list)


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
