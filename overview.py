import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from supabase import create_client

from calculations import (
    weighted_maturity_score,
    state_score_by_dimension,
    industry_peer_benchmark_by_dimension
)


# ==================================================
# DASHBOARD COLOURS
# ==================================================

NAVY = "#173F6B"
LIGHT_BLUE = "#69B3F3"
GOLD = "#D9B300"
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
    # SELECTED ORGANIZATION
    # ==================================================

    # Keep the complete dataset for industry peer
    # benchmarking.
    all_df = df.copy()

    selected_response_id = st.session_state.get(
        "selected_response_id"
    )

    selected_company = st.session_state.get(
        "selected_company"
    )

    selected_industry = st.session_state.get(
        "selected_industry"
    )

    if selected_response_id is None:

        st.info(
            "Select an organization to view its assessment."
        )

        st.stop()


    # Filter dashboard data to the organization selected
    # through the private results link in app.py.
    df = df[
        df["response_id"] == selected_response_id
    ].copy()

    if df.empty:

        st.warning(
            "No assessment data are available "
            "for the selected organization."
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

    all_df["score"] = pd.to_numeric(
        all_df["score"],
        errors="coerce"
    )

    all_df["weight"] = pd.to_numeric(
        all_df["weight"],
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


    # ==================================================
    # OVERVIEW KPI STYLING
    # ==================================================

    st.markdown(
        """
        <style>

        /* ---------------------------------------------
           Keep all four KPI cards the same height
           --------------------------------------------- */

        div[data-testid="stHorizontalBlock"]
        div[data-testid="stVerticalBlockBorderWrapper"]:has(
            div[data-testid="stMetric"]
        ) {
            min-height: 128px !important;
            height: 128px !important;
        }


        /* ---------------------------------------------
           Keep all KPI values visually consistent
           --------------------------------------------- */

        div[data-testid="stHorizontalBlock"]
        div[data-testid="stMetricValue"] {
            font-size: 26px !important;
            line-height: 1.2 !important;
            color: #17375E !important;
            font-weight: 600 !important;
        }


        /* ---------------------------------------------
           Allow KPI values to wrap rather than truncate
           --------------------------------------------- */

        div[data-testid="stHorizontalBlock"]
        div[data-testid="stMetricValue"] > div {
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: unset !important;
            line-height: 1.2 !important;
        }


        /* ---------------------------------------------
           Organization card specifically
           --------------------------------------------- */

        div[data-testid="stHorizontalBlock"]
        > div:nth-child(4)
        div[data-testid="stMetricValue"] {
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: unset !important;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


    # ==================================================
    # OVERVIEW KPIs
    # ==================================================

    col1, col2, col3, col4 = st.columns(
        [1, 1, 1, 1]
    )


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
                "Organization",
                selected_company
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
    # DYNAMIC INDUSTRY PEER BENCHMARK
    # ==================================================

    benchmark_scores, peer_count, benchmark_available = (
        industry_peer_benchmark_by_dimension(
            all_data=all_df,
            selected_response_id=selected_response_id,
            selected_industry=selected_industry,
            metric=benchmark_metric,
            min_peers=2
        )
    )


    # ==================================================
    # BENCHMARK STATUS
    # ==================================================

    if benchmark_available:

        st.caption(
            f"{benchmark_metric} benchmark based on "
            f"{peer_count} other participating organizations "
            f"in {selected_industry}."
        )

    else:

        if (
            selected_industry is None
            or pd.isna(selected_industry)
            or not str(selected_industry).strip()
        ):

            st.info(
                "Industry benchmark unavailable because "
                "the selected organization does not have "
                "an industry classification."
            )

        else:

            st.info(
                f"Industry benchmark unavailable. "
                f"At least 2 other participating organizations "
                f"in {selected_industry} are required to provide "
                f"an anonymized industry comparison. "
                f"Currently available peers: {peer_count}."
            )


    # ==================================================
    # SELECTED ORGANIZATION DIMENSION SCORES
    # ==================================================

    dimension_scores = state_score_by_dimension(
        df
    )

    if dimension_scores.empty:

        st.warning(
            "Dimension scores could not be calculated "
            "for the selected organization."
        )

        st.stop()


    # ==================================================
    # ADD BENCHMARK SCORES WHEN AVAILABLE
    # ==================================================

    if benchmark_available:

        dimension_comparison = (
            dimension_scores.merge(
                benchmark_scores,
                on="dimension",
                how="left"
            )
        )

    else:

        dimension_comparison = (
            dimension_scores.copy()
        )

        dimension_comparison[
            "benchmark_current"
        ] = pd.NA

        dimension_comparison[
            "benchmark_future"
        ] = pd.NA


    # ==================================================
    # RADAR CHART LABELS
    # ==================================================

    dimensions = (
        dimension_comparison["dimension"]
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

    current_scores_closed = (
        current_scores
        + [current_scores[0]]
    )


    if benchmark_available:

        current_benchmark = (
            dimension_comparison[
                "benchmark_current"
            ]
            .astype(float)
            .tolist()
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

    future_scores_closed = (
        future_scores
        + [future_scores[0]]
    )


    if benchmark_available:

        future_benchmark = (
            dimension_comparison[
                "benchmark_future"
            ]
            .astype(float)
            .tolist()
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
        # Selected organization
        # --------------------------------------------------

        fig_current_dimension.add_trace(

            go.Scatterpolar(

                r=current_scores_closed,

                theta=radar_dimensions_closed,

                mode="lines+markers",

                name=selected_company,

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
                    f"{selected_company}: "
                    "%{r:.2f}"
                    "<extra></extra>"
                )
            )
        )


        # --------------------------------------------------
        # Industry peer benchmark
        # --------------------------------------------------

        if benchmark_available:

            fig_current_dimension.add_trace(

                go.Scatterpolar(

                    r=current_benchmark_closed,

                    theta=radar_dimensions_closed,

                    mode="lines+markers",

                    name="Industry Peer Benchmark",

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
                        f"{benchmark_metric} Industry "
                        "Peer Benchmark: %{r:.2f}"
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
        # Selected organization
        # --------------------------------------------------

        fig_future_dimension.add_trace(

            go.Scatterpolar(

                r=future_scores_closed,

                theta=radar_dimensions_closed,

                mode="lines+markers",

                name=selected_company,

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
                    f"{selected_company}: "
                    "%{r:.2f}"
                    "<extra></extra>"
                )
            )
        )


        # --------------------------------------------------
        # Industry peer benchmark
        # --------------------------------------------------

        if benchmark_available:

            fig_future_dimension.add_trace(

                go.Scatterpolar(

                    r=future_benchmark_closed,

                    theta=radar_dimensions_closed,

                    mode="lines+markers",

                    name="Industry Peer Benchmark",

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
                        f"{benchmark_metric} Industry "
                        "Peer Benchmark: %{r:.2f}"
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
# ERROR HANDLING
# ==================================================

except Exception as e:

    st.error(
        "Unable to load dashboard data."
    )

    st.exception(e)