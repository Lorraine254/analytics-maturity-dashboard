import pandas as pd


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
            as_index=False
        )
        .agg(
            weighted_score_sum=("weighted_score", "sum"),
            weight_sum=("weight", "sum")
        )
    )

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

    # Framework order
    dimension_order = [
        "Business Decisions & Analytics",
        "Data & Information",
        "Technology & Infrastructure",
        "Process & Integration",
        "Organization & Governance"
    ]

    dimension_scores["dimension"] = pd.Categorical(
        dimension_scores["dimension"],
        categories=dimension_order,
        ordered=True
    )

    dimension_scores = (
        dimension_scores
        .sort_values("dimension")
        .reset_index(drop=True)
    )

    return dimension_scores


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
# Maturity gap by organization
# --------------------------------------------------
def maturity_gap_by_organization(data):
    """
    Calculate maturity gap for each organization.

    Maturity Gap = Future State Score - Current State Score
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

# Benchmark score by dimension
def benchmark_score_by_dimension(benchmark_data, question_map, metric):
    """
    Calculate PwC reference benchmark scores by dimension.

    Parameters
    ----------
    benchmark_data : DataFrame
        Data from benchmark_reference.

    question_map : DataFrame
        Question metadata containing question_id and dimension.

    metric : str
        One of:
        "Average"
        "Lower Quartile"
        "Median"
        "Top Quartile"
    """

    metric_columns = {
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

    current_column, future_column = metric_columns[metric]

    # Attach each benchmark question to its dimension
    benchmark = benchmark_data.merge(
        question_map[["question_id", "dimension"]],
        on="question_id",
        how="left"
    )

    # Replicate PwC logic:
    # AVERAGE of the selected benchmark level within each dimension
    dimension_benchmark = (
        benchmark
        .groupby("dimension", as_index=False)
        .agg(
            benchmark_current=(current_column, "mean"),
            benchmark_future=(future_column, "mean")
        )
    )

    dimension_order = [
        "Business Decisions & Analytics",
        "Data & Information",
        "Technology & Infrastructure",
        "Process & Integration",
        "Organization & Governance"
    ]

    dimension_benchmark["dimension"] = pd.Categorical(
        dimension_benchmark["dimension"],
        categories=dimension_order,
        ordered=True
    )

    return (
        dimension_benchmark
        .sort_values("dimension")
        .reset_index(drop=True)
    )