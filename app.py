import streamlit as st
import pandas as pd
import altair as alt

from google.oauth2 import service_account
from google.cloud import bigquery

READ_FROM_FILE = True

BAR_WIDTH = 15

def get_bigquery_client():
    """Get Bigquery API client"""

    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return bigquery.Client(credentials=credentials)

@st.experimental_memo(ttl=600)
def run_query(query, _client):
    """Run database query"""

    return _client.query(query).to_dataframe()
    
def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Add features to dataframe"""

    df["day_of_week"] = df["date_time"].dt.day_name()
    df["day_number_of_week"] = df["date_time"].dt.day_of_week

    return df

def get_and_process_data():
    if READ_FROM_FILE:
        df = pd.read_csv("data/test_data.csv", parse_dates=['date_time'])
    else:
        client = get_bigquery_client()
        query = "SELECT * FROM `personal-consumption-tracker.consumption.combined_drinks`"
        df = run_query(query, client)
    
    return process_dataframe(df)


def chart_drinks_per_period(df, aggregation_short):
    """Make a bar chart of the number of drinks consumed per time period"""

    df_agg = df.set_index("date_time").resample(aggregation_short,convention='start').count().reset_index()

    c = alt.Chart(df_agg).mark_bar(width=BAR_WIDTH).encode(x="date_time",y="drink_type").properties(
        title=f'drinks per {aggregation}'
    )

    st.altair_chart(c, use_container_width=True)

def chart_drinks_per_day_of_week(df):
    drinks_count = df.groupby(["day_of_week","day_number_of_week"]).size().rename("count_of_drinks")

    min_date = df["date_time"].min()
    max_date = df["date_time"].max()
    df_date_range = pd.DataFrame(pd.date_range(min_date.date(),max_date.date()),columns=["date"])

    df_date_range["day_of_week"] = df_date_range["date"].dt.day_name()
    df_date_range["day_number_of_week"] = df_date_range["date"].dt.day_of_week
    day_counts = df_date_range.groupby(["day_of_week","day_number_of_week"]).size().rename("count_of_days")

    df_drinks_per_day = pd.concat([drinks_count, day_counts],axis=1).reset_index().sort_values("day_number_of_week")
    df_drinks_per_day["drinks_per_day"] = df_drinks_per_day["count_of_drinks"] / df_drinks_per_day["count_of_days"]

    c = alt.Chart(df_drinks_per_day).mark_bar().encode(x="day_number_of_week",y="drinks_per_day").properties(
        title=f'drinks per day'
    )

    st.altair_chart(c, use_container_width=True)

if __name__ == "__main__":

    st.markdown("### Alcoholic drinks consumed per time period")

    df = get_and_process_data()
    
    aggregation_dict = {"month":"MS","quarter":"QS"}
    aggregation = st.selectbox("aggregation",aggregation_dict.keys())
    aggregation_short = aggregation_dict.get(aggregation)

    chart_drinks_per_period(df, aggregation_short)  

    chart_drinks_per_day_of_week(df)