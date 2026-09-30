import json

from src.planner import (
    create_investigation_plan,
)

from src.investigator import (
    execute_investigation,
)

from src.critic import (
    critique_investigation,
)


question = (
    "Why did contribution profit decline "
    "in the West from August 2025 "
    "to September 2025?"
)


print("\n=== QUESTION ===\n")
print(question)


# -----------------------------
# PLANNER
# -----------------------------

print("\n=== CREATING PLAN ===\n")

plan = create_investigation_plan(
    question
)

print(
    json.dumps(
        plan,
        indent=2,
    )
)


# -----------------------------
# INVESTIGATOR
# -----------------------------

print("\n=== RUNNING INVESTIGATION ===\n")

investigation = execute_investigation(
    question,
    plan,
)


# We don't print all investigation
# evidence because it is very long.

print(
    f"Executed "
    f"{len(investigation.get('executed_steps', []))} "
    f"investigation steps."
)


# -----------------------------
# CRITIC
# -----------------------------

print("\n=== CRITIC REVIEW ===\n")

critique = critique_investigation(
    question,
    plan,
    investigation,
)

print(
    json.dumps(
        critique,
        indent=2,
    )
)