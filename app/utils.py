import json
from pathlib import Path
from loguru import logger
from app.config import MODEL_NAME


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
    Truncate large dictionaries/lists in task results to save LLM tokens (mechanical fallback).
    """
    if result is None:
        return None
    if isinstance(result, list):
        return [truncate_result(item) for item in result[:5]]
    if isinstance(result, dict):
        return {k: truncate_result(v) for k, v in result.items()}
    if isinstance(result, str) and len(result) > 150:
        return result[:150] + "..."
    return result


def summarize_result_with_llm(
    result: any,
    llm_client: any = None,
    model_name: str = MODEL_NAME,
    max_length_threshold: int = 300,
) -> any:
    """
    Summarize large task results using an LLM to preserve key semantic details.
    Falls back to mechanical truncation if the result is small or if the LLM call fails.
    """
    if result is None:
        return None

    # Convert dict/list to string for size evaluation
    result_str = json.dumps(result, default=str) if isinstance(result, (dict, list)) else str(result)

    # Fast path: If result is small, no need to waste LLM tokens or latency
    if len(result_str) <= max_length_threshold:
        return result

    try:
        if llm_client is None:
            from app.llm.client import get_llm
            llm_client = get_llm()

        prompt = (
            "Summarize the following travel API result concisely for an AI planner. "
            "Highlight key facts like prices, dates, names, ratings, or warnings. "
            "Keep the summary under 100 words:\n\n"
            f"{result_str[:2500]}"
        )

        response = llm_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_completion_tokens=200,
        )
        return f"[LLM Summary]: {response.choices[0].message.content.strip()}"

    except Exception as e:
        logger.warning(f"LLM result summarization failed, falling back to truncation: {e}")
        return truncate_result(result)


def serialize_task_to_dict(task, full_context: bool = False, llm_client: any = None) -> dict:
    """
    Serialize a Pydantic Task object into a dictionary representation with hybrid LLM/truncated results.
    """
    summary = {
        "description": task.description,
        "tool_name": task.tool_name,
        "status": task.status.value,
        "result": summarize_result_with_llm(task.result, llm_client=llm_client),
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