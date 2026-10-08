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

STATE_COLORS = {
    "Current": NAVY,
    "Future": LIGHT_BLUE
}


# ==================================================
# QUESTION DISPLAY LABELS
# Short labels are used on the chart.
# Full questions are shown in the hover tooltip.
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

    question_scores = (
        question_scores
        .sort_values("question_order")
        .reset_index(drop=True)
    )

    return question_scores


# ==================================================
# ORGANIZATION SCORE
# ==================================================

def state_score_by_organization(data):

    valid_data = data.dropna(
        subset=[
            "score",
            "weight",
            "company_name",
            "state"
        ]
    ).copy()

    if valid_data.empty:
        return pd.DataFrame(
            columns=[
                "company_name",
                "Current",
                "Future"
            ]
        )

    valid_data["weighted_score"] = (
        valid_data["score"] * valid_data["weight"]
    )

    organization_scores = (
        valid_data
        .groupby(
            [
                "company_name",
                "state"
            ],
            as_index=False
        )
        .agg(
            weighted_score_sum=(
                "weighted_score",
                "sum"
            ),
            weight_sum=(
                "weight",
                "sum"
            )
        )
    )

    organization_scores["state_score"] = (
        organization_scores["weighted_score_sum"]
        / organization_scores["weight_sum"]
    )

    organization_scores = (
        organization_scores
        .pivot(
            index="company_name",
            columns="state",
            values="state_score"
        )
        .reset_index()
    )

    organization_scores.columns.name = None

    return organization_scores


# ==================================================
# BENCHMARK COLUMN MAPPING
# ==================================================

def get_benchmark_columns(metric):

    metric_map = {

        "Average": (
            "average_current",
            "average_future"
        ),

        "Lower Quartile": (
            "lower_quartile_current",
            "lower_quartile_future"
        ),

        "Median": (
            "median_current",
            "median_future"
        ),

        "Top Quartile": (
            "top_quartile_current",
            "top_quartile_future"
        )
    }

    return metric_map[metric]


# ==================================================
# MAIN DIMENSION PAGE
# ==================================================

