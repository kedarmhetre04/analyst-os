from src.database import run_query


def get_database_schema():
    query = """
    SELECT
        table_name,
        column_name,
        data_type
    FROM information_schema.columns
    WHERE table_schema = 'main'
    ORDER BY table_name, ordinal_position;
    """

    return run_query(query)


def get_regional_performance():
    query = """
    SELECT
        region,
        ROUND(SUM(net_sales), 2) AS revenue,
        ROUND(SUM(gross_profit), 2) AS gross_profit,
        ROUND(SUM(contribution_profit), 2) AS contribution_profit,
        COUNT(DISTINCT order_id) AS orders,
        COUNT(DISTINCT customer_id) AS customers
    FROM sales_analysis
    GROUP BY region
    ORDER BY revenue DESC;
    """

    return run_query(query)


def get_monthly_performance():
    query = """
    SELECT
        month,
        region,
        ROUND(revenue, 2) AS revenue,
        ROUND(gross_profit, 2) AS gross_profit,
        ROUND(contribution_profit, 2) AS contribution_profit,
        orders,
        customers,
        ROUND(avg_discount_pct * 100, 2) AS avg_discount_pct,
        ROUND(return_rate * 100, 2) AS return_rate,
        ROUND(late_delivery_rate * 100, 2) AS late_delivery_rate
    FROM monthly_performance
    ORDER BY month, region;
    """

    return run_query(query)


def get_category_performance():
    query = """
    SELECT
        category,
        ROUND(SUM(net_sales), 2) AS revenue,
        ROUND(SUM(gross_profit), 2) AS gross_profit,
        ROUND(SUM(contribution_profit), 2) AS contribution_profit,
        ROUND(AVG(discount_pct) * 100, 2) AS avg_discount_pct,
        ROUND(AVG(returned) * 100, 2) AS return_rate,
        SUM(quantity) AS units_sold
    FROM sales_analysis
    GROUP BY category
    ORDER BY revenue DESC;
    """

    return run_query(query)


def get_top_products(limit=10):
    query = f"""
    SELECT
        product_id,
        MAX(subcategory) AS subcategory,
        ROUND(SUM(net_sales), 2) AS revenue,
        ROUND(SUM(contribution_profit), 2) AS contribution_profit,
        SUM(quantity) AS units_sold
    FROM sales_analysis
    GROUP BY product_id
    ORDER BY revenue DESC
    LIMIT {int(limit)};
    """

    return run_query(query)


def get_high_return_products(limit=10):
    query = f"""
    SELECT
        product_id,
        MAX(category) AS category,
        MAX(subcategory) AS subcategory,
        COUNT(*) AS items_sold,
        SUM(returned) AS returned_items,
        ROUND(AVG(returned) * 100, 2) AS return_rate
    FROM sales_analysis
    GROUP BY product_id
    HAVING COUNT(*) >= 20
    ORDER BY return_rate DESC
    LIMIT {int(limit)};
    """

    return run_query(query)


def run_custom_sql(query):
    return run_query(query)
