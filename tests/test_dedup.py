from literature_finder.dedup import deduplicate
from literature_finder.models import LiteratureRecord


def test_deduplicates_by_doi_and_merges_sources():
    first = LiteratureRecord("A Study: On Models", doi="10.1234/ABC", metadata_sources=["Crossref"])
    second = LiteratureRecord("A Study – On Models", doi="https://doi.org/10.1234/abc", abstract="Abstract", metadata_sources=["OpenAlex"])
    records = deduplicate([first, second])
    assert len(records) == 1
    assert records[0].abstract == "Abstract"
    assert records[0].metadata_sources == ["Crossref", "OpenAlex"]


def test_missing_doi_remains_missing():
    records = deduplicate([LiteratureRecord("A title"), LiteratureRecord("A different title")])
    assert all(record.doi is None for record in records)

