import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client

from calculations import (
    weighted_maturity_score,
    state_score_by_dimension,
    state_score_by_organization,
    maturity_gap_by_organization,
    benchmark_score_by_dimension
)


# ==================================================
# DASHBOARD COLOURS
# ==================================================

NAVY = "#173F6B"
LIGHT_BLUE = "#69B3F3"
GOLD = "#D9B300"
GRID = "rgba(23, 63, 107, 0.15)"
TEXT = "#17375E"

STATE_COLORS = {
    "Current": NAVY,
    "Future": LIGHT_BLUE
}


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
# LOAD BENCHMARK DATA
# ==================================================

@st.cache_data(ttl=5)
def load_benchmark_data():

    response = (
        supabase
        .table("benchmark_reference")
        .select("*")
        .execute()
    )

    return pd.DataFrame(response.data)


# ==================================================
# SHARED CHART STYLING
# ==================================================

def style_chart(fig):

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color=TEXT
        ),
        legend_title_text=None,
        hoverlabel=dict(
            bgcolor="white",
            font_color=TEXT
        )
    )

    fig.update_xaxes(
        gridcolor=GRID,
        zeroline=False
    )

    fig.update_yaxes(
        gridcolor=GRID,
        zeroline=False
    )

    return fig


# ==================================================
# DASHBOARD
# ==================================================
st.title("Overview")
try:

    # ==================================================
    # LOAD DATA
    # ==================================================

    df = load_data()
    benchmark_df = load_benchmark_data()


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


    question_map_df = (
        df[
            ["question_id", "dimension"]
        ]
        .dropna()
        .drop_duplicates()
        .copy()
    )


    # ==================================================
    # PREPARE BENCHMARK DATA
    # ==================================================

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

        benchmark_df[column] = pd.to_numeric(
            benchmark_df[column],
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

    organizations_surveyed = (
        df["company_name"]
        .dropna()
        .nunique()
    )


    # ==================================================
    # OVERVIEW KPIs
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
    # INDUSTRY BENCHMARK SELECTOR
    # ==================================================

    st.write("")


    benchmark_metric = st.segmented_control(
        "Industry Benchmark",
        options=[
            "Average",
            "Lower Quartile",
            "Median",
            "Top Quartile"
        ],
        default="Average",
        key="overview_benchmark"
    )


    # ==================================================
    # BENCHMARK SCORES
    # ==================================================

    benchmark_scores = benchmark_score_by_dimension(
        benchmark_data=benchmark_df,
        question_map=question_map_df,
        metric=benchmark_metric
    )


    # ==================================================
    # DIMENSION SCORES
    # ==================================================

    dimension_scores = state_score_by_dimension(
        df
    )


    dimension_comparison = dimension_scores.merge(
        benchmark_scores,
        on="dimension",
        how="left"
    )


    # ==================================================
    # RADAR CHART LABELS
    # ==================================================

    dimensions = (
        dimension_comparison["dimension"]
        .astype(str)
        .tolist()
    )


    # Wrap only the longer labels
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
        dimension_comparison["Current"]
        .astype(float)
        .tolist()
    )

    current_benchmark = (
        dimension_comparison["benchmark_current"]
        .astype(float)
        .tolist()
    )


    current_scores_closed = (
        current_scores
        + [current_scores[0]]
    )

    current_benchmark_closed = (
        current_benchmark
        + [current_benchmark[0]]
    )


    # ==================================================
    # FUTURE STATE VALUES
    # ==================================================

    future_scores = (
        dimension_comparison["Future"]
        .astype(float)
        .tolist()
    )

    future_benchmark = (
        dimension_comparison["benchmark_future"]
        .astype(float)
        .tolist()
    )


    future_scores_closed = (
        future_scores
        + [future_scores[0]]
    )

    future_benchmark_closed = (
        future_benchmark
        + [future_benchmark[0]]
    )


    # ==================================================
    # DIMENSION RADAR CHARTS
    # ==================================================

    dimension_col1, dimension_col2 = st.columns(2)


    # ==================================================
    # CURRENT STATE RADAR
    # ==================================================

    with dimension_col1:

        fig_current_dimension = go.Figure()


        # --------------------------------------------------
        # Current State Score
        # --------------------------------------------------

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


        # --------------------------------------------------
        # Industry Benchmark
        # --------------------------------------------------

        fig_current_dimension.add_trace(

            go.Scatterpolar(

                r=current_benchmark_closed,

                theta=radar_dimensions_closed,

                mode="lines+markers",

                name="Industry Benchmark",

                line=dict(
                    color=GOLD,
                    width=3
                ),

                marker=dict(
                    size=8,
                    color=GOLD
                ),

                customdata=(
                    dimensions
                    + [dimensions[0]]
                ),

                hovertemplate=(
                    "<b>%{customdata}</b><br>"
                    f"{benchmark_metric} Industry Benchmark: "
                    "%{r:.2f}"
                    "<extra></extra>"
                )
            )
        )


        # --------------------------------------------------
        # Current radar layout
        # --------------------------------------------------

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


        # --------------------------------------------------
        # Future State Score
        # --------------------------------------------------

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


        # --------------------------------------------------
        # Industry Benchmark
        # --------------------------------------------------

        fig_future_dimension.add_trace(

            go.Scatterpolar(

                r=future_benchmark_closed,

                theta=radar_dimensions_closed,

                mode="lines+markers",

                name="Industry Benchmark",

                line=dict(
                    color=GOLD,
                    width=3
                ),

                marker=dict(
                    size=8,
                    color=GOLD
                ),

                customdata=(
                    dimensions
                    + [dimensions[0]]
                ),

                hovertemplate=(
                    "<b>%{customdata}</b><br>"
                    f"{benchmark_metric} Industry Benchmark: "
                    "%{r:.2f}"
                    "<extra></extra>"
                )
            )
        )


        # --------------------------------------------------
        # Future radar layout
        # --------------------------------------------------

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
    # ORGANIZATION ANALYSIS
    # ==================================================

    st.write("")


    organization_scores = (
        state_score_by_organization(df)
    )


    organization_gap = (
        maturity_gap_by_organization(df)
    )


    organization_col1, organization_col2 = (
        st.columns(2)
    )


    # ==================================================
    # STATE SCORE BY ORGANIZATION
    # ==================================================

    with organization_col1:

        org_chart_data = (
            organization_scores
            .melt(
                id_vars="company_name",

                value_vars=[
                    "Current",
                    "Future"
                ],

                var_name="State",

                value_name="Score"
            )
        )


        fig_organization = px.bar(

            org_chart_data,

            x="Score",

            y="company_name",

            color="State",

            orientation="h",

            barmode="group",

            text_auto=".2f",

            color_discrete_map=STATE_COLORS
        )


        number_of_organizations = len(
            organization_scores
        )


        organization_chart_height = max(
            350,
            number_of_organizations * 45 + 150
        )


        fig_organization.update_layout(

            xaxis_title="State Score",

            yaxis_title=None,

            xaxis=dict(
                range=[0, 5.5],
                dtick=1
            ),

            height=organization_chart_height,

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


        style_chart(
            fig_organization
        )


        with st.container(border=True):

            st.subheader(
                "State Score by Organization"
            )

            st.plotly_chart(
                fig_organization,
                use_container_width=True
            )


    # ==================================================
    # MATURITY GAP BY ORGANIZATION
    # ==================================================

    with organization_col2:

        fig_organization_gap = px.bar(

            organization_gap,

            x="maturity_gap",

            y="company_name",

            orientation="h",

            text_auto=".2f",

            color_discrete_sequence=[
                NAVY
            ]
        )


        fig_organization_gap.update_layout(

            xaxis_title="Maturity Gap",

            yaxis_title=None,

            xaxis=dict(
                rangemode="tozero"
            ),

            height=organization_chart_height,

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


        style_chart(
            fig_organization_gap
        )


        with st.container(border=True):

            st.subheader(
                "Maturity Gap by Organization"
            )

            st.plotly_chart(
                fig_organization_gap,
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