# Launch HireLens on Streamlit Community Cloud

This public portfolio app contains synthetic data only. It requires no API keys or secrets.

## Deployment settings

- Repository: `Anujit45X/hirelens`
- Branch: `main`
- Main file: `app.py`
- Python version in Advanced settings: **3.13**
- Dependency file: `requirements.txt` at the repository root
- Theme: `.streamlit/config.toml` at the repository root

At [Streamlit Community Cloud](https://share.streamlit.io/), select **Create app**, select the repository/branch/file above, set Python 3.13, and deploy. Choose an available app subdomain. The repository root is this HireLens project folder, not the containing local Fitplix workspace.

The cloud host runs Python; GitHub Pages cannot run this Streamlit/SQLite application. GitHub stores the source and runs the test workflow.

## Runtime behavior

The database is generated from seed 42 on first startup. Streamlit's cached initialization serializes setup across visitor sessions within the server process. The dashboard then queries SQLite using separate short-lived connections. The database is derived data, not a source of permanent user records; a host restart or redeployment can safely regenerate it. Do not regenerate or modify the database while serving visitors. Each deployed instance keeps its own identical synthetic database.

This is a deployed educational demonstration, not a system for processing real applicant information. It has no authentication, uploads, user profiles or writable business records. The synthetic-data and independence disclosures remain visible.

## Checks before sharing

1. Confirm the **Test HireLens** GitHub Actions workflow is green.
2. Open the live app and visit all three pages.
3. Filter to one channel, role, city and date range; confirm metrics and CSV match.
4. Clear a filter and check the empty state; reset to all values.
5. Keep the public app URL in the repository About field and README after successful deployment.

## Updates and rollback

Commit tested changes to `main`; Community Cloud watches the linked branch. For a failed deployment, inspect **Manage app → logs**. Revert the faulty commit in GitHub and redeploy/reboot from Community Cloud if needed. Dependencies are declared explicitly; `requirements-lock.txt` records the original local environment as a reference.

Documentation: [deployment settings](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [dependency discovery](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).
