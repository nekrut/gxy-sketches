from pathlib import Path

from gxy_sketches.ingest.iwc import IwcIngestor


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "iwc_sample"


def _discover_one(monkeypatch):
    ingestor = IwcIngestor()
    monkeypatch.setattr(
        "gxy_sketches.ingest.iwc.ensure_clone",
        lambda repo_url, dest: FIXTURE_ROOT,
    )
    records = list(ingestor.discover(cache_root=Path("/tmp/unused")))
    assert len(records) == 1
    return records[0]


def test_walk_finds_fixture_workflow(monkeypatch) -> None:
    r = _discover_one(monkeypatch)
    assert r.ecosystem == "iwc"
    assert r.display_name == "Bacterial Variant Calling"
    assert r.version == "0.1.2"
    assert r.license == "MIT"

    paths = {f.relative_path for f in r.files}
    assert any(p.endswith("main.ga") for p in paths)
    assert any(p.endswith("README.md") for p in paths)
    assert any(p.endswith("main-tests.yml") for p in paths)


def test_parses_planemo_manifest_inputs(monkeypatch) -> None:
    r = _discover_one(monkeypatch)
    assert r.test_manifest is not None
    roles = {i.role for i in r.test_manifest.inputs}
    # One top-level File + two collection elements (forward + reverse of SAMPLE1)
    assert "reference" in roles
    assert any(role.endswith("forward") for role in roles)
    assert any(role.endswith("reverse") for role in roles)
    # URLs + SHA-1 are lifted
    ref = next(i for i in r.test_manifest.inputs if i.role == "reference")
    assert ref.url == "https://example.com/test-data/reference.fasta"
    assert ref.sha1 == "a" * 40
    assert ref.filetype == "fasta"
    assert ref.path is None  # remote-only


def test_parses_planemo_manifest_outputs(monkeypatch) -> None:
    r = _discover_one(monkeypatch)
    assert r.test_manifest is not None
    roles = [o.role for o in r.test_manifest.outputs]
    assert "annotated_variants" in roles
    assert "snpeff_variants" in roles

    # Local-path output should be copied from source into the manifest's map.
    annotated = next(o for o in r.test_manifest.outputs if o.role == "annotated_variants")
    assert annotated.path == "expected_output/expected_variants.tabular"
    source_path = r.test_manifest.output_source_map[annotated.path]
    assert source_path.exists()

    # Assertion-only output has no path.
    snpeff = next(o for o in r.test_manifest.outputs if o.role == "snpeff_variants")
    assert snpeff.path is None
    assert any("has_line" in a for a in snpeff.assertions)


def test_metadata_bundle_includes_parsed_manifest(monkeypatch) -> None:
    r = _discover_one(monkeypatch)
    bundle = r.metadata_bundle()
    assert "PARSED TEST MANIFEST" in bundle
    assert "reference" in bundle
    assert "has_line" in bundle


def test_extracts_tool_versions_from_ga(monkeypatch) -> None:
    r = _discover_one(monkeypatch)
    assert r.tool_versions["bwa_mem2"] == "2.2.1+galaxy0"
    assert r.tool_versions["bcftools_call"] == "1.15.1+galaxy3"
    assert r.tool_versions["fastp"] == "0.23.4+galaxy0"
