from src.llm import LLMOutputError, generate_json


PLANNER_PROMPT = """
You are the planning agent for AnalystOS.

Your job is to convert a business question into a concise,
evidence-driven investigation plan using only the data and
analysis capabilities available in AnalystOS.

Available business dimensions and metrics include:
- region
- customer segment
- sales channel
- state
- category
- subcategory
- product
- revenue
- gross profit
- contribution profit
- discount rate
- return rate
- refund amount
- shipping cost
- delivery days
- late delivery rate
- units sold
- orders
- customers

You do NOT perform the analysis yourself.

Rules:
1. First identify the metric or business outcome being investigated.
2. Identify the relevant comparison period and scope.
3. Create only analytical steps supported by the available data.
4. Do not request metrics or dimensions that are not available.
5. Avoid redundant analysis.
6. Use a maximum of 6 investigation steps.
7. Prefer validating the main metric first, then drilling into likely drivers.
8. Do not invent findings.
9. Do not assume causation.
10. The final step should validate that each individual breakdown
    independently reconciles to the overall change.

    Do not add changes across overlapping dimensions such as category,
    state, channel, segment, and product, because the same transactions
    appear in multiple dimensions.
11. Fill in the scope so the application can chart the change:
    - metric: the main metric investigated, one of revenue,
      gross_profit, contribution_profit, orders, or other.
    - region: West, South, Northeast, or Midwest; null if the
      question covers all regions.
    - baseline and comparison periods as YYYY-MM-DD dates.
      Start dates are inclusive and end dates are exclusive,
      so August 2025 is 2025-08-01 to 2025-09-01.
    - Use null for periods the question does not specify.
12. Return JSON only.
"""


PERIOD_SCHEMA = {
    "type": ["object", "null"],
    "properties": {
        "start": {"type": "string"},
        "end": {"type": "string"},
    },
    "required": ["start", "end"],
    "additionalProperties": False,
}

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "objective": {"type": "string"},
        "scope": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": [
                        "revenue",
                        "gross_profit",
                        "contribution_profit",
                        "orders",
                        "other",
                    ],
                },
                "region": {
                    "type": ["string", "null"],
                    "enum": [
                        "West",
                        "South",
                        "Northeast",
                        "Midwest",
                        None,
                    ],
                },
                "baseline_period": PERIOD_SCHEMA,
                "comparison_period": PERIOD_SCHEMA,
            },
            "required": [
                "metric",
                "region",
                "baseline_period",
                "comparison_period",
            ],
            "additionalProperties": False,
        },
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step": {"type": "integer"},
                    "analysis": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["step", "analysis", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["objective", "scope", "steps"],
    "additionalProperties": False,
}


def create_investigation_plan(question):

    try:
        return generate_json(
            PLANNER_PROMPT,
            question,
            "investigation_plan",
            PLAN_SCHEMA,
        )

    except LLMOutputError as error:
        return {
            "objective": question,
            "scope": None,
            "steps": [],
            "error": str(error),
            "raw_output": error.raw_output,
        }
