from app.schemas.planner import (
    ExecutionPlan,
    PlannerResponse,
    Task,
)

from app.registry.tool_registry import (
    AVAILABLE_TOOLS,
    TOOLS,
)


class Planner:
    """
    Responsible for converting a validated PlannerResponse
    into an ExecutionPlan.
    """

    def __init__(self):

        self.required_arguments = self._build_required_arguments()

    def build_plan(
        self,
        goal: str,
        planner_response: PlannerResponse,
    ) -> ExecutionPlan:
        """
        Build an ExecutionPlan from a validated PlannerResponse.
        """

        execution_tasks = []

        for index, planner_task in enumerate(
            planner_response.tasks,
            start=1,
        ):

            self._validate_tool_name(
                planner_task.tool_name,
            )

            self._validate_required_arguments(
                planner_task.tool_name,
                planner_task.arguments,
            )

            execution_tasks.append(
                Task(
                    id=index,
                    description=planner_task.description,
                    tool_name=planner_task.tool_name,
                    arguments=planner_task.arguments,
                    depends_on=getattr(planner_task, "depends_on", []),
                    priority=getattr(planner_task, "priority", 1),
                )
            )

        return ExecutionPlan(
            goal=goal,
            tasks=execution_tasks,
        )

    def _validate_tool_name(
        self,
        tool_name: str,
    ) -> None:
        """
        Validate that the tool exists.
        """

        if tool_name not in AVAILABLE_TOOLS:

            raise ValueError(
                f"Unknown tool: '{tool_name}'."
            )

    def _validate_required_arguments(
        self,
        tool_name: str,
        arguments: dict,
    ) -> None:
        """
        Validate required tool arguments.
        """

        required = self.required_arguments.get(
            tool_name,
            [],
        )

        missing = [

            argument

            for argument in required

            if argument not in arguments

        ]

        if missing:

            raise ValueError(

                f"Tool '{tool_name}' is missing "

                f"required arguments: {missing}"

            )

    def _build_required_arguments(
        self,
    ) -> dict[str, list[str]]:
        """
        Extract required parameters from the tool registry.
        """

        mapping = {}

        for tool in TOOLS:

            function = tool["function"]

            mapping[
                function["name"]
            ] = function[
                "parameters"
            ].get(
                "required",
                [],
            )

        return mapping