# streamlit_app.py

import streamlit as st
import pandas as pd
import altair as alt

from google.oauth2 import service_account
from google.cloud import bigquery

BAR_WIDTH = 15

# Perform query.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=600)
def run_query(query):
    return client.query(query).to_dataframe()
    

# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)



df = run_query("SELECT * FROM `personal-consumption-tracker.consumption.combined_drinks`")

df["day_of_week"] = df["date_time"].dt.day_name()
df["day_number_of_week"] = df["date_time"].dt.day_of_week

st.markdown("### Alcoholic drinks consumed per time period")

aggregation_dict = {"month":"MS","quarter":"QS"}
aggregation = st.selectbox("aggregation",aggregation_dict.keys())
aggregation_short = aggregation_dict.get(aggregation)

def drinks_per_period(df, aggregation_short):

    df_agg = df.set_index("date_time").resample(aggregation_short,convention='start').count().reset_index()

    c = alt.Chart(df_agg).mark_bar(width=BAR_WIDTH).encode(x="date_time",y="drink_type").properties(
        title=f'drinks per {aggregation}'
    )

    st.altair_chart(c, use_container_width=True)

drinks_per_period(df, aggregation_short)

