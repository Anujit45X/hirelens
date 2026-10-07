"""Small Plotly builders. Each chart receives already aggregated, filtered data."""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from hirelens.config import CHANNELS, FUNNEL, LABELS
from hirelens.metrics import format_value, safe_ratio

COLORS = dict(zip(CHANNELS, ["#147D92", "#5356A3", "#D68138", "#2E8B68", "#B55583"]))


def polish(fig, y_title=None):
    fig.update_layout(
        template="plotly_white", font=dict(family="Arial, sans-serif", color="#182B49", size=13),
        margin=dict(l=15, r=20, t=25, b=35), height=350,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend_title_text="", yaxis_title=y_title,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E3EAF2", rangemode="tozero")
    return fig


def trend(frame, metric, money=False):
    fig = px.line(frame, x="date", y=metric, labels=LABELS, markers=False)
    fig.update_traces(line_color="#147D92", line_width=2.5, connectgaps=False)
    polish(fig, LABELS[metric])
    fig.update_xaxes(title=None, tickformat="%d %b")
    if money:
        fig.update_yaxes(tickprefix="₹", tickformat=",.0f")
    return fig


def channel_cost(frame):
    valid = frame.dropna(subset=["cpqa"]).sort_values("cpqa")
    fig = px.bar(valid, x="cpqa", y="channel", orientation="h", color="channel",
                 color_discrete_map=COLORS, labels=LABELS,
                 custom_data=["qualified_applicants", "spend_inr"])
    fig.update_traces(hovertemplate="%{y}<br>Cost per qualified applicant: ₹%{x:,.2f}"
                      "<br>Qualified applicants: %{customdata[0]:,}<br>Spend: ₹%{customdata[1]:,.2f}<extra></extra>")
    polish(fig)
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title="Cost per qualified applicant (INR)", rangemode="tozero", tickprefix="₹")
    fig.update_yaxes(title=None, categoryorder="array", categoryarray=valid["channel"].tolist(), autorange="reversed")
    return fig


def channel_volume(frame):
    fig = px.scatter(frame, x="qualification_rate", y="qualified_applicants", size="spend_inr",
                     color="channel", color_discrete_map=COLORS, hover_name="channel",
                     labels=LABELS, size_max=52, custom_data=["completed_applications", "cpqa"])
    fig.update_traces(hovertemplate="%{hovertext}<br>Qualification rate: %{x:.1%}"
                      "<br>Qualified applicants: %{y:,}<br>Completed applications: %{customdata[0]:,}"
                      "<br>Cost per qualified applicant: ₹%{customdata[1]:,.2f}<extra></extra>")
    polish(fig, "Qualified applicants")
    fig.update_xaxes(tickformat=".0%", range=[0, 1])
    fig.update_layout(legend=dict(orientation="h", y=-.25))
    return fig


def candidate_funnel(totals):
    # Exclude impressions/clicks here so the smaller candidate stages remain readable.
    stages = FUNNEL[2:]
    fig = go.Figure(go.Funnel(y=[LABELS[s] for s in stages], x=[int(totals[s]) for s in stages],
                             textinfo="value+percent initial", marker=dict(color="#147D92"),
                             hovertemplate="%{y}: %{x:,}<extra></extra>"))
    polish(fig)
    fig.update_layout(height=370)
    return fig


def conversion_table(totals):
    rows = []
    for parent, child in zip(FUNNEL, FUNNEL[1:]):
        rate = safe_ratio(totals[child], totals[parent])
        rows.append({"Transition": f"{LABELS[parent]} → {LABELS[child]}",
                     "Entered": format_value(totals[parent]), "Advanced": format_value(totals[child]),
                     "Did not advance": format_value(totals[parent] - totals[child]),
                     "Conversion rate": format_value(rate, "percent")})
    return pd.DataFrame(rows)
