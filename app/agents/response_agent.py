import json

from loguru import logger

from app.config import (
    MODEL_NAME,
    TEMPERATURE,
    MAX_TOKENS,
)

from app.llm import get_llm

from app.prompts import RESPONSE_SYSTEM_PROMPT
from app.utils import build_task_summary

from app.schemas.planner import ExecutionPlan


class ResponseAgent:
    """
    Responsible for converting an executed
    ExecutionPlan into a natural language response.
    """

    def __init__(self):

        self.client = get_llm()

    def generate_response(
        self,
        user_goal: str,
        execution_plan: ExecutionPlan,
    ) -> str:
        """
        Generate a user-friendly response.

        Args:
            user_goal:
                Original user request.

            execution_plan:
                Executed plan containing tool results.

        Returns:
            Final natural language response.
        """

        logger.info(
            "Generating final response."
        )

        execution_summary = self._build_execution_summary(
            execution_plan,
        )

        response = self.client.chat.completions.create(

            model=MODEL_NAME,

            messages=[
                {
                    "role": "system",
                    "content": RESPONSE_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"User Request:\n"
                        f"{user_goal}\n\n"
                        f"Execution Results:\n"
                        f"{execution_summary}"
                    ),
                },
            ],

            temperature=TEMPERATURE,

            max_completion_tokens=MAX_TOKENS,
        )

        return response.choices[0].message.content

    def _build_execution_summary(
        self,
        execution_plan: ExecutionPlan,
    ) -> str:
        """
        Convert the execution plan into a compact summary
        for the LLM.
        """
        summary = [
            build_task_summary(task, full_context=False)
            for task in execution_plan.tasks
        ]
        # Rename tool_name key to tool for LLM prompt context structure matching
        for s in summary:
            s["tool"] = s.pop("tool_name")

        return json.dumps(
            summary,
            indent=2,
            default=str,
        )