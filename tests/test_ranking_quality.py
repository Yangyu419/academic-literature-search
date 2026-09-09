from literature_finder.models import LiteratureRecord, ResearchRequest, SearchPlan
from literature_finder.ranking import rank_records
from literature_finder.search import MIN_RELEVANCE_SCORE


def test_irrelevant_record_does_not_meet_quality_threshold() -> None:
    records = rank_records(
        [LiteratureRecord("Fuel price forecasting", abstract="Retail fuel market analysis")],
        ResearchRequest("PWR fuel assembly structural design"),
    )

    assert records[0].relevance_score < MIN_RELEVANCE_SCORE
    assert records[0].relevance_reason
