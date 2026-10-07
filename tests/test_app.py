"""Exercise real Streamlit page execution and widget transitions without a browser."""
from datetime import date
from pathlib import Path
from streamlit.testing.v1 import AppTest

from hirelens.metrics import format_value

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_pages_filters_empty_and_reset(data):
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    assert app.metric[0].value == format_value(data["spend_inr"].sum(), "money")
    app.multiselect(key="channels").set_value(["HireHarbor"]).run()
    selected = data[data["channel"].eq("HireHarbor")]
    assert app.metric[2].value == format_value(selected["qualified_applicants"].sum())
    app.multiselect(key="roles").set_value(["Data Analyst"]).run()
    app.multiselect(key="cities").set_value(["Mumbai"]).run()
    app.date_input(key="dates").set_value((date(2025, 2, 1), date(2025, 2, 7))).run()
    selected = selected[selected["role"].eq("Data Analyst") & selected["city"].eq("Mumbai")
                        & selected["date"].between("2025-02-01", "2025-02-07")]
    assert app.metric[2].value == format_value(selected["qualified_applicants"].sum())
    app.radio(key="page").set_value("Channel Performance").run()
    assert not app.exception
    assert app.dataframe[0].value["Channel"].tolist() == ["HireHarbor"]
    app.selectbox[0].set_value("City").run()
    assert not app.exception
    app.radio(key="page").set_value("Candidate Funnel").run()
    assert not app.exception
    assert app.metric[0].value == format_value(selected["impressions"].sum())
    app.multiselect(key="channels").set_value([]).run()
    assert not app.exception
    assert "No cohorts match" in app.warning[0].value
    app.button[0].click().run()
    assert not app.exception
    assert len(app.multiselect(key="channels").value) == 5
    app.radio(key="page").set_value("Overview").run()
    assert app.metric[2].value == format_value(data["qualified_applicants"].sum())


def test_partial_date_range_has_useful_message():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    app.date_input(key="dates").set_value((date(2025, 1, 1),)).run()
    assert not app.exception
    assert "both a start and an end" in app.warning[0].value
