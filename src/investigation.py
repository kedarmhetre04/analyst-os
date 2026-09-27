from src.database import run_query


def compare_months(region=None):
    region_filter = ""

    if region:
        region_filter = f"WHERE region = '{region}'"

    query = f"""
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
    {region_filter}
    ORDER BY month, region;
    """

    return run_query(query)


def category_breakdown(region, start_date, end_date):
    query = f"""
    SELECT
        category,
        ROUND(SUM(net_sales), 2) AS revenue,
        ROUND(SUM(gross_profit), 2) AS gross_profit,
        ROUND(SUM(contribution_profit), 2) AS contribution_profit,
        ROUND(AVG(discount_pct) * 100, 2) AS avg_discount_pct,
        ROUND(AVG(returned) * 100, 2) AS return_rate
    FROM sales_analysis
    WHERE region = '{region}'
      AND order_date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY category
    ORDER BY contribution_profit ASC;
    """

    return run_query(query)


def shipping_breakdown(region, start_date, end_date):
    query = f"""
    SELECT
        shipping_mode,
        ROUND(AVG(delivery_days), 2) AS avg_delivery_days,
        ROUND(AVG(late_delivery) * 100, 2) AS late_delivery_rate,
        ROUND(SUM(allocated_shipping_cost), 2) AS shipping_cost,
        ROUND(SUM(contribution_profit), 2) AS contribution_profit
    FROM sales_analysis
    WHERE region = '{region}'
      AND order_date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY shipping_mode
    ORDER BY shipping_cost DESC;
    """

    return run_query(query)


def discount_breakdown(region, start_date, end_date):
    query = f"""
    SELECT
        category,
        ROUND(AVG(discount_pct) * 100, 2) AS avg_discount_pct,
        ROUND(SUM(net_sales), 2) AS revenue,
        ROUND(SUM(contribution_profit), 2) AS contribution_profit
    FROM sales_analysis
    WHERE region = '{region}'
      AND order_date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY category
    ORDER BY avg_discount_pct DESC;
    """

    return run_query(query)


def return_breakdown(region, start_date, end_date):
    query = f"""
    SELECT
        category,
        COUNT(*) AS line_items,
        SUM(returned) AS returned_items,
        ROUND(AVG(returned) * 100, 2) AS return_rate,
        ROUND(SUM(refund_amount), 2) AS refunds
    FROM sales_analysis
    WHERE region = '{region}'
      AND order_date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY category
    ORDER BY return_rate DESC;
    """

    return run_query(query)