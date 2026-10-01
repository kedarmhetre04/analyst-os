from src.pipeline import run_analysis


print()
print("=" * 60)
print("                    ANALYSTOS")
print("          Autonomous Business Analyst")
print("=" * 60)

print(
    "\nAsk AnalystOS a business question."
)

print(
    "Type 'exit' to stop.\n"
)


while True:

    question = input(
        "You: "
    ).strip()

    if question.lower() in [
        "exit",
        "quit",
    ]:
        print(
            "\nAnalystOS session ended."
        )
        break

    if not question:
        continue

    try:

        result = run_analysis(
            question
        )

        print("\n" + "=" * 60)

        print(
            "ANALYSTOS REPORT"
        )

        print("=" * 60 + "\n")

        print(
            result["report"]
        )

        print()

    except Exception as error:

        print(
            f"\nError: {error}\n"
        )