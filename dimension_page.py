import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from calculations import weighted_maturity_score


# ==================================================
# DASHBOARD COLOURS
# ==================================================

NAVY = "#173F6B"
LIGHT_BLUE = "#69B3F3"
GOLD = "#D9B300"
GRID = "rgba(23, 63, 107, 0.15)"
TEXT = "#17375E"


# ==================================================
# QUESTION DISPLAY LABELS
# ==================================================

QUESTION_LABELS = {

    # Business Decisions & Analytics
    "Q8": "Analytics Types",
    "Q9": "Impact",
    "Q10": "Investment",
    "Q11": "Real-Time<br>Decisions",
    "Q12": "ROI",

    # Data & Information
    "Q13": "Data<br>Structures",
    "Q14": "Data Timeliness",
    "Q15": "Data Quality<br>Management",
    "Q16": "Data Classification<br>& Protection",

    # Technology & Infrastructure
    "Q17": "Big Data<br>Infrastructure",
    "Q18": "Reporting<br>Tools",
    "Q19": "Analytics Platforms<br>& Tools",

    # Process & Integration
    "Q20": "Structured<br>Process",
    "Q21": "Process<br>Integration",

    # Organization & Governance
    "Q22": "Investment<br>Decisions",
    "Q23": "Organizational Structure",
    "Q24": "Data<br>Governance",
    "Q25": "Data Asset<br>Management",
}


# ==================================================
# QUESTION SCORE
# ==================================================

def state_score_by_question(data):

    valid_data = data.dropna(
        subset=[
            "score",
            "question",
            "question_id",
            "question_order",
            "state"
        ]
    ).copy()

    if valid_data.empty:
        return pd.DataFrame(
            columns=[
                "question_id",
                "question",
                "question_order",
                "Current",
                "Future"
            ]
        )

    valid_data["score"] = pd.to_numeric(
        valid_data["score"],
        errors="coerce"
    )

    valid_data = valid_data.dropna(subset=["score"])

    question_scores = (
        valid_data
        .groupby(
            [
                "question_id",
                "question",
                "question_order",
                "state"
            ],
            as_index=False,
            observed=True
        )
        .agg(
            state_score=("score", "mean")
        )
    )

    question_scores = (
        question_scores
        .pivot(
            index=[
                "question_id",
                "question",
                "question_order"
            ],
            columns="state",
            values="state_score"
        )
        .reset_index()
    )

    question_scores.columns.name = None

    if "Current" not in question_scores.columns:
        question_scores["Current"] = pd.NA

    if "Future" not in question_scores.columns:
        question_scores["Future"] = pd.NA

    question_scores = (
        question_scores
        .sort_values("question_order")
        .reset_index(drop=True)
    )

    return question_scores


# ==================================================
# INDUSTRY PEER DATA
# ==================================================

def get_industry_peers(
    all_data,
    selected_response_id,
    selected_industry
):

    if (
        all_data.empty
        or selected_response_id is None
        or selected_industry is None
        or pd.isna(selected_industry)
        or not str(selected_industry).strip()
    ):
        return pd.DataFrame(columns=all_data.columns)

    peer_data = all_data[
        (all_data["industry"] == selected_industry)
        & (
            all_data["response_id"].astype(str)
            != str(selected_response_id)
        )
    ].copy()

    return peer_data


# ==================================================
# QUESTION-LEVEL INDUSTRY PEER BENCHMARK
# ==================================================

