from ast import arguments
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

SEMANTIC_LAYER_PATH = Path("config/semantic_layer.md")


def load_semantic_layer():
    if SEMANTIC_LAYER_PATH.exists():
        return SEMANTIC_LAYER_PATH.read_text()

    return ""

from src.tools import (
    get_regional_performance,
    get_category_performance,
    get_top_products,
    get_high_return_products,
    run_custom_sql,
)

from src.investigation import (
    compare_months,
    category_breakdown,
    shipping_breakdown,
    discount_breakdown,
    return_breakdown,
)


# --------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# --------------------------------------------------
# TOOL DEFINITIONS
# --------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "name": "get_regional_performance",
        "description": (
            "Returns revenue, gross profit, contribution profit, "
            "order count, and customer count by region."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_category_performance",
        "description": (
            "Returns revenue, gross profit, contribution profit, "
            "average discount, return rate, and units sold by "
            "product category."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_top_products",
        "description": (
            "Returns the highest-revenue products."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": (
                        "Number of products to return."
                    ),
                }
            },
            "required": ["limit"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_high_return_products",
        "description": (
            "Returns products with the highest return rates "
            "among products with sufficient sales volume."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": (
                        "Number of products to return."
                    ),
                }
            },
            "required": ["limit"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "run_custom_sql",
        "description": (
            "Runs a read-only SQL query against the business "
            "analytics database. Use this when the predefined "
            "tools cannot answer the question."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "A valid read-only DuckDB SQL query."
                    ),
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "strict": True,
    },

    {
    "type": "function",
    "name": "compare_months",
    "description": (
        "Returns monthly business performance for a region, including "
        "revenue, gross profit, contribution profit, discount rate, "
        "return rate, and late delivery rate. Use this to identify "
        "period-over-period changes."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "region": {
                "type": "string",
                "description": "Business region such as West, South, Northeast, or Midwest."
            }
        },
        "required": ["region"],
        "additionalProperties": False,
    },
    "strict": True,
},
{
    "type": "function",
    "name": "category_breakdown",
    "description": (
        "Analyzes revenue, profit, discounts, and returns by product "
        "category for a specific region and date range."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "region": {"type": "string"},
            "start_date": {
                "type": "string",
                "description": "Start date in YYYY-MM-DD format."
            },
            "end_date": {
                "type": "string",
                "description": "End date in YYYY-MM-DD format."
            },
        },
        "required": ["region", "start_date", "end_date"],
        "additionalProperties": False,
    },
    "strict": True,
},
{
    "type": "function",
    "name": "shipping_breakdown",
    "description": (
        "Analyzes shipping cost, delivery speed, late delivery rate, "
        "and contribution profit by shipping mode."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "region": {"type": "string"},
            "start_date": {"type": "string"},
            "end_date": {"type": "string"},
        },
        "required": ["region", "start_date", "end_date"],
        "additionalProperties": False,
    },
    "strict": True,
},
{
    "type": "function",
    "name": "discount_breakdown",
    "description": (
        "Analyzes average discounts, revenue, and contribution profit "
        "by category for a region and date range."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "region": {"type": "string"},
            "start_date": {"type": "string"},
            "end_date": {"type": "string"},
        },
        "required": ["region", "start_date", "end_date"],
        "additionalProperties": False,
    },
    "strict": True,
},
{
    "type": "function",
    "name": "return_breakdown",
    "description": (
        "Analyzes return rate and refund amount by category "
        "for a region and date range."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "region": {"type": "string"},
            "start_date": {"type": "string"},
            "end_date": {"type": "string"},
        },
        "required": ["region", "start_date", "end_date"],
        "additionalProperties": False,
    },
    "strict": True,
},
]


# --------------------------------------------------
# SYSTEM INSTRUCTIONS
# --------------------------------------------------

SEMANTIC_LAYER = load_semantic_layer()

