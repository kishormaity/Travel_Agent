import json

from app.config import (
    MODEL_NAME,
    TEMPERATURE,
    MAX_TOKENS,
)
from app.memory import ConversationMemory
from app.models import get_llm
from app.prompts import SYSTEM_PROMPT
from app.tool_executor import ToolExecutor
from app.tool_registry import TOOLS


class TravelAgent:
    """
    AI Travel Agent with iterative tool calling.
    """

    MAX_TOOL_ITERATIONS = 10

    def __init__(self):
        self.client = get_llm()
        self.memory = ConversationMemory()
        self.tool_executor = ToolExecutor()

        self.memory.add_system_message(
            SYSTEM_PROMPT
        )

    def chat(
        self,
        user_message: str,
    ) -> str:

        self.memory.add_user_message(
            user_message
        )

        for _ in range(
            self.MAX_TOOL_ITERATIONS
        ):

            response = (
                self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=self.memory.get_messages(),
                    tools=TOOLS,
                    tool_choice="auto",
                    temperature=TEMPERATURE,
                    max_completion_tokens=MAX_TOKENS,
                )
            )

            message = response.choices[0].message

            #
            # Finished
            #

            if not message.tool_calls:

                assistant_reply = (
                    message.content
                )

                self.memory.add_assistant_message(
                    assistant_reply
                )

                return assistant_reply

            #
            # Store assistant tool request
            #

            self.memory.add_message(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": message.tool_calls,
                }
            )

            #
            # Execute every tool
            #

            for tool_call in message.tool_calls:

                tool_name = (
                    tool_call.function.name
                )

                arguments = json.loads(
                    tool_call.function.arguments
                )

                tool_result = (
                    self.tool_executor.execute(
                        tool_name,
                        arguments,
                    )
                )

                self.memory.add_message(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(
                            tool_result,
                            default=str,
                        ),
                    }
                )

        raise RuntimeError(
            "Maximum tool iterations exceeded."
        )

    def reset_conversation(self):

        self.memory.clear()

        self.memory.add_system_message(
            SYSTEM_PROMPT
        )