import streamlit as st
import pandas as pd
import plotly.express as px

from calculations import weighted_maturity_score


# --------------------------------------------------
# State score by question
# --------------------------------------------------
def state_score_by_question(data):
    """
    Calculate Current and Future state scores
    for each question within a dimension.
    """

    valid_data = data.dropna(
        subset=[
            "score",
            "question",
            "question_order",
            "state"
        ]
    ).copy()

    if valid_data.empty:
        return pd.DataFrame(
            columns=[
                "question",
                "question_order",
                "Current",
                "Future"
            ]
        )

    # Average responses across organizations
    # for each question and state.
    question_scores = (
        valid_data
        .groupby(
            [
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
                "question",
                "question_order"
            ],
            columns="state",
            values="state_score"
        )
        .reset_index()
    )

    question_scores.columns.name = None

    # Preserve questionnaire order
    question_scores = (
        question_scores
        .sort_values("question_order")
        .reset_index(drop=True)
    )

    return question_scores


# --------------------------------------------------
# State score by organization
# --------------------------------------------------
def state_score_by_organization(data):
    """
    Calculate weighted Current and Future state scores
    for each organization within the selected dimension.
    """

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
        valid_data["score"]
        * valid_data["weight"]
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


# --------------------------------------------------
# Wrap question labels
# --------------------------------------------------
def wrap_question(text, width=28):
    """
    Wrap long question text across multiple lines
    for the x-axis of the vertical bar chart.
    """

    if pd.isna(text):
        return ""

    words = str(text).split()

    lines = []
    current_line = []

    for word in words:

        test_line = " ".join(
            current_line + [word]
        )

        if len(test_line) <= width:
            current_line.append(word)

        else:

            if current_line:
                lines.append(
                    " ".join(current_line)
                )

            current_line = [word]

    if current_line:
        lines.append(
            " ".join(current_line)
        )

    return "<br>".join(lines)


