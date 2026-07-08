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
        execution_plan = self.planner.create_plan(
            user_goal=user_goal,
            prompt_type="planner",
            context=context,
        )

        replan_attempts = 0
        max_replan_attempts = 3

        # 3. Execution & Replanning Loop
        while True:
            execution_plan = self.executor.execute(
                execution_plan,
                on_progress=on_progress,
                policy=policy,
            )

            # Check if there are any failed tasks
            failed_tasks = [
                t for t in execution_plan.tasks
                if t.status == TaskStatus.FAILED
            ]

            if not failed_tasks:
                logger.info("Execution plan completed successfully with all tasks completed (none failed).")
                break

            if replan_attempts >= max_replan_attempts:
                logger.warning("Maximum replanning attempts reached. Ending execution.")
                break

            replan_attempts += 1
            logger.info(
                f"Replanning attempt {replan_attempts}/{max_replan_attempts} "
                f"triggered by task(s): {[t.description for t in failed_tasks]}."
            )

            # Build execution history of all tasks run so far to pass to the replanner
            execution_history = []
            for task in execution_plan.tasks:
                if task.status in (TaskStatus.COMPLETED, TaskStatus.EMPTY_RESULT, TaskStatus.FAILED):
                    execution_history.append(build_task_summary(task, full_context=True))

            # Call planner agent with the replanner prompt
            context["execution_history"] = execution_history
            new_plan = self.planner.create_plan(
                user_goal=user_goal,
                prompt_type="replanner",
                context=context,
            )

            # Merge completed tasks with new plan tasks
            max_existing_id = max((t.id for t in execution_plan.tasks), default=0)

            finished_tasks = [
                t for t in execution_plan.tasks
                if t.status in (TaskStatus.COMPLETED, TaskStatus.EMPTY_RESULT)
            ]

            new_id_map = {}
            for idx, task in enumerate(new_plan.tasks, start=1):
                new_id_map[task.id] = max_existing_id + idx

            mapped_new_tasks = []
            for idx, task in enumerate(new_plan.tasks, start=1):
                mapped_id = new_id_map[task.id]
                mapped_deps = []
                for dep_id in task.depends_on:
                    if dep_id in new_id_map:
                        mapped_deps.append(new_id_map[dep_id])
                    else:
                        # Referencing a completed task from the history
                        completed_dep = next((t for t in finished_tasks if t.id == dep_id), None)
                        if completed_dep:
                            mapped_deps.append(dep_id)

                task.id = mapped_id
                task.depends_on = mapped_deps
                task.status = TaskStatus.PENDING
                task.result = None
                task.error = None
                task.started_at = None
                task.finished_at = None
                task.execution_time = None
                task.worker_id = None
                mapped_new_tasks.append(task)

            execution_plan.tasks = finished_tasks + mapped_new_tasks

        # 4. Generate final friendly response
        response = self.responder.generate_response(
            user_goal=user_goal,
            execution_plan=execution_plan,
        )

        # 5. Add assistant response to history
        self.memory.add_assistant_message(response)

        return response