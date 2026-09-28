import json

from src.planner import create_investigation_plan
from src.investigator import execute_investigation


question = (
    "Why did contribution profit decline in the West "
    "from August 2025 to September 2025?"
)

plan = create_investigation_plan(question)

print("\n=== PLAN ===\n")
print(json.dumps(plan, indent=2))

investigation = execute_investigation(
    question,
    plan,
)

print("\n=== INVESTIGATION RESULTS ===\n")
print(
    json.dumps(
        investigation,
        indent=2
    )
)