import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from src.tools import run_custom_sql

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


INVESTIGATOR_PROMPT = """
You are the investigation agent for AnalystOS.

You receive:
1. A business question
2. An investigation plan

Your job is to generate the SQL required to execute each
investigation step.

A separate Python execution layer will run every SQL query you
provide against the sales_analysis view and attach the resulting
evidence afterward.

For order-level operational metrics:

Late Delivery Rate must be calculated using one row per order.

Use a CTE such as:

WITH order_metrics AS (
    SELECT DISTINCT
        order_id,
        delivery_days,
        late_delivery
    FROM sales_analysis
    WHERE ...
)

Then:

Late Delivery Rate =
SUM(CASE WHEN late_delivery THEN 1 ELSE 0 END)
/
COUNT(*)

Average Delivery Days =
AVG(delivery_days)

Never calculate delivery metrics directly over line-item rows.

When grouping categorical dimensions such as category,
subcategory, state, segment, or sales_channel, use COALESCE
when appropriate so null values are represented as 'Unknown'
rather than silently excluded from interpretation or reconciliation.

Do NOT state that SQL execution is unavailable.
Do NOT claim that a query has already been executed.
Simply describe the analysis being performed and provide the SQL.

Available fields in sales_analysis include:
- order_id
- customer_id
- order_date
- sales_channel
- state
- region
- segment
- product_id
- category
- subcategory
- quantity
- discount_pct
- net_sales
- gross_profit
- allocated_shipping_cost
- returned
- refund_amount
- contribution_profit
- shipping_mode
- delivery_days
- late_delivery
- gross_sales
- discount_amount

Discount Rate =
SUM(discount_amount) / NULLIF(SUM(gross_sales), 0)

Do not use AVG(discount_pct) for aggregated discount analysis.

When ranking positive and negative changes:

- Negative drivers must satisfy contribution_profit_change < 0
- Positive drivers must satisfy contribution_profit_change > 0
- Rank negative and positive changes separately
- Never label a positive change as a negative driver

CASE
    WHEN contribution_profit_change < 0
        THEN 'Negative driver'
    WHEN contribution_profit_change > 0
        THEN 'Positive offset'
    ELSE 'No change'
END AS change_group

For delivery metrics, use the shipping table whenever possible.

Late Delivery Rate =
SUM(late_delivery) / COUNT(*)

Average Delivery Days =
AVG(delivery_days)

The shipping table is one row per order, so delivery metrics
must be calculated from shipping rather than from line-item rows
in sales_analysis.

Grain rules:

LINE-ITEM metrics:
- Return Rate = SUM(returned) / COUNT(*)
- Refund Amount = SUM(refund_amount)
- Revenue = SUM(net_sales)
- Gross Profit = SUM(gross_profit)
- Contribution Profit = SUM(contribution_profit)
- Units Sold = SUM(quantity)

ORDER-LEVEL metrics:
- Orders = COUNT(DISTINCT order_id)
- Average Delivery Days must use one row per order
- Late Delivery Rate = late orders / total distinct orders

Never include the line-item returned flag inside an order-level DISTINCT key.
Do not calculate return rate from orders.

For delivery metrics, use the shipping table because it contains one row per order.

Average Delivery Days =
AVG(shipping.delivery_days)

Late Delivery Rate =
SUM(shipping.late_delivery) / COUNT(*)

When drilling into products after identifying a major negative contributor,
scope the product analysis to that contributor.

Examples:
- If WA is the largest declining state, analyze products within WA.
- If Home & Office is the largest declining category, analyze products within Home & Office.

Do not switch back to West-wide product analysis unless explicitly stated.

For product drill-downs:
- Return only the top 10 negative products and top 5 positive offsets.
- Include product_name, category, subcategory, and contribution_profit_change.
- Rank primarily by absolute contribution-profit change.

When investigating contribution profit changes, always calculate
an explicit contribution-profit bridge:

Contribution Profit Change =
Gross Profit Change
- Refund Amount Change
- Allocated Shipping Cost Change

Be careful with signs:
- Lower refunds are a positive offset.
- Lower shipping costs are a positive offset.
- Higher refunds or shipping costs are negative impacts.

The bridge must reconcile to the observed contribution-profit change
within normal floating-point or rounding tolerance.


When displaying only a subset of products:

- Clearly label them as top product contributors, not a complete reconciliation.
- Calculate the cumulative contribution-profit change represented by
  the displayed products.
- Compare that amount with the total regional contribution-profit change.
- Report the coverage percentage.

Rules:
1. Use only read-only SQL.
2. Do not invent columns.
3. Execute only analyses needed by the plan.
4. Prefer grouped comparisons between relevant periods.
5. Quantify changes whenever possible.
6. Do not make final causal conclusions.
7. Return JSON only.
8. Never say that no SQL execution interface is available.
   Your responsibility is to generate executable SQL; the application
   executes it separately.

Return:

{
  "executed_steps": [
    {
      "step": 1,
      "analysis": "...",
      "sql": "...",
      "evidence": [...]
    }
  ]
}
"""


def execute_investigation(question, plan):

    prompt = f"""
BUSINESS QUESTION:
{question}

INVESTIGATION PLAN:
{json.dumps(plan, indent=2)}
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        instructions=INVESTIGATOR_PROMPT,
        input=prompt,
    )

    raw = response.output_text

    try:
        investigation = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "error": "Investigator returned invalid JSON",
            "raw_output": raw,
        }

    results = []

    for step in investigation.get("executed_steps", []):

        sql = step.get("sql")

        if not sql:
            continue

        try:
            df = run_custom_sql(sql)

            results.append({
                "step": step.get("step"),
                "analysis": step.get("analysis"),
                "sql": sql,
                "evidence": json.loads(
                    df.to_json(
                        orient="records",
                        date_format="iso",
                    )
                ),
            })

        except Exception as error:
            results.append({
                "step": step.get("step"),
                "analysis": step.get("analysis"),
                "sql": sql,
                "error": str(error),
            })

    return {
        "executed_steps": results
    }