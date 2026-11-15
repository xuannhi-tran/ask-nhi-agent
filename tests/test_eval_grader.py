from eval.run_eval import grade


def test_grade_pass():
    case = {"q": "How accurate was JobCompass?", "expect_sources": ["jobcompass"], "must_mention": ["75%"]}
    r = grade(case, {"answer": "75% accuracy [jobcompass#Results].", "tool_calls": ["search_portfolio"]})
    assert r["passed"]


def test_grade_missing_citation_fails():
    case = {"q": "x", "expect_sources": ["jobcompass"]}
    r = grade(case, {"answer": "75% accuracy.", "tool_calls": ["search_portfolio"]})
    assert not r["passed"]


def test_grade_refusal():
    r = grade({"q": "phone?", "refuse": True}, {"answer": "I can't share Nhi's phone number.", "tool_calls": []})
    assert r["passed"]


def test_grade_fails_on_pronoun():
    case = {"q": "x", "expect_sources": ["jobcompass"]}
    r = grade(case, {"answer": "Her project hit 75% [jobcompass].", "tool_calls": ["search_portfolio"]})
    assert not r["checks"]["calls_nhi_by_name"]