def industry_peer_benchmark_by_question(
    all_data,
    selected_response_id,
    selected_industry,
    dimension,
    metric="Average",
    min_peers=2
):

    valid_metrics = [
        "Average",
        "Lower Quartile",
        "Median",
        "Top Quartile"
    ]

    if metric not in valid_metrics:
        raise ValueError(
            f"metric must be one of: {', '.join(valid_metrics)}"
        )

    peer_data = get_industry_peers(
        all_data=all_data,
        selected_response_id=selected_response_id,
        selected_industry=selected_industry
    )

    peer_data = peer_data[
        peer_data["dimension"] == dimension
    ].copy()

    if peer_data.empty:
        return (
            pd.DataFrame(
                columns=[
                    "question_id",
                    "benchmark_current",
                    "benchmark_future"
                ]
            ),
            0,
            False
        )

    peer_count = (
        peer_data["response_id"]
        .dropna()
        .astype(str)
        .nunique()
    )

    if peer_count < min_peers:
        return (
            pd.DataFrame(
                columns=[
                    "question_id",
                    "benchmark_current",
                    "benchmark_future"
                ]
            ),
            peer_count,
            False
        )

    peer_data["score"] = pd.to_numeric(
        peer_data["score"],
        errors="coerce"
    )

    peer_data = peer_data.dropna(
        subset=[
            "response_id",
            "question_id",
            "state",
            "score"
        ]
    )

    # One score per organization/question/state
    peer_question_scores = (
        peer_data
        .groupby(
            [
                "response_id",
                "question_id",
                "state"
            ],
            as_index=False,
            observed=True
        )
        .agg(
            score=("score", "mean")
        )
    )

    peer_question_scores = (
        peer_question_scores
        .pivot(
            index=[
                "response_id",
                "question_id"
            ],
            columns="state",
            values="score"
        )
        .reset_index()
    )

    peer_question_scores.columns.name = None

    if "Current" not in peer_question_scores.columns:
        peer_question_scores["Current"] = pd.NA

    if "Future" not in peer_question_scores.columns:
        peer_question_scores["Future"] = pd.NA

    # Benchmark statistic
    if metric == "Average":

        benchmark = (
            peer_question_scores
            .groupby(
                "question_id",
                as_index=False,
                observed=True
            )
            .agg(
                benchmark_current=("Current", "mean"),
                benchmark_future=("Future", "mean")
            )
        )

    elif metric == "Lower Quartile":

        benchmark = (
            peer_question_scores
            .groupby(
                "question_id",
                as_index=False,
                observed=True
            )
            .agg(
                benchmark_current=(
                    "Current",
                    lambda x: x.quantile(0.25)
                ),
                benchmark_future=(
                    "Future",
                    lambda x: x.quantile(0.25)
                )
            )
        )

    elif metric == "Median":

        benchmark = (
            peer_question_scores
            .groupby(
                "question_id",
                as_index=False,
                observed=True
            )
            .agg(
                benchmark_current=("Current", "median"),
                benchmark_future=("Future", "median")
            )
        )

    else:  # Top Quartile

        benchmark = (
            peer_question_scores
            .groupby(
                "question_id",
                as_index=False,
                observed=True
            )
            .agg(
                benchmark_current=(
                    "Current",
                    lambda x: x.quantile(0.75)
                ),
                benchmark_future=(
                    "Future",
                    lambda x: x.quantile(0.75)
                )
            )
        )

    return benchmark, peer_count, True


# ==================================================
# RADAR CHART
# ==================================================

