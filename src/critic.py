import json
from pathlib import Path

from src.llm import LLMOutputError, generate_json


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

Use FAIL only for problems that make the main conclusion
unreliable, such as wrong metric definitions, wrong grain,
double counting, failed queries for essential steps, or
breakdowns that do not reconcile. A FAIL triggers a new
investigation, so make each recommended_fix specific and
actionable.

Rows marked "truncated": true were capped by the application;
treat them as partial results.

Each step's "sql" is the query that actually produced its evidence.
"failed_attempts" lists earlier queries for that step that failed
and were replaced; their errors do not apply to the final "sql".
A step with an "error" field has no evidence.

Return JSON only.
"""


STRING_LIST = {
    "type": "array",
    "items": {"type": "string"},
}

CRITIQUE_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["PASS", "PASS_WITH_WARNINGS", "FAIL"],
        },
        "summary": {"type": "string"},
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                    },
                    "step": {"type": ["integer", "null"]},
                    "issue": {"type": "string"},
                    "recommended_fix": {"type": "string"},
                },
                "required": [
                    "severity",
                    "step",
                    "issue",
                    "recommended_fix",
                ],
                "additionalProperties": False,
            },
        },
        "validated_findings": STRING_LIST,
        "limitations": STRING_LIST,
    },
    "required": [
        "verdict",
        "summary",
        "issues",
        "validated_findings",
        "limitations",
    ],
    "additionalProperties": False,
}


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

    try:
        return generate_json(
            CRITIC_PROMPT,
            prompt,
            "critique",
            CRITIQUE_SCHEMA,
        )

    except LLMOutputError as error:

        return {
            "verdict": "FAIL",
            "summary": (
                "Critic returned invalid JSON."
            ),
            "issues": [],
            "validated_findings": [],
            "limitations": [],
            "raw_output": error.raw_output,
        }
