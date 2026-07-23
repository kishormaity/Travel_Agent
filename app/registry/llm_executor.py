import json
from datetime import datetime
from loguru import logger
from langchain_core.prompts import ChatPromptTemplate
from app.llm import get_llm
from app.prompts import EXECUTION_SYSTEM_PROMPT


class LLMExecutor:
    """
    Executes reasoning, text generation, and fallback tasks
    using a standard LangChain LCEL (Prompt | LLM) runnable chain.
    """

    def __init__(self):
        self.llm = get_llm()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_instruction}"),
            ("user", "{user_content}"),
        ])
        self.chain = self.prompt | self.llm

    def execute(self, description: str, arguments: dict = None, user_request: str = None) -> str:
        """
        Execute a reasoning/fallback task using the LangChain runnable chain.
        """
        arguments = arguments or {}
        logger.info(
            f"Executing LLM reasoning task: '{description}' with arguments: {arguments}"
        )

        system_instruction = (
            f"{EXECUTION_SYSTEM_PROMPT}\n\n"
            f"Current Local Date and Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "You are executing a sub-task. Produce a direct, helpful, and concise answer "
            "answering only what is requested."
        )

        user_content = ""
        if user_request:
            user_content += f"Overall User Goal:\n{user_request}\n\n"
        user_content += f"Task Description: {description}"
        if arguments:
            user_content += f"\nArguments: {json.dumps(arguments, ensure_ascii=False)}"

        try:
            response = self.chain.invoke({
                "system_instruction": system_instruction,
                "user_content": user_content,
            })

            result = response.content.strip()
            logger.info("LLM reasoning task completed successfully via LangChain chain.")
            return result

        except Exception as error:
            logger.exception("LLM reasoning task execution failed.")
            raise error
