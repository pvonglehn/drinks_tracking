import streamlit as st

from google.oauth2 import service_account
from google.cloud import bigquery

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