import streamlit as st
import pandas as pd
import altair as alt
import os

from helpers import get_bigquery_client, run_query

env = os.environ.get("STREAMLIT_ENV","prod")
READ_FROM_FILE = True if env == "dev" else False 

BAR_WIDTH = 15

def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Add features to dataframe"""

    df["day_of_week"] = df["date_time"].dt.day_name()
    df["day_number_of_week"] = df["date_time"].dt.day_of_week
    df["quarter"] = df["date_time"].dt.quarter
    df["year"] = df["date_time"].dt.year
    df["date"] = df["date_time"].dt.date

    return df

def get_and_process_data():
    if READ_FROM_FILE:
        df = pd.read_csv("data/test_data.csv", parse_dates=['date_time'])
    else:
        client = get_bigquery_client()
        query = "SELECT * FROM `personal-consumption-tracker.consumption.combined_drinks`"
        df = run_query(query, client)
    
    return process_dataframe(df)


def chart_drinks_per_period(df, aggregation_short, aggregation_label, normalization):
    """Make a bar chart of the number of drinks consumed per time period"""

    df_date_range = get_date_spine(df)

    df["date"] = pd.to_datetime(df["date_time"].dt.date, utc=True)
    df_date_range = df_date_range.merge(df.drop_duplicates(subset="date")[["date","drink_type"]], left_on="date", right_on="date", how="left")
    
    if aggregation_label == "day of week":
        count_of_days = df.groupby(["day_of_week","day_number_of_week"]).size().rename("count_of_drinks")
        count_of_drinks = df_date_range.groupby(["day_of_week","day_number_of_week"]).size().rename("count_of_days")
        count_drinking_days = ((df_date_range.groupby(["date","day_of_week","day_number_of_week"])["drink_type"].count() > 0)
        .groupby(["day_of_week","day_number_of_week"]).sum().rename("count_drinking_days"))

    else:
        count_of_days = df_date_range.set_index("date").resample(aggregation_short,convention='start').size().rename("count_of_days")
        count_of_drinks = df.set_index("date_time").resample(aggregation_short,convention='start').size().rename("count_of_drinks")
        count_drinking_days = (df_date_range.groupby("date")["drink_type"].count() > 0).resample(aggregation_short,convention='start').sum().rename("count_drinking_days")

    df_agg = pd.concat([count_of_drinks, count_of_days, count_drinking_days], axis=1).reset_index()
    df_agg = df_agg.rename({"index":"date_time"}, axis=1)
    df_agg["drinks_per_day"] = df_agg["count_of_drinks"] / df_agg["count_of_days"]
    df_agg["% days alcohol consumed"] = 100*(df_agg["count_drinking_days"] / df_agg["count_of_days"])


    if aggregation_label == "day of week":
        x = alt.X('day_of_week:N', type="nominal" ,sort=None)
        df_agg = df_agg.sort_values("day_number_of_week")

    else:
        x = "date_time"

    if normalization == 'average drinks per day':
        y_column_to_chart = "drinks_per_day"
        line = alt.Chart(pd.DataFrame({'y': [1]})).mark_rule().encode(y='y')
    elif normalization == "absolute count":
        y_column_to_chart = "count_of_drinks" 
        line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule().encode(y='y')
    elif normalization == "% days alcohol consumed":
        y_column_to_chart = "% days alcohol consumed"
        line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule().encode(y='y')



    c = alt.Chart(df_agg).mark_bar(width=BAR_WIDTH).encode(x=x,y=y_column_to_chart).properties(
        title=f'drinks by {aggregation_label}'
    )

    st.altair_chart(c + line, use_container_width=True)

def get_date_spine(df):
    """Get dataframe with days between max and min of dataframe"""

    min_date = df["date_time"].min()
    max_date = pd.to_datetime("today")
    df_date_range = pd.DataFrame(pd.date_range(min_date.date(),max_date.date(), tz="UTC"),columns=["date"])

    df_date_range["day_of_week"] = df_date_range["date"].dt.day_name()
    df_date_range["day_number_of_week"] = df_date_range["date"].dt.day_of_week

    return df_date_range


if __name__ == "__main__":

    st.markdown("### Alcoholic drinks consumed per time period")

    df = get_and_process_data()
    
    aggregation_dict = {"month":"MS","quarter":"QS","year":"YS","day of week":None}
    aggregation_label = st.selectbox("aggregation",aggregation_dict.keys())
    aggregation_short = aggregation_dict.get(aggregation_label)

    normalization = st.radio("normalization",["average drinks per day", "absolute count","% days alcohol consumed"])

    chart_drinks_per_period(df, aggregation_short, aggregation_label, normalization) 


    st.markdown(("#### Information about alcohol consumption and mortality risk" 
 
                 "\nConsuming 100g alcohol per week (roughly 1 drink per day) or more "
                 "is associated with increased risk of all cause mortality " 
                 "according to a 2018 [study](https://doi.org/10.1016/S0140-6736(18)30134-X) in the Lancet."
                 "\nAlthough moderate drinking is associated with lower risk of cardiovascular disease events"
                 ", there is no amount of alcohol consumption which results in lower all cause mortality risk."))
    st.image("media/all_cause_mortality.jpg") 

