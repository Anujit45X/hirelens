"""SQLite persistence and parameterized queries. User values never become SQL text."""
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
import sqlite3

import pandas as pd

from hirelens.config import DATABASE_PATH, DIMENSIONS, FUNNEL, MEASURES
from hirelens.generate import validate_data


@dataclass(frozen=True)
class Filters:
    start: str
    end: str
    # None means all; an empty tuple means deliberately select nothing.
    channels: tuple[str, ...] | None = None
    roles: tuple[str, ...] | None = None
    cities: tuple[str, ...] | None = None


def write_database(frame: pd.DataFrame, path: Path = DATABASE_PATH) -> None:
    """Replace only the cohorts table in one transaction, after validation."""
    validate_data(frame)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    integer_fields = ", ".join(
        f"{name} INTEGER NOT NULL CHECK (typeof({name}) = 'integer' AND {name} >= 0)"
        for name in FUNNEL
    )
    funnel_checks = ", ".join(f"CHECK ({child} <= {parent})" for parent, child in zip(FUNNEL, FUNNEL[1:]))
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute("BEGIN")  # Include DDL in the transaction so a failed write preserves the old table.
        conn.execute("DROP TABLE IF EXISTS cohorts")
        conn.execute(f"""CREATE TABLE cohorts (
            date TEXT NOT NULL, channel TEXT NOT NULL, role TEXT NOT NULL, city TEXT NOT NULL,
            spend_inr REAL NOT NULL CHECK (spend_inr >= 0), {integer_fields},
            PRIMARY KEY (date, channel, role, city), {funnel_checks}
        )""")
        placeholders = ", ".join("?" for _ in frame.columns)
        conn.executemany(f"INSERT INTO cohorts VALUES ({placeholders})", frame.itertuples(index=False, name=None))
        conn.execute("CREATE INDEX idx_cohorts_segments ON cohorts(channel, role, city, date)")


def where_clause(filters: Filters) -> tuple[str, list]:
    clauses = ["date >= ?", "date <= ?"]
    values = [filters.start, filters.end]
    for column, selected in (("channel", filters.channels), ("role", filters.roles), ("city", filters.cities)):
        if selected is None:
            continue
        if not selected:
            clauses.append("1 = 0")
        else:
            placeholders = ", ".join("?" for _ in selected)
            clauses.append(f"{column} IN ({placeholders})")
            values.extend(selected)
    return " WHERE " + " AND ".join(clauses), values


def read_rows(filters: Filters, path: Path = DATABASE_PATH) -> pd.DataFrame:
    where, values = where_clause(filters)
    with closing(sqlite3.connect(path)) as conn:
        return pd.read_sql_query("SELECT * FROM cohorts" + where + " ORDER BY date, channel, role, city", conn, params=values)


def aggregate(filters: Filters, group_by: str | None = None, path: Path = DATABASE_PATH) -> pd.DataFrame:
    # SQL identifiers cannot be bound. Validate them against a fixed allowlist instead.
    if group_by is not None and group_by not in DIMENSIONS:
        raise ValueError("Unsupported grouping dimension")
    fields = ", ".join(f"COALESCE(SUM({name}), 0) AS {name}" for name in MEASURES)
    prefix = f"{group_by}, " if group_by else ""
    suffix = f" GROUP BY {group_by} ORDER BY {group_by}" if group_by else ""
    where, values = where_clause(filters)
    with closing(sqlite3.connect(path)) as conn:
        return pd.read_sql_query(f"SELECT {prefix}{fields} FROM cohorts" + where + suffix, conn, params=values)


def filter_options(path: Path = DATABASE_PATH) -> dict:
    with closing(sqlite3.connect(path)) as conn:
        start, end = conn.execute("SELECT MIN(date), MAX(date) FROM cohorts").fetchone()
        options = {column: [row[0] for row in conn.execute(f"SELECT DISTINCT {column} FROM cohorts ORDER BY {column}")]
                   for column in ("channel", "role", "city")}
    return {"start": start, "end": end, **options}
