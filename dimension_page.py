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
GRID = "rgba(23, 63, 107, 0.15)"
TEXT = "#17375E"


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

    # Ensure both columns exist
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
# QUESTION CHART
# ==================================================

def create_question_chart(
    question_scores,
    state_column,
    state_label,
    color
):

    chart_data = question_scores.copy()

    chart_data["question_label"] = (
        chart_data["question_id"]
        .map(QUESTION_LABELS)
        .fillna(chart_data["question_id"])
    )

    chart_data[state_column] = pd.to_numeric(
        chart_data[state_column],
        errors="coerce"
    )

    chart_data = chart_data.dropna(
        subset=[state_column]
    ).copy()

    number_of_questions = len(chart_data)

    if number_of_questions == 0:
        return None


    # ==================================================
    # 3+ QUESTIONS → RADAR CHART
    # ==================================================

    if number_of_questions >= 3:

        question_labels = (
            chart_data["question_label"]
            .astype(str)
            .tolist()
        )

        full_questions = (
            chart_data["question"]
            .astype(str)
            .tolist()
        )

        state_values = (
            chart_data[state_column]
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

        radar_values = (
            state_values
            + [state_values[0]]
        )

        fig = go.Figure()

        fig.add_trace(
            go.Scatterpolar(
                r=radar_values,
                theta=radar_labels,
                mode="lines+markers",
                name=state_label,
                line=dict(
                    color=color,
                    width=3
                ),
                marker=dict(
                    color=color,
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
                    f"{state_label}: "
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
    # 1–2 QUESTIONS → BAR CHART
    # ==================================================

    fig = px.bar(
        chart_data,
        x="question_label",
        y=state_column,
        text_auto=".1f",
        custom_data=[
            "question"
        ],
        color_discrete_sequence=[
            color
        ]
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{customdata[0]}</b>"
            "<br><br>"
            f"{state_label}: "
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
        xaxis=dict(
            gridcolor=GRID
        ),
        showlegend=False,
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
    benchmark_df=None,
    dimension=None,
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


    # ==================================================
    # ENSURE NUMERIC COLUMNS
    # ==================================================

    dimension_df["score"] = pd.to_numeric(
        dimension_df["score"],
        errors="coerce"
    )

    dimension_df["weight"] = pd.to_numeric(
        dimension_df["weight"],
        errors="coerce"
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

    # Prefer response_id because one response represents
    # one participating organization/assessment.
    if "response_id" in dimension_df.columns:

        organizations_surveyed = (
            dimension_df["response_id"]
            .dropna()
            .nunique()
        )

    else:

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
    # PREPARE QUESTION SCORES
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


    # ==================================================
    # SIDE-BY-SIDE QUESTION ANALYSIS
    # ==================================================

    current_col, future_col = st.columns(
        2,
        gap="medium"
    )


    # ==================================================
    # LEFT: CURRENT STATE SCORE BY QUESTION
    # ==================================================

    with current_col:

        with st.container(border=True):

            st.subheader(
                "Current State Score by Question"
            )

            current_fig = create_question_chart(
                question_scores=question_scores,
                state_column="Current",
                state_label="Current State Score",
                color=NAVY
            )

            if current_fig is not None:

                st.plotly_chart(
                    current_fig,
                    use_container_width=True
                )

            else:

                st.info(
                    "No Current State question scores "
                    "are available."
                )


    # ==================================================
    # RIGHT: FUTURE STATE SCORE BY QUESTION
    # ==================================================

    with future_col:

        with st.container(border=True):

            st.subheader(
                "Future State Score by Question"
            )

            future_fig = create_question_chart(
                question_scores=question_scores,
                state_column="Future",
                state_label="Future State Score",
                color=LIGHT_BLUE
            )

            if future_fig is not None:

                st.plotly_chart(
                    future_fig,
                    use_container_width=True
                )

            else:

                st.info(
                    "No Future State question scores "
                    "are available."
                )