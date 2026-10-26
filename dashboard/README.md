# Local BI prototype
1. Install Python 3.10+.
2. From the project root run: `pip install -r dashboard/requirements.txt`
3. Run: `streamlit run dashboard/app.py`
4. Ensure the `data/silver` files are present.
This dashboard reads local synthetic CSV files; it is not connected to BigQuery until a connector/query layer is added.
streamlit run app.py 