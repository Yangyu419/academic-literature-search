from literature_finder.dedup import deduplicate
from literature_finder.models import LiteratureRecord


def test_deduplicates_by_doi_and_merges_sources():
    first = LiteratureRecord("A Study: On Models", doi="10.1234/ABC", metadata_sources=["Crossref"])
    second = LiteratureRecord("A Study – On Models", doi="https://doi.org/10.1234/abc", abstract="Abstract", metadata_sources=["OpenAlex"])
    first.raw["download_candidates"] = [{"url": "https://repo.example/first.pdf", "priority": 10}]
    second.raw["download_candidates"] = [{"url": "https://repo.example/second.pdf", "priority": 20}]
    records = deduplicate([first, second])
    assert len(records) == 1
    assert records[0].abstract == "Abstract"
    assert records[0].metadata_sources == ["Crossref", "OpenAlex"]
    assert {item["url"] for item in records[0].raw["download_candidates"]} == {
        "https://repo.example/first.pdf", "https://repo.example/second.pdf"
    }


def test_missing_doi_remains_missing():
    records = deduplicate([LiteratureRecord("A title"), LiteratureRecord("A different title")])
    assert all(record.doi is None for record in records)


def test_blank_author_does_not_break_title_deduplication():
    records = deduplicate([
        LiteratureRecord("A title", authors=[""], publication_date="2024"),
        LiteratureRecord("A title", authors=["Ada Lovelace"], publication_date="2024"),
    ])
    assert len(records) == 1
