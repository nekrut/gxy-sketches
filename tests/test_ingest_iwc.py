from pathlib import Path

from gxy_sketches.ingest.iwc import IwcIngestor


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "iwc_sample"


def test_walk_finds_fixture_workflow(monkeypatch) -> None:
    ingestor = IwcIngestor()
    # bypass ensure_clone by pointing at the checked-in fixture
    monkeypatch.setattr(
        "gxy_sketches.ingest.iwc.ensure_clone",
        lambda repo_url, dest: FIXTURE_ROOT,
    )
    records = list(ingestor.discover(cache_root=Path("/tmp/unused")))
    assert len(records) == 1
    r = records[0]
    assert r.ecosystem == "iwc"
    assert r.display_name == "Bacterial Variant Calling"
    assert r.version == "0.1.2"
    assert r.license == "MIT"

    paths = {f.relative_path for f in r.files}
    assert any(p.endswith("main.ga") for p in paths)
    assert any(p.endswith("README.md") for p in paths)
    assert any(p.endswith("main-tests.yml") for p in paths)

    # test_data harvest
    names = {p.name for p in r.test_data_paths}
    assert names == {"reads_1.fastq.gz", "reads_2.fastq.gz", "reference.fasta"}


def test_metadata_bundle_contains_readme(monkeypatch) -> None:
    ingestor = IwcIngestor()
    monkeypatch.setattr(
        "gxy_sketches.ingest.iwc.ensure_clone",
        lambda repo_url, dest: FIXTURE_ROOT,
    )
    record = next(iter(ingestor.discover(cache_root=Path("/tmp/unused"))))
    bundle = record.metadata_bundle()
    assert "Haploid SNV" in bundle
    assert "bwa-mem2" in bundle
