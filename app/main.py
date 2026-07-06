from app.agent import TravelAgent
from app.utils import (
    print_header,
    print_info,
    print_success,
    print_error,
    setup_logger,
)


def main():
    logger = setup_logger()

    print_header("🌍 AI Travel Agent")

    print_info("Type 'exit' or 'quit' to end the conversation.")
    print_info("Type 'reset' to clear the conversation history.\n")

    agent = TravelAgent()

    while True:
        try:
            user_input = input("👤 You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                print_success("Thank you for using AI Travel Agent. Goodbye!")
                break

            if user_input.lower() == "reset":
                agent.reset_conversation()
                print_success("Conversation has been reset.")
                continue

            logger.info(f"User: {user_input}")

            response = agent.chat(user_input)

            logger.info(f"Assistant: {response}")

            print(f"\n🤖 Travel Agent: {response}\n")

        except KeyboardInterrupt:
            print("\n")
            print_success("Application terminated.")
            break

        except Exception as error:
            logger.exception(error)
            print_error(str(error))


if __name__ == "__main__":
    main()