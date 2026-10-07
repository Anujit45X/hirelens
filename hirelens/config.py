"""Shared names and fixed simulation settings."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "data" / "hirelens.db"
SEED = 42
START_DATE = "2025-01-01"
DAYS = 90
CHANNELS = ("TalentBeacon", "CareerOrbit", "RoleRipple", "HireHarbor", "SkillSignal")
ROLES = ("Software Engineer", "Data Analyst", "Sales Executive", "Customer Support")
CITIES = ("Bengaluru", "Mumbai", "Hyderabad")
DIMENSIONS = ("date", "channel", "role", "city")
FUNNEL = (
    "impressions", "clicks", "application_starts", "completed_applications",
    "qualified_applicants", "interviews", "hires",
)
MEASURES = ("spend_inr", *FUNNEL)
LABELS = {
    "spend_inr": "Spend (INR)", "impressions": "Impressions", "clicks": "Clicks",
    "application_starts": "Application starts", "completed_applications": "Completed applications",
    "qualified_applicants": "Qualified applicants", "interviews": "Interviews", "hires": "Hires",
    "ctr": "CTR", "cpc": "Cost per click (INR)", "cpa": "Cost per application (INR)",
    "cpqa": "Cost per qualified applicant (INR)", "cph": "Cost per hire (INR)",
    "qualification_rate": "Qualification rate", "channel": "Channel", "role": "Role",
    "city": "City", "date": "Acquisition date",
}
