import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from src.tools import (
    get_regional_performance,
    get_category_performance,
    get_top_products,
    get_high_return_products,
    run_custom_sql,
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
]


# --------------------------------------------------
# SYSTEM INSTRUCTIONS
# --------------------------------------------------

SYSTEM_PROMPT = """
You are AnalystOS, an autonomous business data analyst.

Your job is to answer business questions using evidence from
the available analytics tools.

Rules:

1. Use tools whenever the question requires business data.
2. Never invent numbers.
3. Clearly distinguish facts from interpretation.
4. Use the predefined analytics tools when possible.
5. Use run_custom_sql only when necessary.
6. When using SQL, only write read-only queries.
7. Explain findings in clear business language.
8. Highlight important drivers, risks, or anomalies.
9. Suggest useful follow-up analysis when appropriate.
10. Do not claim causation unless the evidence supports it.

Keep responses concise but analytical.
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
