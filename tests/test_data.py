import numpy as np
import pandas as pd
import pytest

from hirelens.config import CHANNELS, CITIES, DIMENSIONS, FUNNEL, MEASURES, ROLES
from hirelens.generate import generate_data, validate_data


def test_complete_reproducible_grid(data):
    assert len(data) == 90 * 5 * 4 * 3 == 5400
    assert data["date"].nunique() == 90
    assert data["date"].min() == "2025-01-01"
    assert data["date"].max() == "2025-03-31"
    assert set(data["channel"]) == set(CHANNELS)
    assert set(data["role"]) == set(ROLES)
    assert set(data["city"]) == set(CITIES)
    assert not data.duplicated(list(DIMENSIONS)).any()
    assert data.groupby("date").size().eq(60).all()
    pd.testing.assert_frame_equal(data, generate_data())
    assert not data.equals(generate_data(seed=43))


def test_nonnegative_integer_monotone_funnel(data):
    assert not data.isna().any().any()
    assert (data[list(MEASURES)] >= 0).all().all()
    assert np.isfinite(data[list(MEASURES)]).all().all()
    for stage in FUNNEL:
        assert pd.api.types.is_integer_dtype(data[stage])
    assert (np.diff(data[list(FUNNEL)].values, axis=1) <= 0).all()
    assert (data["spend_inr"] * 100).sub((data["spend_inr"] * 100).round()).abs().max() < 1e-7


def test_nonuniform_performance(data):
    assert data["spend_inr"].nunique() > 1000
    totals = data.groupby("channel")[list(MEASURES)].sum()
    assert (totals["qualified_applicants"] / totals["completed_applications"]).std() > .05
    assert data.groupby("date")["qualified_applicants"].sum().nunique() > 30


@pytest.mark.parametrize("corruption", ["negative", "fractional", "funnel", "null", "duplicate", "infinite"])
def test_validation_rejects_bad_data(data, corruption):
    frame = data.copy()
    if corruption == "negative":
        frame.loc[0, "spend_inr"] = -1
    elif corruption == "fractional":
        frame["hires"] = frame["hires"].astype(float)
        frame.loc[0, "hires"] = .5
    elif corruption == "funnel":
        frame.loc[0, "hires"] = frame.loc[0, "interviews"] + 1
    elif corruption == "null":
        frame.loc[0, "city"] = None
    elif corruption == "duplicate":
        frame = pd.concat([frame, frame.iloc[[0]]])
    else:
        frame.loc[0, "spend_inr"] = float("inf")
    with pytest.raises(ValueError):
        validate_data(frame)
