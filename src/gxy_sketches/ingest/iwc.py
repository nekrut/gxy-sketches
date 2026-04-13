"""Ingest Galaxy Intergalactic Workflow Commission (IWC) workflows.

The IWC repo layout is one directory per workflow under `workflows/<category>/<name>/`.
Each leaf workflow dir typically contains:
    - <name>.ga           Galaxy Workflow Format 2 (JSON)
    - <name>-tests.yml    planemo test spec
    - README.md / CHANGELOG.md
    - test-data/          small inputs used by the planemo tests
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from ..schema import WorkflowFile, WorkflowRecord
from .base import collect_files, ensure_clone, read_file_if_exists


IWC_REPO_URL = "https://github.com/galaxyproject/iwc.git"


class IwcIngestor:
    ecosystem = "iwc"

    def __init__(self, repo_url: str = IWC_REPO_URL) -> None:
        self.repo_url = repo_url

    def discover(self, cache_root: Path) -> Iterable[WorkflowRecord]:
        repo = ensure_clone(self.repo_url, cache_root / "iwc")
        yield from self._walk(repo)

    def _walk(self, repo: Path) -> Iterable[WorkflowRecord]:
        workflows_root = repo / "workflows"
        if not workflows_root.exists():
            return
        for ga_file in sorted(workflows_root.rglob("*.ga")):
            wf_dir = ga_file.parent
            # Skip if this .ga sits above a nested workflow dir (rare)
            if any(p.suffix == ".ga" for p in wf_dir.parent.glob("*.ga")) and wf_dir == workflows_root:
                continue
            record = self._build_record(repo, wf_dir, ga_file)
            if record is not None:
                yield record

    def _build_record(
        self, repo: Path, wf_dir: Path, ga_file: Path
    ) -> WorkflowRecord | None:
        slug = wf_dir.relative_to(repo / "workflows").as_posix().replace("/", "--")
        display_name = self._extract_name(ga_file) or wf_dir.name

        files: list[WorkflowFile] = []
        # Galaxy workflow JSON — truncated inside read helper if huge
        ga = read_file_if_exists(ga_file)
        if ga is not None:
            files.append(
                WorkflowFile(
                    relative_path=ga_file.relative_to(repo).as_posix(),
                    content=ga.content,
                )
            )

        # Standard docs in the workflow dir
        for rel in ("README.md", "CHANGELOG.md"):
            wf = read_file_if_exists(wf_dir / rel)
            if wf is not None:
                files.append(
                    WorkflowFile(
                        relative_path=(wf_dir / rel).relative_to(repo).as_posix(),
                        content=wf.content,
                    )
                )

        # Planemo test spec (describes expected outputs)
        for test_yml in sorted(wf_dir.glob("*-tests.yml")):
            wf = read_file_if_exists(test_yml)
            if wf is not None:
                files.append(
                    WorkflowFile(
                        relative_path=test_yml.relative_to(repo).as_posix(),
                        content=wf.content,
                    )
                )

        # Harvest test_data files (small-by-convention in IWC)
        test_data_paths: list[Path] = []
        test_data_dir = wf_dir / "test-data"
        if test_data_dir.is_dir():
            for f in sorted(test_data_dir.rglob("*")):
                if f.is_file():
                    test_data_paths.append(f)

        version = self._extract_version(ga_file)
        license_ = self._extract_license(ga_file)

        return WorkflowRecord(
            ecosystem="iwc",
            slug=slug,
            display_name=display_name,
            source_url=f"https://github.com/galaxyproject/iwc/tree/main/{wf_dir.relative_to(repo).as_posix()}",
            version=version,
            license=license_,
            files=files,
            test_data_paths=test_data_paths,
            raw_root=wf_dir,
        )

    @staticmethod
    def _extract_name(ga_file: Path) -> str | None:
        try:
            data = json.loads(ga_file.read_text())
        except (OSError, json.JSONDecodeError):
            return None
        return data.get("name")

    @staticmethod
    def _extract_version(ga_file: Path) -> str | None:
        try:
            data = json.loads(ga_file.read_text())
        except (OSError, json.JSONDecodeError):
            return None
        # gxformat2 stores version as release or version
        return data.get("release") or data.get("version")

    @staticmethod
    def _extract_license(ga_file: Path) -> str | None:
        try:
            data = json.loads(ga_file.read_text())
        except (OSError, json.JSONDecodeError):
            return None
        return data.get("license")
