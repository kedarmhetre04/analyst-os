import json
import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


REPORTER_PROMPT = """
You are the final reporting agent for AnalystOS.

Your job is to convert validated analytical findings into a clear,
concise business explanation for a non-technical stakeholder.

You receive:
1. The original business question
2. The investigation plan
3. The investigation evidence
4. The Critic review

Rules:

1. Use only validated evidence.
2. Never invent numbers.
3. Do not repeat findings that the Critic rejected.
4. Clearly distinguish observed evidence from interpretation.
5. Do not claim causation unless explicitly supported.
6. Keep the explanation concise and business-focused.
7. Avoid technical SQL language unless necessary.
8. Explain the most important financial driver first.
9. Then explain where the change was concentrated.
10. Mention meaningful positive offsets.
11. End with a practical next analysis or business action.
12. If the Critic verdict is FAIL, clearly state that the analysis
    is not reliable enough for a final conclusion.

Use this structure:

Executive Summary

What Changed

Main Drivers

Where the Change Was Concentrated

Offsets / Positive Factors

Limitations

Recommended Next Step
"""


def generate_report(
    question,
    plan,
    investigation,
    critique,
):

    prompt = f"""
ORIGINAL QUESTION:

{question}


INVESTIGATION PLAN:

{json.dumps(plan, indent=2)}


INVESTIGATION RESULTS:

{json.dumps(investigation, indent=2)}


CRITIC REVIEW:

{json.dumps(critique, indent=2)}
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        instructions=REPORTER_PROMPT,
        input=prompt,
    )

    return response.output_text