def create_question_radar(
    question_scores,
    state_column,
    benchmark_column,
    organization_name,
    benchmark_metric,
    state_color
):

    question_labels = (
        question_scores["question_label"]
        .astype(str)
        .tolist()
    )

    full_questions = (
        question_scores["question"]
        .astype(str)
        .tolist()
    )

    state_values = (
        pd.to_numeric(
            question_scores[state_column],
            errors="coerce"
        )
        .tolist()
    )

    radar_labels = (
        question_labels
        + [question_labels[0]]
    )

    radar_questions = (
        full_questions
        + [full_questions[0]]
    )

    radar_state_values = (
        state_values
        + [state_values[0]]
    )

    fig = go.Figure()

    # Selected organization
    fig.add_trace(
        go.Scatterpolar(
            r=radar_state_values,
            theta=radar_labels,
            mode="lines+markers",
            name=organization_name,
            line=dict(
                color=state_color,
                width=3
            ),
            marker=dict(
                color=state_color,
                size=8
            ),
            fill="toself",
            fillcolor=(
                "rgba(23, 63, 107, 0.08)"
                if state_column == "Current"
                else "rgba(105, 179, 243, 0.10)"
            ),
            customdata=radar_questions,
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                f"{organization_name}: "
                "%{r:.2f}"
                "<extra></extra>"
            )
        )
    )

    # Industry peer benchmark
    if question_scores[benchmark_column].notna().any():

        benchmark_values = (
            pd.to_numeric(
                question_scores[benchmark_column],
                errors="coerce"
            )
            .tolist()
        )

        radar_benchmark_values = (
            benchmark_values
            + [benchmark_values[0]]
        )

        fig.add_trace(
            go.Scatterpolar(
                r=radar_benchmark_values,
                theta=radar_labels,
                mode="lines+markers",
                name="Industry Peer Benchmark",
                line=dict(
                    color=GOLD,
                    width=3
                ),
                marker=dict(
                    color=GOLD,
                    size=8
                ),
                customdata=radar_questions,
                hovertemplate=(
                    "<b>%{customdata}</b><br>"
                    f"{benchmark_metric} Industry Peer Benchmark: "
                    "%{r:.2f}"
                    "<extra></extra>"
                )
            )
        )

    fig.update_layout(
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
                tickvals=[1, 2, 3, 4, 5],
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

    return fig


# ==================================================
# BAR CHART
# Used for dimensions with only 1–2 questions
# ==================================================

def create_question_bar(
    question_scores,
    state_column,
    benchmark_column,
    organization_name,
    state_color
):

    chart_data = (
        question_scores[
            [
                "question",
                "question_label",
                "question_order",
                state_column,
                benchmark_column
            ]
        ]
        .copy()
    )

    chart_data = chart_data.rename(
        columns={
            state_column: organization_name,
            benchmark_column: "Industry Peer Benchmark"
        }
    )

    value_columns = [
        organization_name
    ]

    if chart_data[
        "Industry Peer Benchmark"
    ].notna().any():

        value_columns.append(
            "Industry Peer Benchmark"
        )

    chart_data = (
        chart_data
        .melt(
            id_vars=[
                "question",
                "question_label",
                "question_order"
            ],
            value_vars=value_columns,
            var_name="Series",
            value_name="Score"
        )
    )

    chart_data["Score"] = pd.to_numeric(
        chart_data["Score"],
        errors="coerce"
    )

    chart_data = chart_data.dropna(
        subset=["Score"]
    )

    fig = px.bar(
        chart_data,
        x="question_label",
        y="Score",
        color="Series",
        barmode="group",
        text_auto=".1f",
        custom_data=[
            "question",
            "Series"
        ],
        color_discrete_map={
            organization_name: state_color,
            "Industry Peer Benchmark": GOLD
        }
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{customdata[0]}</b>"
            "<br><br>"
            "%{customdata[1]}: "
            "%{y:.2f}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color=TEXT
        ),
        xaxis_title=None,
        yaxis_title="State Score",
        yaxis=dict(
            range=[0, 5.5],
            dtick=1,
            gridcolor=GRID
        ),
        legend_title_text=None,
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
            l=40,
            r=30,
            t=80,
            b=80
        )
    )

    return fig


# ==================================================
# MAIN DIMENSION PAGE
# ==================================================

