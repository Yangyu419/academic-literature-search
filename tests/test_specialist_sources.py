from literature_finder.domain_router import is_nuclear_topic, specialist_adapters
from literature_finder.sources import CoreAdapter, HalAdapter, OstiAdapter
from literature_finder.sources.link_only import InisAdapter, NrcAdamsAdapter


class _Client:
    def __init__(self, payload):
        self.payload = payload

    def get_json(self, url, **kwargs):
        return self.payload


def test_domain_router_enables_nuclear_specialists():
    assert is_nuclear_topic("M5 fuel cladding irradiation")
    names = {adapter.name for adapter in specialist_adapters("核燃料包壳")}
    assert {"OSTI", "NRC ADAMS", "IAEA INIS", "HAL", "CORE"} <= names


def test_link_only_providers_do_not_claim_structured_api():
    nrc, inis = NrcAdamsAdapter(), InisAdapter()
    assert nrc.available is False and inis.available is False
    assert "q=" in nrc.search_url("fuel rod")
    assert nrc.search("fuel rod") == []


def test_osti_and_hal_map_provider_ids():
    osti = OstiAdapter(_Client({"records": [{"title": "A report", "osti_id": 123, "doi": "10.1234/x"}]}))
    hal = HalAdapter(_Client({"response": {"docs": [{"title_s": ["A paper"], "docid": "456"}]}}))
    assert osti.search("fuel")[0].source_ids == {"osti": "123"}
    assert hal.search("fuel")[0].source_ids == {"hal": "456"}


def test_core_is_skipped_without_key(monkeypatch):
    monkeypatch.delenv("CORE_API_KEY", raising=False)
    adapter = CoreAdapter(_Client({}))
    assert adapter.available is False
    assert adapter.search("anything") == []
