from contextlib import closing
from io import StringIO
import sqlite3
import pandas as pd
import pytest

from hirelens.config import MEASURES
from hirelens.database import Filters, aggregate, read_rows, write_database


def test_sql_filters_and_export_reconcile(database, data):
    filters = Filters("2025-02-01", "2025-02-07", ("HireHarbor",), ("Data Analyst",), ("Mumbai",))
    rows = read_rows(filters, database)
    expected = data.loc[data["date"].between(filters.start, filters.end)
                        & data["channel"].eq("HireHarbor") & data["role"].eq("Data Analyst")
                        & data["city"].eq("Mumbai")].reset_index(drop=True)
    pd.testing.assert_frame_equal(rows, expected)
    assert len(rows) == 7
    totals = aggregate(filters, path=database).iloc[0]
    for measure in MEASURES:
        assert totals[measure] == pytest.approx(expected[measure].sum())
    exported = pd.read_csv(StringIO(rows.to_csv(index=False)))
    pd.testing.assert_frame_equal(exported, rows)


def test_grouped_totals_match_independent_pandas(database, data):
    filters = Filters("2025-01-01", "2025-03-31")
    for group in ("date", "channel", "role", "city"):
        actual = aggregate(filters, group, database).set_index(group)
        expected = data.groupby(group)[list(MEASURES)].sum()
        pd.testing.assert_frame_equal(actual, expected, check_exact=False)


def test_empty_filters_and_inclusive_boundaries(database):
    assert len(read_rows(Filters("2025-01-01", "2025-01-01"), database)) == 60
    assert len(read_rows(Filters("2025-03-31", "2025-03-31"), database)) == 60
    for filters in [Filters("2030-01-01", "2030-01-02"), Filters("2025-01-01", "2025-03-31", channels=())]:
        assert read_rows(filters, database).empty
        assert aggregate(filters, path=database).iloc[0].eq(0).all()
        assert aggregate(filters, "channel", database).empty


def test_sql_injection_is_a_literal_value(database):
    attack = "HireHarbor') OR 1=1 --"
    filters = Filters("2025-01-01", "2025-03-31", (attack,))
    assert read_rows(filters, database).empty
    assert aggregate(filters, path=database)["spend_inr"].iloc[0] == 0
    with pytest.raises(ValueError):
        aggregate(filters, "channel; DROP TABLE cohorts", database)
    assert len(read_rows(Filters("2025-01-01", "2025-03-31"), database)) == 5400


def test_database_constraints_and_idempotent_generation(database, data):
    with closing(sqlite3.connect(database)) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE cohorts SET hires = interviews + 1")
        conn.rollback()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE cohorts SET clicks = 0.5")
        conn.rollback()
    write_database(data, database)
    assert len(read_rows(Filters("2025-01-01", "2025-03-31"), database)) == 5400
