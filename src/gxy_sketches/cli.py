"""Typer CLI: ingest, generate, validate, list."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import typer
from rich.console import Console
from rich.table import Table

import os

from .generate.claude_cli import ClaudeCliGenerator
from .generate.llm import SketchGenerator
from .generate.sketch_writer import write_sketch
from .ingest import IwcIngestor, NfCoreIngestor
from .schema import WorkflowRecord
from .validate import load_sketch, validate_corpus

app = typer.Typer(help="gxy-sketches — distill open workflows into skill-like sketches.")
console = Console()


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _cache_root() -> Path:
    return _project_root() / "workflows_cache"


def _sketches_root() -> Path:
    return _project_root() / "sketches"


def _ingestor_for(source: str):
    if source == "iwc":
        return IwcIngestor()
    if source == "nf-core":
        return NfCoreIngestor()
    raise typer.BadParameter(f"unknown source: {source}")


def _build_generator(backend: str):
    if backend == "auto":
        backend = "api" if os.environ.get("ANTHROPIC_API_KEY") else "claude-cli"
    if backend == "api":
        return SketchGenerator()
    if backend == "claude-cli":
        return ClaudeCliGenerator()
    raise typer.BadParameter(f"unknown backend: {backend}")


@app.command()
def ingest(
    source: str = typer.Argument(..., help="iwc | nf-core"),
    limit: int | None = typer.Option(None, help="only process the first N workflows"),
) -> None:
    """Clone (or update) a source repo and report discovered workflows."""
    ingestor = _ingestor_for(source)
    cache = _cache_root()
    cache.mkdir(parents=True, exist_ok=True)
    count = 0
    for record in ingestor.discover(cache):
        console.print(f"[green]•[/green] {record.ecosystem} / {record.slug}  ({record.display_name})")
        count += 1
        if limit is not None and count >= limit:
            break
    console.print(f"[bold]discovered:[/bold] {count} workflows")


@app.command()
def generate(
    source: str = typer.Option(..., help="iwc | nf-core"),
    only: str | None = typer.Option(None, help="slug of a single workflow to process"),
    overwrite: bool = typer.Option(False, help="overwrite existing sketch directories"),
    limit: int | None = typer.Option(None, help="cap number of sketches generated"),
    backend: str = typer.Option(
        "auto",
        help="auto | api | claude-cli. 'auto' picks api if ANTHROPIC_API_KEY is set, else claude-cli.",
    ),
) -> None:
    """Generate sketches for discovered workflows via Claude."""
    ingestor = _ingestor_for(source)
    generator = _build_generator(backend)
    sketches = _sketches_root()
    sketches.mkdir(parents=True, exist_ok=True)
    cache = _cache_root()

    processed = 0
    for record in ingestor.discover(cache):
        if only and record.slug != only:
            continue
        try:
            generated = generator.generate(record)
        except Exception as e:
            console.print(f"[red]✗[/red] {record.slug}: {e}")
            continue
        try:
            target = write_sketch(generated, record, sketches, overwrite=overwrite)
        except FileExistsError as e:
            console.print(f"[yellow]skip[/yellow] {record.slug}: {e}")
            continue
        console.print(f"[green]✓[/green] {record.slug} → {target.relative_to(_project_root())}")
        processed += 1
        if limit is not None and processed >= limit:
            break

    console.print(f"[bold]wrote {processed} sketches[/bold]")


@app.command(name="validate")
def validate_cmd() -> None:
    """Lint the sketch corpus."""
    report = validate_corpus(_sketches_root())
    for issue in report.issues:
        console.print(f"[red]{issue}[/red]")
    console.print(
        f"[bold]{report.sketches_checked} sketches checked, "
        f"{len(report.issues)} issues[/bold]"
    )
    if not report.ok:
        raise typer.Exit(code=1)


@app.command(name="list")
def list_cmd(
    domain: str | None = typer.Option(None, help="filter by domain"),
    source: str | None = typer.Option(None, help="filter by ecosystem"),
) -> None:
    """Tabulate sketches in the corpus."""
    table = Table(title="Sketches")
    table.add_column("name")
    table.add_column("domain")
    table.add_column("source")
    table.add_column("tools")

    for md in sorted(_sketches_root().rglob("SKETCH.md")):
        try:
            sketch = load_sketch(md.parent)
        except Exception:
            continue
        fm = sketch.frontmatter
        if domain and fm.domain != domain:
            continue
        if source and fm.source.ecosystem != source:
            continue
        table.add_row(
            fm.name,
            fm.domain,
            f"{fm.source.ecosystem}/{fm.source.workflow}",
            ", ".join(fm.tools[:4]),
        )
    console.print(table)


if __name__ == "__main__":
    app()
