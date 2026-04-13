"""Tests for the LLM-facing generator with a mocked Anthropic client."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock

from gxy_sketches.generate.llm import SketchGenerator
from gxy_sketches.generate.sketch_writer import write_sketch
from gxy_sketches.schema import WorkflowFile, WorkflowRecord


VALID_PAYLOAD = {
    "frontmatter": {
        "name": "haploid-variant-calling-bacterial",
        "description": "Use when you need to call SNVs and small indels against a haploid bacterial reference from short-read Illumina data.",
        "domain": "variant-calling",
        "organism_class": ["bacterial", "haploid"],
        "input_data": ["short-reads-paired", "reference-fasta"],
        "source": {
            "ecosystem": "iwc",
            "workflow": "Bacterial Variant Calling",
            "url": "https://example.com",
            "version": "0.1.2",
            "license": "MIT",
        },
        "tools": ["bwa-mem2", "bcftools"],
        "tags": ["bacteria", "snv"],
        "test_data": [
            {"path": "test_data/reads_1.fastq.gz", "role": "reads_forward"},
            {"path": "test_data/reads_2.fastq.gz", "role": "reads_reverse"},
            {"path": "test_data/reference.fasta", "role": "reference"},
        ],
        "expected_output": [
            {"path": "expected_output/variants.vcf", "kind": "vcf", "description": "Filtered haploid variants."}
        ],
    },
    "body": "# Haploid bacterial variant calling\n\n## When to use this sketch\n- Bacteria\n",
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


def _record(tmp_path: Path) -> WorkflowRecord:
    # Point at a real small fixture so test_data can be copied
    fixture = Path(__file__).parent / "fixtures" / "iwc_sample" / "workflows" / "variant-calling" / "bacterial"
    test_data = [fixture / "test-data" / f for f in ("reads_1.fastq.gz", "reads_2.fastq.gz", "reference.fasta")]
    return WorkflowRecord(
        ecosystem="iwc",
        slug="bacterial",
        display_name="Bacterial Variant Calling",
        source_url="https://example.com",
        version="0.1.2",
        license="MIT",
        files=[WorkflowFile(relative_path="README.md", content="hello")],
        test_data_paths=test_data,
        raw_root=fixture,
    )


def test_generate_and_write_end_to_end(tmp_path: Path) -> None:
    client = _mock_client(VALID_PAYLOAD)
    gen = SketchGenerator(client=client)
    record = _record(tmp_path)

    generated = gen.generate(record)
    assert generated.frontmatter.name == "haploid-variant-calling-bacterial"

    sketches_root = tmp_path / "sketches"
    target = write_sketch(generated, record, sketches_root)
    assert target.is_dir()
    assert (target / "SKETCH.md").exists()
    # test data should have been copied in
    assert (target / "test_data" / "reads_1.fastq.gz").exists()
    assert (target / "test_data" / "reference.fasta").exists()
    # expected_output stub was created
    assert (target / "expected_output" / "variants.vcf").exists()

    content = (target / "SKETCH.md").read_text()
    assert content.startswith("---\n")
    assert "haploid-variant-calling-bacterial" in content
    assert "# Haploid bacterial variant calling" in content


def test_generator_passes_cache_control_on_system_prompt() -> None:
    client = _mock_client(VALID_PAYLOAD)
    gen = SketchGenerator(client=client)
    record = _record(Path("/tmp"))
    gen.generate(record)

    call = client.messages.create.call_args
    system = call.kwargs["system"]
    assert isinstance(system, list)
    assert system[0]["cache_control"] == {"type": "ephemeral"}


def test_generator_backfills_source_from_record() -> None:
    payload = {
        "frontmatter": {
            "name": "example-sketch-name",
            "description": "Use when the payload omits source fields and the generator should back-fill them from the workflow record.",
            "domain": "variant-calling",
            "source": {"ecosystem": "iwc", "workflow": "x", "url": "https://x"},
            "test_data": [],
            "expected_output": [],
        },
        "body": "# x\n",
    }
    client = _mock_client(payload)
    gen = SketchGenerator(client=client)
    record = _record(Path("/tmp"))

    generated = gen.generate(record)
    assert generated.frontmatter.source.version == "0.1.2"
    assert generated.frontmatter.source.license == "MIT"
