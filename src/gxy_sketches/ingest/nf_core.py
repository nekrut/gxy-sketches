"""Ingest nf-core pipelines.

Strategy for v1:
    * Query the nf-core pipelines catalog JSON (https://nf-co.re/pipelines.json)
      to enumerate pipelines and their metadata (name, description, latest release).
    * For each pipeline, shallow-clone into `workflows_cache/nf-core/<name>/`.
    * Harvest the metadata bundle: README, docs/usage.md, docs/output.md,
      nextflow_schema.json, .nf-core.yml, CITATIONS.md.
    * Record the `conf/test.config` profile so the generator knows where the
      pipeline's small test data lives.
    * Walk `modules/nf-core/**/main.nf` and parse `container` directives to
      produce a {tool_name -> version} map for `WorkflowRecord.tool_versions`.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import httpx

from ..schema import WorkflowFile, WorkflowRecord
from .base import collect_files, ensure_clone


NF_CORE_CATALOG_URL = "https://nf-co.re/pipelines.json"


NF_CORE_METADATA_FILES = [
    "README.md",
    "CITATIONS.md",
    "nextflow_schema.json",
    ".nf-core.yml",
    "docs/usage.md",
    "docs/output.md",
    "conf/test.config",
    "conf/test_full.config",
]


class NfCoreIngestor:
    ecosystem = "nf-core"

    def __init__(
        self,
        catalog_url: str = NF_CORE_CATALOG_URL,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.catalog_url = catalog_url
        self._client = http_client or httpx.Client(timeout=30.0, follow_redirects=True)

    def discover(self, cache_root: Path) -> Iterable[WorkflowRecord]:
        catalog = self._fetch_catalog()
        for entry in catalog:
            record = self._ingest_pipeline(entry, cache_root)
            if record is not None:
                yield record

    def _fetch_catalog(self) -> list[dict]:
        resp = self._client.get(self.catalog_url)
        resp.raise_for_status()
        data = resp.json()
        # nf-co.re returns an object with a "remote_workflows" list
        if isinstance(data, dict):
            return data.get("remote_workflows") or data.get("pipelines") or []
        if isinstance(data, list):
            return data
        return []

    def _ingest_pipeline(self, entry: dict, cache_root: Path) -> WorkflowRecord | None:
        name = entry.get("name")
        if not name:
            return None
        full_name = entry.get("full_name") or f"nf-core/{name}"
        clone_url = entry.get("clone_url") or f"https://github.com/{full_name}.git"

        dest = cache_root / "nf-core" / name
        try:
            ensure_clone(clone_url, dest)
        except Exception:
            return None

        files = collect_files(dest, NF_CORE_METADATA_FILES)
        if not files:
            return None

        tool_versions = _scan_modules_tool_versions(dest)

        version = self._latest_release(entry)
        license_ = entry.get("license") or "MIT"

        # nf-core test data lives in the nf-core/test-datasets repo on a
        # per-pipeline branch and is referenced by URL (and by samplesheet
        # CSV one level in) from `conf/test.config`. v1 does not build a
        # TestManifest for nf-core — the generator will emit sketches with
        # empty test_data/expected_output and describe the test profile in
        # the body prose. v2 can add a samplesheet + nextflow.config parser.
        return WorkflowRecord(
            ecosystem="nf-core",
            slug=name,
            display_name=full_name,
            source_url=f"https://github.com/{full_name}",
            version=version,
            license=license_,
            files=files,
            test_manifest=None,
            tool_versions=tool_versions,
            raw_root=dest,
        )

    @staticmethod
    def _latest_release(entry: dict) -> str | None:
        releases = entry.get("releases") or []
        if not releases:
            return None
        # catalog entries typically list releases newest-first
        latest = releases[0]
        if isinstance(latest, dict):
            return latest.get("tag_name") or latest.get("name")
        return str(latest)


# `container "...biocontainers/fastp:0.23.4--h5f740d0_1..."` or
# `container 'quay.io/biocontainers/samtools:1.21--h96c455f_1'`
_CONTAINER_RE = re.compile(r"biocontainers/([A-Za-z0-9_.\-]+):([^'\"\s}]+)")
# Also match the singularity fallback depot.galaxyproject.org URL
_DEPOT_RE = re.compile(r"depot\.galaxyproject\.org/singularity/([A-Za-z0-9_.\-]+):([^'\"\s}]+)")


def _scan_modules_tool_versions(pipeline_root: Path) -> dict[str, str]:
    """Parse every `modules/nf-core/**/main.nf` for container version pins.

    Returns a dict keyed by tool directory name (lower-case, dots and
    underscores preserved), value is the container tag after the colon
    (cleaned of trailing build hashes like `--h5f740d0_1`).
    """
    out: dict[str, str] = {}
    modules_root = pipeline_root / "modules" / "nf-core"
    if not modules_root.is_dir():
        return out
    for main_nf in modules_root.rglob("main.nf"):
        tool_dir = main_nf.parent.name.lower()
        if not tool_dir:
            continue
        try:
            text = main_nf.read_text()
        except OSError:
            continue
        version = _extract_container_version(text)
        if version is None:
            continue
        # If multiple matches per tool, keep the first non-empty one.
        out.setdefault(tool_dir, version)
    return out


def _extract_container_version(main_nf_text: str) -> str | None:
    for rx in (_CONTAINER_RE, _DEPOT_RE):
        m = rx.search(main_nf_text)
        if m is None:
            continue
        raw = m.group(2)
        # Strip the conda-build hash suffix after `--` to get "0.23.4"
        version = raw.split("--", 1)[0]
        # And strip any trailing quote/bracket just in case
        version = version.rstrip("'\"}")
        if version:
            return version
    return None
