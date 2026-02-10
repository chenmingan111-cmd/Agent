from app.core.risk import risk_analyzer

def test_risk_scoring():
    # 1. Low risk
    dsl_low = {"query": {"match_all": {}}, "size": 10}
    res = risk_analyzer.evaluate(dsl_low)
    assert res["level"] == "low"
    
    # 2. Medium risk (deep page > 10000)
    dsl_med = {"query": {"match_all": {}}, "size": 200, "from": 9900}
    res = risk_analyzer.evaluate(dsl_med)
    assert res["level"] == "medium"
    
    # 3. High risk (wildcard + script)
    dsl_high = {
        "query": {
            "wildcard": {"field": "*"},
            "script": "doc['field'].value"
        }
    }
    res = risk_analyzer.evaluate(dsl_high)
    assert res["level"] == "high"
    assert "Wildcard query used" in res["reasons"]
    assert "Scripting used" in res["reasons"]
