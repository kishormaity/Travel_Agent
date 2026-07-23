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

    def get_conversation_summary(
        self,
        llm_client,
        model_name: str,
        word_threshold: int = 300,
        max_combined_chars: int = 1500,
    ) -> str:
        """
        Get the conversation summary, returning combined context or updating via LLM if threshold/length limit is reached.
        """
        if not self.messages:
            return self.summary

        new_messages = self.messages[self.summarized_up_to:] if self.summary else self.messages
        
        if not new_messages:
            return self.summary

        new_messages_text = "\n".join(
            f"- {msg.get('role', 'user').capitalize()}: {msg.get('content', '')}"
            for msg in new_messages 
            if isinstance(msg, dict) and msg.get('content')
        )

        new_words = sum(len(msg.get("content", "").split()) for msg in new_messages if isinstance(msg, dict))

        # Combine previous summary with recent unsummarized updates
        if self.summary:
            combined_context = f"{self.summary}\n\nRecent Updates:\n{new_messages_text}"
        else:
            combined_context = new_messages_text

        # Fast path: below word threshold AND within context size limit -> return combined context directly
        if new_words < word_threshold and len(combined_context) < max_combined_chars:
            return combined_context

        # LLM Path: Trigger summarization if new words >= threshold OR combined context exceeds size limit
        if self.summary:
            prompt = (
                "You are an AI maintaining an ongoing travel plan summary for an interactive travel assistant.\n"
                "Your task is to update the Previous Summary with the New Messages (user requests, assistant proposals, tool outputs) below.\n\n"
                "CRITICAL INSTRUCTIONS:\n"
                "1. IDENTIFY ESSENTIAL CHANGES: Carefully analyze the New Messages to detect any updated user choices or mind-changes "
                "(e.g., changes to destination, budget, travel dates, flight class, hotel ratings, dietary restrictions, or trip constraints).\n"
                "2. OVERWRITE UPDATED FIELDS: Overwrite specific details in the Previous Summary ONLY if the user explicitly modified or updated them in the New Messages.\n"
                "3. RETAIN SHORT TOOL FINDINGS: Keep essential tool outputs and recommendations (e.g., top flight numbers/prices, key weather conditions, hotel names) as SHORT concise bullet points. Never store raw API payloads or full JSON outputs.\n"
                "4. PRESERVE UNCHANGED PREFERENCES: Retain all non-conflicting preferences, budget limits, and constraints from the Previous Summary.\n"
                "5. OUTPUT FORMAT: Output a clean, concise bulleted summary listing active travel preferences, destination, budget, constraints, and relevant tool results.\n\n"
                f"=== PREVIOUS SUMMARY ===\n{self.summary}\n\n"
                f"=== NEW MESSAGES ===\n{new_messages_text}"
            )
        else:
            prompt = (
                "Summarize the conversation history (user requests, assistant proposals, and tool outputs), focusing on destination, "
                "travel preferences (hotel rating, flight class, dietary restrictions), budget, travel dates, constraints, and key tool findings.\n"
                "Output a clean, concise bulleted summary.\n\n"
                f"=== NEW MESSAGES ===\n{new_messages_text}"
            )

        try:
            response = llm_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_completion_tokens=400
            )
            self.summary = response.choices[0].message.content.strip()
            self.summarized_up_to = len(self.messages)
            return self.summary
        except Exception as error:
            logger.exception(f"Failed to update conversation summary: {error}")
            return combined_context

    def get_history_context(self, max_recent: int) -> list[dict]:
        """
        Return only the recent messages.
        """
        return self.messages[-max_recent:] if self.messages else []

    def clear(self):
        """
        Clear the conversation history and summary.
        """
        self.messages = []
        self.summary = ""
        self.summarized_up_to = 0
