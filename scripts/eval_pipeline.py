"""
Run the full AnalystOS pipeline on questions with known answers
and score the results.

Ground truth is computed directly from the database, so the
expected values always match the current data.

Usage:
    python -m scripts.eval_pipeline

This makes real LLM calls (several per question).
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from src.pipeline import run_analysis
from src.visualizations import (
    get_period_summary,
    parse_period,
    parse_scope,
)


REPORTS_DIR = Path("reports")

RELATIVE_TOLERANCE = 0.01

CASES = [
    {
        "question": (
            "Why did contribution profit decline in the West "
            "from August 2025 to September 2025?"
        ),
        "metric": "contribution_profit",
        "region": "West",
        "baseline": {"start": "2025-08-01", "end": "2025-09-01"},
        "comparison": {"start": "2025-09-01", "end": "2025-10-01"},
    },
    {
        "question": (
            "How did revenue in the South change from Q1 2025 "
            "to Q2 2025, and what drove the change?"
        ),
        "metric": "revenue",
        "region": "South",
        "baseline": {"start": "2025-01-01", "end": "2025-04-01"},
        "comparison": {"start": "2025-04-01", "end": "2025-07-01"},
    },
    {
        "question": (
            "How did total gross profit across all regions change "
            "from 2024 to 2025?"
        ),
        "metric": "gross_profit",
        "region": None,
        "baseline": {"start": "2024-01-01", "end": "2025-01-01"},
        "comparison": {"start": "2025-01-01", "end": "2026-01-01"},
    },
]


NUMBER_PATTERN = re.compile(
    r"(\d[\d,]*(?:\.\d+)?)\s*([kKmM])?(?![\d])"
)

SUFFIX_MULTIPLIERS = {
    None: 1,
    "k": 1_000,
    "m": 1_000_000,
}


def expected_change(case):
    scope = {
        "region": case["region"],
        "metric": case["metric"],
        "baseline": parse_period(case["baseline"]),
        "comparison": parse_period(case["comparison"]),
    }

    summary = get_period_summary(scope)
    metric = case["metric"]

    return float(
        summary.iloc[1][metric] - summary.iloc[0][metric]
    )


def is_close(value, expected):
    tolerance = max(abs(expected) * RELATIVE_TOLERANCE, 1)

    return abs(abs(value) - abs(expected)) <= tolerance


def numbers_in_evidence(investigation):
    for step in investigation.get("executed_steps", []):
        for row in step.get("evidence", []):
            for value in row.values():
                if isinstance(value, (int, float)):
                    yield value


def numbers_in_text(text):
    for digits, suffix in NUMBER_PATTERN.findall(text or ""):
        multiplier = SUFFIX_MULTIPLIERS[
            suffix.lower() if suffix else None
        ]
        yield float(digits.replace(",", "")) * multiplier


def scope_matches(plan, case):
    scope = parse_scope(plan)

    if not scope:
        return False

    return (
        scope["region"] == case["region"]
        and scope["baseline"] == parse_period(case["baseline"])
        and scope["comparison"] == parse_period(case["comparison"])
    )


def evaluate_case(case):
    expected = expected_change(case)
    result = run_analysis(case["question"])

    investigation = result["investigation"]
    steps = investigation.get("executed_steps", [])

    return {
        "question": case["question"],
        "expected_change": round(expected, 2),
        "scope_correct": scope_matches(result["plan"], case),
        "evidence_has_answer": any(
            is_close(value, expected)
            for value in numbers_in_evidence(investigation)
        ),
        "report_has_answer": any(
            is_close(value, expected)
            for value in numbers_in_text(result["report"])
        ),
        "verdict": result["critique"].get("verdict"),
        "investigation_attempts": len(result["attempts"]),
        "failed_steps": sum(1 for step in steps if "error" in step),
        "repaired_sql_queries": sum(
            len(step.get("failed_attempts", []))
            for step in steps
        ),
        "result": result,
    }


def passed(score):
    return (
        score["scope_correct"]
        and score["evidence_has_answer"]
        and score["report_has_answer"]
        and score["verdict"] != "FAIL"
        and score["failed_steps"] == 0
    )


def main():
    scores = [evaluate_case(case) for case in CASES]

    print("\n" + "=" * 60)
    print("ANALYSTOS EVALUATION")
    print("=" * 60)

    for score in scores:
        status = "PASS" if passed(score) else "FAIL"

        print(f"\n[{status}] {score['question']}")
        print(f"  expected change:      {score['expected_change']:,.2f}")
        print(f"  scope correct:        {score['scope_correct']}")
        print(f"  answer in evidence:   {score['evidence_has_answer']}")
        print(f"  answer in report:     {score['report_has_answer']}")
        print(f"  critic verdict:       {score['verdict']}")
        print(f"  investigation tries:  {score['investigation_attempts']}")
        print(f"  failed SQL steps:     {score['failed_steps']}")
        print(f"  repaired SQL queries: {score['repaired_sql_queries']}")

    total_passed = sum(passed(score) for score in scores)

    print(f"\n{total_passed}/{len(scores)} cases passed.")

    REPORTS_DIR.mkdir(exist_ok=True)
    output_path = (
        REPORTS_DIR
        / f"eval_{datetime.now():%Y%m%d_%H%M%S}.json"
    )
    output_path.write_text(
        json.dumps(scores, indent=2, default=str)
    )

    print(f"Full results saved to {output_path}")

    sys.exit(0 if total_passed == len(scores) else 1)


if __name__ == "__main__":
    main()
