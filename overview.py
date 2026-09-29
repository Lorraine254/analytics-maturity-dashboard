import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

from calculations import (
    weighted_maturity_score,
    state_score_by_dimension,
    maturity_gap_by_dimension,
    state_score_by_organization,
    maturity_gap_by_organization
)



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
# Load reporting data
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
# Dashboard
# --------------------------------------------------
st.title("Analytics Maturity Dashboard")

try:

    # --------------------------------------------------
    # Load data
    # --------------------------------------------------
    df = load_data()

    # Ensure score and weight are numeric
    df["score"] = pd.to_numeric(
        df["score"],
        errors="coerce"
    )

    df["weight"] = pd.to_numeric(
        df["weight"],
        errors="coerce"
    )


    # --------------------------------------------------
    # Current and Future datasets
    # --------------------------------------------------
    current_df = df[
        df["state"] == "Current"
    ].copy()

    future_df = df[
        df["state"] == "Future"
    ].copy()


    # --------------------------------------------------
    # Overall scores
    # --------------------------------------------------
    current_score = weighted_maturity_score(
        current_df
    )

    future_score = weighted_maturity_score(
        future_df
    )

    maturity_gap = (
        future_score - current_score
    )

    organizations_surveyed = (
        df["company_name"]
        .dropna()
        .nunique()
    )


    # --------------------------------------------------
    # Overview
    # --------------------------------------------------
    st.subheader("Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Overall Current State Score",
            value=f"{current_score:.2f}"
        )

    with col2:
        st.metric(
            label="Overall Future State Score",
            value=f"{future_score:.2f}"
        )

    with col3:
        st.metric(
            label="Maturity Gap",
            value=f"{maturity_gap:.2f}"
        )

    with col4:
        st.metric(
            label="Organizations Surveyed",
            value=organizations_surveyed
        )


    # --------------------------------------------------
    # State filter
    # Controls both dimension and organization charts
    # --------------------------------------------------
    st.write("")

    state_view = st.segmented_control(
        "State",
        options=[
            "Current",
            "Future",
            "Current vs Future"
        ],
        default="Current vs Future",
        key="overview_state"
    )


    # ==================================================
    # DIMENSION ANALYSIS
    # ==================================================

    dimension_scores = state_score_by_dimension(df)
    gap_scores = maturity_gap_by_dimension(df)

    dimension_col1, dimension_col2 = st.columns(2)


    # --------------------------------------------------
    # State Score by Dimension
    # --------------------------------------------------
    with dimension_col1:

        st.subheader("State Score by Dimension")

        if state_view == "Current":

            chart_data = dimension_scores[
                ["dimension", "Current"]
            ].copy()

            chart_data = chart_data.rename(
                columns={"Current": "Score"}
            )

            fig_dimension = px.bar(
                chart_data,
                x="dimension",
                y="Score",
                text_auto=".2f"
            )

        elif state_view == "Future":

            chart_data = dimension_scores[
                ["dimension", "Future"]
            ].copy()

            chart_data = chart_data.rename(
                columns={"Future": "Score"}
            )

            fig_dimension = px.bar(
                chart_data,
                x="dimension",
                y="Score",
                text_auto=".2f"
            )

        else:

            chart_data = dimension_scores.melt(
                id_vars="dimension",
                value_vars=[
                    "Current",
                    "Future"
                ],
                var_name="State",
                value_name="Score"
            )

            fig_dimension = px.bar(
                chart_data,
                x="dimension",
                y="Score",
                color="State",
                barmode="group",
                text_auto=".2f"
            )

        fig_dimension.update_layout(
            xaxis_title=None,
            yaxis_title="State Score",
            yaxis=dict(
                range=[0, 5.5],
                dtick=1
            ),
            legend_title_text=None,
            height=450,
            margin=dict(
                l=20,
                r=20,
                t=20,
                b=100
            )
        )

        fig_dimension.update_traces(
            textposition="outside",
            cliponaxis=False
        )

        st.plotly_chart(
            fig_dimension,
            use_container_width=True
        )


    # --------------------------------------------------
    # Maturity Gap by Dimension
    # --------------------------------------------------
    with dimension_col2:

        st.subheader("Maturity Gap by Dimension")

        fig_dimension_gap = px.bar(
            gap_scores,
            x="dimension",
            y="maturity_gap",
            text_auto=".2f"
        )

        fig_dimension_gap.update_layout(
            xaxis_title=None,
            yaxis_title="Maturity Gap",
            yaxis=dict(
                rangemode="tozero"
            ),
            height=450,
            margin=dict(
                l=20,
                r=20,
                t=20,
                b=100
            )
        )

        fig_dimension_gap.update_traces(
            textposition="outside",
            cliponaxis=False
        )

        st.plotly_chart(
            fig_dimension_gap,
            use_container_width=True
        )


    # ==================================================
    # ORGANIZATION ANALYSIS
    # ==================================================

    organization_scores = state_score_by_organization(df)

    organization_gap = maturity_gap_by_organization(df)

    organization_col1, organization_col2 = st.columns(2)


    # --------------------------------------------------
    # State Score by Organization
    # --------------------------------------------------
    with organization_col1:

        st.subheader("State Score by Organization")

        if state_view == "Current":

            org_chart_data = organization_scores[
                ["company_name", "Current"]
            ].copy()

            org_chart_data = org_chart_data.rename(
                columns={"Current": "Score"}
            )

            fig_organization = px.bar(
                org_chart_data,
                x="Score",
                y="company_name",
                orientation="h",
                text_auto=".2f"
            )

        elif state_view == "Future":

            org_chart_data = organization_scores[
                ["company_name", "Future"]
            ].copy()

            org_chart_data = org_chart_data.rename(
                columns={"Future": "Score"}
            )

            fig_organization = px.bar(
                org_chart_data,
                x="Score",
                y="company_name",
                orientation="h",
                text_auto=".2f"
            )

        else:

            org_chart_data = organization_scores.melt(
                id_vars="company_name",
                value_vars=[
                    "Current",
                    "Future"
                ],
                var_name="State",
                value_name="Score"
            )

            fig_organization = px.bar(
                org_chart_data,
                x="Score",
                y="company_name",
                color="State",
                orientation="h",
                barmode="group",
                text_auto=".2f"
            )

        fig_organization.update_layout(
            xaxis_title="State Score",
            yaxis_title=None,
            xaxis=dict(
                range=[0, 5.5],
                dtick=1
            ),
            legend_title_text=None,
            height=450,
            margin=dict(
                l=20,
                r=40,
                t=20,
                b=40
            )
        )

        fig_organization.update_traces(
            textposition="outside",
            cliponaxis=False
        )

        st.plotly_chart(
            fig_organization,
            use_container_width=True
        )


    # --------------------------------------------------
    # Maturity Gap by Organization
    # --------------------------------------------------
    with organization_col2:

        st.subheader("Maturity Gap by Organization")

        fig_organization_gap = px.bar(
            organization_gap,
            x="maturity_gap",
            y="company_name",
            orientation="h",
            text_auto=".2f"
        )

        fig_organization_gap.update_layout(
            xaxis_title="Maturity Gap",
            yaxis_title=None,
            xaxis=dict(
                rangemode="tozero"
            ),
            height=450,
            margin=dict(
                l=20,
                r=40,
                t=20,
                b=40
            )
        )

        fig_organization_gap.update_traces(
            textposition="outside",
            cliponaxis=False
        )

        st.plotly_chart(
            fig_organization_gap,
            use_container_width=True
        )


except Exception as e:

    st.error(
        "Unable to load dashboard data."
    )

    st.exception(e)