SYSTEM_PROMPT = f"""
You are AnalystOS, an autonomous business data analyst.

Your job is to answer business questions using evidence from
the available analytics tools.

You must follow the business definitions and relationships
provided below.

--- BUSINESS SEMANTIC LAYER ---

{SEMANTIC_LAYER}

--- END SEMANTIC LAYER ---

Rules:

1. Use tools whenever the question requires business data.
2. Never invent numbers.
3. Follow the metric definitions in the semantic layer.
4. Clearly distinguish facts from interpretation.
5. Use predefined analytics tools when possible.
6. Use run_custom_sql when custom analysis is required.
7. Only write read-only SQL.
8. Explain findings in clear business language.
9. Do not claim causation unless the data supports it.
10. Mention limitations when the available data cannot support
    a conclusion.

When asked "why" a business metric changed:

1. First confirm that the change actually occurred.
2. Compare the relevant periods.
3. Investigate likely drivers such as category mix,
   discounts, returns, and shipping.
4. Use multiple tools when necessary.
5. Do not stop after finding the first plausible explanation; test alternative drivers when the data allows.
6. Quantify important drivers whenever the data allows.
7. Distinguish evidence from hypotheses.
8. End with:
   - What changed
   - Likely drivers
   - Evidence
   - Recommended next analysis or action
"""


# --------------------------------------------------
# TOOL EXECUTION
# --------------------------------------------------

def dataframe_to_json(df):
    return df.to_json(
        orient="records",
        date_format="iso",
    )


def execute_tool(name, arguments):

    if name == "get_regional_performance":
        result = get_regional_performance()

    elif name == "get_category_performance":
        result = get_category_performance()

    elif name == "get_top_products":
        result = get_top_products(
            arguments["limit"]
        )

    elif name == "get_high_return_products":
        result = get_high_return_products(
            arguments["limit"]
        )

    elif name == "run_custom_sql":
        result = run_custom_sql(
            arguments["query"]
        )
    elif name == "compare_months":
        result = compare_months(
            arguments["region"]
        )

    elif name == "category_breakdown":
        result = category_breakdown(
            arguments["region"],
            arguments["start_date"],
            arguments["end_date"],
        )

    elif name == "shipping_breakdown":
        result = shipping_breakdown(
            arguments["region"],
            arguments["start_date"],
            arguments["end_date"],
        )

    elif name == "discount_breakdown":
        result = discount_breakdown(
            arguments["region"],
            arguments["start_date"],
            arguments["end_date"],
        )

    elif name == "return_breakdown":
        result = return_breakdown(
            arguments["region"],
            arguments["start_date"],
            arguments["end_date"],
        )
    

    else:
        raise ValueError(
            f"Unknown tool: {name}"
        )
    

    return dataframe_to_json(result)


# --------------------------------------------------
# AGENT LOOP
# --------------------------------------------------

def ask_analyst(question):

    conversation = [
        {
            "role": "user",
            "content": question,
        }
    ]

    while True:

        response = client.responses.create(
            model="gpt-5.6-luna",
            instructions=SYSTEM_PROMPT,
            input=conversation,
            tools=TOOLS,
        )

        # Preserve model output in the conversation.
        conversation.extend(response.output)

        tool_calls = [
            item
            for item in response.output
            if item.type == "function_call"
        ]

        # No tool requested = final answer
        if not tool_calls:
            return response.output_text

        for call in tool_calls:

            arguments = json.loads(
                call.arguments
            )

            print(
                f"\n[Agent selected tool: "
                f"{call.name}]"
            )

            if call.name == "run_custom_sql":
                print(
                    f"[SQL: "
                    f"{arguments['query']}]"
                )

            try:

                tool_result = execute_tool(
                    call.name,
                    arguments,
                )

            except Exception as error:

                tool_result = json.dumps({
                    "error": str(error)
                })

            conversation.append(
                {
                    "type":
                        "function_call_output",
                    "call_id":
                        call.call_id,
                    "output":
                        tool_result,
                }
            )
