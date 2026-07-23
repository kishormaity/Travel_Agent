import json
from datetime import datetime
from loguru import logger

from app.config import MODEL_NAME, RESPONSE_TEMPERATURE, MAX_TOKENS
from app.llm import get_llm
from app.prompts import RESPONSE_SYSTEM_PROMPT
from app.schemas.planner import ExecutionPlan
from app.utils import summarize_result_with_llm


class ResponseAgent:
    """Responsible for converting execution plan results into a natural language response."""

    def __init__(self):
        self.client = get_llm()

    def generate_response(self, user_goal: str, execution_plan: ExecutionPlan) -> str:
        """Generate a user-friendly response based on tool execution results."""
        logger.info("Generating final response.")
        execution_summary = self._build_execution_summary(execution_plan)

        system_message = (
            f"{RESPONSE_SYSTEM_PROMPT}\n\n"
            f"Current Local Date and Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        user_content = f"User Request:\n{user_goal}\n\nExecution Results:\n{execution_summary}"

        response = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_content},
            ],
            temperature=RESPONSE_TEMPERATURE,
            max_completion_tokens=MAX_TOKENS,
        )

        return response.choices[0].message.content

    def _build_execution_summary(self, execution_plan: ExecutionPlan) -> str:
        """Convert execution plan tasks into a compact JSON summary to minimize tokens."""
        summary = []
        for task in execution_plan.tasks.values():
            item = {
                "tool": task.tool_name,
                "description": task.description,
                "result": summarize_result_with_llm(task.result),
            }
            if task.error:
                item["error"] = task.error
            summary.append(item)

        return json.dumps(summary, indent=2, default=str)