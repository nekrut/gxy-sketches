"""Unit tests for the nf-core ingestor's tool-version parser.

We don't exercise the HTTP catalog or git clone path — those are touched
end-to-end in the real ingest runs. This file covers the deterministic
bits the generator cares about: parsing `container` directives out of
`modules/nf-core/*/main.nf` files.
"""

from __future__ import annotations

from pathlib import Path

from gxy_sketches.ingest.nf_core import _extract_container_version, _scan_modules_tool_versions


BIOCONTAINER_MAIN_NF = """\
process FASTP {
    tag "$meta.id"
    label 'process_medium'

    conda "bioconda::fastp=0.23.4"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/fastp:0.23.4--h5f740d0_1' :
        'biocontainers/fastp:0.23.4--h5f740d0_1' }"

    input:
    tuple val(meta), path(reads)
}
"""


NO_CONTAINER_MAIN_NF = """\
process LOCAL {
    script: 'echo hi'
}
"""


def test_extract_container_version_biocontainer() -> None:
    assert _extract_container_version(BIOCONTAINER_MAIN_NF) == "0.23.4"


def test_extract_container_version_missing() -> None:
    assert _extract_container_version(NO_CONTAINER_MAIN_NF) is None


def test_scan_modules_walks_tool_tree(tmp_path: Path) -> None:
    root = tmp_path / "modules" / "nf-core"
    (root / "fastp").mkdir(parents=True)
    (root / "fastp" / "main.nf").write_text(BIOCONTAINER_MAIN_NF)

    (root / "samtools" / "sort").mkdir(parents=True)
    samtools_sort = (
        'container "quay.io/biocontainers/samtools:1.21--h96c455f_1"\n'
    )
    (root / "samtools" / "sort" / "main.nf").write_text(samtools_sort)

    (root / "empty").mkdir()
    (root / "empty" / "main.nf").write_text(NO_CONTAINER_MAIN_NF)

    versions = _scan_modules_tool_versions(tmp_path)
    assert versions["fastp"] == "0.23.4"
    assert versions["sort"] == "1.21"
    assert "empty" not in versions  # no version, skipped
