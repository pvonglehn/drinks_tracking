import streamlit as st
import pandas as pd
import altair as alt
import os

from helpers import get_bigquery_client, run_query


def get_and_process_data():

    client = get_bigquery_client()
    query = "SELECT * FROM `personal-consumption-tracker.dbt_pvonglehn.fasting_times`"
    df = run_query(query, client)
    
    return df

if __name__ == "__main__":

    st.markdown("### Alcoholic drinks consumed per time period")

    df = get_and_process_data()

    st.write(df)