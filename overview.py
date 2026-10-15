import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client

from calculations import (
    weighted_maturity_score,
    state_score_by_dimension
)


# ==================================================
# DASHBOARD COLOURS
# ==================================================

NAVY = "#173F6B"
LIGHT_BLUE = "#69B3F3"
GRID = "rgba(23, 63, 107, 0.15)"
TEXT = "#17375E"


# ==================================================
# SUPABASE CONNECTION
# ==================================================

@st.cache_resource
def init_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )


supabase = init_supabase()


# ==================================================
# LOAD ASSESSMENT DATA
# ==================================================

@st.cache_data(ttl=5)
def load_data():
    response = (
        supabase
        .table("vw_analytics_maturity_reporting")
        .select("*")
        .execute()
    )

    return pd.DataFrame(response.data)


# ==================================================
# DASHBOARD
# ==================================================

st.title("Overview")

try:

    # ==================================================
    # LOAD DATA
    # ==================================================

    df = load_data()

    if df.empty:
        st.info(
            "No assessment responses are available yet."
        )
        st.stop()


    # ==================================================
    # PREPARE ASSESSMENT DATA
    # ==================================================

    df["score"] = pd.to_numeric(
        df["score"],
        errors="coerce"
    )

    df["weight"] = pd.to_numeric(
        df["weight"],
        errors="coerce"
    )


    # ==================================================
    # KPI CALCULATIONS
    # ==================================================

    current_df = df[
        df["state"] == "Current"
    ].copy()

    future_df = df[
        df["state"] == "Future"
    ].copy()


    current_score = weighted_maturity_score(
        current_df
    )

    future_score = weighted_maturity_score(
        future_df
    )

    maturity_gap = (
        future_score - current_score
    )

    # Use response_id so each submitted assessment
    # is counted once.
    organizations_surveyed = (
        df["response_id"]
        .dropna()
        .nunique()
    )


    # ==================================================
    # OVERVIEW KPI CARDS
    # ==================================================

    col1, col2, col3, col4 = st.columns(4)


    with col1:

        with st.container(border=True):

            st.metric(
                "Overall Current State Score",
                f"{current_score:.2f}"
            )


    with col2:

        with st.container(border=True):

            st.metric(
                "Overall Future State Score",
                f"{future_score:.2f}"
            )


    with col3:

        with st.container(border=True):

            st.metric(
                "Maturity Gap",
                f"{maturity_gap:.2f}"
            )


    with col4:

        with st.container(border=True):

            st.metric(
                "Organizations Surveyed",
                organizations_surveyed
            )


    # ==================================================
    # DIMENSION SCORES
    # ==================================================

    dimension_scores = state_score_by_dimension(
        df
    )

    if dimension_scores.empty:

        st.info(
            "Dimension-level maturity scores "
            "are not available yet."
        )

        st.stop()


    # ==================================================
    # RADAR CHART LABELS
    # ==================================================

    dimensions = (
        dimension_scores["dimension"]
        .astype(str)
        .tolist()
    )


    dimension_labels = {

        "Business Decisions & Analytics":
            "Business Decisions<br>& Analytics",

        "Data & Information":
            "Data & Information",

        "Technology & Infrastructure":
            "Technology<br>& Infrastructure",

        "Process & Integration":
            "Process & Integration",

        "Organization & Governance":
            "Organization<br>& Governance"
    }


    radar_dimensions = [
        dimension_labels.get(
            dimension,
            dimension
        )
        for dimension in dimensions
    ]


    # Close radar polygon
    radar_dimensions_closed = (
        radar_dimensions
        + [radar_dimensions[0]]
    )


    # ==================================================
    # CURRENT STATE VALUES
    # ==================================================

    current_scores = (
        dimension_scores["Current"]
        .astype(float)
        .tolist()
    )

    current_scores_closed = (
        current_scores
        + [current_scores[0]]
    )


    # ==================================================
    # FUTURE STATE VALUES
    # ==================================================

    future_scores = (
        dimension_scores["Future"]
        .astype(float)
        .tolist()
    )

    future_scores_closed = (
        future_scores
        + [future_scores[0]]
    )


    # ==================================================
    # DIMENSION RADAR CHARTS
    # ==================================================

    st.write("")

    dimension_col1, dimension_col2 = st.columns(2)


    # ==================================================
    # CURRENT STATE RADAR
    # ==================================================

    with dimension_col1:

        fig_current_dimension = go.Figure()


        fig_current_dimension.add_trace(

            go.Scatterpolar(

                r=current_scores_closed,

                theta=radar_dimensions_closed,

                mode="lines+markers",

                name="Current State Score",

                line=dict(
                    color=NAVY,
                    width=3
                ),

                marker=dict(
                    size=8,
                    color=NAVY
                ),

                fill="toself",

                fillcolor=(
                    "rgba(23, 63, 107, 0.10)"
                ),

                customdata=(
                    dimensions
                    + [dimensions[0]]
                ),

                hovertemplate=(
                    "<b>%{customdata}</b><br>"
                    "Current State Score: %{r:.2f}"
                    "<extra></extra>"
                )
            )
        )


        fig_current_dimension.update_layout(

            paper_bgcolor="rgba(0,0,0,0)",

            plot_bgcolor="rgba(0,0,0,0)",

            font=dict(
                color=TEXT
            ),

            polar=dict(

                bgcolor="rgba(0,0,0,0)",

                radialaxis=dict(

                    visible=True,

                    range=[0, 5],

                    tickvals=[
                        1,
                        2,
                        3,
                        4,
                        5
                    ],

                    gridcolor=GRID,

                    linecolor=GRID
                ),

                angularaxis=dict(

                    gridcolor=GRID,

                    linecolor=GRID,

                    tickfont=dict(
                        size=11,
                        color=TEXT
                    )
                )
            ),

            legend=dict(

                orientation="h",

                yanchor="bottom",

                y=1.05,

                xanchor="center",

                x=0.5
            ),

            hoverlabel=dict(
                bgcolor="white",
                font_color=TEXT
            ),

            height=520,

            margin=dict(
                l=70,
                r=70,
                t=80,
                b=60
            )
        )


        with st.container(border=True):

            st.subheader(
                "Current State Score by Dimension"
            )

            st.plotly_chart(
                fig_current_dimension,
                use_container_width=True
            )


    # ==================================================
    # FUTURE STATE RADAR
    # ==================================================

    with dimension_col2:

        fig_future_dimension = go.Figure()


        fig_future_dimension.add_trace(

            go.Scatterpolar(

                r=future_scores_closed,

                theta=radar_dimensions_closed,

                mode="lines+markers",

                name="Future State Score",

                line=dict(
                    color=LIGHT_BLUE,
                    width=3
                ),

                marker=dict(
                    size=8,
                    color=LIGHT_BLUE
                ),

                fill="toself",

                fillcolor=(
                    "rgba(105, 179, 243, 0.10)"
                ),

                customdata=(
                    dimensions
                    + [dimensions[0]]
                ),

                hovertemplate=(
                    "<b>%{customdata}</b><br>"
                    "Future State Score: %{r:.2f}"
                    "<extra></extra>"
                )
            )
        )


        fig_future_dimension.update_layout(

            paper_bgcolor="rgba(0,0,0,0)",

            plot_bgcolor="rgba(0,0,0,0)",

            font=dict(
                color=TEXT
            ),

            polar=dict(

                bgcolor="rgba(0,0,0,0)",

                radialaxis=dict(

                    visible=True,

                    range=[0, 5],

                    tickvals=[
                        1,
                        2,
                        3,
                        4,
                        5
                    ],

                    gridcolor=GRID,

                    linecolor=GRID
                ),

                angularaxis=dict(

                    gridcolor=GRID,

                    linecolor=GRID,

                    tickfont=dict(
                        size=11,
                        color=TEXT
                    )
                )
            ),

            legend=dict(

                orientation="h",

                yanchor="bottom",

                y=1.05,

                xanchor="center",

                x=0.5
            ),

            hoverlabel=dict(
                bgcolor="white",
                font_color=TEXT
            ),

            height=520,

            margin=dict(
                l=70,
                r=70,
                t=80,
                b=60
            )
        )


        with st.container(border=True):

            st.subheader(
                "Future State Score by Dimension"
            )

            st.plotly_chart(
                fig_future_dimension,
                use_container_width=True
            )


# ==================================================
# ERROR HANDLING
# ==================================================

except Exception as e:

    st.error(
        "Unable to load dashboard data."
    )

    st.exception(e)