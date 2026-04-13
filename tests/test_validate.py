from pathlib import Path

from gxy_sketches.validate import validate_corpus


LOCAL_SKETCH_YAML = """\
---
name: {name}
description: Use when you need to validate that the corpus linter is working end-to-end on a fixture sketch.
domain: variant-calling
organism_class: [bacterial, haploid]
input_data: [short-reads-paired]
source:
  ecosystem: iwc
  workflow: Bacterial Variant Calling
  url: https://example.com
  version: 0.1.2
  license: MIT
tools: [bcftools]
tags: [bacteria]
test_data:
  - role: reads
    path: test_data/reads.fq
expected_output:
  - role: variants
    path: expected_output/out.vcf
    kind: vcf
    description: Variants
---

# Title

## When to use this sketch
- Bacteria
"""


REMOTE_SKETCH_YAML = """\
---
name: {name}
description: Use when the test data is hosted on Zenodo rather than checked in alongside the sketch.
domain: variant-calling
source:
  ecosystem: iwc
  workflow: Remote Variant Calling
  url: https://example.com
  version: 0.1.0
  license: MIT
test_data:
  - role: reference
    url: https://zenodo.org/records/1/files/ref.fasta
    sha1: deadbeef
    filetype: fasta
expected_output:
  - role: variants
    description: Assertion-only expected output
    assertions:
      - "has_line: chr1 42 A G"
---

# Remote Sketch
"""


def _make_local_sketch(root: Path, name: str, *, with_orphan: bool = False, big: bool = False) -> Path:
    d = root / "variant-calling" / name
    (d / "test_data").mkdir(parents=True)
    (d / "expected_output").mkdir(parents=True)
    (d / "SKETCH.md").write_text(LOCAL_SKETCH_YAML.format(name=name))
    (d / "test_data" / "reads.fq").write_text("ACGT\n")
    (d / "expected_output" / "out.vcf").write_text("##fileformat=VCFv4.2\n")
    if with_orphan:
        (d / "test_data" / "undeclared.txt").write_text("orphan")
    if big:
        (d / "test_data" / "huge.bin").write_bytes(b"x" * (6 * 1024 * 1024))
    return d


def _make_remote_sketch(root: Path, name: str) -> Path:
    d = root / "variant-calling" / name
    (d / "test_data").mkdir(parents=True)
    (d / "expected_output").mkdir(parents=True)
    (d / "SKETCH.md").write_text(REMOTE_SKETCH_YAML.format(name=name))
    # Writer would drop these helper files; simulate them.
    (d / "test_data" / "README.md").write_text("# Remote inputs\n")
    (d / "expected_output" / "ASSERTIONS.md").write_text("# asserts\n")
    return d


def test_clean_local_corpus_passes(tmp_path: Path) -> None:
    _make_local_sketch(tmp_path, "clean-sketch-fixture")
    report = validate_corpus(tmp_path)
    assert report.ok, [str(i) for i in report.issues]


def test_remote_only_sketch_passes(tmp_path: Path) -> None:
    _make_remote_sketch(tmp_path, "remote-sketch-fixture")
    report = validate_corpus(tmp_path)
    assert report.ok, [str(i) for i in report.issues]


def test_orphan_file_flagged(tmp_path: Path) -> None:
    _make_local_sketch(tmp_path, "orphan-fixture", with_orphan=True)
    report = validate_corpus(tmp_path)
    codes = {i.code for i in report.issues}
    assert "ORPHAN_FILE" in codes


def test_bundle_too_big_flagged(tmp_path: Path) -> None:
    _make_local_sketch(tmp_path, "huge-fixture", big=True)
    report = validate_corpus(tmp_path)
    codes = {i.code for i in report.issues}
    assert "BUNDLE_TOO_BIG" in codes


def test_duplicate_name_flagged(tmp_path: Path) -> None:
    _make_local_sketch(tmp_path, "dup-fixture")
    other = tmp_path / "assembly" / "dup-fixture"
    (other / "test_data").mkdir(parents=True)
    (other / "expected_output").mkdir(parents=True)
    (other / "SKETCH.md").write_text(LOCAL_SKETCH_YAML.format(name="dup-fixture"))
    (other / "test_data" / "reads.fq").write_text("ACGT\n")
    (other / "expected_output" / "out.vcf").write_text("##fileformat=VCFv4.2\n")

    report = validate_corpus(tmp_path)
    codes = {i.code for i in report.issues}
    assert "DUPLICATE_NAME" in codes
