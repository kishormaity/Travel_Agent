from typing import Callable
from loguru import logger

from app.agents.execution_agent import ExecutionAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.response_agent import ResponseAgent
from app.memory import ConversationMemory
from app.schemas.planner import (
    ExecutionPlan,
    ProgressEvent,
    ExecutionPolicy,
    TaskStatus,
)
from app.config import MODEL_NAME
from app.utils import build_task_summary


class CoordinatorAgent:

    def __init__(self):

        self.planner = PlannerAgent()

        self.executor = ExecutionAgent()

        self.responder = ResponseAgent()

        self.memory = ConversationMemory()

    def run(
        self,
        user_goal: str,
        on_progress: Callable[[ProgressEvent], None] = None,
        policy: ExecutionPolicy = ExecutionPolicy.FAIL_FAST,
    ) -> str:
        """
        Run the travel agent workflow.
        """

        # 1. Add user message and update the history summary
        self.memory.add_user_message(user_goal)
        self.memory.update_summary(self.planner.client, MODEL_NAME)

        context = self.memory.get_history_context(max_recent=5)

        # 2. Generate initial execution plan
        active_plan = self.planner.create_plan(
            user_goal=user_goal,
            prompt_type="planner",
            context=context,
        )

        replan_attempts = 0
        max_replan_attempts = 3

        # 3. Execution & Replanning Loop
        while True:
            executed_plan = self.executor.execute(
                active_plan,
                on_progress=on_progress,
                policy=policy,
            )

            # Check if there are any failed tasks
            failed_tasks = [
                t for t in executed_plan.tasks
                if t.status == TaskStatus.FAILED
            ]

            if not failed_tasks:
                logger.info("Execution plan completed successfully with all tasks completed (none failed).")
                active_plan = executed_plan
                break

            # Fast-abort on infrastructure failures (e.g. connection timed out, API rate limits)
            infra_failures = [t for t in failed_tasks if t.failure_type == "infrastructure"]
            if infra_failures:
                logger.error(
                    f"Execution failed due to transient infrastructure errors: "
                    f"{[t.error for t in infra_failures]}. Replanning aborted."
                )
                active_plan = executed_plan
                break

            if replan_attempts >= max_replan_attempts:
                logger.warning("Maximum replanning attempts reached. Ending execution.")
                active_plan = executed_plan
                break

            replan_attempts += 1
            logger.info(
                f"Replanning attempt {replan_attempts}/{max_replan_attempts} "
                f"triggered by task(s): {[t.description for t in failed_tasks]}."
            )

            # Build execution history of all tasks run so far to pass to the replanner
            execution_history = []
            for task in executed_plan.tasks:
                if task.status in (TaskStatus.COMPLETED, TaskStatus.EMPTY_RESULT, TaskStatus.FAILED):
                    execution_history.append(build_task_summary(task, full_context=True))

            max_existing_id = max((t.id for t in executed_plan.tasks), default=0)

            # Call planner agent with the replanner prompt
            context["execution_history"] = execution_history
            context["start_id"] = max_existing_id + 1

            new_plan = self.planner.create_plan(
                user_goal=user_goal,
                prompt_type="replanner",
                context=context,
                start_id=max_existing_id + 1,
            )

            finished_tasks = [
                t for t in executed_plan.tasks
                if t.status in (TaskStatus.COMPLETED, TaskStatus.EMPTY_RESULT)
            ]

            executed_plan.tasks = finished_tasks + new_plan.tasks
            active_plan = executed_plan

        # 4. Generate final friendly response
        response = self.responder.generate_response(
            user_goal=user_goal,
            execution_plan=active_plan,
        )

        # 5. Add assistant response to history
        self.memory.add_assistant_message(response)

        return response