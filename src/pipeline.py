from src.planner import create_investigation_plan
from src.investigator import execute_investigation
from src.critic import critique_investigation
from src.reporter import generate_report


# Total investigations per question, including the first one.
# Each retry is driven by the Critic's issues from the previous run.
MAX_INVESTIGATION_ATTEMPTS = 2


def should_retry(critique):

    # A critic that returned unparseable output has not actually
    # found a problem with the investigation.
    if "raw_output" in critique:
        return False

    return critique.get("verdict") == "FAIL"


def run_analysis(question):

    print("\n[1/4] Creating investigation plan...")

    plan = create_investigation_plan(
        question
    )

    attempts = []
    feedback = None

    for attempt in range(1, MAX_INVESTIGATION_ATTEMPTS + 1):

        print(
            f"[2/4] Running investigation "
            f"(attempt {attempt})..."
        )

        investigation = execute_investigation(
            question,
            plan,
            feedback,
        )


        print("[3/4] Reviewing analysis...")

        critique = critique_investigation(
            question,
            plan,
            investigation,
        )


        print(
            f"[Critic verdict: "
            f"{critique.get('verdict')}]"
        )

        attempts.append({
            "attempt": attempt,
            "investigation": investigation,
            "critique": critique,
        })

        if not should_retry(critique):
            break

        feedback = critique


    print("[4/4] Generating final report...\n")

    report = generate_report(
        question,
        plan,
        investigation,
        critique,
    )

    return {
        "question": question,
        "plan": plan,
        "investigation": investigation,
        "critique": critique,
        "attempts": attempts,
        "report": report,
    }
