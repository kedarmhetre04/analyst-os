from src.database import run_query


query = """
SELECT
    region,
    ROUND(SUM(net_sales), 2) AS revenue,
    ROUND(SUM(gross_profit), 2) AS gross_profit,
    ROUND(SUM(contribution_profit), 2) AS contribution_profit
FROM sales_analysis
GROUP BY region
ORDER BY revenue DESC;
"""

result = run_query(query)

print(result)