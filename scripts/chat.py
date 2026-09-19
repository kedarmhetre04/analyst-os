from src.agent import ask_analyst


print()
print("=" * 60)
print("              ANALYSTOS")
print("      Agentic Business Intelligence")
print("=" * 60)

print(
    "\nAsk a business question."
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

        answer = ask_analyst(
            question
        )

        print(
            "\nAnalystOS:"
        )

        print(answer)

        print()

    except Exception as error:

        print(
            f"\nError: {error}\n"
        )
