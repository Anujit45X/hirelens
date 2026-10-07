"""Start with: python -m streamlit run app.py"""
from datetime import date
import sqlite3

import streamlit as st

from hirelens.config import DATABASE_PATH
from hirelens.database import Filters, aggregate, filter_options, read_rows, write_database
from hirelens.generate import generate_data
from hirelens.metrics import add_metrics
from hirelens import views

st.set_page_config(page_title="HireLens — Recruitment Marketing Analytics", page_icon="🔎", layout="wide")
st.html("""<style>
    [data-testid="stMetricValue"] { font-size: 1.65rem; }
    [data-testid="stMetricLabel"] { white-space: normal; }
</style>""")


def reset_filters():
    for key in ("dates", "channels", "roles", "cities"):
        st.session_state.pop(key, None)


@st.cache_resource
def initialize_database():
    """Streamlit serializes this first-run setup across visitor sessions."""
    if not DATABASE_PATH.exists():
        write_database(generate_data())


def main():
    st.title("HireLens")
    st.markdown("**Recruitment Marketing Analytics**")
    st.info("Synthetic data — portfolio demonstration")
    st.caption("Which recruitment advertising channels generate qualified applicants most efficiently? Independent educational project; not an official Joveo product.")
    with st.spinner("Preparing synthetic cohorts…"):
        initialize_database()

    options = filter_options()
    start, end = date.fromisoformat(options["start"]), date.fromisoformat(options["end"])
    with st.sidebar:
        st.header("Explore HireLens")
        page = st.radio("Page", ["Overview", "Channel Performance", "Candidate Funnel"], key="page")
        st.divider()
        st.subheader("Filter acquisition cohorts")
        dates = st.date_input("Acquisition dates", (start, end), min_value=start, max_value=end, key="dates")
        channels = st.multiselect("Channels", options["channel"], default=options["channel"], key="channels")
        roles = st.multiselect("Job roles", options["role"], default=options["role"], key="roles")
        cities = st.multiselect("Cities", options["city"], default=options["city"], key="cities")
        st.button("Reset filters", on_click=reset_filters, width="stretch")
        st.caption("All values are selected initially. Clearing a list selects no cohorts. Filters apply to every page and the CSV.")
    if len(dates) != 2:
        st.warning("Select both a start and an end date to display a complete date range.")
        st.stop()
    filters = Filters(dates[0].isoformat(), dates[1].isoformat(), tuple(channels), tuple(roles), tuple(cities))
    rows = read_rows(filters)
    st.caption(f"{dates[0]:%d %b %Y} – {dates[1]:%d %b %Y} · {len(rows):,} daily cohorts · INR · Fully observed simulated outcomes")
    if rows.empty:
        st.warning("No cohorts match these filters. Select at least one channel, role and city, or use Reset filters.")
        st.stop()
    totals = add_metrics(aggregate(filters)).iloc[0]
    if page == "Overview":
        views.overview(totals, add_metrics(aggregate(filters, "date")), add_metrics(aggregate(filters, "channel")))
    elif page == "Channel Performance":
        dimension = st.selectbox("Compare segment context", ["Role", "City"])
        views.channel_performance(add_metrics(aggregate(filters, "channel")),
                                  add_metrics(aggregate(filters, dimension.lower())), dimension)
    else:
        views.candidate_funnel(totals)

    st.divider()
    with st.expander("Inspect and download filtered cohorts"):
        st.caption("One row per acquisition date × channel × role × city. Synthetic data; all outcomes fully observed. CSV contains the filtered raw counts and spend, not row-level ratios.")
        st.download_button("Download filtered CSV", data=rows.to_csv(index=False).encode("utf-8"),
                           file_name=f"hirelens_synthetic_{dates[0]}_{dates[1]}.csv", mime="text/csv")
        st.dataframe(rows, hide_index=True, width="stretch")
    with st.expander("Metric guide and assumptions"):
        st.markdown("""
        - **CTR:** clicks ÷ impressions. **Cost per click:** spend ÷ clicks.
        - **Cost per application:** spend ÷ completed applications.
        - **Cost per qualified applicant:** spend ÷ qualified applicants. **Cost per hire:** spend ÷ hires.
        - **Qualification rate:** qualified applicants ÷ completed applications.
        - **Step conversion:** next-stage count ÷ previous-stage count.
        - Every ratio divides **summed numerators by summed denominators**. A zero denominator displays **N/A**.
        - Qualified means meeting a simulated role's screening criteria. Spend is advertising cost only, excluding recruiter and platform fees.
        - Dates are acquisition dates, not interview or hire event dates. Real recruitment outcomes arrive with delays; use mature cohorts or explicit observation windows.
        - Channel names and performance parameters are fictional. This dataset contains no personal or Joveo data.
        """)


try:
    main()
except (sqlite3.Error, OSError) as error:
    st.error("HireLens could not read or create its local database. Check folder permissions and regenerate it using: python -m scripts.generate_data")
    st.code(str(error))
    st.stop()
