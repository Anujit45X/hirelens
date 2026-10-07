# HireLens — Recruitment Marketing Analytics

**Live dashboard:** [hirelens-anujit.streamlit.app](https://hirelens-anujit.streamlit.app/) · [GitHub source](https://github.com/Anujit45X/hirelens)

**Synthetic data — portfolio demonstration.** An independent educational project for a recruitment marketing analytics portfolio. It is not an official Joveo product, is not affiliated with Joveo, and uses no Joveo or personal data.

**Business question:** Which recruitment advertising channels generate qualified applicants most efficiently?

HireLens follows advertising spend through applications, screening, interviews and hires. Its primary efficiency metric is cost per qualified applicant (CPQA), considered alongside qualification rate, volume and cost per hire. The project connects familiar Excel reporting concepts with a reproducible Python → SQLite → Streamlit workflow.

## Quick start

For a public launch, follow [DEPLOYMENT.md](DEPLOYMENT.md). The repository includes a GitHub Actions workflow for automated tests on pushes and pull requests.

Python 3.11–3.13 is recommended; this project was tested with Python 3.13. SQLite is included with Python. Run these commands **inside the `hirelens` project folder**.

Windows PowerShell (activation is unnecessary, avoiding execution-policy issues):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m scripts.generate_data
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app.py
```

macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m scripts.generate_data
.venv/bin/python -m pytest -q
.venv/bin/python -m streamlit run app.py
```

Open http://localhost:8501. Stop the foreground server with Ctrl+C. For a different port, add `--server.port 8502`. The app creates the database on first launch if it does not exist; the generator also writes a full CSV. To recreate exactly the tested dependency environment, install `requirements-lock.txt` instead of `requirements.txt` (lock captured on Windows/Python 3.13).

The development session used a virtual environment in the parent workspace. From this project folder, the existing interpreter is `..\.venv\Scripts\python.exe`; substitute it for `.\.venv\Scripts\python.exe` to reuse that environment.

## Dashboard tour

- **Overview:** spend, completed applications, qualified applicants, hires, CTR and all four costs, plus daily qualified-applicant, CPQA and spend trends. A dynamic callout identifies the lowest observed CPQA in the selected population.
- **Channel Performance:** CPQA comparison, qualification-rate versus volume plot (bubble area = spend), full channel scorecard and role/city context. Filter to one role and city to make more comparable channel comparisons.
- **Candidate Funnel:** impressions and clicks, readable candidate funnel from start to hire, counts lost at every step and step-to-step conversion rates.

Acquisition-date, channel, job-role and city filters persist across pages. Dates are inclusive. All categories are initially selected; clearing a category intentionally returns no data. Reset restores the full population. Expand **Inspect and download filtered cohorts** to export exactly the raw rows matching the current filters. The filename identifies the synthetic dataset and selected dates; the rows contain their own channel/role/city context. Ratios are not exported at row level.

## Data model and assumptions

The fixed seed is **42**. There are **5,400 rows = 90 days × 5 channels × 4 roles × 3 cities**, covering **1 January–31 March 2025**. Grain and primary key: `(date, channel, role, city)`.

| Column | Meaning |
| --- | --- |
| date | Acquisition date of the advertising cohort (ISO date, Indian local calendar day) |
| channel | Fictional channel: TalentBeacon, CareerOrbit, RoleRipple, HireHarbor or SkillSignal |
| role | Software Engineer, Data Analyst, Sales Executive or Customer Support |
| city | Bengaluru, Mumbai or Hyderabad |
| spend_inr | Advertising spend in INR, rounded to paise; excludes recruitment salaries and platform fees |
| impressions | Ad exposures in the cohort; not unique people |
| clicks | Modeled clicks from those impressions |
| application_starts | Clicks progressing to an application start |
| completed_applications | Starts resulting in a submitted application |
| qualified_applicants | Completed applications meeting simulated role screening criteria |
| interviews | Qualified applicants progressing to an interview |
| hires | Interviewed applicants ultimately hired |

The simulation enforces `impressions ≥ clicks ≥ application_starts ≥ completed_applications ≥ qualified_applicants ≥ interviews ≥ hires ≥ 0`. Counts are integers; spend is finite and nonnegative. Each simulated application journey belongs to one acquisition cohort and channel. These are attributed application journeys, not globally deduplicated real people. Repeat clicks, multi-touch attribution, repeated applications and cross-device identity are deliberately out of scope.

**Acquisition-date cohorts with fully observed outcomes:** all later interviews and hires are attributed back to acquisition date. Even the final day is mature in this simulation. Dates in charts are therefore **not interview or hire event dates**. In real recruitment, outcomes arrive with delays; use fixed follow-up windows, track cohort maturity, and account for right censoring before comparing recent and older cohorts.

Channel budgets, CPMs and stage probabilities differ. Roles vary in demand, auction cost, qualification difficulty and interview-to-hire conversion. Cities vary in demand and auction cost. Weekends, a monthly cycle, gradual demand growth and daily/row-level random variation change performance over time. A channel–role interaction changes screening fit. Poisson impressions and sequential binomial transitions create imperfect, coherent funnels. All parameters are illustrative assumptions, **not market benchmarks or claims about real Indian recruitment**. Pin dependencies to reproduce exact draws across environments.

## Metric definitions

Every numerator and denominator below is **summed over the same filtered population** before division.

| Metric | Formula | Interpretation |
| --- | --- | --- |
| Spend | SUM(spend_inr) | Advertising investment |
| Completed applications | SUM(completed_applications) | Submitted applications |
| Qualified applicants | SUM(qualified_applicants) | Screening-qualified applications |
| Hires | SUM(hires) | Fully observed hiring outcomes |
| CTR | SUM(clicks) / SUM(impressions) | Share of impressions producing a click |
| Cost per click (CPC) | SUM(spend_inr) / SUM(clicks) | INR per click |
| Cost per application (CPA) | SUM(spend_inr) / SUM(completed_applications) | INR per completed application |
| Cost per qualified applicant (CPQA) | SUM(spend_inr) / SUM(qualified_applicants) | INR per qualified applicant; primary efficiency metric |
| Cost per hire (CPH) | SUM(spend_inr) / SUM(hires) | Advertising INR per hire, excluding other hiring costs |
| Qualification rate | SUM(qualified_applicants) / SUM(completed_applications) | Screening quality among completed applications |
| Step conversion | SUM(next stage) / SUM(previous stage) | Share advancing to the next stage |

Undefined ratios (zero denominator) are stored as NaN and displayed as **N/A**, never zero or infinity. Undefined time-series points are gaps; undefined channel costs are excluded from bars with an explanatory caption. A genuine zero numerator with a positive denominator produces zero. Candidate-funnel percentages use **application starts** as their base; the conversion table uses the **previous stage**.

**Why average row rates fail:** 10 clicks from 100 impressions and 9 clicks from 900 impressions have row CTRs of 10% and 1%. The correct combined CTR is 19/1,000 = **1.9%**, not (10% + 1%)/2 = 5.5%. In Excel, think `SUM(clicks)/SUM(impressions)`, not `AVERAGE(CTR)`.

## Architecture and SQL

```text
hirelens/
├── app.py                      # Streamlit entrypoint, filters and navigation
├── hirelens/
│   ├── config.py               # Fixed settings, names and labels
│   ├── generate.py             # Reproducible simulation and validation
│   ├── database.py             # SQLite schema, bound filters, SQL aggregation
│   ├── metrics.py              # Ratio calculations and INR/N/A formatting
│   ├── charts.py               # Plotly chart builders
│   └── views.py                # Overview, Channel Performance, Candidate Funnel
├── scripts/generate_data.py    # Regenerate SQLite and full CSV
├── data/                       # Generated hirelens.db and hirelens.csv (gitignored)
├── tests/                      # Integrity, metrics, SQL and Streamlit interaction tests
├── .streamlit/config.toml      # Theme and local server settings
├── pytest.ini
├── requirements.txt            # Compatible direct dependency ranges
├── requirements-lock.txt       # Exact tested environment
└── README.md
```

Flow: generate → validate → insert into SQLite → filter and aggregate in SQL → calculate ratios in pandas → render with Plotly/Streamlit. No user-entered value is interpolated into SQL. Bound `?` parameters cover dates and category selections; SQL grouping identifiers come from an allowlist. The database has a composite primary key, nonnegative count/spend checks, integer count checks and funnel-order constraints. Rerunning the generator replaces the project's `cohorts` table, avoiding duplicate rows.

Representative query (the app builds matching placeholder counts for selected categories):

```sql
SELECT channel,
       SUM(spend_inr) AS spend_inr,
       SUM(qualified_applicants) AS qualified_applicants
FROM cohorts
WHERE date >= ? AND date <= ? AND role IN (?) AND city IN (?)
GROUP BY channel
ORDER BY channel;
-- Bound values: ('2025-01-01', '2025-03-31', 'Data Analyst', 'Mumbai')
-- Then CPQA = spend_inr / qualified_applicants; zero denominator -> N/A.
```

## How to discuss this in an interview

1. Start with the decision: identify channels acquiring qualified applicants efficiently, then assess volume and hiring quality.
2. Explain the grain before presenting metrics. In Excel terms, the SQLite table is the clean source table and grouped SQL totals play the role of PivotTables.
3. Walk through the Overview, then compare channels within the same role/city. Broad channel rankings can reflect different segment mixes.
4. Use Candidate Funnel to identify where journeys stop progressing. A large loss suggests a place to investigate, not a proven cause or automatic optimization target.
5. Explain why cohort maturity and ratios of sums matter. Low CPQA alone is insufficient for budget allocation; confirm volume, cost per hire, uncertainty and operational capacity with real data.

Suggested next experiment: compare a small controlled budget change for comparable roles/cities using mature cohorts. This project is descriptive and synthetic; it does not estimate causal channel lift or validate real business recommendations.

### Example readout from the default simulation

Across all 90 days and segments, SkillSignal has the lowest CPQA (**₹32.45**, 59,240 qualified applicants). HireHarbor has slightly more qualified applicants (**59,683**) at **₹35.60** each. RoleRipple produces cheap clicks (**₹3.68 CPC**) but the highest CPQA (**₹111.96**). That illustrates why optimizing clicks alone can miss the business objective. These results follow from the simulation's assumptions; they are not findings about real advertising platforms. Recalculate the comparison within one role and city before explaining the channel ranking.

## Verification and maintenance

Verified locally on 5 October 2026 with Python 3.13.3: **18 tests passed**, `pip check` reported no broken requirements, and the running server health endpoint returned `ok`. Browser review covered the three pages, chart rendering, desktop/narrow layouts, and a real CSV download reconciled against all 5,400 SQLite rows. The automated interaction test also checks combined date/channel/role/city filtering, clearing selections, and resetting. This is representative interaction coverage, not an exhaustive test of every possible filter combination.

`python -m pytest -q` checks the complete grid and deterministic seed; negative, non-finite and fractional data; funnel consistency; meaningful variation; weighted ratios and N/A; inclusive SQL dates and multiple filters; SQL injection handling; persistence constraints; CSV reconciliation; page navigation, filter changes, empty states, partial dates and reset. Tests use temporary databases for persistence checks. Streamlit smoke tests use the app's default database, so regenerate the default seed before testing if you have experimented with a custom seed.

If the database is unavailable/corrupt, stop the app and rerun `python -m scripts.generate_data`. Use `--seed 43 --database data/experiment.db` for a separate experiment; the dashboard continues to read `data/hirelens.db`. No credentials or external services are required.

Implementation references: [Streamlit chart API](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart), [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest). Business data and model assumptions are entirely generated locally.

