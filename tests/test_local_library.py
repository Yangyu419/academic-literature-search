from pathlib import Path

from pypdf import PdfWriter

from literature_finder.library import LocalLibraryChecker
from literature_finder.models import LiteratureRecord


def _write_pdf(path: Path, *, title: str, author: str = "Jane Smith", doi: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    metadata = {"/Title": title, "/Author": author, "/CreationDate": "D:20240101000000"}
    if doi:
        metadata["/DOI"] = doi
    writer.add_metadata(metadata)
    with path.open("wb") as handle:
        writer.write(handle)


def test_manual_pdf_doi_is_indexed_and_detected(tmp_path: Path):
    existing = tmp_path / "pdf" / "manual-name.pdf"
    _write_pdf(existing, title="M5 cladding corrosion behavior", doi="10.1234/ABC")
    checker = LocalLibraryChecker(tmp_path)
    checker.refresh()
    record = LiteratureRecord("M5 cladding corrosion behavior", doi="https://doi.org/10.1234/abc")
    result = checker.check(record)
    assert result.exists is True
    assert result.matched_by == "doi"
    assert result.existing_path == str(existing)


def test_no_doi_uses_strict_title_author_year(tmp_path: Path):
    existing = tmp_path / "pdf" / "manual.pdf"
    _write_pdf(existing, title="A study of fuel rods", author="Jane Smith")
    checker = LocalLibraryChecker(tmp_path)
    checker.refresh()
    same = LiteratureRecord("A study of fuel rods", authors=["Smith, Jane"], publication_date="2024")
    different_author = LiteratureRecord("A study of fuel rods", authors=["John Doe"], publication_date="2024")
    assert checker.check(same).exists is True
    assert checker.check(different_author).exists is False
