from __future__ import annotations

from literature_finder.domain_router import specialist_adapters
from literature_finder.pipeline import default_adapters
from literature_finder.sources import (
    DoajAdapter,
    EuropePmcAdapter,
    NuclearFuelInlAdapter,
    OatdAdapter,
    OecdNeaAdapter,
    ThesesFrAdapter,
    ZenodoAdapter,
)


class _JsonClient:
    def __init__(self, payload):
        self.payload = payload

    def get_json(self, url, **kwargs):
        return self.payload


class _Response:
    def __init__(self, content: bytes, content_type: str = "text/html"):
        self.content = content
        self.headers = {"Content-Type": content_type}

    def close(self):
        pass


class _HtmlClient:
    def __init__(self, content: bytes | None = None, error: Exception | None = None):
        self.content = content or b""
        self.error = error

    def request(self, method, url, **kwargs):
        if self.error:
            raise self.error
        return _Response(self.content)


def test_europe_pmc_maps_full_text_pdf():
    adapter = EuropePmcAdapter(_JsonClient({"resultList": {"result": [{
        "id": "123", "source": "MED", "title": "A paper", "doi": "10.1000/x",
        "fullTextUrlList": {"fullTextUrl": [{"documentStyle": "pdf", "site": "PMC", "url": "https://pmc.example/a.pdf"}]},
    }]}}))
    record = adapter.search("fuel")[0]
    assert record.source_record_id == "123"
    assert record.pdf_url == "https://pmc.example/a.pdf"
    assert record.doi == "10.1000/x"


def test_doaj_maps_article_link_and_pdf():
    adapter = DoajAdapter(_JsonClient({"results": [{"id": "abc", "bibjson": {
        "title": "Open article", "identifier": [{"type": "doi", "id": "10.1000/doaj"}],
        "journal": {"title": "Open Journal"}, "link": [{"type": "pdf", "url": "https://journal.example/a.pdf"}],
    }}]}))
    record = adapter.search("fuel")[0]
    assert record.source_record_id == "abc"
    assert record.pdf_url.endswith(".pdf")
    assert record.doi == "10.1000/doaj"


def test_zenodo_maps_files_pdf():
    adapter = ZenodoAdapter(_JsonClient({"hits": {"hits": [{
        "id": 7, "metadata": {"title": "Report", "doi": "10.5281/zenodo.7", "creators": [{"name": "A Author"}]},
        "files": [{"key": "report.pdf", "links": {"self": "https://zenodo.example/report.pdf"}}],
    }]}}))
    record = adapter.search("fuel")[0]
    assert record.source_ids == {"zenodo": "7"}
    assert record.pdf_source == "Zenodo"


def test_thesis_adapters_map_records():
    oatd = OatdAdapter(_JsonClient({"results": [{"id": "o1", "title": "A thesis", "pdf_url": "https://repo.example/t.pdf"}]}))
    theses = ThesesFrAdapter(_JsonClient({"response": {"docs": [{"nnt": "2024ABC", "title_s": ["Une these"]}]}}))
    assert oatd.search("fuel")[0].literature_type == "学位论文"
    assert theses.search("fuel")[0].source_record_id == "2024ABC"


def test_official_html_adapters_parse_and_fallback():
    nea_html = b'<a href="/pub/a.pdf">NEA report</a>'
    inl_html = b'<a href="/content/a.pdf">INL report</a>'
    nea = OecdNeaAdapter(_HtmlClient(nea_html), respect_robots=False).search("fuel")
    inl = NuclearFuelInlAdapter(_HtmlClient(inl_html), respect_robots=False).search("fuel")
    assert nea[0].pdf_url == "https://oecd-nea.org/pub/a.pdf"
    assert inl[0].pdf_url == "https://nuclearfuel.inl.gov/content/a.pdf"

    fallback_nea = OecdNeaAdapter(_HtmlClient(error=RuntimeError("parse failure")), respect_robots=False).search("fuel")
    fallback_inl = NuclearFuelInlAdapter(_HtmlClient(error=RuntimeError("parse failure")), respect_robots=False).search("fuel")
    assert fallback_nea[0].landing_page_url.startswith("https://oecd-nea.org/tools/publication")
    assert fallback_nea[0].pdf_url is None
    assert fallback_inl[0].landing_page_url == NuclearFuelInlAdapter.landing_url
    assert fallback_inl[0].pdf_url is None


def test_router_and_default_adapters_include_required_sources():
    common = {adapter.name for adapter in default_adapters("general topic")}
    nuclear = {adapter.name for adapter in specialist_adapters("核燃料组件")}
    thesis = {adapter.name for adapter in specialist_adapters("doctoral thesis on fuel")}
    assert {"Europe PMC", "DOAJ", "Zenodo", "HAL", "arXiv"} <= common
    assert {"OSTI", "IAEA INIS", "NRC ADAMS", "OECD-NEA", "INL Advanced Fuels Campaign"} <= nuclear
    assert {"OATD", "theses.fr", "CORE"} <= thesis
