import json
from datetime import datetime
from app.config import MODEL_NAME
from app.llm import get_llm
from app.prompts import EXECUTION_SYSTEM_PROMPT
from loguru import logger

class LLMExecutor:
    """
    Executes reasoning, text generation, and other fallback tasks
    using the LLM directly instead of calling API tools.
    """

    def __init__(self):
        self.client = get_llm()

    def execute(self, description: str, arguments: dict = None) -> str:
        """
        Execute a reasoning/fallback task using the LLM with EXECUTION_SYSTEM_PROMPT.
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

        user_content = f"Task Description: {description}"
        if arguments:
            user_content += f"\nArguments: {json.dumps(arguments, ensure_ascii=False)}"

        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3,
                max_completion_tokens=1024,
            )

            result = response.choices[0].message.content.strip()
            logger.info("LLM reasoning task completed successfully.")
            return result

        except Exception as error:
            logger.exception("LLM reasoning task execution failed.")
            raise error
