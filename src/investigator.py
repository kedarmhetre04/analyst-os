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