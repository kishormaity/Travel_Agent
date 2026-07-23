from loguru import logger
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, get_buffer_string
from langchain_core.chat_history import InMemoryChatMessageHistory


class ConversationMemory:
    """
    Stores and manages conversation history using LangChain's InMemoryChatMessageHistory and message utilities.
    """

    def __init__(self):
        self.chat_history = InMemoryChatMessageHistory()
        self.summary = ""
        self.summarized_up_to = 0

    @property
    def messages(self) -> list[BaseMessage]:
        return self.chat_history.messages

    def add_message(self, message: BaseMessage | dict):
        """
        Add a BaseMessage or raw dict message to the conversation history.
        """
        if isinstance(message, dict):
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                self.chat_history.add_message(SystemMessage(content=content))
            elif role == "assistant":
                self.chat_history.add_ai_message(content)
            else:
                self.chat_history.add_user_message(content)
        elif isinstance(message, BaseMessage):
            self.chat_history.add_message(message)

    def add_system_message(self, content: str):
        self.chat_history.add_message(SystemMessage(content=content))

    def add_user_message(self, content: str):
        self.chat_history.add_user_message(content)

    def add_assistant_message(self, content: str):
        self.chat_history.add_ai_message(content)

    def get_messages(self) -> list[BaseMessage]:
        """
        Return the complete conversation message history.
        """
        return self.chat_history.messages

    def get_conversation_summary(
        self,
        llm_client,
        model_name: str = None,
        word_threshold: int = 300,
        max_combined_chars: int = 1500,
    ) -> str:
        """
        Get or update the conversation summary using LangChain's get_buffer_string utility.
        """
        all_messages = self.chat_history.messages
        if not all_messages:
            return self.summary

        new_messages = all_messages[self.summarized_up_to:] if self.summary else all_messages
        if not new_messages:
            return self.summary

        # Automatically format messages to string using LangChain's get_buffer_string
        new_messages_text = get_buffer_string(new_messages)

        new_words = sum(len(msg.content.split()) for msg in new_messages if hasattr(msg, "content") and isinstance(msg.content, str))

        # Combine previous summary with recent unsummarized updates
        if self.summary:
            combined_context = f"{self.summary}\n\nRecent Updates:\n{new_messages_text}"
        else:
            combined_context = new_messages_text

        # Fast path: below word threshold AND within context size limit
        if new_words < word_threshold and len(combined_context) < max_combined_chars:
            return combined_context

        # LLM Path: Trigger summarization if threshold or length limit is reached
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
            response = llm_client.invoke(prompt)
            self.summary = response.content.strip()
            self.summarized_up_to = len(all_messages)
            return self.summary
        except Exception as error:
            logger.exception(f"Failed to update conversation summary: {error}")
            return combined_context

    def get_history_context(self, max_recent: int) -> list[BaseMessage]:
        """
        Return only recent LangChain messages.
        """
        return self.chat_history.messages[-max_recent:] if self.chat_history.messages else []

    def clear(self):
        """
        Clear the conversation history and summary.
        """
        self.chat_history.clear()
        self.summary = ""
        self.summarized_up_to = 0
