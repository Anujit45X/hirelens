"""The three dashboard pages; SQL and metric calculations live in separate modules."""
import pandas as pd
import streamlit as st

from hirelens import charts
from hirelens.config import LABELS
from hirelens.metrics import format_value, safe_ratio


def plot(fig, key):
    st.plotly_chart(fig, width="stretch", key=key, config={"displaylogo": False})


def metric_cards(totals):
    cards = [("spend_inr", "money"), ("completed_applications", "number"),
             ("qualified_applicants", "number"), ("hires", "number")]
    for column, (name, kind) in zip(st.columns([1.6, 1.2, 1.2, .8]), cards):
        column.metric(LABELS[name], format_value(totals[name], kind), border=True)
    rates = [("ctr", "percent"), ("cpc", "money"), ("cpa", "money"), ("cpqa", "money"), ("cph", "money")]
    # A compact table avoids five crowded KPI cards with long labels.
    st.dataframe(pd.DataFrame({LABELS[name]: [format_value(totals[name], kind)] for name, kind in rates}),
                 hide_index=True, width="stretch")


def overview(totals, daily, channels):
    st.subheader("Overview")
    metric_cards(totals)
    valid = channels.dropna(subset=["cpqa"])
    if not valid.empty and valid["cpqa"].nunique() > 1:
        best = valid.loc[valid["cpqa"].idxmin()]
        st.info(f"{best['channel']} has the lowest observed cost per qualified applicant in this selection: "
                f"{format_value(best['cpqa'], 'money')} across {format_value(best['qualified_applicants'])} qualified applicants. "
                "Compare the same role and city before considering a budget change.")
    left, right = st.columns(2)
    with left:
        st.markdown("#### Qualified applicants over time")
        plot(charts.trend(daily, "qualified_applicants"), "overview_volume")
    with right:
        st.markdown("#### Cost per qualified applicant over time")
        plot(charts.trend(daily, "cpqa", money=True), "overview_cost")
    st.markdown("#### Spend over time")
    plot(charts.trend(daily, "spend_inr", money=True), "overview_spend")
    st.caption("Daily points use acquisition date. Each daily cost is that day's total spend divided by that day's qualified applicants. Undefined costs appear as gaps.")


def channel_performance(channels, segments, segment_dimension):
    st.subheader("Channel Performance")
    st.caption("Cost per qualified applicant = total advertising spend ÷ total qualified applicants. Lower is more efficient within a comparable population.")
    st.markdown("#### Acquisition efficiency")
    if channels["cpqa"].notna().any():
        plot(charts.channel_cost(channels), "channel_cost")
    else:
        st.info("No qualified applicants in this selection. Cost per qualified applicant is N/A for every channel.")
    missing = channels.loc[channels["cpqa"].isna(), "channel"].tolist()
    if missing:
        st.caption("N/A (zero qualified applicants), excluded from cost bars: " + ", ".join(missing))
    st.markdown("#### Qualification quality and volume")
    if channels["qualification_rate"].notna().any():
        plot(charts.channel_volume(channels.dropna(subset=["qualification_rate"])), "channel_quality")
    else:
        st.info("Qualification rate is N/A because no applications were completed.")
    st.caption("Qualification rate = qualified applicants ÷ completed applications. Bubble area represents spend; hover for the channel and exact values.")
    st.markdown("#### Channel scorecard")
    columns = ["channel", "spend_inr", "completed_applications", "qualified_applicants", "hires",
               "ctr", "cpc", "cpa", "cpqa", "cph", "qualification_rate"]
    table = channels[columns].sort_values("cpqa", na_position="last").copy()
    for name in columns[1:]:
        kind = "percent" if name in ("ctr", "qualification_rate") else "money" if name in ("spend_inr", "cpc", "cpa", "cpqa", "cph") else "number"
        table[name] = table[name].map(lambda value: format_value(value, kind))
    st.dataframe(table.rename(columns=LABELS), hide_index=True, width="stretch")
    st.markdown(f"#### Context by {segment_dimension.lower()}")
    segment_view = segments[[segment_dimension.lower(), "spend_inr", "qualified_applicants", "cpqa"]].copy()
    for name in ("spend_inr", "cpqa"):
        segment_view[name] = segment_view[name].map(lambda value: format_value(value, "money"))
    segment_view["qualified_applicants"] = segment_view["qualified_applicants"].map(format_value)
    st.dataframe(segment_view.rename(columns=LABELS), hide_index=True, width="stretch")
    st.caption("These are descriptive synthetic results, not proof of channel lift. Role and city mix, sample size, and hiring outcomes matter alongside cost.")


def candidate_funnel(totals):
    st.subheader("Candidate Funnel")
    st.caption("Outcomes belong to the original acquisition-date cohort, including interviews and hires. All outcomes are fully observed in this simulation.")
    first, second, third = st.columns(3)
    first.metric("Impressions", format_value(totals["impressions"]), border=True)
    second.metric("Clicks", format_value(totals["clicks"]), border=True)
    third.metric("CTR", format_value(totals["ctr"], "percent"), border=True)
    st.markdown("#### From application start to hire")
    if totals["application_starts"]:
        plot(charts.candidate_funnel(totals), "candidate_funnel")
    else:
        st.info("No applications were started in this selection. See the transition table for N/A conversions.")
    st.caption("Percentages inside the funnel are relative to application starts; impressions and clicks are shown above to keep candidate stages readable.")
    st.markdown("#### Conversion at every step")
    st.dataframe(charts.conversion_table(totals), hide_index=True, width="stretch")
    rate = safe_ratio(totals["hires"], totals["completed_applications"])
    st.caption(f"Completed application → hire: {format_value(rate, 'percent')}. In real hiring, recent cohorts need time to mature; comparing them with older cohorts can understate conversion.")
