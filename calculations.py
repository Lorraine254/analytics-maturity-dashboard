import pandas as pd


# --------------------------------------------------
# Framework dimension order
# --------------------------------------------------

DIMENSION_ORDER = [
    "Business Decisions & Analytics",
    "Data & Information",
    "Technology & Infrastructure",
    "Process & Integration",
    "Organization & Governance"
]


# --------------------------------------------------
# Overall weighted maturity score
# --------------------------------------------------

def weighted_maturity_score(data):
    """
    Calculate the overall weighted maturity score.

    Formula:
        SUM(score * weight) / SUM(valid weights)

    Rows with missing scores or weights are excluded.
    This ensures that "I am not aware" responses, which
    are stored as null scores, do not reduce the maturity score.
    """

    valid_data = data.dropna(
        subset=["score", "weight"]
    ).copy()

    if valid_data.empty:
        return 0.0

    total_weight = valid_data["weight"].sum()

    if total_weight == 0:
        return 0.0

    weighted_score = (
        valid_data["score"] * valid_data["weight"]
    ).sum() / total_weight

    return weighted_score


# --------------------------------------------------
# State score by dimension
# --------------------------------------------------

def state_score_by_dimension(data):
    """
    Calculate the weighted Current and Future state scores
    for each maturity dimension.

    Formula for each dimension and state:
        SUM(score * weight) / SUM(valid weights)

    Returns:
        DataFrame with columns:
        dimension | Current | Future
    """

    valid_data = data.dropna(
        subset=["score", "weight", "dimension", "state"]
    ).copy()

    if valid_data.empty:
        return pd.DataFrame(
            columns=["dimension", "Current", "Future"]
        )

    # Calculate weighted component
    valid_data["weighted_score"] = (
        valid_data["score"] * valid_data["weight"]
    )

    # Aggregate by dimension and state
    dimension_scores = (
        valid_data
        .groupby(
            ["dimension", "state"],
            as_index=False,
            observed=False
        )
        .agg(
            weighted_score_sum=("weighted_score", "sum"),
            weight_sum=("weight", "sum")
        )
    )

    # Avoid division by zero
    dimension_scores = dimension_scores[
        dimension_scores["weight_sum"] > 0
    ].copy()

    # Calculate maturity score
    dimension_scores["state_score"] = (
        dimension_scores["weighted_score_sum"]
        / dimension_scores["weight_sum"]
    )

    # Current and Future as separate columns
    dimension_scores = (
        dimension_scores
        .pivot(
            index="dimension",
            columns="state",
            values="state_score"
        )
        .reset_index()
    )

    # Remove pivot column label
    dimension_scores.columns.name = None

    # Ensure both state columns exist
    if "Current" not in dimension_scores.columns:
        dimension_scores["Current"] = pd.NA

    if "Future" not in dimension_scores.columns:
        dimension_scores["Future"] = pd.NA

    # Framework order
    dimension_scores["dimension"] = pd.Categorical(
        dimension_scores["dimension"],
        categories=DIMENSION_ORDER,
        ordered=True
    )

    dimension_scores = (
        dimension_scores
        .sort_values("dimension")
        .reset_index(drop=True)
    )

    return dimension_scores[
        ["dimension", "Current", "Future"]
    ]


# --------------------------------------------------
# Maturity gap by dimension
# --------------------------------------------------

def maturity_gap_by_dimension(data):
    """
    Calculate the maturity gap for each dimension.

    Maturity Gap = Future State Score - Current State Score

    Dimension order follows the maturity framework.
    """

    dimension_scores = state_score_by_dimension(data)

    if dimension_scores.empty:
        return pd.DataFrame(
            columns=["dimension", "maturity_gap"]
        )

    dimension_scores["maturity_gap"] = (
        dimension_scores["Future"]
        - dimension_scores["Current"]
    )

    gap_scores = dimension_scores[
        ["dimension", "maturity_gap"]
    ].copy()

    return gap_scores


# --------------------------------------------------
# State score by organization
# --------------------------------------------------

def state_score_by_organization(data):
    """
    Calculate weighted Current and Future state scores
    for each organization.

    Retained for compatibility with the existing dashboard.
    """

    valid_data = data.dropna(
        subset=["score", "weight", "company_name", "state"]
    ).copy()

    if valid_data.empty:
        return pd.DataFrame(
            columns=["company_name", "Current", "Future"]
        )

    valid_data["weighted_score"] = (
        valid_data["score"] * valid_data["weight"]
    )

    organization_scores = (
        valid_data
        .groupby(
            ["company_name", "state"],
            as_index=False
        )
        .agg(
            weighted_score_sum=("weighted_score", "sum"),
            weight_sum=("weight", "sum")
        )
    )

    organization_scores = organization_scores[
        organization_scores["weight_sum"] > 0
    ].copy()

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

    if "Current" not in organization_scores.columns:
        organization_scores["Current"] = pd.NA

    if "Future" not in organization_scores.columns:
        organization_scores["Future"] = pd.NA

    return organization_scores


