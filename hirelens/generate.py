"""Generate daily acquisition cohorts, each with fully observed simulated outcomes."""
import numpy as np
import pandas as pd

from hirelens.config import CHANNELS, CITIES, DAYS, DIMENSIONS, FUNNEL, MEASURES, ROLES, SEED, START_DATE


def validate_data(frame: pd.DataFrame) -> None:
    """Reject missing fields, duplicate grain, negative/fractional counts and invalid funnels."""
    expected = [*DIMENSIONS, *MEASURES]
    if list(frame.columns) != expected or frame.empty:
        raise ValueError("Expected nonempty data with the documented columns in order.")
    if frame.isna().any().any() or frame.duplicated(list(DIMENSIONS)).any():
        raise ValueError("Cohorts must have no nulls or duplicate dimension combinations.")
    pd.to_datetime(frame["date"], format="%Y-%m-%d", errors="raise")
    values = frame[list(MEASURES)].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Measures must be finite and nonnegative.")
    counts = frame[list(FUNNEL)].to_numpy(dtype=float)
    if (counts != np.floor(counts)).any():
        raise ValueError("Funnel counts must be integers.")
    if (np.diff(counts, axis=1) > 0).any():
        raise ValueError("Each downstream funnel count must be no greater than its parent.")


def generate_data(seed: int = SEED) -> pd.DataFrame:
    """Return 5,400 reproducible rows. Probabilities are teaching assumptions, not benchmarks."""
    rng = np.random.default_rng(seed)
    # Channel: daily budget, CPM, CTR, start rate, completion rate, qualification rate.
    profiles = {
        "TalentBeacon": (2100, 155, .030, .27, .68, .46),
        "CareerOrbit": (1900, 115, .024, .25, .72, .52),
        "RoleRipple": (1450, 72, .020, .22, .58, .26),
        "HireHarbor": (1700, 125, .028, .29, .76, .58),
        "SkillSignal": (1550, 175, .033, .30, .80, .68),
    }
    # Role: demand/budget, auction cost, qualification difficulty, interview-to-hire rate.
    role_profiles = {
        "Software Engineer": (1.30, 1.30, .82, .22),
        "Data Analyst": (1.05, 1.12, .93, .26),
        "Sales Executive": (1.10, .86, 1.10, .34),
        "Customer Support": (.82, .73, 1.15, .38),
    }
    city_profiles = {"Bengaluru": (1.20, 1.15), "Mumbai": (1.10, 1.10), "Hyderabad": (.90, .90)}
    rows = []
    for day_index, day in enumerate(pd.date_range(START_DATE, periods=DAYS)):
        weekend = day.dayofweek >= 5
        season = 1 + .10 * np.sin(2 * np.pi * day_index / 30)
        demand_trend = 1 + .0018 * day_index
        daily_market = rng.lognormal(0, .07)
        for channel in CHANNELS:
            budget, cpm, ctr, start_rate, completion_rate, quality = profiles[channel]
            for role in ROLES:
                demand, auction_cost, difficulty, hire_rate = role_profiles[role]
                for city in CITIES:
                    city_demand, city_cost = city_profiles[city]
                    spend = round(budget * demand * city_demand * season * demand_trend
                                  * (.72 if weekend else 1) * rng.lognormal(0, .22), 2)
                    actual_cpm = cpm * auction_cost * city_cost * daily_market * rng.lognormal(0, .12)
                    impressions = int(rng.poisson(spend / actual_cpm * 1000))
                    clicks = int(rng.binomial(impressions, min(.12, ctr * rng.lognormal(0, .12))))
                    starts = int(rng.binomial(clicks, start_rate * (.90 if weekend else 1)))
                    completed = int(rng.binomial(starts, completion_rate))
                    # An interaction makes segment comparisons meaningful rather than identical rankings.
                    fit = 1.18 if channel == "SkillSignal" and role == "Software Engineer" else 1.0
                    qualified = int(rng.binomial(completed, min(.92, quality * difficulty * fit)))
                    interviews = int(rng.binomial(qualified, .43 + .03 * np.sin(day_index / 14)))
                    hires = int(rng.binomial(interviews, hire_rate))
                    rows.append((day.strftime("%Y-%m-%d"), channel, role, city, spend,
                                 impressions, clicks, starts, completed, qualified, interviews, hires))
    frame = pd.DataFrame(rows, columns=[*DIMENSIONS, *MEASURES])
    validate_data(frame)
    return frame
