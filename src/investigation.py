from src.database import run_query


# All filters are passed as query parameters, never formatted
# into the SQL string, because region and dates come from the LLM.

SCOPE_FILTER = """
    region = ?
      AND order_date BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)
"""


def compare_months(region=None):
    query = """
    SELECT
        month,
        region,
        revenue,
        gross_profit,
        contribution_profit,
        avg_discount_pct,
        return_rate,
        late_delivery_rate
    FROM monthly_performance
    WHERE CAST(? AS VARCHAR) IS NULL
       OR region = ?
    ORDER BY month, region;
    """

    return run_query(query, [region, region])


def category_breakdown(region, start_date, end_date):
    query = f"""
    SELECT
        category,
        ROUND(SUM(net_sales), 2) AS revenue,
        ROUND(SUM(gross_profit), 2) AS gross_profit,
        ROUND(SUM(contribution_profit), 2) AS contribution_profit,
        ROUND(
            SUM(discount_amount) / NULLIF(SUM(gross_sales), 0) * 100,
            2
        ) AS discount_rate_pct,
        ROUND(AVG(returned) * 100, 2) AS return_rate
    FROM sales_analysis
    WHERE {SCOPE_FILTER}
    GROUP BY category
    ORDER BY contribution_profit ASC;
    """

    return run_query(query, [region, start_date, end_date])


def shipping_breakdown(region, start_date, end_date):
    # Delivery metrics come from shipping (one row per order);
    # profit comes from sales_analysis (one row per line item).
    query = f"""
    WITH scoped_orders AS (
        SELECT order_id
        FROM orders
        WHERE {SCOPE_FILTER}
    ),

    delivery AS (
        SELECT
            s.shipping_mode,
            COUNT(*) AS orders,
            ROUND(AVG(s.delivery_days), 2) AS avg_delivery_days,
            ROUND(AVG(s.late_delivery) * 100, 2) AS late_delivery_rate,
            ROUND(SUM(s.shipping_cost), 2) AS shipping_cost
        FROM shipping s
        JOIN scoped_orders o
            ON s.order_id = o.order_id
        GROUP BY s.shipping_mode
    ),

    profit AS (
        SELECT
            shipping_mode,
            ROUND(SUM(contribution_profit), 2) AS contribution_profit
        FROM sales_analysis
        WHERE {SCOPE_FILTER}
        GROUP BY shipping_mode
    )

    SELECT
        d.*,
        p.contribution_profit
    FROM delivery d
    LEFT JOIN profit p
        ON d.shipping_mode = p.shipping_mode
    ORDER BY d.shipping_cost DESC;
    """

    return run_query(
        query,
        [region, start_date, end_date] * 2,
    )


def discount_breakdown(region, start_date, end_date):
    query = f"""
    SELECT
        category,
        ROUND(
            SUM(discount_amount) / NULLIF(SUM(gross_sales), 0) * 100,
            2
        ) AS discount_rate_pct,
        ROUND(SUM(net_sales), 2) AS revenue,
        ROUND(SUM(contribution_profit), 2) AS contribution_profit
    FROM sales_analysis
    WHERE {SCOPE_FILTER}
    GROUP BY category
    ORDER BY discount_rate_pct DESC;
    """

    return run_query(query, [region, start_date, end_date])


def return_breakdown(region, start_date, end_date):
    query = f"""
    SELECT
        category,
        COUNT(*) AS line_items,
        SUM(returned) AS returned_items,
        ROUND(AVG(returned) * 100, 2) AS return_rate,
        ROUND(SUM(refund_amount), 2) AS refunds
    FROM sales_analysis
    WHERE {SCOPE_FILTER}
    GROUP BY category
    ORDER BY return_rate DESC;
    """

    return run_query(query, [region, start_date, end_date])
