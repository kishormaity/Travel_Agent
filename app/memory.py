class ConversationMemory:
    """
    Stores the conversation history between the user and the AI agent.
    """

    def __init__(self):
        self.messages = []

    def add_system_message(self, content: str):
        self.messages.append(
            {
                "role": "system",
                "content": content,
            }
        )

    def add_user_message(self, content: str):
        self.messages.append(
            {
                "role": "user",
                "content": content,
            }
        )

    def add_assistant_message(self, content: str):
        self.messages.append(
            {
                "role": "assistant",
                "content": content,
            }
        )

    def get_messages(self):
        """
        Return the complete conversation history.
        """
        return self.messages

    def clear(self):
        """
        Clear the conversation history.
        """
        self.messages = []