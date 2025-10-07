"""Streamlit dashboard visualizing metrics stored in DuckDB."""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

from app.config import get_settings

st.set_page_config(page_title="Data Platform Analytics", layout="wide")
st.title("Data Platform Metrics")

settings = get_settings()
warehouse_path = Path(settings.duckdb_path)

if not warehouse_path.exists():
    st.info("No data available yet. Run the ETL flow or ingest via the API.")
else:
    with duckdb.connect(str(warehouse_path)) as conn:
        df = conn.execute("select * from metrics order by timestamp desc").fetch_df()
    st.metric("Records", len(df))
    st.dataframe(df, use_container_width=True)

    if not df.empty:
        trend = (
            df.groupby(["metric", pd.Grouper(key="timestamp", freq="1H")])["value"].mean()
            .reset_index()
        )
        fig = px.line(trend, x="timestamp", y="value", color="metric", title="Metric Trends")
        st.plotly_chart(fig, use_container_width=True)

        alerts = df[df["value"] > df["value"].mean() * 1.5]
        if not alerts.empty:
            st.warning("Anomaly detected for metrics: " + ", ".join(alerts["metric"].unique()))
        else:
            st.success("No anomalies detected")