def render_dimension_page(
    df,
    benchmark_df,
    dimension,
    title=None
):

    if title is None:
        title = dimension


    # ==================================================
    # FILTER DIMENSION
    # ==================================================

    dimension_df = df[
        df["dimension"] == dimension
    ].copy()

    if dimension_df.empty:

        st.warning(
            f"No data available for {dimension}."
        )

        return


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

    organizations_surveyed = (
        dimension_df["company_name"]
        .dropna()
        .nunique()
    )


    # ==================================================
    # KPI CARDS
    # ==================================================

    col1, col2, col3, col4 = st.columns(4)

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
                "Organizations Surveyed",
                organizations_surveyed
            )

    st.write("")


    # ==================================================
    # STATE + INDUSTRY BENCHMARK CONTROLS
    # ==================================================

    control_col1, control_col2, control_spacer = st.columns(
    [1, 4.5, 1]
)

    with control_col1:

        state_view = st.segmented_control(
            "State",
            options=[
                "Current",
                "Future"
            ],
            default="Current",
            key=f"state_{dimension}"
        )

    with control_col2:

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


    # ==================================================
    # SELECT BENCHMARK COLUMN
    # ==================================================

    (
        benchmark_current_column,
        benchmark_future_column
    ) = get_benchmark_columns(
        benchmark_metric
    )

    if state_view == "Current":

        state_column = "Current"
        benchmark_column = benchmark_current_column
        state_color = NAVY

    else:

        state_column = "Future"
        benchmark_column = benchmark_future_column
        state_color = LIGHT_BLUE


    # ==================================================
    # PREPARE QUESTION SCORES
    # ==================================================

    question_scores = (
        state_score_by_question(
            dimension_df
        )
    )

    question_scores = (
        question_scores
        .merge(
            benchmark_df[
                [
                    "question_id",
                    benchmark_column
                ]
            ],
            on="question_id",
            how="left"
        )
    )

    question_scores = (
        question_scores
        .rename(
            columns={
                benchmark_column:
                    "Industry Benchmark"
            }
        )
    )

    question_scores = (
        question_scores
        .sort_values("question_order")
        .reset_index(drop=True)
    )

    question_scores["question_label"] = (
        question_scores["question_id"]
        .map(QUESTION_LABELS)
        .fillna(question_scores["question_id"])
    )


    # ==================================================
    # PREPARE ORGANIZATION SCORES
    # ==================================================

    organization_scores = (
        state_score_by_organization(
            dimension_df
        )
    )

    organization_data = pd.DataFrame()

    if not organization_scores.empty:

        if state_view == "Current":

            organization_data = (
                organization_scores[
                    [
                        "company_name",
                        "Current"
                    ]
                ]
                .copy()
                .rename(
                    columns={
                        "Current": "Score"
                    }
                )
            )

        else:

            organization_data = (
                organization_scores[
                    [
                        "company_name",
                        "Future"
                    ]
                ]
                .copy()
                .rename(
                    columns={
                        "Future": "Score"
                    }
                )
            )

        organization_data = (
            organization_data
            .dropna(
                subset=["Score"]
            )
            .sort_values(
                "Score",
                ascending=True
            )
        )


    # ==================================================
    # SIDE-BY-SIDE ANALYSIS
    # ==================================================

    question_col, organization_col = st.columns(
        2,
        gap="medium"
    )


    # ==================================================
    # LEFT: STATE SCORE BY QUESTION
    # ==================================================

    with question_col:

        with st.container(border=True):

            st.subheader(
                "State Score by Question"
            )

            number_of_questions = len(
                question_scores
            )


            # ==================================================
            # 3+ QUESTIONS → RADAR CHART
            # ==================================================

            if number_of_questions >= 3:

                question_labels = (
                    question_scores[
                        "question_label"
                    ]
                    .astype(str)
                    .tolist()
                )

                full_questions = (
                    question_scores[
                        "question"
                    ]
                    .astype(str)
                    .tolist()
                )

                state_values = (
                    pd.to_numeric(
                        question_scores[
                            state_column
                        ],
                        errors="coerce"
                    )
                    .tolist()
                )

                benchmark_values = (
                    pd.to_numeric(
                        question_scores[
                            "Industry Benchmark"
                        ],
                        errors="coerce"
                    )
                    .tolist()
                )


                # Close radar polygon
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

                radar_benchmark_values = (
                    benchmark_values
                    + [benchmark_values[0]]
                )


                fig_question = go.Figure()


                # ------------------------------------------
                # STATE SCORE
                # ------------------------------------------

                fig_question.add_trace(

                    go.Scatterpolar(

                        r=radar_state_values,

                        theta=radar_labels,

                        mode="lines+markers",

                        name=f"{state_view} State Score",

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
                            if state_view == "Current"
                            else
                            "rgba(105, 179, 243, 0.10)"
                        ),

                        customdata=radar_questions,

                        hovertemplate=(
                            "<b>%{customdata}</b><br>"
                            f"{state_view} State Score: "
                            "%{r:.2f}"
                            "<extra></extra>"
                        )
                    )
                )


                # ------------------------------------------
                # INDUSTRY BENCHMARK
                # ------------------------------------------

                fig_question.add_trace(

                    go.Scatterpolar(

                        r=radar_benchmark_values,

                        theta=radar_labels,

                        mode="lines+markers",

                        name="Industry Benchmark",

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
                            f"{benchmark_metric} "
                            "Industry Benchmark: "
                            "%{r:.2f}"
                            "<extra></extra>"
                        )
                    )
                )


                fig_question.update_layout(

                    paper_bgcolor=(
                        "rgba(0,0,0,0)"
                    ),

                    plot_bgcolor=(
                        "rgba(0,0,0,0)"
                    ),

                    font=dict(
                        color=TEXT
                    ),

                    polar=dict(

                        bgcolor=(
                            "rgba(0,0,0,0)"
                        ),

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


                st.plotly_chart(
                    fig_question,
                    use_container_width=True
                )


            # ==================================================
            # 1–2 QUESTIONS → GROUPED BAR CHART
            # ==================================================

            else:

                question_chart_data = (
                    question_scores[
                        [
                            "question",
                            "question_label",
                            "question_order",
                            state_column,
                            "Industry Benchmark"
                        ]
                    ]
                    .copy()
                )

                question_chart_data = (
                    question_chart_data
                    .rename(
                        columns={
                            state_column:
                                f"{state_view} State Score"
                        }
                    )
                )

                question_chart_data = (
                    question_chart_data
                    .melt(
                        id_vars=[
                            "question",
                            "question_label",
                            "question_order"
                        ],
                        value_vars=[
                            f"{state_view} State Score",
                            "Industry Benchmark"
                        ],
                        var_name="Series",
                        value_name="Score"
                    )
                )


                fig_question = px.bar(

                    question_chart_data,

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

                        f"{state_view} State Score":
                            state_color,

                        "Industry Benchmark":
                            GOLD
                    }
                )


                fig_question.update_traces(

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


                fig_question.update_layout(

                    paper_bgcolor=(
                        "rgba(0,0,0,0)"
                    ),

                    plot_bgcolor=(
                        "rgba(0,0,0,0)"
                    ),

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

                    xaxis=dict(
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


                st.plotly_chart(
                    fig_question,
                    use_container_width=True
                )


    # ==================================================
    # RIGHT: STATE SCORE BY ORGANIZATION
    # ==================================================

    with organization_col:

        with st.container(border=True):

            st.subheader(
                "State Score by Organization"
            )

            if not organization_data.empty:

                fig_organization = px.bar(

                    organization_data,

                    x="Score",

                    y="company_name",

                    orientation="h",

                    text_auto=".2f",

                    color_discrete_sequence=[
                        state_color
                    ]
                )


                fig_organization.update_layout(

                    paper_bgcolor=(
                        "rgba(0,0,0,0)"
                    ),

                    plot_bgcolor=(
                        "rgba(0,0,0,0)"
                    ),

                    font=dict(
                        color=TEXT
                    ),

                    xaxis_title="State Score",

                    yaxis_title=None,

                    xaxis=dict(
                        range=[0, 5.5],
                        dtick=1,
                        gridcolor=GRID
                    ),

                    yaxis=dict(
                        gridcolor=GRID
                    ),

                    # Match question chart height
                    height=520,

                    margin=dict(
                        l=20,
                        r=50,
                        t=80,
                        b=60
                    ),

                    hoverlabel=dict(
                        bgcolor="white",
                        font_color=TEXT
                    ),

                    showlegend=False
                )


                fig_organization.update_traces(

                    textposition="outside",

                    cliponaxis=False,

                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        f"{state_view} State Score: "
                        "%{x:.2f}"
                        "<extra></extra>"
                    )
                )


                st.plotly_chart(
                    fig_organization,
                    use_container_width=True
                )

            else:

                st.info(
                    "No organization data available."
                )