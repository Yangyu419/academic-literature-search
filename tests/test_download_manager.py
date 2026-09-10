from pathlib import Path

from pypdf import PdfWriter

from literature_finder.download import DownloadManager
from literature_finder.models import LiteratureRecord


def _pdf_bytes(*, title: str, doi: str) -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    writer.add_metadata({"/Title": title, "/Author": "Jane Smith", "/DOI": doi})
    stream = __import__("io").BytesIO()
    writer.write(stream)
    return stream.getvalue()


class _Response:
    headers = {"Content-Type": "application/pdf"}

    def __init__(self, payload: bytes):
        self.payload = payload

    def iter_content(self, size: int):
        yield self.payload

    def close(self):
        pass


class _Client:
    min_interval = 0.0

    def __init__(self, payload: bytes):
        self.payload = payload
        self.calls = 0

    def request(self, method: str, url: str, **kwargs):
        self.calls += 1
        return _Response(self.payload)


class _FallbackClient:
    min_interval = 0.0

    def __init__(self, payload: bytes):
        self.payload = payload
        self.urls: list[str] = []

    def request(self, method: str, url: str, **kwargs):
        self.urls.append(url)
        if "bad" in url:
            return _Response(b"<html>not a pdf</html>")
        return _Response(self.payload)


def _record(doi: str, title: str = "A study of fuel rods") -> LiteratureRecord:
    return LiteratureRecord(
        title, authors=["Jane Smith"], publication_date="2024", doi=doi,
        download_url="https://repository.example/paper.pdf", download_permission_verified=True,
        best_legal_access_url="https://repository.example/paper", pdf_url="https://repository.example/paper.pdf",
    )


def test_existing_doi_skips_before_http_request(tmp_path: Path):
    payload = _pdf_bytes(title="A study of fuel rods", doi="10.1234/abc")
    existing = tmp_path / "pdf" / "manual.pdf"
    existing.parent.mkdir()
    existing.write_bytes(payload)
    client = _Client(payload)
    results = DownloadManager(client=client).download([_record("10.1234/ABC")], tmp_path)
    assert client.calls == 0
    assert results[0].status == "skipped_existing"


def test_post_download_sha256_duplicate_removes_new_file(tmp_path: Path):
    payload = _pdf_bytes(title="A study of fuel rods", doi="10.1234/existing")
    existing = tmp_path / "pdf" / "existing.pdf"
    existing.parent.mkdir()
    existing.write_bytes(payload)
    record = _record("10.1234/new", title="Different source title")
    client = _Client(payload)
    results = DownloadManager(client=client).download([record], tmp_path)
    assert client.calls == 1
    assert results[0].status == "skipped_duplicate"
    assert len(list((tmp_path / "pdf").glob("*.pdf"))) == 1
    assert not list((tmp_path / ".download_tmp").glob("*.part"))


def test_force_redownload_is_explicit_override(tmp_path: Path):
    payload = _pdf_bytes(title="A study of fuel rods", doi="10.1234/abc")
    existing = tmp_path / "pdf" / "manual.pdf"
    existing.parent.mkdir()
    existing.write_bytes(payload)
    client = _Client(_pdf_bytes(title="A newer copy", doi="10.1234/abc"))
    results = DownloadManager(client=client).download([_record("10.1234/ABC")], tmp_path, force_redownload=True)
    assert client.calls == 1
    assert results[0].status == "downloaded"


def test_failed_first_candidate_falls_back_to_next_candidate(tmp_path: Path):
    payload = _pdf_bytes(title="A fallback paper", doi="10.1234/fallback")
    record = _record("10.1234/fallback", title="A fallback paper")
    record.download_url = "https://public.example/bad.pdf"
    record.raw["download_candidates"] = [
        {"url": "https://public.example/bad.pdf", "priority": 10, "source": "repository"},
        {"url": "https://public.example/good.pdf", "priority": 20, "source": "repository mirror"},
    ]
    client = _FallbackClient(payload)

    results = DownloadManager(client=client).download([record], tmp_path)

    assert client.urls == ["https://public.example/bad.pdf", "https://public.example/good.pdf"]
    assert results[0].status == "downloaded"
