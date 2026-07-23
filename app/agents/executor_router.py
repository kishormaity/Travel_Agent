from app.registry.tool_executor import ToolExecutor
from app.registry.llm_executor import LLMExecutor
from app.registry.tool_registry import AVAILABLE_TOOLS
from app.schemas.planner.task import Task

class ExecutorRouter:
    def __init__(self):
        self.tool_executor = ToolExecutor()
        self.llm_executor = LLMExecutor()
        
    def execute(self, task: Task, user_request: str = None) -> any:
        """Route the task execution based on registry configuration."""
        if task.tool_name in AVAILABLE_TOOLS and AVAILABLE_TOOLS[task.tool_name] is not None:
            return self.tool_executor.execute(task.tool_name, task.arguments)
        else:
            return self.llm_executor.execute(task.description, task.arguments, user_request=user_request)