# --------------------------------------------------
# Maturity gap by organization
# --------------------------------------------------

def maturity_gap_by_organization(data):
    """
    Calculate maturity gap for each organization.

    Maturity Gap = Future State Score - Current State Score

    Retained for compatibility with the existing dashboard.
    """

    organization_scores = state_score_by_organization(data)

    if organization_scores.empty:
        return pd.DataFrame(
            columns=["company_name", "maturity_gap"]
        )

    organization_scores["maturity_gap"] = (
        organization_scores["Future"]
        - organization_scores["Current"]
    )

    return organization_scores[
        ["company_name", "maturity_gap"]
    ].copy()


# --------------------------------------------------
# PwC benchmark score by dimension
# --------------------------------------------------

# def benchmark_score_by_dimension(
#     benchmark_data,
#     question_map,
#     metric
# ):
#     """
#     Calculate PwC reference benchmark scores by dimension.

#     Retained so the existing benchmark functionality remains
#     available while the dashboard transitions to dynamic
#     industry peer benchmarking.

#     Parameters
#     ----------
#     benchmark_data : DataFrame
#         Data from benchmark_reference.

#     question_map : DataFrame
#         Question metadata containing question_id and dimension.

#     metric : str
#         One of:
#         "Average"
#         "Lower Quartile"
#         "Median"
#         "Top Quartile"
#     """

#     metric_columns = {
#         "Average": (
#             "average_current",
#             "average_future"
#         ),
#         "Lower Quartile": (
#             "lower_quartile_current",
#             "lower_quartile_future"
#         ),
#         "Median": (
#             "median_current",
#             "median_future"
#         ),
#         "Top Quartile": (
#             "top_quartile_current",
#             "top_quartile_future"
#         )
#     }

#     current_column, future_column = metric_columns[metric]

#     # Attach each benchmark question to its dimension
#     benchmark = benchmark_data.merge(
#         question_map[["question_id", "dimension"]],
#         on="question_id",
#         how="left"
#     )

#     # Replicate PwC logic:
#     # average of the selected benchmark level within each dimension
#     dimension_benchmark = (
#         benchmark
#         .groupby(
#             "dimension",
#             as_index=False,
#             observed=False
#         )
#         .agg(
#             benchmark_current=(current_column, "mean"),
#             benchmark_future=(future_column, "mean")
#         )
#     )

#     dimension_benchmark["dimension"] = pd.Categorical(
#         dimension_benchmark["dimension"],
#         categories=DIMENSION_ORDER,
#         ordered=True
#     )

#     return (
#         dimension_benchmark
#         .sort_values("dimension")
#         .reset_index(drop=True)
#     )


# --------------------------------------------------
# Industry peer organizations
# --------------------------------------------------

def get_industry_peers(
    all_data,
    selected_response_id,
    selected_industry
):
    """
    Return assessments belonging to other organizations
    in the selected organization's industry.

    The selected organization is explicitly excluded using
    response_id.

    Parameters
    ----------
    all_data : DataFrame
        Complete analytics maturity reporting dataset.

    selected_response_id : str
        response_id of the organization currently being viewed.

    selected_industry : str
        Industry of the organization currently being viewed.

    Returns
    -------
    DataFrame
        Assessment rows belonging only to peer organizations.
    """

    if (
        all_data.empty
        or selected_response_id is None
        or selected_industry is None
        or pd.isna(selected_industry)
        or not str(selected_industry).strip()
    ):
        return pd.DataFrame(
            columns=all_data.columns
        )

    peer_data = all_data[
        (all_data["industry"] == selected_industry)
        & (
            all_data["response_id"]
            != selected_response_id
        )
    ].copy()

    return peer_data


# --------------------------------------------------
# Count industry peers
# --------------------------------------------------

def count_industry_peers(peer_data):
    """
    Count the number of unique peer assessments.

    One response_id represents one organization assessment.
    """

    if (
        peer_data.empty
        or "response_id" not in peer_data.columns
    ):
        return 0

    return (
        peer_data["response_id"]
        .dropna()
        .nunique()
    )


# --------------------------------------------------
# Dimension scores for individual peer organizations
# --------------------------------------------------