# --------------------------------------------------
# Render dimension page
# --------------------------------------------------
def render_dimension_page(
    df,
    dimension,
    title=None
):

    if title is None:
        title = dimension


    # --------------------------------------------------
    # Filter selected dimension
    # --------------------------------------------------
    dimension_df = df[
        df["dimension"] == dimension
    ].copy()

    if dimension_df.empty:

        st.warning(
            f"No data available for {dimension}."
        )

        return


    # --------------------------------------------------
    # Page title
    # --------------------------------------------------
    st.title(title)


    # --------------------------------------------------
    # Current and Future data
    # --------------------------------------------------
    current_df = dimension_df[
        dimension_df["state"] == "Current"
    ].copy()

    future_df = dimension_df[
        dimension_df["state"] == "Future"
    ].copy()


    # --------------------------------------------------
    # KPI calculations
    # --------------------------------------------------
    current_score = weighted_maturity_score(
        current_df
    )

    future_score = weighted_maturity_score(
        future_df
    )

    maturity_gap = (
        future_score
        - current_score
    )

    organizations_surveyed = (
        dimension_df["company_name"]
        .dropna()
        .nunique()
    )


    # --------------------------------------------------
    # KPI cards
    # --------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Current State Score",
            f"{current_score:.2f}"
        )

    with col2:
        st.metric(
            "Future State Score",
            f"{future_score:.2f}"
        )

    with col3:
        st.metric(
            "Maturity Gap",
            f"{maturity_gap:.2f}"
        )

    with col4:
        st.metric(
            "Organizations Surveyed",
            organizations_surveyed
        )


    # --------------------------------------------------
    # State selector
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
        key=f"state_{dimension}"
    )


    # --------------------------------------------------
    # Prepare chart data
    # --------------------------------------------------
    question_scores = (
        state_score_by_question(
            dimension_df
        )
    )

    question_scores["question_label"] = (
        question_scores["question"]
        .apply(wrap_question)
    )

    organization_scores = (
        state_score_by_organization(
            dimension_df
        )
    )


    # ==================================================
    # STATE SCORE BY QUESTION
    # ==================================================
    st.subheader(
        "State Score by Question"
    )


    # --------------------------------------------------
    # Current State
    # --------------------------------------------------
    if state_view == "Current":

        chart_data = question_scores[
            [
                "question",
                "question_label",
                "question_order",
                "Current"
            ]
        ].copy()

        chart_data = chart_data.rename(
            columns={
                "Current": "Score"
            }
        )

        fig_question = px.bar(
            chart_data,
            x="question_label",
            y="Score",
            text_auto=".1f",
            custom_data=[
                "question"
            ]
        )

        fig_question.update_traces(
            hovertemplate=(
                "<b>%{customdata[0]}</b>"
                "<br><br>"
                "Current State Score: %{y:.2f}"
                "<extra></extra>"
            )
        )


    # --------------------------------------------------
    # Future State
    # --------------------------------------------------
    elif state_view == "Future":

        chart_data = question_scores[
            [
                "question",
                "question_label",
                "question_order",
                "Future"
            ]
        ].copy()

        chart_data = chart_data.rename(
            columns={
                "Future": "Score"
            }
        )

        fig_question = px.bar(
            chart_data,
            x="question_label",
            y="Score",
            text_auto=".1f",
            custom_data=[
                "question"
            ]
        )

        fig_question.update_traces(
            hovertemplate=(
                "<b>%{customdata[0]}</b>"
                "<br><br>"
                "Future State Score: %{y:.2f}"
                "<extra></extra>"
            )
        )


    # --------------------------------------------------
    # Current vs Future
    # --------------------------------------------------
    else:

        chart_data = question_scores.melt(
            id_vars=[
                "question",
                "question_label",
                "question_order"
            ],
            value_vars=[
                "Current",
                "Future"
            ],
            var_name="State",
            value_name="Score"
        )

        fig_question = px.bar(
            chart_data,
            x="question_label",
            y="Score",
            color="State",
            barmode="group",
            text_auto=".1f",
            custom_data=[
                "question",
                "State"
            ]
        )

        fig_question.update_traces(
            hovertemplate=(
                "<b>%{customdata[0]}</b>"
                "<br><br>"
                "State: %{customdata[1]}"
                "<br>"
                "Score: %{y:.2f}"
                "<extra></extra>"
            )
        )


    # --------------------------------------------------
    # Question chart formatting
    # --------------------------------------------------
    fig_question.update_layout(
        xaxis_title=None,
        yaxis_title="State Score",
        yaxis=dict(
            range=[0, 5.5],
            dtick=1
        ),
        legend_title_text=None,
        height=520,
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=130
        )
    )

    fig_question.update_xaxes(
        tickangle=0,
        automargin=True,
        tickfont=dict(
            size=10
        )
    )

    fig_question.update_traces(
        textposition="outside",
        cliponaxis=False
    )

    st.plotly_chart(
        fig_question,
        use_container_width=True
    )


    # Add some spacing between charts
    st.write("")


    # ==================================================
    # STATE SCORE BY ORGANIZATION
    # ==================================================
    st.subheader(
        "State Score by Organization"
    )


    # --------------------------------------------------
    # Current State
    # --------------------------------------------------
    if state_view == "Current":

        org_data = organization_scores[
            [
                "company_name",
                "Current"
            ]
        ].copy()

        org_data = org_data.rename(
            columns={
                "Current": "Score"
            }
        )

        fig_org = px.bar(
            org_data,
            x="Score",
            y="company_name",
            orientation="h",
            text_auto=".1f"
        )

        fig_org.update_traces(
            hovertemplate=(
                "<b>%{y}</b>"
                "<br>"
                "Current State Score: %{x:.2f}"
                "<extra></extra>"
            )
        )


    # --------------------------------------------------
    # Future State
    # --------------------------------------------------
    elif state_view == "Future":

        org_data = organization_scores[
            [
                "company_name",
                "Future"
            ]
        ].copy()

        org_data = org_data.rename(
            columns={
                "Future": "Score"
            }
        )

        fig_org = px.bar(
            org_data,
            x="Score",
            y="company_name",
            orientation="h",
            text_auto=".1f"
        )

        fig_org.update_traces(
            hovertemplate=(
                "<b>%{y}</b>"
                "<br>"
                "Future State Score: %{x:.2f}"
                "<extra></extra>"
            )
        )


    # --------------------------------------------------
    # Current vs Future
    # --------------------------------------------------
    else:

        org_data = organization_scores.melt(
            id_vars="company_name",
            value_vars=[
                "Current",
                "Future"
            ],
            var_name="State",
            value_name="Score"
        )

        fig_org = px.bar(
            org_data,
            x="Score",
            y="company_name",
            color="State",
            orientation="h",
            barmode="group",
            text_auto=".1f",
            custom_data=[
                "State"
            ]
        )

        fig_org.update_traces(
            hovertemplate=(
                "<b>%{y}</b>"
                "<br>"
                "State: %{customdata[0]}"
                "<br>"
                "Score: %{x:.2f}"
                "<extra></extra>"
            )
        )


    # --------------------------------------------------
    # Dynamic organization chart height
    # --------------------------------------------------
    number_of_organizations = len(
        organization_scores
    )

    organization_chart_height = max(
        350,
        number_of_organizations * 45 + 150
    )


    # --------------------------------------------------
    # Organization chart formatting
    # --------------------------------------------------
    fig_org.update_layout(
        xaxis_title="State Score",
        yaxis_title=None,
        xaxis=dict(
            range=[0, 5.5],
            dtick=1
        ),
        legend_title_text=None,
        height=organization_chart_height,
        margin=dict(
            l=20,
            r=40,
            t=20,
            b=40
        )
    )

    fig_org.update_traces(
        textposition="outside",
        cliponaxis=False
    )

    st.plotly_chart(
        fig_org,
        use_container_width=True
    )