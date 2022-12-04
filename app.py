# streamlit_app.py

import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from google.cloud import bigquery

# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)

# Perform query.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=600)
def run_query(query):
    return client.query(query).to_dataframe()


df = run_query("SELECT * FROM `personal-consumption-tracker.consumption.combined_drinks`").set_index("date_time")

df_agg = df.resample("M").count()

st.bar_chart(data=df_agg)

# st.write(df.resample("M").sum())