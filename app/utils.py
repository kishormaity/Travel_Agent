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