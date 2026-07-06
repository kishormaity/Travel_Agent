from app.models import get_llm
from app.config import MODEL_NAME, TEMPERATURE, MAX_TOKENS
from app.prompts import SYSTEM_PROMPT
from app.memory import ConversationMemory


class TravelAgent:
    """
    AI Travel Agent
    """

    def __init__(self):
        self.client = get_llm()
        self.memory = ConversationMemory()

        # Add the system prompt once at the beginning
        self.memory.add_system_message(SYSTEM_PROMPT)

    def chat(self, user_message: str) -> str:
        """
        Process a user message and return the AI response.
        """

        # Store user message
        self.memory.add_user_message(user_message)

        # Call Groq
        response = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=self.memory.get_messages(),
            temperature=TEMPERATURE,
            max_completion_tokens=MAX_TOKENS,
        )

        # Extract assistant response
        assistant_reply = response.choices[0].message.content

        # Save assistant response
        self.memory.add_assistant_message(assistant_reply)

        return assistant_reply

    def reset_conversation(self):
        """
        Clear conversation history.
        """

        self.memory.clear()
        self.memory.add_system_message(SYSTEM_PROMPT)