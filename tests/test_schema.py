from pathlib import Path

import pytest
from pydantic import ValidationError

from gxy_sketches.schema import (
    ExpectedOutputRef,
    SketchFrontmatter,
    SketchSource,
    TestDataRef,
    TestManifest,
    WorkflowFile,
    WorkflowRecord,
)


def _base_source() -> SketchSource:
    return SketchSource(
        ecosystem="nf-core",
        workflow="nf-core/bacass",
        url="https://github.com/nf-core/bacass",
        version="2.2.0",
        license="MIT",
    )


def test_frontmatter_happy_path_with_local_test_data() -> None:
    fm = SketchFrontmatter(
        name="haploid-variant-calling-bacterial",
        description="Use when you need to call SNVs and small indels against a haploid bacterial reference from short reads.",
        domain="variant-calling",
        organism_class=["bacterial", "haploid"],
        input_data=["short-reads-paired", "reference-fasta"],
        source=_base_source(),
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


def test_frontmatter_happy_path_with_url_test_data() -> None:
    fm = SketchFrontmatter(
        name="haploid-variant-calling-remote",
        description="Use when the test data lives on Zenodo and is fetched at runtime rather than bundled with the sketch.",
        domain="variant-calling",
        source=_base_source(),
        test_data=[
            TestDataRef(
                role="reference",
                url="https://zenodo.org/records/1/files/ref.fasta",
                sha1="deadbeef",
                filetype="fasta",
            )
        ],
        expected_output=[
            ExpectedOutputRef(
                role="variants",
                description="Expected variant calls",
                assertions=["has_line: chr1 42 A G"],
            )
        ],
    )
    assert fm.test_data[0].url.startswith("https://")
    assert fm.expected_output[0].assertions == ["has_line: chr1 42 A G"]


@pytest.mark.parametrize(
    "bad_name",
    ["HasUpper", "has_underscore", "ab", "-leading-hyphen"],
)
def test_frontmatter_name_must_be_kebab_case(bad_name: str) -> None:
    with pytest.raises(ValidationError):
        SketchFrontmatter(
            name=bad_name,
            description="x" * 50,
            domain="variant-calling",
            source=_base_source(),
        )


def test_test_data_path_must_be_under_test_data() -> None:
    with pytest.raises(ValidationError):
        TestDataRef(path="expected_output/foo", role="reads")
    with pytest.raises(ValidationError):
        TestDataRef(path="/abs/path", role="reads")
    with pytest.raises(ValidationError):
        TestDataRef(path="test_data/../escape", role="reads")


def test_test_data_ref_needs_path_or_url() -> None:
    with pytest.raises(ValidationError):
        TestDataRef(role="reads")


def test_expected_output_needs_something() -> None:
    with pytest.raises(ValidationError):
        ExpectedOutputRef(description="nothing to anchor on")


def test_expected_output_path_must_be_under_expected_output() -> None:
    with pytest.raises(ValidationError):
        ExpectedOutputRef(
            path="test_data/foo", kind="vcf", description="x"
        )


def test_expected_output_assertions_only_is_valid() -> None:
    eo = ExpectedOutputRef(
        role="variants",
        description="Content-level check",
        assertions=["has_line: foo"],
    )
    assert eo.path is None and eo.url is None
    assert eo.assertions == ["has_line: foo"]


def test_workflow_record_metadata_bundle_includes_files_and_manifest() -> None:
    record = WorkflowRecord(
        ecosystem="iwc",
        slug="w",
        display_name="W",
        source_url="https://example.com",
        files=[WorkflowFile(relative_path="README.md", content="hello readme")],
        test_manifest=TestManifest(
            inputs=[
                TestDataRef(
                    role="reference",
                    url="https://example.com/ref.fa",
                    filetype="fasta",
                )
            ],
            outputs=[
                ExpectedOutputRef(
                    role="variants",
                    description="Assertions only",
                    assertions=["has_line: foo"],
                )
            ],
        ),
        raw_root=Path("/tmp"),
    )
    bundle = record.metadata_bundle()
    assert "README.md" in bundle
    assert "hello readme" in bundle
    assert "PARSED TEST MANIFEST" in bundle
    assert "reference" in bundle
    assert "has_line: foo" in bundle
