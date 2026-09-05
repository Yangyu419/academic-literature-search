from literature_finder.query_planner import build_plan, parse_request


def test_year_and_type_parsing_and_expansion():
    request = parse_request("2020-2026 年 large language model agent memory 硕博士论文和期刊", target_count=50)
    assert request.start_year == 2020
    assert request.end_year == 2026
    assert "博士论文" in request.literature_types
    plan = build_plan(request)
    assert "large language model" in plan.expanded_terms
    assert any("agent memory" in query for query in plan.queries)

