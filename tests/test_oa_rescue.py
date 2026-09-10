from literature_finder.models import LiteratureRecord
from literature_finder.oa_rescue import OpenAccessRescue


class _Client:
    def __init__(self):
        self.calls = []

    def get_json(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if "unpaywall" in url:
            return {"is_oa": True, "best_oa_location": {"url_for_pdf": "https://repo.example/paper.pdf", "version": "acceptedVersion"}}
        return {"open_access": {"is_oa": True}, "locations": [{"pdf_url": "https://openalex.example/paper.pdf", "is_oa": True}]}


def test_oa_rescue_uses_unpaywall_and_openalex_without_guessing_pdf_urls():
    client = _Client()
    record = LiteratureRecord("A DOI-only paper", doi="https://doi.org/10.1000/rescue")

    OpenAccessRescue(client, email="researcher@example.org").rescue(record)

    urls = {item["url"] for item in record.raw["download_candidates"]}
    assert "https://repo.example/paper.pdf" in urls
    assert "https://openalex.example/paper.pdf" in urls
    assert record.download_permission_verified is True
    assert client.calls[0][1]["params"]["email"] == "researcher@example.org"