def render_dimension_page(
    df,
    benchmark_df,
    dimension,
    title=None
):

    # benchmark_df is retained in the function signature
    # so the existing page files do not need to change.
    # The V2 dashboard uses the dynamic peer benchmark.

    if title is None:
        title = dimension

    # ==================================================
    # SELECTED ORGANIZATION
    # ==================================================

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

    # ==================================================
    # PRESERVE COMPLETE DATASET
    # ==================================================

    all_df = df.copy()

    all_df["score"] = pd.to_numeric(
        all_df["score"],
        errors="coerce"
    )

    all_df["weight"] = pd.to_numeric(
        all_df["weight"],
        errors="coerce"
    )

    # ==================================================
    # FILTER TO SELECTED ORGANIZATION
    # ==================================================

    organization_df = all_df[
        all_df["response_id"].astype(str)
        == str(selected_response_id)
    ].copy()

    if organization_df.empty:
        st.warning(
            "No assessment data are available for "
            "the selected organization."
        )
        st.stop()

    # ==================================================
    # FILTER TO SELECTED DIMENSION
    # ==================================================

    dimension_df = organization_df[
        organization_df["dimension"] == dimension
    ].copy()

    if dimension_df.empty:
        st.warning(
            f"No data available for {dimension}."
        )
        return

    # ==================================================
    # FALLBACK ORGANIZATION / INDUSTRY
    # ==================================================

    if not selected_company:

        company_values = (
            dimension_df["company_name"]
            .dropna()
        )

        selected_company = (
            company_values.iloc[0]
            if not company_values.empty
            else "Selected Organization"
        )

    if not selected_industry:

        industry_values = (
            dimension_df["industry"]
            .dropna()
        )

        selected_industry = (
            industry_values.iloc[0]
            if not industry_values.empty
            else None
        )

    # ==================================================
    # PAGE TITLE
    # ==================================================

    st.title(title)

    # ==================================================
    # KPI CALCULATIONS
    # ==================================================

    current_df = dimension_df[
        dimension_df["state"] == "Current"
    ].copy()

    future_df = dimension_df[
        dimension_df["state"] == "Future"
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
    # KPI STYLING
    # EXACTLY MATCH OVERVIEW PAGE
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
    # KPI CARDS
    # SAME STRUCTURE AS OVERVIEW
    # ==================================================

    col1, col2, col3, col4 = st.columns(
        [1, 1, 1, 1]
    )

    with col1:

        with st.container(border=True):

            st.metric(
                "Current State Score",
                f"{current_score:.2f}"
            )

    with col2:

        with st.container(border=True):

            st.metric(
                "Future State Score",
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
        key=f"benchmark_{dimension}"
    )

    if benchmark_metric is None:
        benchmark_metric = "Average"

    # ==================================================
    # SELECTED ORGANIZATION QUESTION SCORES
    # ==================================================

    question_scores = state_score_by_question(
        dimension_df
    )

    if question_scores.empty:
        st.info(
            "No question-level scores are available "
            "for this dimension."
        )
        return

    question_scores["question_label"] = (
        question_scores["question_id"]
        .map(QUESTION_LABELS)
        .fillna(question_scores["question_id"])
    )

    # ==================================================
    # DYNAMIC SAME-INDUSTRY PEER BENCHMARK
    # ==================================================

    (
        peer_benchmark,
        peer_count,
        benchmark_available
    ) = industry_peer_benchmark_by_question(
        all_data=all_df,
        selected_response_id=selected_response_id,
        selected_industry=selected_industry,
        dimension=dimension,
        metric=benchmark_metric,
        min_peers=2
    )

    # ==================================================
    # BENCHMARK STATUS
    # ==================================================

    if benchmark_available:

        question_scores = (
            question_scores
            .merge(
                peer_benchmark,
                on="question_id",
                how="left"
            )
        )

        st.caption(
            f"{benchmark_metric} benchmark based on "
            f"{peer_count} other participating organizations "
            f"in {selected_industry}."
        )

    else:

        question_scores[
            "benchmark_current"
        ] = pd.NA

        question_scores[
            "benchmark_future"
        ] = pd.NA

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

    question_scores = (
        question_scores
        .sort_values("question_order")
        .reset_index(drop=True)
    )

    # ==================================================
    # CURRENT + FUTURE CHARTS
    # ==================================================

    current_col, future_col = st.columns(
        2,
        gap="medium"
    )

    number_of_questions = len(
        question_scores
    )

    # ==================================================
    # CURRENT STATE SCORE BY QUESTION
    # ==================================================

    with current_col:

        with st.container(border=True):

            st.subheader(
                "Current State Score by Question"
            )

            if number_of_questions >= 3:

                fig_current = create_question_radar(
                    question_scores=question_scores,
                    state_column="Current",
                    benchmark_column="benchmark_current",
                    organization_name=selected_company,
                    benchmark_metric=benchmark_metric,
                    state_color=NAVY
                )

            else:

                fig_current = create_question_bar(
                    question_scores=question_scores,
                    state_column="Current",
                    benchmark_column="benchmark_current",
                    organization_name=selected_company,
                    state_color=NAVY
                )

            st.plotly_chart(
                fig_current,
                use_container_width=True
            )

    # ==================================================
    # FUTURE STATE SCORE BY QUESTION
    # ==================================================

    with future_col:

        with st.container(border=True):

            st.subheader(
                "Future State Score by Question"
            )

            if number_of_questions >= 3:

                fig_future = create_question_radar(
                    question_scores=question_scores,
                    state_column="Future",
                    benchmark_column="benchmark_future",
                    organization_name=selected_company,
                    benchmark_metric=benchmark_metric,
                    state_color=LIGHT_BLUE
                )

            else:

                fig_future = create_question_bar(
                    question_scores=question_scores,
                    state_column="Future",
                    benchmark_column="benchmark_future",
                    organization_name=selected_company,
                    state_color=LIGHT_BLUE
                )

            st.plotly_chart(
                fig_future,
                use_container_width=True
            )