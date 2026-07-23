from loguru import logger

from app.registry.tool_registry import AVAILABLE_TOOLS


class ToolExecutor:
    """
    Executes tool calls requested by the LLM.
    """

    def execute(self, tool_name: str, arguments: dict):
        """
        Execute a tool with the provided arguments.

        Args:
            tool_name: Name of the tool selected by the LLM.
            arguments: Arguments required by the tool.

        Returns:
            Result returned by the tool.
        """

        logger.info(
            f"Executing tool='{tool_name}' with arguments={arguments}"
        )

        tool = AVAILABLE_TOOLS.get(tool_name)

        if tool is None:
            raise ValueError(
                f"Unknown tool: {tool_name}"
            )

        try:
            arguments = arguments or {}

            if hasattr(tool, "invoke"):
                result = tool.invoke(arguments)
            else:
                result = tool(**arguments)

            logger.info(
                f"{tool_name} returned {type(result).__name__}"
            )

            return result

        except Exception as error:

            logger.exception(
                f"Tool execution failed: {tool_name}"
            )

            raise error