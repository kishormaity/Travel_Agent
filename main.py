from app.agent import TravelAgent


def main():
    agent = TravelAgent()

    print("=" * 60)
    print("🌍 AI Travel Agent")
    print("Type 'exit' to quit.")
    print("=" * 60)

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in {"exit", "quit", "bye"}:
            print("\n👋 Goodbye!")
            break

        if not user_input:
            continue

        try:
            response = agent.chat(user_input)
            print(f"\nAgent: {response}")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

        except Exception as error:
            print(f"\n❌ Error: {error}")


if __name__ == "__main__":
    main()