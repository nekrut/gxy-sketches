"""Tests for `_enrich_tools_with_versions` — matches LLM tool names to
parsed source versions via normalised + prefix lookup.
"""

from __future__ import annotations

from gxy_sketches.generate.llm import _enrich_tools_with_versions


SOURCE_VERSIONS = {
    "fastp": "0.23.4+galaxy0",
    "bwa_mem2": "2.2.1+galaxy0",
    "bcftools_call": "1.15.1+galaxy3",
    "bcftools_norm": "1.15.1+galaxy3",
    "samtools_sort": "1.21",
    "multiqc": "1.25.1",
}


def _names(tools: list[dict]) -> set[str]:
    return {t["name"] for t in tools}


def test_exact_match() -> None:
    out = _enrich_tools_with_versions(["fastp", "multiqc"], SOURCE_VERSIONS)
    versions = {t["name"]: t.get("version") for t in out}
    assert versions == {"fastp": "0.23.4+galaxy0", "multiqc": "1.25.1"}


def test_normalised_match_strips_punctuation() -> None:
    out = _enrich_tools_with_versions(["bwa-mem2"], SOURCE_VERSIONS)
    assert out == [{"name": "bwa-mem2", "version": "2.2.1+galaxy0"}]


def test_prefix_match_for_tool_family() -> None:
    out = _enrich_tools_with_versions(["bcftools", "samtools"], SOURCE_VERSIONS)
    versions = {t["name"]: t.get("version") for t in out}
    # Both families share a single version across call/norm/sort.
    assert versions["bcftools"] in {"1.15.1+galaxy3"}
    assert versions["samtools"] == "1.21"


def test_unknown_tool_passes_through_without_version() -> None:
    out = _enrich_tools_with_versions(["mystery-tool"], SOURCE_VERSIONS)
    assert out == [{"name": "mystery-tool"}]


def test_accepts_pre_structured_input() -> None:
    out = _enrich_tools_with_versions(
        [{"name": "fastp"}, {"name": "preset", "version": "9.9.9"}],
        SOURCE_VERSIONS,
    )
    versions = {t["name"]: t.get("version") for t in out}
    assert versions == {"fastp": "0.23.4+galaxy0", "preset": "9.9.9"}
