"""Tests for the LLM-facing generator with a mocked Anthropic client."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock

from gxy_sketches.generate.llm import SketchGenerator
from gxy_sketches.generate.sketch_writer import write_sketch
from gxy_sketches.ingest.iwc import IwcIngestor


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "iwc_sample"


# The LLM is no longer asked to emit source/test_data/expected_output —
# those are filled in from the ingestor's parsed manifest.
VALID_PAYLOAD = {
    "frontmatter": {
        "name": "haploid-variant-calling-bacterial",
        "description": "Use when you need to call SNVs and small indels against a haploid bacterial reference from short-read Illumina data.",
        "domain": "variant-calling",
        "organism_class": ["bacterial", "haploid"],
        "input_data": ["short-reads-paired", "reference-fasta"],
        "tools": ["bwa-mem2", "bcftools"],
        "tags": ["bacteria", "snv"],
    },
    "body": (
        "# Haploid bacterial variant calling\n\n"
        "## When to use this sketch\n- Bacteria\n\n"
        "## Test data\nParsed from the source planemo manifest.\n"
    ),
}


@dataclass
class _Block:
    text: str


@dataclass
class _Response:
    content: list[_Block]


def _mock_client(payload: dict) -> MagicMock:
    client = MagicMock()
    client.messages.create.return_value = _Response(content=[_Block(text=json.dumps(payload))])
    return client


def _fixture_record(monkeypatch):
    """Build a real WorkflowRecord from the checked-in IWC fixture."""
    ingestor = IwcIngestor()
    monkeypatch.setattr(
        "gxy_sketches.ingest.iwc.ensure_clone",
        lambda repo_url, dest: FIXTURE_ROOT,
    )
    return next(iter(ingestor.discover(cache_root=Path("/tmp/unused"))))


def test_generate_uses_parsed_manifest_for_test_data(tmp_path, monkeypatch) -> None:
    record = _fixture_record(monkeypatch)
    assert record.test_manifest is not None
    # sanity: manifest has both URL inputs and a local expected-output path
    assert any(i.url for i in record.test_manifest.inputs)
    assert any(o.path for o in record.test_manifest.outputs)

    client = _mock_client(VALID_PAYLOAD)
    gen = SketchGenerator(client=client)
    generated = gen.generate(record)

    # Source fields were back-filled from the record, not the LLM payload.
    assert generated.frontmatter.source.ecosystem == "iwc"
    assert generated.frontmatter.source.version == "0.1.2"
    assert generated.frontmatter.source.license == "MIT"

    # test_data / expected_output were lifted from the parsed manifest.
    roles = {td.role for td in generated.frontmatter.test_data}
    assert "reference" in roles
    output_roles = {eo.role for eo in generated.frontmatter.expected_output}
    assert "annotated_variants" in output_roles


def test_write_materializes_remote_and_local(tmp_path, monkeypatch) -> None:
    record = _fixture_record(monkeypatch)
    client = _mock_client(VALID_PAYLOAD)
    gen = SketchGenerator(client=client)
    generated = gen.generate(record)

    target = write_sketch(generated, record, tmp_path / "sketches")
    assert (target / "SKETCH.md").exists()
    # URL-only inputs get a README manifest instead of per-file bundles.
    assert (target / "test_data" / "README.md").exists()
    # Local expected output was copied from the fixture's test-data dir.
    assert (target / "expected_output" / "expected_variants.tabular").exists()
    # Assertion-only output → ASSERTIONS.md stub.
    assert (target / "expected_output" / "ASSERTIONS.md").exists()


def test_generator_passes_cache_control_on_system_prompt() -> None:
    client = _mock_client(VALID_PAYLOAD)
    gen = SketchGenerator(client=client)
    # Minimal record with no manifest — the cache_control assertion doesn't
    # depend on the ingestor shape.
    from gxy_sketches.schema import WorkflowRecord

    record = WorkflowRecord(
        ecosystem="iwc",
        slug="w",
        display_name="W",
        source_url="https://example.com",
        raw_root=Path("/tmp"),
    )
    gen.generate(record)
    call = client.messages.create.call_args
    system = call.kwargs["system"]
    assert isinstance(system, list)
    assert system[0]["cache_control"] == {"type": "ephemeral"}
