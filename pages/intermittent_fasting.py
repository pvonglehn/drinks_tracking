import streamlit as st
import pandas as pd
import altair as alt
import os
import datetime

from helpers import get_bigquery_client, run_query


def get_and_process_data():

    client = get_bigquery_client()
    query = "SELECT * FROM `personal-consumption-tracker.dbt_pvonglehn.fasting_times`"
    df = run_query(query, client)
    
    return df

if __name__ == "__main__":

    df = get_and_process_data()

    st.markdown("### Intermittent fasting")

    min_date = df["full_date"].min()
    max_date = datetime.datetime.now()

    start_date, end_date = st.date_input("Select date range", (min_date, max_date))

    df = df.loc[(df["full_date"].astype(str)>=str(start_date)) & (df["full_date"].astype(str)<=str(end_date))]

    cumsum = (df["fasting_time_hours"].value_counts(normalize=True)
                                    .sort_index(ascending=False)
                                    .cumsum()
                                    .rename("fraction_of_days")
                                    .to_frame()
                                    .reset_index()
                                    .rename({"index":"fasting_time_hours"},axis=1)
            )

    c = alt.Chart(cumsum).mark_bar().encode(x="fasting_time_hours",y="fraction_of_days").properties(
        title=f'fraction of days with nightly fasting hours >= x')

    try:
        fraction_above_16_hours = cumsum.query("fasting_time_hours == 16")["fraction_of_days"].values[0]
    except IndexError:
        fraction_above_16_hours = 0


    line_x = alt.Chart(pd.DataFrame({'x': [16]})).mark_rule(strokeDash=[3,5]).encode(x='x')
    line_y = alt.Chart(pd.DataFrame({'y': [fraction_above_16_hours]})).mark_rule(strokeDash=[3,5]).encode(y='y')




    st.altair_chart( c + line_x + line_y, use_container_width=True)
    st.markdown("### Information about intermittent fasting  "
                "\n'Intermittent fasting (IF) is an increasingly popular dietary approach used for weight loss and overall health.'"
                "See this 2016 [article](https://translational-medicine.biomedcentral.com/articles/10.1186/s12967-016-1044-0)"
                " in the Journal of Translational Medicine  "
                "\n\nOne common type of intermittent fasting is th 16:8 schedule, where food is consumed in an 8 hour window each day"
                "e.g. 11am-7pm followed by a 16 hour period of fasting.")