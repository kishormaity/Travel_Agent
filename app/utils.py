import json
from pathlib import Path
from loguru import logger


def setup_logger():
    """
    Configure the application logger.
    """
    logger.remove()

    logger.add(
        "travel_agent.log",
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        enqueue=True,
    )

    logger.add(
        sink=lambda msg: print(msg, end=""),
        level="INFO",
    )

    return logger


def save_json(file_path: str, data: dict):
    """
    Save a dictionary as a JSON file.
    """
    path = Path(file_path)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def load_json(file_path: str):
    """
    Load data from a JSON file.
    """
    path = Path(file_path)

    if not path.exists():
        return None

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def print_header(title: str):
    """
    Print a formatted header in the terminal.
    """
    print("\n" + "=" * 60)
    print(title.center(60))
    print("=" * 60)


def print_success(message: str):
    print(f"✅ {message}")


def print_error(message: str):
    print(f"❌ {message}")


def print_info(message: str):
    print(f"ℹ️ {message}")


def truncate_result(result: any) -> any:
    """
    Truncate large dictionaries/lists in task results to save LLM tokens.
    """
    if result is None:
        return None
    if isinstance(result, list):
        if not result:
            return []
        max_items = 5
        truncated_list = [truncate_result(item) for item in result[:max_items]]
        if len(result) > max_items:
            truncated_list.append(f"... and {len(result) - max_items} more items")
        return truncated_list
    if isinstance(result, dict):
        truncated = {}
        for k, v in result.items():
            if k == "instructions" and isinstance(v, list):
                truncated[k] = f"[{len(v)} instruction steps]"
            else:
                truncated[k] = truncate_result(v)
        return truncated
    if isinstance(result, str) and len(result) > 150:
        return result[:150] + "..."
    return result


def build_task_summary(task, full_context: bool = False) -> dict:
    """
    Build a dictionary representation of a task with truncated results.
    """
    summary = {
        "description": task.description,
        "tool_name": task.tool_name,
        "status": task.status.value,
        "result": truncate_result(task.result),
        "error": task.error,
    }
    if full_context:
        summary.update({
            "task_id": task.id,
            "arguments": task.arguments,
            "depends_on": task.depends_on,
            "priority": task.priority,
        })
    return summary