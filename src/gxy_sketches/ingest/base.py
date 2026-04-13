"""Ingestor protocol + shared helpers.

An ingestor clones (or updates) a source repo into `workflows_cache/` and
yields one `WorkflowRecord` per workflow/pipeline. Adding a new ecosystem
is purely additive — implement `discover()` and register in `cli.py`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable, Protocol

from ..schema import WorkflowFile, WorkflowRecord


class Ingestor(Protocol):
    ecosystem: str

    def discover(self, cache_root: Path) -> Iterable[WorkflowRecord]: ...


def ensure_clone(repo_url: str, dest: Path, depth: int = 1) -> Path:
    """Shallow-clone or fast-forward a git repo.

    Writes go to `dest`. If `dest` already exists and is a git checkout, we
    `git fetch --depth=1 && git reset --hard origin/HEAD`. Otherwise clone.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    if (dest / ".git").exists():
        subprocess.run(
            ["git", "-C", str(dest), "fetch", "--depth", str(depth), "origin"],
            check=True,
        )
        head = subprocess.run(
            ["git", "-C", str(dest), "rev-parse", "--abbrev-ref", "origin/HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        subprocess.run(
            ["git", "-C", str(dest), "reset", "--hard", head],
            check=True,
        )
    else:
        subprocess.run(
            ["git", "clone", "--depth", str(depth), repo_url, str(dest)],
            check=True,
        )
    return dest


def read_file_if_exists(path: Path, max_bytes: int = 200_000) -> WorkflowFile | None:
    """Read a text file into a WorkflowFile; skip if missing or too big."""
    if not path.exists() or not path.is_file():
        return None
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) > max_bytes:
        data = data[:max_bytes] + b"\n... [truncated]\n"
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return WorkflowFile(relative_path=str(path), content=text)


def collect_files(root: Path, relative_paths: list[str]) -> list[WorkflowFile]:
    """Read an explicit list of files relative to `root`, skipping missing ones.

    The returned `WorkflowFile.relative_path` is kept relative to `root` so
    the generator sees stable paths regardless of where the cache lives.
    """
    out: list[WorkflowFile] = []
    for rel in relative_paths:
        p = root / rel
        wf = read_file_if_exists(p)
        if wf is None:
            continue
        out.append(WorkflowFile(relative_path=rel, content=wf.content))
    return out
