import json
from app.registry.tool_registry import get_planner_tools_description

from loguru import logger
from pydantic import ValidationError

from app.config import (
    MODEL_NAME,
    TEMPERATURE,
    MAX_TOKENS,
)

from app.llm import get_llm
from app.planner import Planner
from app.prompts import PLANNER_SYSTEM_PROMPT, REPLANNER_SYSTEM_PROMPT

from app.schemas.planner import (
    PlannerResponse,
    ExecutionPlan,
)


class PlannerAgent:
    """
    Responsible for generating a valid planner response
    from the LLM and delegating execution plan creation
    to the Planner.
    """

    MAX_RETRIES = 3

    def __init__(self):

        self.client = get_llm()

        self.planner = Planner()

    def create_plan(
        self,
        user_goal: str,
        prompt_type: str = "planner",
        context: dict = None,
        start_id: int = 1,
    ) -> ExecutionPlan:
        """
        Generate an execution plan.

        Args:
            user_goal:
                Original user request.
            prompt_type:
                The type of prompt to use ("planner" or "replanner").
            context:
                Context dict containing memory summary, recent messages, and execution history.
            start_id:
                Starting integer ID for the generated tasks.

        Returns:
            ExecutionPlan
        """

        for attempt in range(self.MAX_RETRIES):

            planner_response = self._generate_plan(
                user_goal=user_goal,
                prompt_type=prompt_type,
                context=context,
            )

            try:

                return self.planner.build_plan(
                    goal=user_goal,
                    planner_response=planner_response,
                    start_id=start_id,
                )

            except ValueError as error:

                logger.warning(
                    f"Planner validation failed: {error}"
                )

        raise RuntimeError(
            "Planner failed after maximum retries."
        )

    def _generate_plan(
        self,
        user_goal: str,
        prompt_type: str = "planner",
        context: dict = None,
    ) -> PlannerResponse:
        """
        Generate a valid planner response.
        """

        for attempt in range(self.MAX_RETRIES):

            logger.info(
                f"Planner attempt {attempt + 1} ({prompt_type})"
            )

            raw_response = self._call_llm(
                user_goal=user_goal,
                prompt_type=prompt_type,
                context=context,
            )

            planner_response = self._parse_response(
                raw_response,
            )

            if planner_response is not None:

                logger.info(
                    f"Planner generated a valid execution plan for {prompt_type}."
                )

                return planner_response

            logger.warning(
                "Planner returned an invalid response. Retrying..."
            )

        raise RuntimeError(
            "Planner failed after maximum retries."
        )

    def _call_llm(
        self,
        user_goal: str,
        prompt_type: str = "planner",
        context: dict = None,
    ) -> str:
        """
        Call the planner LLM.
        """

        context = context or {}

        if prompt_type == "replanner":

            execution_history_str = json.dumps(
                context.get("execution_history", []),
                indent=2,
                default=str,
            )

            start_id = context.get("start_id", 1)
            system_prompt = REPLANNER_SYSTEM_PROMPT.replace(
                "{execution_history}",
                execution_history_str,
            ).replace(
                "{available_tools}",
                get_planner_tools_description(),
            ).replace(
                "{start_id}",
                str(start_id),
            ).replace(
                "{start_id_plus_1}",
                str(start_id + 1),
            ).replace(
                "{start_id_plus_2}",
                str(start_id + 2),
            )

        else:

            system_prompt = PLANNER_SYSTEM_PROMPT.replace(
                "{available_tools}",
                get_planner_tools_description(),
            )

        from datetime import datetime
        current_time_context = f"\n\nCurrent Local Date and Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        messages = [
            {
                "role": "system",
                "content": system_prompt + current_time_context,
            }
        ]

        # Injects the historical conversation summary if available
        if context.get("conversation_summary"):

            messages.append({
                "role": "system",
                "content": f"Historical Conversation Summary:\n{context['conversation_summary']}"
            })

        # Appends the most recent chat history messages
        if context.get("recent_messages"):

            messages.extend(context["recent_messages"])

        else:

            messages.append({
                "role": "user",
                "content": user_goal,
            })

        response = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=TEMPERATURE,
            max_completion_tokens=MAX_TOKENS,
        )

        return response.choices[0].message.content

    def _parse_response(
        self,
        raw_response: str,
    ) -> PlannerResponse | None:
        """
        Parse and validate the planner response.
        """

        try:

            data = json.loads(
                raw_response,
            )

            return PlannerResponse.model_validate(
                data,
            )

        except (
            json.JSONDecodeError,
            ValidationError,
        ) as error:

            logger.warning(error)

            return None