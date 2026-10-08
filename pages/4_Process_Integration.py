import streamlit as st
import pandas as pd
from supabase import create_client

from dimension_page import render_dimension_page


# -------------------------------------------------
# Initialize Supabase
# -------------------------------------------------

@st.cache_resource
def init_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )


supabase = init_supabase()


# -------------------------------------------------
# Load assessment data
# -------------------------------------------------

@st.cache_data(ttl=5)
def load_data():
    response = (
        supabase
        .table("vw_analytics_maturity_reporting")
        .select("*")
        .execute()
    )

    return pd.DataFrame(response.data)


# -------------------------------------------------
# Load benchmark data
# -------------------------------------------------

@st.cache_data(ttl=300)
def load_benchmark_data():
    response = (
        supabase
        .table("benchmark_reference")
        .select("*")
        .execute()
    )

    return pd.DataFrame(response.data)


# -------------------------------------------------
# Render Process & Integration page
# -------------------------------------------------

try:

    # ---------------------------------------------
    # Load assessment data
    # ---------------------------------------------

    df = load_data()

    if df.empty:
        st.info("No assessment responses are available yet.")
        st.stop()

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


    # ---------------------------------------------
    # Load benchmark data
    # ---------------------------------------------

    benchmark_df = load_benchmark_data()

    benchmark_columns = [
        "average_current",
        "average_future",
        "lower_quartile_current",
        "lower_quartile_future",
        "median_current",
        "median_future",
        "top_quartile_current",
        "top_quartile_future"
    ]

    for column in benchmark_columns:

        if column in benchmark_df.columns:

            benchmark_df[column] = pd.to_numeric(
                benchmark_df[column],
                errors="coerce"
            )


    # ---------------------------------------------
    # Render page
    # ---------------------------------------------

    render_dimension_page(
        df=df,
        benchmark_df=benchmark_df,
        dimension="Process & Integration",
        title="Process & Integration"
    )


except Exception as e:

    st.error(
        "Unable to load dashboard data."
    )

    st.exception(e)