def peer_dimension_scores(peer_data):
    """
    Calculate Current and Future dimension scores separately
    for every peer organization.

    Each organization receives its own weighted dimension score
    before any industry benchmark statistic is calculated.

    Returns
    -------
    DataFrame with columns:
        response_id
        company_name
        dimension
        Current
        Future
    """

    required_columns = {
        "response_id",
        "score",
        "weight",
        "dimension",
        "state"
    }

    if (
        peer_data.empty
        or not required_columns.issubset(peer_data.columns)
    ):
        return pd.DataFrame(
            columns=[
                "response_id",
                "company_name",
                "dimension",
                "Current",
                "Future"
            ]
        )

    peer_scores = []

    for response_id, organization_data in peer_data.groupby(
        "response_id"
    ):

        dimension_scores = state_score_by_dimension(
            organization_data
        )

        if dimension_scores.empty:
            continue

        if "company_name" in organization_data.columns:
            company_names = (
                organization_data["company_name"]
                .dropna()
            )

            company_name = (
                company_names.iloc[0]
                if not company_names.empty
                else None
            )

        else:
            company_name = None

        dimension_scores["response_id"] = response_id
        dimension_scores["company_name"] = company_name

        peer_scores.append(
            dimension_scores[
                [
                    "response_id",
                    "company_name",
                    "dimension",
                    "Current",
                    "Future"
                ]
            ]
        )

    if not peer_scores:
        return pd.DataFrame(
            columns=[
                "response_id",
                "company_name",
                "dimension",
                "Current",
                "Future"
            ]
        )

    return pd.concat(
        peer_scores,
        ignore_index=True
    )


# --------------------------------------------------
# Dynamic industry peer benchmark
# --------------------------------------------------

def industry_peer_benchmark_by_dimension(
    all_data,
    selected_response_id,
    selected_industry,
    metric="Average",
    min_peers=5
):
    """
    Calculate an anonymized industry peer benchmark by dimension.

    Benchmark methodology
    ---------------------
    1. Select organizations in the same industry.
    2. Exclude the organization currently being viewed.
    3. Calculate each peer organization's weighted dimension score.
    4. Calculate the selected statistic across those organization-level
       dimension scores.

    Parameters
    ----------
    all_data : DataFrame
        Complete analytics maturity reporting dataset.

    selected_response_id : str
        response_id of the organization currently being viewed.

    selected_industry : str
        Industry of the selected organization.

    metric : str
        One of:
        "Average"
        "Lower Quartile"
        "Median"
        "Top Quartile"

    min_peers : int
        Minimum number of other organizations required before
        an industry benchmark is displayed.

    Returns
    -------
    benchmark_df : DataFrame
        Columns:
        dimension
        benchmark_current
        benchmark_future

    peer_count : int
        Number of other organizations in the same industry.

    benchmark_available : bool
        True when peer_count >= min_peers and benchmark data
        can be calculated.
    """

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

    # --------------------------------------------------
    # Identify same-industry peers
    # --------------------------------------------------

    peer_data = get_industry_peers(
        all_data=all_data,
        selected_response_id=selected_response_id,
        selected_industry=selected_industry
    )

    peer_count = count_industry_peers(
        peer_data
    )

    # --------------------------------------------------
    # Apply privacy threshold
    # --------------------------------------------------

    if peer_count < min_peers:

        empty_benchmark = pd.DataFrame(
            columns=[
                "dimension",
                "benchmark_current",
                "benchmark_future"
            ]
        )

        return (
            empty_benchmark,
            peer_count,
            False
        )

    # --------------------------------------------------
    # Calculate organization-level dimension scores
    # --------------------------------------------------

    peer_scores = peer_dimension_scores(
        peer_data
    )

    if peer_scores.empty:

        empty_benchmark = pd.DataFrame(
            columns=[
                "dimension",
                "benchmark_current",
                "benchmark_future"
            ]
        )

        return (
            empty_benchmark,
            peer_count,
            False
        )

    # --------------------------------------------------
    # Aggregate peer organization scores
    # --------------------------------------------------

    if metric == "Average":

        benchmark = (
            peer_scores
            .groupby(
                "dimension",
                as_index=False,
                observed=False
            )
            .agg(
                benchmark_current=("Current", "mean"),
                benchmark_future=("Future", "mean")
            )
        )

    elif metric == "Lower Quartile":

        benchmark = (
            peer_scores
            .groupby(
                "dimension",
                as_index=False,
                observed=False
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
            peer_scores
            .groupby(
                "dimension",
                as_index=False,
                observed=False
            )
            .agg(
                benchmark_current=("Current", "median"),
                benchmark_future=("Future", "median")
            )
        )

    else:  # Top Quartile

        benchmark = (
            peer_scores
            .groupby(
                "dimension",
                as_index=False,
                observed=False
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

    # --------------------------------------------------
    # Apply framework dimension order
    # --------------------------------------------------

    benchmark["dimension"] = pd.Categorical(
        benchmark["dimension"],
        categories=DIMENSION_ORDER,
        ordered=True
    )

    benchmark = (
        benchmark
        .sort_values("dimension")
        .reset_index(drop=True)
    )

    return (
        benchmark,
        peer_count,
        True
    )