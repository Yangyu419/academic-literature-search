from literature_finder.clarification import assess, clarification_prompt
from literature_finder.models import ResearchRequest


def test_broad_nuclear_fuel_needs_clarification():
    decision = assess(ResearchRequest("核燃料"))
    assert decision.needed is True
    assert "包壳" in decision.questions[0]
    assert clarification_prompt(ResearchRequest("核燃料"))


def test_specific_topic_does_not_need_clarification():
    decision = assess(ResearchRequest("核燃料包壳锆合金辐照损伤"))
    assert decision.needed is False

