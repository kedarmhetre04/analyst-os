from datetime import date, timedelta

from src.database import run_query


REGIONS = {"West", "South", "Northeast", "Midwest"}

# Dimension names are inserted into SQL, so only allow known columns.
DIMENSIONS = {
    "category",
    "subcategory",
    "state",
    "segment",
    "sales_channel",
    "shipping_mode",
}

METRIC_LABELS = {
    "revenue": "Revenue",
    "gross_profit": "Gross Profit",
    "contribution_profit": "Contribution Profit",
    "orders": "Orders",
}


def parse_period(period):
    if not isinstance(period, dict):
        return None

    try:
        start = date.fromisoformat(period["start"])
        end = date.fromisoformat(period["end"])
    except (KeyError, TypeError, ValueError):
        return None

    if start >= end:
        return None

    return {"start": start, "end": end}


def parse_scope(plan):
    """
    Validate the planner's scope. Returns None when the question
    does not describe a comparison between two periods.
    """
    scope = (plan or {}).get("scope")

    if not isinstance(scope, dict):
        return None

    baseline = parse_period(scope.get("baseline_period"))
    comparison = parse_period(scope.get("comparison_period"))

    if not baseline or not comparison:
        return None

    region = scope.get("region")
    metric = scope.get("metric")

    return {
        "region": region if region in REGIONS else None,
        "metric": (
            metric
            if metric in METRIC_LABELS
            else "contribution_profit"
        ),
        "baseline": baseline,
        "comparison": comparison,
    }


def format_period(period):
    start = period["start"]
    end = period["end"]
    last_day = end - timedelta(days=1)

    is_full_month = (
        start.day == 1
        and end.day == 1
        and last_day.month == start.month
        and last_day.year == start.year
    )

    if is_full_month:
        return start.strftime("%b %Y")

    return f"{start:%Y-%m-%d} to {last_day:%Y-%m-%d}"


def period_params(scope):
    return [
        scope["baseline"]["start"],
        scope["baseline"]["end"],
        scope["comparison"]["start"],
        scope["comparison"]["end"],
    ]


def get_period_summary(scope):
    """
    One row for the baseline period and one for the comparison
    period, with the components of the contribution-profit bridge.
    """
    query = """
    WITH periods AS (
        SELECT
            'baseline' AS period,
            1 AS sort_order,
            CAST(? AS DATE) AS start_date,
            CAST(? AS DATE) AS end_date

        UNION ALL

        SELECT
            'comparison',
            2,
            CAST(? AS DATE),
            CAST(? AS DATE)
    )

    SELECT
        p.period,
        COALESCE(ROUND(SUM(s.net_sales), 2), 0) AS revenue,
        COALESCE(ROUND(SUM(s.gross_profit), 2), 0) AS gross_profit,
        COALESCE(ROUND(SUM(s.contribution_profit), 2), 0)
            AS contribution_profit,
        COALESCE(ROUND(SUM(s.refund_amount), 2), 0) AS refund_amount,
        COALESCE(ROUND(SUM(s.allocated_shipping_cost), 2), 0)
            AS shipping_cost,
        COUNT(DISTINCT s.order_id) AS orders

    FROM periods p

    LEFT JOIN sales_analysis s
        ON s.order_date >= p.start_date
       AND s.order_date < p.end_date
       AND (CAST(? AS VARCHAR) IS NULL OR s.region = ?)

    GROUP BY p.period, p.sort_order
    ORDER BY p.sort_order;
    """

    region = scope["region"]

    return run_query(
        query,
        period_params(scope) + [region, region],
    )


def get_dimension_changes(scope, dimension="category"):
    """
    Change in the scope's metric between the two periods,
    broken down by one dimension.
    """
    if dimension not in DIMENSIONS:
        raise ValueError(f"Unsupported dimension: {dimension}")

    baseline_filter = (
        "order_date >= CAST(? AS DATE) "
        "AND order_date < CAST(? AS DATE)"
    )
    comparison_filter = baseline_filter

    if scope["metric"] == "orders":
        baseline_value = (
            f"COUNT(DISTINCT CASE WHEN {baseline_filter} "
            f"THEN order_id END)"
        )
        comparison_value = (
            f"COUNT(DISTINCT CASE WHEN {comparison_filter} "
            f"THEN order_id END)"
        )
    else:
        column = {
            "revenue": "net_sales",
            "gross_profit": "gross_profit",
            "contribution_profit": "contribution_profit",
        }[scope["metric"]]

        baseline_value = (
            f"SUM(CASE WHEN {baseline_filter} "
            f"THEN {column} ELSE 0 END)"
        )
        comparison_value = (
            f"SUM(CASE WHEN {comparison_filter} "
            f"THEN {column} ELSE 0 END)"
        )

    query = f"""
    WITH changes AS (
        SELECT
            COALESCE(CAST({dimension} AS VARCHAR), 'Unknown')
                AS {dimension},
            {baseline_value} AS baseline,
            {comparison_value} AS comparison
        FROM sales_analysis
        WHERE (CAST(? AS VARCHAR) IS NULL OR region = ?)
        GROUP BY 1
    )

    SELECT
        {dimension},
        ROUND(baseline, 2) AS baseline,
        ROUND(comparison, 2) AS comparison,
        ROUND(comparison - baseline, 2) AS change
    FROM changes
    ORDER BY change;
    """

    region = scope["region"]

    return run_query(
        query,
        period_params(scope) + [region, region],
    )
