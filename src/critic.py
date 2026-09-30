import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


SEMANTIC_LAYER_PATH = Path(
    "config/semantic_layer.md"
)


def load_semantic_layer():

    if SEMANTIC_LAYER_PATH.exists():
        return SEMANTIC_LAYER_PATH.read_text()

    return ""


SEMANTIC_LAYER = load_semantic_layer()


CRITIC_PROMPT = f"""
You are the Critic Agent for AnalystOS.

Your job is to review an investigation before its findings
are presented to a business stakeholder.

You do NOT perform a new investigation.
You evaluate whether the existing evidence is reliable.

--- BUSINESS SEMANTIC LAYER ---

{SEMANTIC_LAYER}

--- END SEMANTIC LAYER ---

Check the investigation for:

1. Whether each SQL query answers the intended analysis.
2. Whether metric definitions follow the semantic layer.
3. Incorrect aggregation grain.
4. Double counting.
5. Contradictions between different pieces of evidence.
6. Unsupported causal claims.
7. Missing evidence required for a conclusion.
8. Whether individual breakdowns reconcile to the overall change.
9. Suspicious percentages, rates, or calculations.
10. Whether the investigation is sufficient to answer the
    original business question.

Important:

- Do not invent additional evidence.
- Do not assume a finding is correct simply because SQL ran.
- Distinguish serious issues from minor limitations.
- A valid reconciliation may have very small floating-point differences.
- Overlapping dimensions such as category, state, channel,
  segment, and product must NOT be added together.

Return JSON only using:

{{
    "verdict": "PASS" or "PASS_WITH_WARNINGS" or "FAIL",

    "summary": "...",

    "issues": [
        {{
            "severity": "high" or "medium" or "low",
            "step": 1,
            "issue": "...",
            "recommended_fix": "..."
        }}
    ],

    "validated_findings": [
        "..."
    ],

    "limitations": [
        "..."
    ]
}}
"""


def critique_investigation(
    question,
    plan,
    investigation,
):

    prompt = f"""
ORIGINAL BUSINESS QUESTION:

{question}


INVESTIGATION PLAN:

{json.dumps(plan, indent=2)}


INVESTIGATION RESULTS:

{json.dumps(investigation, indent=2)}
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        instructions=CRITIC_PROMPT,
        input=prompt,
    )

    raw_output = response.output_text

    try:
        return json.loads(
            raw_output
        )

    except json.JSONDecodeError:

        return {
            "verdict": "FAIL",
            "summary": (
                "Critic returned invalid JSON."
            ),
            "issues": [],
            "validated_findings": [],
            "limitations": [],
            "raw_output": raw_output,
        }