import math
import pandas as pd
import pytest

from hirelens.metrics import add_metrics, format_value, safe_ratio


def test_ratios_use_sums_not_average_rates():
    # Row CTRs are 10% and 1%; their average (5.5%) is the WRONG combined CTR.
    rows = pd.DataFrame({"spend_inr": [100, 900], "impressions": [100, 900],
                         "clicks": [10, 9], "completed_applications": [5, 3],
                         "qualified_applicants": [4, 1], "hires": [1, 0]})
    result = add_metrics(rows.sum().to_frame().T).iloc[0]
    assert result["ctr"] == pytest.approx(19 / 1000)
    assert result["ctr"] != pytest.approx(.055)
    assert result["cpc"] == pytest.approx(1000 / 19)
    assert result["cpa"] == 125
    assert result["cpqa"] == 200
    assert result["cph"] == 1000
    assert result["qualification_rate"] == pytest.approx(5 / 8)


def test_zero_denominators_are_undefined():
    rows = pd.DataFrame({"spend_inr": [0, 100], "impressions": [0, 0], "clicks": [0, 0],
                         "completed_applications": [0, 0], "qualified_applicants": [0, 0], "hires": [0, 0]})
    result = add_metrics(rows)
    assert result[["ctr", "cpc", "cpa", "cpqa", "cph", "qualification_rate"]].isna().all().all()
    assert math.isnan(safe_ratio(1, 0))
    assert safe_ratio(0, 10) == 0
    assert format_value(float("nan"), "money") == "N/A"
    assert format_value(1234567.8, "money") == "₹12,34,567.80"
    assert format_value(.025, "percent") == "2.50%"
