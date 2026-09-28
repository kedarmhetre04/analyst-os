import json

from src.planner import create_investigation_plan


question = (
    "Why did contribution profit decline in the West "
    "from August 2025 to September 2025?"
)

plan = create_investigation_plan(question)

print("\n=== INVESTIGATION PLAN ===\n")

print(
    json.dumps(
        plan,
        indent=2
    )
)