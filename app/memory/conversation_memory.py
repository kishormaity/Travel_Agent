from loguru import logger

class ConversationMemory:
    """
    Stores the conversation history between the user and the AI agent.
    """

    def __init__(self):
        self.messages = []
        self.summary = ""
        self.summarized_up_to = 0

    def add_message(
        self,
        message: dict,
    ):
        """
        Add a raw message to the conversation.
        """
        self.messages.append(message)

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

    def update_summary(self, llm_client, model_name: str):
        """
        Use the LLM to update the conversation summary based on current messages.
        """
        if not self.messages:
            return

        prompt = (
            "You are a helpful assistant. Summarize the conversation history between the user and the travel assistant. "
            "Focus on extracting and summarizing the user's travel preferences, constraints, budget, and destination details. "
            "Ignore system instructions or tool execution logs. Keep the summary concise."
        )

        messages_to_summarize = [
            {"role": "system", "content": prompt}
        ]

        if self.summary:
            messages_to_summarize.append(
                {"role": "system", "content": f"Current summary: {self.summary}"}
            )
            # Feed only the new messages that occurred since the last summary update
            new_messages = self.messages[self.summarized_up_to:]
            if not new_messages:
                return  # No new messages to summarize
            messages_to_summarize.extend(new_messages)
        else:
            messages_to_summarize.extend(self.messages)

        try:
            response = llm_client.chat.completions.create(
                model=model_name,
                messages=messages_to_summarize,
                temperature=0.3,
                max_completion_tokens=500
            )
            self.summary = response.choices[0].message.content.strip()
            self.summarized_up_to = len(self.messages)
        except Exception as error:
            logger.exception(f"Failed to update conversation summary: {error}")

    def get_history_context(self, max_recent: int = 5) -> dict:
        """
        Return the summary and the most recent messages.
        """
        return {
            "conversation_summary": self.summary,
            "recent_messages": self.messages[-max_recent:] if self.messages else []
        }

    def clear(self):
        """
        Clear the conversation history and summary.
        """
        self.messages = []
        self.summary = ""
        self.summarized_up_to = 0
