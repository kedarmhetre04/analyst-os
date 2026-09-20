
from src.database import run_query

query = """
SELECT
    ROUND(SUM(allocated_shipping_cost), 2)
        AS allocated_shipping_total,
    ROUND((SELECT SUM(shipping_cost) FROM shipping), 2)
        AS original_shipping_total,
    ROUND(SUM(net_sales), 2) AS revenue,
    ROUND(SUM(gross_profit), 2) AS gross_profit,
    ROUND(SUM(refund_amount), 2) AS refunds,
    ROUND(SUM(contribution_profit), 2)
        AS contribution_profit
FROM sales_analysis;
"""

result = run_query(query)

print("\n=== METRIC VALIDATION ===")
print(result.to_string(index=False))

allocated = result["allocated_shipping_total"].iloc[0]
original = result["original_shipping_total"].iloc[0]

assert abs(allocated - original) < 0.01, (
    "Shipping allocation does not reconcile!"
)

print("\nPASS: Shipping costs reconcile.")
