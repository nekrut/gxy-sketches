from pathlib import Path

import pytest
from pydantic import ValidationError

from gxy_sketches.schema import (
    ExpectedOutputRef,
    SketchFrontmatter,
    SketchSource,
    TestDataRef,
    WorkflowFile,
    WorkflowRecord,
)


def test_frontmatter_happy_path() -> None:
    fm = SketchFrontmatter(
        name="haploid-variant-calling-bacterial",
        description="Use when you need to call SNVs and small indels against a haploid bacterial reference from short reads.",
        domain="variant-calling",
        organism_class=["bacterial", "haploid"],
        input_data=["short-reads-paired", "reference-fasta"],
        source=SketchSource(
            ecosystem="nf-core",
            workflow="nf-core/bacass",
            url="https://github.com/nf-core/bacass",
            version="2.2.0",
            license="MIT",
        ),
        tools=["fastp", "bwa-mem2", "samtools", "bcftools"],
        tags=["bacteria", "wgs", "snv"],
        test_data=[TestDataRef(path="test_data/reads_1.fastq.gz", role="reads_forward")],
        expected_output=[
            ExpectedOutputRef(
                path="expected_output/variants.vcf",
                kind="vcf",
                description="Final filtered haploid variants.",
            )
        ],
    )
    assert fm.name == "haploid-variant-calling-bacterial"


@pytest.mark.parametrize(
    "bad_name",
    ["HasUpper", "has_underscore", "ab", "has--double-hyphen-start-", "-leading-hyphen"],
)
def test_frontmatter_name_must_be_kebab_case(bad_name: str) -> None:
    with pytest.raises(ValidationError):
        SketchFrontmatter(
            name=bad_name,
            description="x" * 50,
            domain="variant-calling",
            source=SketchSource(
                ecosystem="iwc",
                workflow="w",
                url="https://example.com",
            ),
        )


def test_test_data_path_must_be_under_test_data() -> None:
    with pytest.raises(ValidationError):
        TestDataRef(path="expected_output/foo", role="reads")
    with pytest.raises(ValidationError):
        TestDataRef(path="/abs/path", role="reads")
    with pytest.raises(ValidationError):
        TestDataRef(path="test_data/../escape", role="reads")


def test_expected_output_path_must_be_under_expected_output() -> None:
    with pytest.raises(ValidationError):
        ExpectedOutputRef(path="test_data/foo", kind="vcf", description="x")


def test_workflow_record_metadata_bundle_includes_files() -> None:
    record = WorkflowRecord(
        ecosystem="iwc",
        slug="w",
        display_name="W",
        source_url="https://example.com",
        files=[
            WorkflowFile(relative_path="README.md", content="hello readme"),
            WorkflowFile(relative_path="test.yml", content="hello tests"),
        ],
        raw_root=Path("/tmp"),
    )
    bundle = record.metadata_bundle()
    assert "README.md" in bundle
    assert "hello readme" in bundle
    assert "test.yml" in bundle
