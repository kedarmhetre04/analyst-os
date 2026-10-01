from src.planner import create_investigation_plan
from src.investigator import execute_investigation
from src.critic import critique_investigation
from src.reporter import generate_report


def run_analysis(question):

    print("\n[1/4] Creating investigation plan...")

    plan = create_investigation_plan(
        question
    )


    print("[2/4] Running investigation...")

    investigation = execute_investigation(
        question,
        plan,
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
        "report": report,
    }