import json
from functools import lru_cache

from src.llm import LLMOutputError, generate_json
from src.tools import get_database_schema, run_custom_sql


MAX_EVIDENCE_ROWS = 200
MAX_SQL_REPAIRS = 2


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
- product_name
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

Product coverage rule:

When calculating coverage for displayed top products:

- Use only product-level contribution-profit changes in the numerator.
- Use the overall regional contribution-profit change as the denominator.
- Do NOT include category or subcategory changes in the denominator.
- Category, subcategory, and product are overlapping hierarchical views
  of the same transactions and must never be summed together.

Product coverage % =
Net contribution-profit change of displayed product rows
/
Overall regional contribution-profit change

If the displayed product subset does not reconcile to the full product-level
change, clearly label it as partial coverage.

For delivery metrics, always use the shipping table directly.
The shipping table contains one row per order.

Do not derive delivery_days or late_delivery from sales_analysis.

Rules:
1. Each step must be exactly one read-only SELECT (or WITH ... SELECT)
   statement. Other statement types are rejected.
2. Do not invent columns.
3. Execute only analyses needed by the plan.
4. Prefer grouped comparisons between relevant periods.
5. Quantify changes whenever possible.
6. Do not make final causal conclusions.
7. Results are capped at {max_rows} rows, so aggregate rather than
   returning raw line items.
8. Never say that no SQL execution interface is available.
   Your responsibility is to generate executable SQL; the application
   executes it separately.
"""

INVESTIGATOR_PROMPT = INVESTIGATOR_PROMPT.format(max_rows=MAX_EVIDENCE_ROWS)


SQL_REPAIR_PROMPT = """
You are the SQL repair agent for AnalystOS.

A DuckDB query written for an investigation step failed.
Return a corrected query that performs the same analysis.

Follow the same rules as the investigation agent:

--- INVESTIGATION RULES ---

{investigator_prompt}

--- END INVESTIGATION RULES ---
"""

SQL_REPAIR_PROMPT = SQL_REPAIR_PROMPT.format(
    investigator_prompt=INVESTIGATOR_PROMPT
)


@lru_cache(maxsize=1)
def get_schema_reference():
    """
    Every table and view with its columns, read from the live
    database so the model never has to guess names.
    """
    schema = get_database_schema()

    lines = [
        "--- DATABASE SCHEMA ---",
        "",
        "These are the only tables, views, and columns that exist.",
        "",
    ]

    for table, columns in schema.groupby("table_name", sort=True):
        column_list = ", ".join(
            f"{row.column_name} {row.data_type}"
            for row in columns.itertuples()
        )
        lines.append(f"{table}: {column_list}")

    lines += ["", "--- END DATABASE SCHEMA ---"]

    return "\n".join(lines)


def with_schema(instructions):
    return f"{instructions}\n{get_schema_reference()}\n"


INVESTIGATION_SCHEMA = {
    "type": "object",
    "properties": {
        "executed_steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step": {"type": "integer"},
                    "analysis": {"type": "string"},
                    "sql": {"type": "string"},
                },
                "required": ["step", "analysis", "sql"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["executed_steps"],
    "additionalProperties": False,
}

SQL_REPAIR_SCHEMA = {
    "type": "object",
    "properties": {
        "sql": {"type": "string"},
    },
    "required": ["sql"],
    "additionalProperties": False,
}


def build_investigation_prompt(question, plan, feedback=None):

    prompt = f"""
BUSINESS QUESTION:
{question}

INVESTIGATION PLAN:
{json.dumps(plan, indent=2)}
"""

    if feedback:
        prompt += f"""

A previous attempt at this investigation was rejected by the
Critic agent. Address every issue below in the new SQL.

CRITIC REVIEW OF PREVIOUS ATTEMPT:
{json.dumps(feedback, indent=2)}
"""

    return prompt


def run_step_sql(sql):

    df, truncated = run_custom_sql(
        sql,
        max_rows=MAX_EVIDENCE_ROWS,
    )

    return {
        "evidence": json.loads(
            df.to_json(
                orient="records",
                date_format="iso",
            )
        ),
        "row_count": len(df),
        "truncated": truncated,
    }


def repair_sql(question, step, sql, error):

    prompt = f"""
BUSINESS QUESTION:
{question}

STEP {step.get("step")}: {step.get("analysis")}

FAILED SQL:
{sql}

ERROR:
{error}
"""

    repaired = generate_json(
        with_schema(SQL_REPAIR_PROMPT),
        prompt,
        "sql_repair",
        SQL_REPAIR_SCHEMA,
    )

    return repaired["sql"]


def execute_step(question, step):

    sql = step.get("sql")
    failed_attempts = []

    for _ in range(MAX_SQL_REPAIRS + 1):

        try:
            result = run_step_sql(sql)

            return {
                "step": step.get("step"),
                "analysis": step.get("analysis"),
                "sql": sql,
                "failed_attempts": failed_attempts,
                **result,
            }

        except Exception as error:
            failed_attempts.append({
                "sql": sql,
                "error": str(error),
            })

            if len(failed_attempts) > MAX_SQL_REPAIRS:
                break

            try:
                sql = repair_sql(question, step, sql, error)
            except LLMOutputError:
                break

    return {
        "step": step.get("step"),
        "analysis": step.get("analysis"),
        "sql": sql,
        "failed_attempts": failed_attempts[:-1],
        "error": failed_attempts[-1]["error"],
    }


def execute_investigation(question, plan, feedback=None):

    try:
        investigation = generate_json(
            with_schema(INVESTIGATOR_PROMPT),
            build_investigation_prompt(question, plan, feedback),
            "investigation",
            INVESTIGATION_SCHEMA,
        )

    except LLMOutputError as error:
        return {
            "executed_steps": [],
            "error": str(error),
            "raw_output": error.raw_output,
        }

    results = [
        execute_step(question, step)
        for step in investigation["executed_steps"]
        if step.get("sql")
    ]

    return {
        "executed_steps": results
    }
