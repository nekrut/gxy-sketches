"""Ingest Galaxy Intergalactic Workflow Commission (IWC) workflows.

The IWC repo layout is one directory per workflow under `workflows/<category>/<name>/`.
Each leaf workflow dir typically contains:
    - <name>.ga           Galaxy Workflow Format 2 (JSON)
    - <name>-tests.yml    planemo test spec
    - README.md / CHANGELOG.md
    - test-data/          small inputs used by the planemo tests

Planemo test YAML shape (relevant parts):

    - doc: ...
      job:
        <label>:
          class: File
          location: https://zenodo.org/.../file.fasta.gz?download=1
          filetype: fasta.gz
          hashes:
            - {hash_function: SHA-1, hash_value: abcdef...}
        <label>:
          class: Collection
          collection_type: list:paired
          elements:
            - class: Collection
              type: paired
              identifier: ERR018930
              elements:
                - class: File
                  identifier: forward
                  location: https://.../ERR018930_forward.fastqsanger.gz
                  hashes: [...]
                - class: File
                  identifier: reverse
                  ...
      outputs:
        <label>:
          path: test-data/expected.tabular          # local golden
        <label>:
          asserts:                                  # inline assertion-only
            - has_line: {line: "..."}
        <label>:
          element_tests:                            # per-element asserts (collection)
            ERR018930:
              asserts: [...]
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import yaml

from ..schema import (
    ExpectedOutputRef,
    TestDataRef,
    TestManifest,
    WorkflowFile,
    WorkflowRecord,
)
from .base import ensure_clone, read_file_if_exists


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
            try:
                record = self._build_record(repo, wf_dir, ga_file)
            except Exception:
                # One malformed workflow must never poison whole-repo discovery.
                continue
            if record is not None:
                yield record

    def _build_record(
        self, repo: Path, wf_dir: Path, ga_file: Path
    ) -> WorkflowRecord | None:
        dir_slug = wf_dir.relative_to(repo / "workflows").as_posix().replace("/", "--")
        # If the workflow dir contains more than one .ga file, each represents
        # a distinct workflow variant — disambiguate the slug with the .ga
        # basename so we don't collapse them into one WorkflowRecord.
        sibling_ga = sorted(wf_dir.glob("*.ga"))
        if len(sibling_ga) > 1:
            slug = f"{dir_slug}--{ga_file.stem}"
        else:
            slug = dir_slug
        display_name = self._extract_name(ga_file) or wf_dir.name

        files: list[WorkflowFile] = []
        ga = read_file_if_exists(ga_file)
        if ga is not None:
            files.append(
                WorkflowFile(
                    relative_path=ga_file.relative_to(repo).as_posix(),
                    content=ga.content,
                )
            )
        for rel in ("README.md", "CHANGELOG.md"):
            wf = read_file_if_exists(wf_dir / rel)
            if wf is not None:
                files.append(
                    WorkflowFile(
                        relative_path=(wf_dir / rel).relative_to(repo).as_posix(),
                        content=wf.content,
                    )
                )

        # Match test yml to its ga file by basename when possible; otherwise
        # take the first one (IWC convention is one test file per workflow).
        test_yml_path: Path | None = None
        ga_stem = ga_file.stem
        candidates = sorted(wf_dir.glob("*-tests.yml"))
        paired = [t for t in candidates if t.name.startswith(ga_stem + "-")]
        chosen = paired[0] if paired else (candidates[0] if candidates else None)
        if chosen is not None:
            wf = read_file_if_exists(chosen)
            if wf is not None:
                files.append(
                    WorkflowFile(
                        relative_path=chosen.relative_to(repo).as_posix(),
                        content=wf.content,
                    )
                )
            test_yml_path = chosen

        test_manifest = (
            self._parse_test_yml(test_yml_path, wf_dir) if test_yml_path else None
        )

        version = self._extract_version(ga_file)
        license_ = self._extract_license(ga_file)

        source_url = (
            f"https://github.com/galaxyproject/iwc/tree/main/"
            f"{wf_dir.relative_to(repo).as_posix()}"
        )

        return WorkflowRecord(
            ecosystem="iwc",
            slug=slug,
            display_name=display_name,
            source_url=source_url,
            version=version,
            license=license_,
            files=files,
            test_manifest=test_manifest,
            raw_root=wf_dir,
        )

    # ----- planemo test parser -----

    def _parse_test_yml(self, test_yml: Path, wf_dir: Path) -> TestManifest | None:
        """Best-effort parse. Any failure yields `None` rather than propagating —
        the goal is to never break whole-repo discovery just because one
        workflow has an unusual planemo spec.
        """
        try:
            raw = yaml.safe_load(test_yml.read_text())
            if not isinstance(raw, list) or not raw:
                return None
            first = raw[0]
            if not isinstance(first, dict):
                return None

            inputs: list[TestDataRef] = []
            for label, spec in (first.get("job") or {}).items():
                inputs.extend(_flatten_job_entry(label, spec))

            outputs: list[ExpectedOutputRef] = []
            output_source_map: dict[str, Path] = {}
            for label, spec in (first.get("outputs") or {}).items():
                try:
                    ref, src = _parse_output_entry(label, spec, wf_dir)
                except Exception:
                    continue
                if ref is not None:
                    outputs.append(ref)
                    if src is not None and ref.path is not None:
                        output_source_map[ref.path] = src

            if not inputs and not outputs:
                return None
            return TestManifest(
                inputs=inputs, outputs=outputs, output_source_map=output_source_map
            )
        except Exception:
            return None

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
        return data.get("release") or data.get("version")

    @staticmethod
    def _extract_license(ga_file: Path) -> str | None:
        try:
            data = json.loads(ga_file.read_text())
        except (OSError, json.JSONDecodeError):
            return None
        return data.get("license")


def _flatten_job_entry(label: str, spec: Any, role_prefix: str = "") -> list[TestDataRef]:
    """Recursively flatten a planemo `job:` entry into one TestDataRef per File."""
    out: list[TestDataRef] = []
    if not isinstance(spec, dict):
        return out
    klass = spec.get("class")
    base_role = role_prefix + _sluggify(label) if role_prefix else _sluggify(label)

    if klass == "File":
        ref = _file_spec_to_ref(role=base_role, spec=spec)
        if ref is not None:
            out.append(ref)
        return out

    if klass == "Collection":
        for elem in spec.get("elements") or []:
            if not isinstance(elem, dict):
                continue
            elem_id = elem.get("identifier") or elem.get("name") or "elem"
            out.extend(
                _flatten_job_entry(str(elem_id), elem, role_prefix=base_role + "__")
            )
        return out

    # Unknown / missing class — ignore (some planemo files encode inline
    # parameter values that aren't data files).
    return out


def _file_spec_to_ref(role: str, spec: dict) -> TestDataRef | None:
    """Return a TestDataRef, or None if the spec has no retrievable source."""
    url = spec.get("location") or None
    if url is not None and not isinstance(url, str):
        url = None
    if not url:
        return None  # planemo entry without a URL can't be materialized here
    sha1 = None
    for h in spec.get("hashes") or []:
        if isinstance(h, dict) and str(h.get("hash_function", "")).upper() in (
            "SHA-1",
            "SHA1",
        ):
            sha1 = h.get("hash_value")
            break
    filetype = spec.get("filetype")
    return TestDataRef(
        role=role,
        url=url,
        path=None,
        sha1=sha1,
        filetype=filetype,
        description=None,
    )


def _parse_output_entry(
    label: str, spec: Any, wf_dir: Path
) -> tuple[ExpectedOutputRef | None, Path | None]:
    """Return (expected_output_ref, local_source_path_for_copy_or_None)."""
    if not isinstance(spec, dict):
        return None, None
    role = _sluggify(label)

    source_path: Path | None = None
    local_path: str | None = None
    path_str = spec.get("path")
    if isinstance(path_str, str):
        candidate = (wf_dir / path_str).resolve()
        if candidate.exists() and candidate.is_file():
            source_path = candidate
            local_path = f"expected_output/{candidate.name}"

    assertions: list[str] = _flatten_asserts(spec)

    if not source_path and not assertions:
        return None, None

    return (
        ExpectedOutputRef(
            role=role,
            path=local_path,
            kind=None,
            description=(
                f"Expected output `{label}` from the source workflow test."
                if not assertions
                else f"Content assertions for `{label}`."
            ),
            assertions=assertions,
        ),
        source_path,
    )


def _flatten_asserts(spec: dict) -> list[str]:
    out: list[str] = []
    asserts = spec.get("asserts")
    if asserts is not None:
        out.extend(_render_asserts(asserts))
    element_tests = spec.get("element_tests") or {}
    if isinstance(element_tests, dict):
        for elem_id, sub in element_tests.items():
            if not isinstance(sub, dict):
                continue
            for rendered in _render_asserts(sub.get("asserts")):
                out.append(f"{elem_id}: {rendered}")
    return out


def _render_asserts(asserts: Any) -> list[str]:
    if asserts is None:
        return []
    if isinstance(asserts, dict):
        asserts = [asserts]
    if not isinstance(asserts, list):
        return []
    out: list[str] = []
    for a in asserts:
        if not isinstance(a, dict):
            continue
        for check, payload in a.items():
            if isinstance(payload, dict):
                val = payload.get("line") or payload.get("text") or str(payload)
            else:
                val = str(payload)
            out.append(f"{check}: {val}")
    return out


def _sluggify(text: str) -> str:
    import re

    s = re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")
    return s or "x"
