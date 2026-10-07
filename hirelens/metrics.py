"""Ratios of sums: call these helpers only after aggregating additive measures."""
import math
import pandas as pd

RATIOS = {
    "ctr": ("clicks", "impressions"),
    "cpc": ("spend_inr", "clicks"),
    "cpa": ("spend_inr", "completed_applications"),
    "cpqa": ("spend_inr", "qualified_applicants"),
    "cph": ("spend_inr", "hires"),
    "qualification_rate": ("qualified_applicants", "completed_applications"),
}


def safe_ratio(numerator: float, denominator: float) -> float:
    """NaN preserves undefined ratios; display formatting converts it to N/A."""
    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return float("nan")
    return numerator / denominator


def add_metrics(totals: pd.DataFrame) -> pd.DataFrame:
    result = totals.copy()
    for name, (numerator, denominator) in RATIOS.items():
        result[name] = result[numerator] / result[denominator].replace(0, float("nan"))
    return result


def format_value(value: float, kind: str = "number") -> str:
    if pd.isna(value) or not math.isfinite(float(value)):
        return "N/A"
    if kind == "percent":
        return f"{value:.2%}"
    # Indian digit grouping: 12,34,567 rather than 1,234,567.
    number = f"{abs(value):.2f}" if kind == "money" else f"{abs(value):.0f}"
    whole, dot, decimals = number.partition(".")
    tail = whole[-3:]
    head = whole[:-3]
    groups = []
    while head:
        groups.insert(0, head[-2:])
        head = head[:-2]
    grouped = ",".join([*groups, tail])
    sign = "-" if value < 0 else ""
    return f"{sign}{'₹' if kind == 'money' else ''}{grouped}{dot}{decimals}"
