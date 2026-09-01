from meechrtk.governor import TokenGovernor

def test_estimate_tokens():
    assert TokenGovernor.estimate_tokens("hello world") == 3

def test_governor_preserves_relevant_error():
    g=TokenGovernor()
    result=g.optimize("Fix the build error", "Unrelated conversation.\n\nERROR: module missing at src/app.py line 42\n\nMore unrelated history", budget="balanced", max_tokens=2000)
    assert "ERROR" in result["final_prompt"]
    assert result["optimized_tokens"] <= result["original_tokens"] or result["original_tokens"] < 10
    assert any(d["action"] in {"KEEP","COMPRESS","DROP"} for d in result["decisions"])

def test_budget_modes():
    g=TokenGovernor()
    for mode in g.BUDGETS:
        r=g.optimize("continue project", "project architecture and old decisions", budget=mode, max_tokens=1000)
        assert r["budget_fraction"] == g.BUDGETS[mode]
