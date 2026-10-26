# Deploy Education DW Dashboard on Streamlit Community Cloud

## Entry point
Set the Main file path to:
`dashboard/app.py`

## Default behavior
The app starts in Local Silver mode. The dashboard uses the CSV files in:
`data/silver/`

BigQuery Live is optional and read-only in this deployment version. The app looks for
a Streamlit Secret named `gcp_service_account`. Do not commit credentials or JSON key
files to GitHub.

## GitHub preparation
1. Upload the contents of this project folder to a GitHub repository.
2. Confirm `dashboard/app.py`, `dashboard/requirements.txt`, `requirements.txt`, and `data/silver/*.csv` are present.
3. Do not upload `gcp_key.json`, service-account JSON, or `.streamlit/secrets.toml`.

## Streamlit Community Cloud
1. Sign in at https://share.streamlit.io/
2. Select **Create app** and choose the repository and branch.
3. Set Main file path to `dashboard/app.py`.
4. Deploy.

## Optional BigQuery Live setup
Only if you want Live mode:
1. Create or use a dedicated service account with the minimum required read permissions on the intended dataset.
2. In the app's **Settings → Secrets**, add a TOML section named `gcp_service_account` with the service account JSON fields as TOML values.
3. Grant only read access for the dashboard. This build disables write buttons because the original app used `CREATE OR REPLACE TABLE` against Silver tables.
4. Never expose service-account credentials in a public repository.
