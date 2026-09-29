import streamlit as st
import pandas as pd
from supabase import create_client

from dimension_page import render_dimension_page


# --------------------------------------------------
# Supabase connection
# --------------------------------------------------
@st.cache_resource
def init_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )


supabase = init_supabase()


# --------------------------------------------------
# Load data
# --------------------------------------------------
@st.cache_data(ttl=5)
def load_data():

    response = (
        supabase
        .table("vw_analytics_maturity_reporting")
        .select("*")
        .execute()
    )

    return pd.DataFrame(response.data)


# --------------------------------------------------
# Load and prepare data
# --------------------------------------------------
try:

    df = load_data()

    df["score"] = pd.to_numeric(
        df["score"],
        errors="coerce"
    )

    df["weight"] = pd.to_numeric(
        df["weight"],
        errors="coerce"
    )

    df["question_order"] = pd.to_numeric(
        df["question_order"],
        errors="coerce"
    )


    # --------------------------------------------------
    # Render page
    # --------------------------------------------------
    render_dimension_page(
        df=df,
        dimension="Technology & Infrastructure",
        title="Technology & Infrastructure"
    )


except Exception as e:

    st.error(
        "Unable to load dashboard data."
    )

    st.exception(e)